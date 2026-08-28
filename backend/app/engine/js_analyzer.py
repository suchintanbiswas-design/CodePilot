"""
Deterministic JavaScript Semantic Analyzer for CodePilot.

Uses the existing esprima parser to produce an ESTree-compliant AST,
then walks it to detect correctness and security defects that regex
rules cannot catch.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional


class JavaScriptSemanticAnalyzer:
    """AST-based semantic analyzer for JavaScript source code."""

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        """Analyze JavaScript source and return a list of issues."""
        try:
            import esprima
        except ImportError:
            return []

        try:
            tree = esprima.parseScript(code, {"loc": True})
        except Exception:
            # Syntax errors are handled by SyntaxValidator; skip here
            return []

        issues: List[Dict[str, Any]] = []
        tree_dict = tree.toDict()
        self._walk(tree_dict, issues)
        return issues

    # ── AST walk ──────────────────────────────────────────────────────

    def _walk(self, node: Any, issues: List[Dict[str, Any]]) -> None:
        """Recursively walk the ESTree dict and dispatch to rule checkers."""
        if isinstance(node, dict):
            node_type = node.get("type")

            # Rule: JS_LOOSE_EQUALITY
            if node_type == "BinaryExpression":
                self._check_loose_equality(node, issues)

            # Rule: JS_DANGEROUS_EVAL — eval(...)
            # Rule: JS_DOCUMENT_WRITE — document.write(...)
            if node_type == "CallExpression":
                self._check_dangerous_eval(node, issues)
                self._check_document_write(node, issues)

            # Rule: JS_DANGEROUS_EVAL — new Function(...)
            if node_type == "NewExpression":
                self._check_dangerous_new_function(node, issues)

            # Rule: JS_INNERHTML_XSS — element.innerHTML = ...
            if node_type == "AssignmentExpression":
                self._check_innerhtml_xss(node, issues)

            # Rule: JS_SWITCH_FALLTHROUGH
            if node_type == "SwitchStatement":
                self._check_switch_fallthrough(node, issues)

            # Recurse into all child values
            for value in node.values():
                self._walk(value, issues)

        elif isinstance(node, list):
            for item in node:
                self._walk(item, issues)

    # ── Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _get_line(node: Dict[str, Any]) -> int:
        """Extract line number from an ESTree node."""
        loc = node.get("loc")
        if loc and isinstance(loc, dict):
            start = loc.get("start")
            if start and isinstance(start, dict):
                return start.get("line", 1)
        return 1

    @staticmethod
    def _is_null_literal(node: Dict[str, Any]) -> bool:
        """Check if a node is the literal `null`."""
        return (
            node.get("type") == "Literal"
            and node.get("raw") == "null"
        )

    @staticmethod
    def _is_constant_string(node: Dict[str, Any]) -> bool:
        """Check if a node is a constant string literal."""
        if node.get("type") == "Literal":
            value = node.get("value")
            return isinstance(value, str)
        if node.get("type") == "TemplateLiteral":
            # Template literal is constant only if it has no expressions
            exprs = node.get("expressions", [])
            return len(exprs) == 0
        return False

    @classmethod
    def _is_terminal(cls, stmt: Dict[str, Any]) -> bool:
        """Check if a statement is terminal (break, return, throw, continue)."""
        if not stmt or not isinstance(stmt, dict):
            return False
        t = stmt.get("type")
        if t in ("BreakStatement", "ReturnStatement", "ThrowStatement", "ContinueStatement"):
            return True
        if t == "BlockStatement":
            body = stmt.get("body", [])
            if body and isinstance(body, list):
                return cls._is_terminal(body[-1])
        return False

    @staticmethod
    def _make_issue(
        line_number: int,
        severity: str,
        description: str,
        rule_name: str,
        rule_type: str,
    ) -> Dict[str, Any]:
        return {
            "severity": severity,
            "line_number": line_number,
            "description": description,
            "rule_type": rule_type,
            "rule_name": rule_name,
        }

    # ── Rule: JS_LOOSE_EQUALITY ──────────────────────────────────────

    def _check_loose_equality(
        self,
        node: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect == and != operators, recommending === and !==."""
        operator = node.get("operator")
        if operator not in ("==", "!="):
            return

        left = node.get("left", {})
        right = node.get("right", {})

        # Suppress idiomatic `x == null` / `x != null`
        # This intentionally covers both null and undefined
        if self._is_null_literal(left) or self._is_null_literal(right):
            return

        strict_op = "===" if operator == "==" else "!=="
        issues.append(self._make_issue(
            line_number=self._get_line(node),
            severity="Medium",
            description=(
                f"Loose equality operator '{operator}' performs type coercion "
                f"which can cause unexpected results. "
                f"Use strict equality '{strict_op}' instead."
            ),
            rule_name="JS_LOOSE_EQUALITY",
            rule_type="Bugs",
        ))

    # ── Rule: JS_DANGEROUS_EVAL ──────────────────────────────────────

    def _check_dangerous_eval(
        self,
        node: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect eval() calls with non-constant arguments."""
        callee = node.get("callee", {})

        # Only match direct `eval(...)` calls
        if callee.get("type") != "Identifier" or callee.get("name") != "eval":
            return

        args = node.get("arguments", [])

        # Suppress constant-string argument: eval("1 + 1")
        if args and self._is_constant_string(args[0]):
            return

        issues.append(self._make_issue(
            line_number=self._get_line(node),
            severity="Critical",
            description=(
                "Dangerous eval() call: dynamically evaluating code can execute "
                "arbitrary JavaScript and exposes the application to code injection "
                "attacks. Use JSON.parse() for data, or explicit logic instead."
            ),
            rule_name="JS_DANGEROUS_EVAL",
            rule_type="Security",
        ))

    def _check_dangerous_new_function(
        self,
        node: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect new Function() with non-constant body argument."""
        callee = node.get("callee", {})

        # Only match `new Function(...)`
        if callee.get("type") != "Identifier" or callee.get("name") != "Function":
            return

        args = node.get("arguments", [])
        if not args:
            return

        # The last argument is the function body
        body_arg = args[-1]

        # Suppress constant-string body: new Function("x", "return x + 1")
        if self._is_constant_string(body_arg):
            return

        issues.append(self._make_issue(
            line_number=self._get_line(node),
            severity="Critical",
            description=(
                "Dangerous new Function() call: dynamically constructing a function "
                "from a string can execute arbitrary JavaScript code. "
                "Use explicit function definitions or safe alternatives."
            ),
            rule_name="JS_DANGEROUS_EVAL",
            rule_type="Security",
        ))

    # ── Rule: JS_INNERHTML_XSS ───────────────────────────────────────

    def _check_innerhtml_xss(
        self,
        node: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect assignment to innerHTML/outerHTML with dynamic content."""
        left = node.get("left", {})
        right = node.get("right", {})

        # Must be a MemberExpression on the left
        if left.get("type") != "MemberExpression":
            return

        prop = left.get("property", {})
        prop_name = prop.get("name", "") if prop.get("type") == "Identifier" else ""

        if prop_name not in ("innerHTML", "outerHTML"):
            return

        # Suppress constant-string assignments: element.innerHTML = ""
        if self._is_constant_string(right):
            return

        issues.append(self._make_issue(
            line_number=self._get_line(node),
            severity="High",
            description=(
                f"Unsafe assignment to '{prop_name}': setting {prop_name} with "
                f"dynamic content can lead to Cross-Site Scripting (XSS) "
                f"vulnerabilities. Use 'textContent' for plain text, or sanitize "
                f"HTML content before insertion."
            ),
            rule_name="JS_INNERHTML_XSS",
            rule_type="Security",
        ))

    # ── Rule: JS_DOCUMENT_WRITE ──────────────────────────────────────

    def _check_document_write(
        self,
        node: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect document.write() and document.writeln() calls."""
        callee = node.get("callee", {})

        # Must be a MemberExpression: document.write(...)
        if callee.get("type") != "MemberExpression":
            return

        obj = callee.get("object", {})
        prop = callee.get("property", {})

        # Only match `document.write` / `document.writeln`
        if obj.get("type") != "Identifier" or obj.get("name") != "document":
            return

        method_name = prop.get("name", "") if prop.get("type") == "Identifier" else ""
        if method_name not in ("write", "writeln"):
            return

        issues.append(self._make_issue(
            line_number=self._get_line(node),
            severity="High",
            description=(
                f"Insecure document.{method_name}() call: document.write() "
                f"can introduce XSS vulnerabilities and interferes with "
                f"document parsing. Use DOM APIs such as 'createElement' "
                f"and 'appendChild', or set 'textContent'/'innerHTML' safely."
            ),
            rule_name="JS_DOCUMENT_WRITE",
            rule_type="Security",
        ))

    # ── Rule: JS_SWITCH_FALLTHROUGH ──────────────────────────────────

    def _check_switch_fallthrough(
        self,
        node: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect a non-empty switch case that falls through to the next."""
        cases = node.get("cases", [])
        if not cases or not isinstance(cases, list):
            return

        # Iterate all cases except the last one (which has nothing to fall through to)
        for i in range(len(cases) - 1):
            current_case = cases[i]
            if not isinstance(current_case, dict) or current_case.get("type") != "SwitchCase":
                continue

            consequent = current_case.get("consequent", [])
            # Empty cases (intentional grouping) are safe
            if not consequent or not isinstance(consequent, list):
                continue

            last_stmt = consequent[-1]
            if not self._is_terminal(last_stmt):
                test_node = current_case.get("test")
                case_label = "case" if test_node else "default case"

                issues.append(self._make_issue(
                    line_number=self._get_line(current_case),
                    severity="Medium",
                    description=(
                        f"Switch fallthrough: this {case_label} falls through to the next "
                        "case without a terminal statement (break, return, throw, continue). "
                        "If intentional, refactor to make it explicit; otherwise, add a break statement."
                    ),
                    rule_name="JS_SWITCH_FALLTHROUGH",
                    rule_type="Bugs",
                ))
