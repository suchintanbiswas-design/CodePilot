import re
from typing import Any, Dict, List, Set


class JavaSemanticAnalyzer:
    """
    Deterministic Java-specific semantic analysis.
    Uses whole-source symbol tracking to detect:
      - equals() overload vs override + missing hashCode()
      - String reference comparison (== / !=)
      - Floating-point usage for financial/currency values
    """

    # Variable names that strongly suggest financial/currency usage
    _FINANCIAL_NAMES = frozenset({
        "balance", "amount", "price", "cost", "total", "payment",
        "rate", "salary", "income", "revenue", "tax", "fee", "charge",
        "deposit", "withdrawal", "interest", "premium", "discount",
        "subtotal", "grandtotal", "wage", "profit", "loss", "debt",
        "credit", "debit", "fund", "budget", "expense", "money",
        "cash", "commission", "tip", "refund",
    })

    # Class names that suggest financial context
    _FINANCIAL_CLASS_NAMES = frozenset({
        "account", "bank", "payment", "invoice", "transaction",
        "wallet", "ledger", "finance", "billing", "order",
        "cart", "checkout", "currency", "money",
    })

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        lines = code.split("\n")

        # ── Whole-source discovery ────────────────────────────────────
        classes_info = self._discover_classes(lines)
        string_vars = self._discover_string_variables(lines)
        string_getters = self._discover_string_getters(lines)
        is_financial_context = self._detect_financial_context(lines)

        # ── Rule 1: equals() overload + hashCode() contract ──────────
        issues.extend(self._check_equals_contract(lines, classes_info))

        # ── Rule 2: String reference comparison ──────────────────────
        issues.extend(
            self._check_string_reference_comparison(
                lines, string_vars, string_getters
            )
        )

        # ── Rule 3: Floating-point currency ──────────────────────────
        issues.extend(
            self._check_floating_point_currency(lines, is_financial_context)
        )

        return issues

    # ── Discovery helpers ─────────────────────────────────────────────

    def _discover_classes(
        self, lines: list[str]
    ) -> dict[str, dict]:
        """Map class names to info about their equals/hashCode methods."""
        classes: dict[str, dict] = {}
        current_class = None

        for line in lines:
            clean = re.sub(r'//.*', '', line)

            m_class = re.search(
                r'\bclass\s+(\w+)', clean
            )
            if m_class:
                current_class = m_class.group(1)
                if current_class not in classes:
                    classes[current_class] = {
                        "has_equals_object": False,
                        "has_equals_specific": False,
                        "equals_specific_type": None,
                        "equals_specific_line": 0,
                        "has_hashcode": False,
                        "has_override_annotation_before_equals": False,
                    }

            if current_class and current_class in classes:
                info = classes[current_class]

                # public boolean equals(Object ...)
                if re.search(
                    r'\bboolean\s+equals\s*\(\s*Object\s+', clean
                ):
                    info["has_equals_object"] = True

                # public boolean equals(SpecificType ...)
                m_eq = re.search(
                    r'\bboolean\s+equals\s*\(\s*(\w+)\s+', clean
                )
                if m_eq:
                    param_type = m_eq.group(1)
                    if param_type != "Object":
                        info["has_equals_specific"] = True
                        info["equals_specific_type"] = param_type
                        info["equals_specific_line"] = lines.index(line) + 1

                # hashCode
                if re.search(r'\bint\s+hashCode\s*\(', clean):
                    info["has_hashcode"] = True

        return classes

    def _discover_string_variables(self, lines: list[str]) -> set[str]:
        """Find variable names explicitly typed as String."""
        string_vars: set[str] = set()
        for line in lines:
            clean = re.sub(r'//.*', '', line)
            # String varName   or   String varName =
            for m in re.finditer(
                r'\bString\s+(\w+)\s*[;=,)]', clean
            ):
                string_vars.add(m.group(1))
            # Method parameters: (String paramName, ...)
            for m in re.finditer(
                r'String\s+(\w+)', clean
            ):
                string_vars.add(m.group(1))
        return string_vars

    def _discover_string_getters(self, lines: list[str]) -> set[str]:
        """Find method names that return String."""
        getters: set[str] = set()
        for line in lines:
            clean = re.sub(r'//.*', '', line)
            # public String getXxx(...)  or  String getXxx(...)
            m = re.search(
                r'\bString\s+(\w+)\s*\(', clean
            )
            if m:
                name = m.group(1)
                # Exclude constructors and common non-getter names
                if name[0].islower():
                    getters.add(name)
        return getters

    def _detect_financial_context(self, lines: list[str]) -> bool:
        """Return True if the source file has financial/currency context."""
        full_text = "\n".join(lines).lower()
        for cls_name in self._FINANCIAL_CLASS_NAMES:
            if cls_name in full_text:
                return True
        return False

    # ── Rule implementations ──────────────────────────────────────────

    def _check_equals_contract(
        self,
        lines: list[str],
        classes_info: dict[str, dict],
    ) -> List[Dict[str, Any]]:
        """Rule 1: equals(SpecificType) without equals(Object), missing hashCode."""
        issues: List[Dict[str, Any]] = []
        for cls_name, info in classes_info.items():
            if info["has_equals_specific"] and not info["has_equals_object"]:
                spec_type = info["equals_specific_type"]
                line_num = info["equals_specific_line"]
                parts = []
                parts.append(
                    f"equals({spec_type}) overloads rather than overrides "
                    f"Object.equals(Object)"
                )
                if not info["has_hashcode"]:
                    parts.append("hashCode() is missing")
                desc = ", and ".join(parts) + "."
                issues.append({
                    "severity": "High",
                    "category": "Correctness",
                    "line_number": line_num,
                    "description": (
                        f"In class '{cls_name}': {desc} "
                        f"Java collection APIs (List.contains, HashSet, HashMap) "
                        f"will not use the intended equality semantics."
                    ),
                    "confidence": "High",
                    "rule_type": "Correctness",
                })
        return issues

    def _check_string_reference_comparison(
        self,
        lines: list[str],
        string_vars: set[str],
        string_getters: set[str],
    ) -> List[Dict[str, Any]]:
        """Rule 2: String == String or String != String."""
        issues: List[Dict[str, Any]] = []

        for i, line in enumerate(lines):
            line_num = i + 1
            clean = re.sub(r'//.*', '', line)

            # Skip lines that are clearly not comparisons
            if '==' not in clean and '!=' not in clean:
                continue

            # Match patterns: expr == expr  or  expr != expr
            for m in re.finditer(
                r'(\b[\w.()]+)\s*(==|!=)\s*([\w.()]+\b)', clean
            ):
                lhs = m.group(1).strip()
                op = m.group(2)
                rhs = m.group(3).strip()

                if self._is_string_expr(lhs, string_vars, string_getters) and \
                   self._is_string_expr(rhs, string_vars, string_getters):
                    issues.append({
                        "severity": "High",
                        "category": "Correctness",
                        "line_number": line_num,
                        "description": (
                            f"String comparison using '{op}' compares object "
                            f"references, not contents. Use .equals() or "
                            f".equalsIgnoreCase() instead."
                        ),
                        "confidence": "High",
                        "rule_type": "Correctness",
                    })
                    break  # One finding per line is enough

        return issues

    def _check_floating_point_currency(
        self,
        lines: list[str],
        is_financial_context: bool,
    ) -> List[Dict[str, Any]]:
        """Rule 3: double/float for financial values."""
        issues: List[Dict[str, Any]] = []
        reported_lines: set[int] = set()

        for i, line in enumerate(lines):
            line_num = i + 1
            clean = re.sub(r'//.*', '', line)

            # Skip lines using BigDecimal (safe pattern)
            if "BigDecimal" in clean:
                continue

            # Check field/variable declarations: double balance; or double balance = ...
            # Exclude method signatures (double getBalance()) and method params
            m_decl = re.search(
                r'\b(double|float)\s+(\w+)\s*[;=]', clean
            )
            if m_decl and line_num not in reported_lines:
                var_type = m_decl.group(1)
                var_name = m_decl.group(2)
                # Skip if this looks like a method: double getBalance() {
                if re.search(r'\b(double|float)\s+\w+\s*\(', clean):
                    pass
                elif self._is_financial_name(var_name):
                    issues.append({
                        "severity": "Medium",
                        "category": "Correctness",
                        "line_number": line_num,
                        "description": (
                            f"'{var_type} {var_name}' uses floating-point "
                            f"for a financial/currency value. Floating-point "
                            f"arithmetic causes precision errors in monetary "
                            f"calculations. Use BigDecimal or integer minor "
                            f"units (e.g. cents) instead."
                        ),
                        "confidence": "High",
                        "rule_type": "Correctness",
                    })
                    reported_lines.add(line_num)

            # Check floating-point arithmetic with financial variable names
            if is_financial_context and line_num not in reported_lines:
                m_calc = re.search(
                    r'\b(double|float)\s+(\w+)\s*=\s*[\d.]+\s*[+\-*/]\s*[\d.]+',
                    clean,
                )
                if m_calc:
                    var_name = m_calc.group(2)
                    var_type = m_calc.group(1)
                    if self._is_financial_name(var_name):
                        issues.append({
                            "severity": "Medium",
                            "category": "Correctness",
                            "line_number": line_num,
                            "description": (
                                f"'{var_type} {var_name}' uses floating-point "
                                f"arithmetic for a financial calculation. "
                                f"Floating-point causes precision errors "
                                f"(e.g. 0.1 + 0.2 != 0.3). Use BigDecimal "
                                f"or integer minor units instead."
                            ),
                            "confidence": "High",
                            "rule_type": "Correctness",
                        })
                        reported_lines.add(line_num)

        return issues

    # ── Private helpers ───────────────────────────────────────────────

    def _is_string_expr(
        self,
        expr: str,
        string_vars: set[str],
        string_getters: set[str],
    ) -> bool:
        """Heuristically determine if an expression is a String."""
        # Direct string variable
        bare = expr.strip()
        if bare in string_vars:
            return True

        # String literal
        if bare.startswith('"') and bare.endswith('"'):
            return True

        # Method call on known string getter: obj.getXxx()
        m_call = re.match(r'(\w+)\.(\w+)\(\)', bare)
        if m_call:
            method = m_call.group(2)
            if method in string_getters:
                return True
            # Common String-returning methods
            if method in {
                "toString", "trim", "toLowerCase", "toUpperCase",
                "substring", "replace", "strip", "intern",
                "getName", "getId", "getType", "getCode",
                "getValue", "getTitle", "getLabel",
            }:
                return True
            # Getter patterns commonly returning String
            if re.match(
                r'get\w*(?:Name|Number|Id|Code|Type|Key|Label|'
                r'Title|Description|Address|Email|Password|Text|'
                r'Status|Token|Num)$',
                method,
            ):
                return True

        # getter-style call without explicit receiver: getXxx()
        m_getter = re.match(r'(\w+)\(\)', bare)
        if m_getter and m_getter.group(1) in string_getters:
            return True

        # Variable names commonly holding strings
        name_lower = bare.split(".")[-1].lower()
        if name_lower in {
            "name", "username", "password", "email", "address",
            "title", "description", "message", "text", "label",
            "accountnumber", "accountnum", "account_number",
            "id", "code", "type", "status",
        }:
            return True

        return False

    def _is_financial_name(self, var_name: str) -> bool:
        """Check if a variable name indicates financial/currency usage."""
        name_lower = var_name.lower()
        # Check exact match or suffix/prefix match
        for fn in self._FINANCIAL_NAMES:
            if fn == name_lower:
                return True
            if name_lower.endswith(fn) or name_lower.startswith(fn):
                return True
        return False

    def _is_likely_financial_var(self, var_name: str, line: str) -> bool:
        """In financial context, check if a var is likely financial."""
        return self._is_financial_name(var_name)
