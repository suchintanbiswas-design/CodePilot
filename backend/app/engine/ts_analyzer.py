"""
Deterministic TypeScript Semantic Analyzer for CodePilot.

Operates on raw TypeScript source code with lexical masking for strings 
and comments to accurately detect semantic rules without relying on 
an external AST, due to the esprima parser stripping TS types.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List


class TypeScriptSemanticAnalyzer:
    """Regex-based deterministic semantic analyzer for TypeScript."""

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        """Analyze TypeScript source and return a list of issues."""
        issues: List[Dict[str, Any]] = []
        
        # Mask strings and comments so regexes don't flag them
        masked_code = self._mask_code(code)

        # Phase 1 rules
        self._check_unsafe_any_declaration(masked_code, issues)
        self._check_explicit_any_cast(masked_code, issues)
        
        # Phase 2 rules
        self._check_non_null_assertion(masked_code, issues)
        self._check_banned_types(masked_code, issues)

        # Phase 3 rules
        self._check_compiler_ignore(code, issues)

        return issues

    def _mask_code(self, code: str) -> str:
        """
        Replaces contents of comments and strings with spaces to prevent false positives.
        Preserves newlines so line numbers remain accurate.
        """
        result = list(code)
        i = 0
        n = len(code)
        state = 'NORMAL'

        while i < n:
            c = code[i]
            
            if state == 'NORMAL':
                if c == '/' and i + 1 < n and code[i+1] == '/':
                    state = 'IN_SL_COMMENT'
                    result[i] = ' '
                    result[i+1] = ' '
                    i += 2
                    continue
                elif c == '/' and i + 1 < n and code[i+1] == '*':
                    state = 'IN_ML_COMMENT'
                    result[i] = ' '
                    result[i+1] = ' '
                    i += 2
                    continue
                elif c == '"':
                    state = 'IN_STRING'
                    result[i] = ' '
                    i += 1
                    continue
                elif c == "'":
                    state = 'IN_SQ_STRING'
                    result[i] = ' '
                    i += 1
                    continue
                elif c == '`':
                    state = 'IN_TICK_STRING'
                    result[i] = ' '
                    i += 1
                    continue
            
            elif state == 'IN_SL_COMMENT':
                if c == '\n':
                    state = 'NORMAL'
                else:
                    result[i] = ' '
            elif state == 'IN_ML_COMMENT':
                if c == '*' and i + 1 < n and code[i+1] == '/':
                    state = 'NORMAL'
                    result[i] = ' '
                    result[i+1] = ' '
                    i += 2
                    continue
                elif c != '\n':
                    result[i] = ' '
            elif state in ('IN_STRING', 'IN_SQ_STRING', 'IN_TICK_STRING'):
                if c == '\\':
                    result[i] = ' '
                    if i + 1 < n:
                        result[i+1] = ' '
                        i += 2
                        continue
                elif (state == 'IN_STRING' and c == '"') or \
                     (state == 'IN_SQ_STRING' and c == "'") or \
                     (state == 'IN_TICK_STRING' and c == '`'):
                    state = 'NORMAL'
                    result[i] = ' '
                elif c != '\n':
                    result[i] = ' '
            
            i += 1
            
        return "".join(result)

    def _get_line(self, masked_code: str, index: int) -> int:
        """Calculate line number by counting newlines up to the given index."""
        return masked_code.count('\n', 0, index) + 1

    def _make_issue(
        self,
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

    # ---------------------------------------------------------------
    # Rules
    # ---------------------------------------------------------------

    def _check_compiler_ignore(
        self,
        code: str,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect TypeScript compiler suppression directives."""
        # Extract only single-line comments to avoid strings and block comments
        sl_code_chars = [' '] * len(code)
        i = 0
        n = len(code)
        state = 'NORMAL'
        while i < n:
            c = code[i]
            if state == 'NORMAL':
                if c == '/' and i + 1 < n and code[i+1] == '/':
                    state = 'IN_SL_COMMENT'
                    sl_code_chars[i] = '/'
                    sl_code_chars[i+1] = '/'
                    i += 2
                    continue
                elif c == '/' and i + 1 < n and code[i+1] == '*':
                    state = 'IN_ML_COMMENT'
                    i += 2
                    continue
                elif c in '"\'`':
                    state = 'IN_STRING_' + c
            elif state == 'IN_SL_COMMENT':
                if c == '\n':
                    state = 'NORMAL'
                    sl_code_chars[i] = '\n'
                else:
                    sl_code_chars[i] = c
            elif state == 'IN_ML_COMMENT':
                if c == '*' and i + 1 < n and code[i+1] == '/':
                    state = 'NORMAL'
                    i += 2
                    continue
            elif state.startswith('IN_STRING_'):
                q = state[-1]
                if c == '\\':
                    if i + 1 < n:
                        i += 2
                        continue
                elif c == q:
                    state = 'NORMAL'
            
            if c == '\n' and state != 'IN_SL_COMMENT':
                sl_code_chars[i] = '\n'
            
            i += 1
            
        sl_code = "".join(sl_code_chars)

        pattern = re.compile(r'//\s*(@ts-ignore|@ts-nocheck)\b')
        for match in pattern.finditer(sl_code):
            line_number = self._get_line(sl_code, match.start())
            directive = match.group(1)
            issues.append(self._make_issue(
                line_number=line_number,
                severity="Medium",
                description=(
                    f"Compiler Suppression: using '{directive}' silently suppresses "
                    f"TypeScript's compiler diagnostics and can hide genuine defects. "
                    f"Recommend fixing the underlying typing issue or using '@ts-expect-error' "
                    f"if the API typing is temporarily incorrect."
                ),
                rule_name="TS_COMPILER_IGNORE",
                rule_type="Type Safety",
            ))

    def _check_non_null_assertion(
        self,
        masked_code: str,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect TypeScript's non-null assertion operator (!) when used to bypass safety."""
        # Preceded by alphanumeric, ], ), or !. Followed by anything except = (to avoid !=, !==, ! ==).
        # Also naturally avoids logical NOT (!value) because it wouldn't be preceded by the above chars.
        pattern = re.compile(r'(?<=[a-zA-Z0-9_\]\)!])!(?!\s*=)')
        for match in pattern.finditer(masked_code):
            line_number = self._get_line(masked_code, match.start())
            issues.append(self._make_issue(
                line_number=line_number,
                severity="Medium",
                description=(
                    "Non-null assertion: using '!' to bypass TypeScript's null/undefined safety "
                    "can cause runtime crashes if the value is unexpectedly null. "
                    "Recommend using optional chaining (?.) or explicit null checks."
                ),
                rule_name="TS_NON_NULL_ASSERTION",
                rule_type="Bugs",
            ))

    def _check_banned_types(
        self,
        masked_code: str,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect TypeScript wrapper/object types (String, Boolean, etc.) used as annotations."""
        # Match types right after a colon (with optional array brackets or generics inside the type)
        pattern = re.compile(r':\s*(?:[a-zA-Z0-9_$]+\s*<\s*)?(String|Boolean|Number|Object|Symbol)\b')
        for match in pattern.finditer(masked_code):
            line_number = self._get_line(masked_code, match.start(1))
            banned_type = match.group(1)
            lower_type = banned_type.lower()
            issues.append(self._make_issue(
                line_number=line_number,
                severity="Low",
                description=(
                    f"Banned type wrapper: use the primitive '{lower_type}' instead of the wrapper object "
                    f"'{banned_type}'. The wrapper object can lead to unexpected type mismatches."
                ),
                rule_name="TS_BANNED_TYPES",
                rule_type="Best Practices",
            ))

    def _check_unsafe_any_declaration(
        self,
        masked_code: str,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect explicit any type declarations (e.g. : any)."""
        pattern = re.compile(r':\s*any\b')
        for match in pattern.finditer(masked_code):
            line_number = self._get_line(masked_code, match.start())
            issues.append(self._make_issue(
                line_number=line_number,
                severity="Medium",
                description=(
                    "Unsafe 'any' declaration: explicitly declaring a value as 'any' "
                    "disables TypeScript's type checking for that value and can hide "
                    "runtime defects. Recommend 'unknown' or a specific type instead."
                ),
                rule_name="TS_UNSAFE_ANY_DECLARATION",
                rule_type="Type Safety",
            ))

    def _check_explicit_any_cast(
        self,
        masked_code: str,
        issues: List[Dict[str, Any]],
    ) -> None:
        """Detect explicit casts bypassing type checking (e.g. as any, <any>)."""
        pattern = re.compile(r'\bas\s+any\b|<\s*any\s*>')
        for match in pattern.finditer(masked_code):
            line_number = self._get_line(masked_code, match.start())
            issues.append(self._make_issue(
                line_number=line_number,
                severity="High",
                description=(
                    "Explicit 'any' cast: casting a value to 'any' suppresses "
                    "compile-time guarantees and bypasses strict type safety. "
                    "Recommend using a real interface/type or 'unknown' with validation."
                ),
                rule_name="TS_EXPLICIT_ANY_CAST",
                rule_type="Type Safety",
            ))
