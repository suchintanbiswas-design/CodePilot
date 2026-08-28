"""
Deterministic Python Semantic Analyzer for CodePilot.

Uses Python's built-in `ast` module for whole-source semantic analysis.
Detects correctness and security defects that regex-based rules cannot catch.
"""
from __future__ import annotations

import ast
from typing import Any, Dict, List

# Mutable constructor names that produce mutable objects when called with no args
_MUTABLE_CONSTRUCTORS = frozenset({
    "list", "dict", "set", "bytearray", "OrderedDict",
})


class PythonSemanticAnalyzer:
    """AST-based semantic analyzer for Python source code."""

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        """Analyze Python source and return a list of issues."""
        try:
            tree = ast.parse(code)
        except SyntaxError:
            # Syntax errors are handled by SyntaxValidator; skip here
            return []

        issues: List[Dict[str, Any]] = []
        self._walk(tree, issues)
        return issues

    # ── AST walk ──────────────────────────────────────────────────────

    def _walk(self, tree: ast.AST, issues: List[Dict[str, Any]]) -> None:
        """Walk the entire AST and dispatch to rule checkers."""
        for node in ast.walk(tree):
            # Rule: PY_MUTABLE_DEFAULT_ARG
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self._check_mutable_defaults(node, issues)

            # Rule: PY_DANGEROUS_EVAL & PY_OS_SYSTEM_INJECTION
            if isinstance(node, ast.Call):
                self._check_dangerous_eval(node, issues)
                self._check_os_system_injection(node, issues)

            # Rule: PY_BROAD_EXCEPTION
            if isinstance(node, ast.ExceptHandler):
                self._check_broad_exception(node, issues)

            # Rule: PY_IS_LITERAL_COMPARISON
            if isinstance(node, ast.Compare):
                self._check_is_literal_comparison(node, issues)

            # Rule: PY_OS_SYSTEM_INJECTION
            # (handled within ast.Call)

    # ── Rule: PY_MUTABLE_DEFAULT_ARG ─────────────────────────────────

    def _check_mutable_defaults(
        self,
        node: ast.FunctionDef | ast.AsyncFunctionDef,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect mutable default arguments in function definitions."""
        func_name = node.name

        # Check positional defaults
        for default in node.args.defaults:
            self._check_single_default(default, func_name, issues)

        # Check keyword-only defaults
        for default in node.args.kw_defaults:
            if default is not None:
                self._check_single_default(default, func_name, issues)

    def _check_single_default(
        self,
        default: ast.expr,
        func_name: str,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Check if a single default value is a mutable literal or constructor."""
        mutable_type = self._get_mutable_type(default)
        if mutable_type:
            issues.append(self._make_issue(
                line_number=default.lineno,
                severity="High",
                description=(
                    f"Mutable default argument in function '{func_name}': "
                    f"default value {mutable_type} is shared across all calls. "
                    f"Use None as sentinel and create the mutable inside the function body."
                ),
                rule_name="PY_MUTABLE_DEFAULT_ARG",
                rule_type="Bugs",
            ))

    @staticmethod
    def _get_mutable_type(node: ast.expr) -> str | None:
        """Return a human-readable type string if node is a mutable default, else None."""
        # Literal list: []
        if isinstance(node, ast.List):
            return "[]"
        # Literal dict: {}
        if isinstance(node, ast.Dict):
            return "{}"
        # Literal set: {1, 2}  (ast.Set)
        if isinstance(node, ast.Set):
            return "set literal"
        # Constructor calls: list(), dict(), set(), bytearray(), OrderedDict()
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name) and func.id in _MUTABLE_CONSTRUCTORS:
                return f"{func.id}()"
            # Handle OrderedDict imported as collections.OrderedDict
            if isinstance(func, ast.Attribute) and func.attr in _MUTABLE_CONSTRUCTORS:
                return f"{func.attr}()"
        return None

    # ── Rule: PY_DANGEROUS_EVAL ──────────────────────────────────────

    def _check_dangerous_eval(
        self,
        node: ast.Call,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect calls to eval() or exec() with non-constant arguments."""
        func = node.func
        if not isinstance(func, ast.Name):
            return
        if func.id not in ("eval", "exec"):
            return

        # Suppress constant-string calls: eval("1 + 2"), exec("print('hi')")
        if node.args and len(node.args) >= 1:
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                return

        func_name = func.id
        if func_name == "eval":
            desc = (
                "Dangerous eval() call: dynamically evaluating input can execute "
                "arbitrary Python code. Use ast.literal_eval() for safe evaluation "
                "of literal expressions, or parse input explicitly."
            )
        else:
            desc = (
                "Dangerous exec() call: dynamically executing code can run "
                "arbitrary Python statements. Avoid exec() and use explicit "
                "logic or safe alternatives."
            )

        issues.append(self._make_issue(
            line_number=node.lineno,
            severity="Critical",
            description=desc,
            rule_name=f"PY_DANGEROUS_{func_name.upper()}",
            rule_type="Security",
        ))

    # ── Rule: PY_OS_SYSTEM_INJECTION ─────────────────────────────────

    def _check_os_system_injection(
        self,
        node: ast.Call,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect dangerous OS command execution with user-controlled input."""
        func = node.func
        if not isinstance(func, ast.Attribute):
            return
        if not isinstance(func.value, ast.Name):
            return

        module_name = func.value.id
        method_name = func.attr

        is_vulnerable = False

        if module_name == "os" and method_name in ("system", "popen"):
            is_vulnerable = True
        elif module_name == "subprocess" and method_name in ("run", "call", "Popen"):
            # Check for shell=True
            has_shell_true = False
            for kw in node.keywords:
                if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    has_shell_true = True
                    break
            if has_shell_true:
                is_vulnerable = True

        if not is_vulnerable:
            return

        # Find the command argument (usually args[0] or kwarg 'args'/'cmd')
        command_arg = None
        if node.args:
            command_arg = node.args[0]
        else:
            for kw in node.keywords:
                if kw.arg in ("args", "cmd"):
                    command_arg = kw.value
                    break
        
        if not command_arg:
            return

        # Suppress if the command is a static literal (e.g. string or list of static elements).
        # We only want to flag dynamic commands (f-strings, concatenation, variable references)
        # to prevent noise on completely hardcoded safe/intended calls.
        if isinstance(command_arg, ast.Constant):
            return

        # For lists, if all elements are constants, we also suppress.
        if isinstance(command_arg, ast.List):
            if all(isinstance(elt, ast.Constant) for elt in command_arg.elts):
                return

        issues.append(self._make_issue(
            line_number=node.lineno,
            severity="Critical",
            description=(
                f"Dangerous OS command execution: using '{module_name}.{method_name}' "
                f"with dynamic arguments can lead to command injection vulnerabilities. "
                f"Use the 'subprocess' module with a list of arguments and 'shell=False'."
            ),
            rule_name="PY_OS_SYSTEM_INJECTION",
            rule_type="Security",
        ))

    # ── Rule: PY_BROAD_EXCEPTION ─────────────────────────────────────

    def _check_broad_exception(
        self,
        node: ast.ExceptHandler,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect broadly catching Exception or BaseException without re-raising."""
        if node.type is None:
            # Bare except: is already handled by the CATCH_ALL_PY regex rule
            return

        is_broad = False
        exception_name = ""

        # Check if catching a single exception by name
        if isinstance(node.type, ast.Name):
            if node.type.id in ("Exception", "BaseException"):
                is_broad = True
                exception_name = node.type.id

        # Check if catching a tuple of exceptions
        elif isinstance(node.type, ast.Tuple):
            for elt in node.type.elts:
                if isinstance(elt, ast.Name) and elt.id in ("Exception", "BaseException"):
                    is_broad = True
                    exception_name = elt.id
                    break

        if not is_broad:
            return

        # Check if the handler explicitly re-raises
        for child in ast.walk(node):
            if isinstance(child, ast.Raise):
                # An explicit re-raise found; suppress the finding
                return

        issues.append(self._make_issue(
            line_number=node.lineno,
            severity="High",
            description=(
                f"Catch-all exception handling: catching '{exception_name}' broadly "
                f"masks programming errors and runtime issues. If necessary, explicitly "
                f"re-raise using 'raise' or catch more specific exception types."
            ),
            rule_name="PY_BROAD_EXCEPTION",
            rule_type="Bugs",
        ))

    # ── Rule: PY_IS_LITERAL_COMPARISON ───────────────────────────────

    def _check_is_literal_comparison(
        self,
        node: ast.Compare,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect identity comparison (is / is not) against non-singleton literals."""
        # AST represents comparisons like `x is 0` as:
        # ast.Compare(left=ast.Name(id='x'), ops=[ast.Is()], comparators=[ast.Constant(value=0)])
        
        for op, comparator in zip(node.ops, node.comparators):
            if not isinstance(op, (ast.Is, ast.IsNot)):
                continue

            literal_type = None

            # Check for primitives: int, str, float, etc. (excluding None, True, False)
            if isinstance(comparator, ast.Constant):
                # None, True, False are safe singletons to compare with 'is'
                # Use identity check ('is') since 0 == False in Python
                if comparator.value is not None and comparator.value is not True and comparator.value is not False:
                    literal_type = repr(comparator.value)
            
            # Check for collection literals: [], {}, ()
            elif isinstance(comparator, ast.List):
                literal_type = "[]"
            elif isinstance(comparator, ast.Dict):
                literal_type = "{}"
            elif isinstance(comparator, ast.Tuple):
                literal_type = "()"
            elif isinstance(comparator, ast.Set):
                literal_type = "set literal"

            if literal_type is not None:
                op_name = "is not" if isinstance(op, ast.IsNot) else "is"
                issues.append(self._make_issue(
                    line_number=node.lineno,
                    severity="Medium",
                    description=(
                        f"Identity comparison with literal: using '{op_name}' with {literal_type}. "
                        f"Identity checks compare memory addresses, not values. "
                        f"Use '==' or '!=' for equality comparison."
                    ),
                    rule_name="PY_IS_LITERAL_COMPARISON",
                    rule_type="Bugs",
                ))

    # ── Helpers ───────────────────────────────────────────────────────

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
