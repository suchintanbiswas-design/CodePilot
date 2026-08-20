"""
Deterministic Syntax Validator for CodePilot.

Validates source code syntax using language-specific parsers without executing code.
Produces findings in CodePilot's standard issue format for integration with the
Hybrid Engine, Confidence Engine, and Scoring Engine.
"""
from __future__ import annotations

import ast
import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SyntaxValidator:
    """Parse-only syntax validation for supported languages."""

    def validate(self, source_code: str, language: str) -> List[Dict[str, Any]]:
        """Validate source code syntax for the given language.

        Parameters
        ----------
        source_code : str
            The source code to validate.
        language : str
            The resolved final language name (e.g. "Python", "Java").

        Returns
        -------
        list[dict]
            A list of syntax issues in CodePilot's standard issue format.
            Empty list if no syntax errors are found.
        """
        if not source_code or not source_code.strip():
            return []

        # Normalize parser input (CRLF/CR -> LF, remove BOM)
        normalized_code = source_code.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")

        lang = language.lower()
        validators = {
            "python": self._validate_python,
            "java": self._validate_java,
            "c": self._validate_c,
            "c++": self._validate_cpp,
            "javascript": self._validate_javascript,
            "typescript": self._validate_typescript,
        }

        validator = validators.get(lang)
        if not validator:
            return []

        try:
            return validator(normalized_code)
        except Exception as e:
            logger.warning(f"Syntax validator internal error for {language}: {e}")
            return []

    def _make_issue(
        self,
        line_number: int,
        description: str,
        language: str,
    ) -> Dict[str, Any]:
        """Create a syntax issue in CodePilot's standard format."""
        return {
            "severity": "Critical",
            "line_number": line_number,
            "description": description,
            "rule_type": "Syntax",
            "confidence": 100,
            "source": "static",
        }

    # ---------------------------------------------------------------
    # Python — stdlib ast.parse()
    # ---------------------------------------------------------------
    def _validate_python(self, code: str) -> List[Dict[str, Any]]:
        try:
            ast.parse(code)
            return []
        except SyntaxError as e:
            line = e.lineno or 1
            msg = e.msg if e.msg else "Syntax error"
            return [self._make_issue(line, f"Python syntax error: {msg}", "Python")]

    # ---------------------------------------------------------------
    # Java — javalang parser
    # ---------------------------------------------------------------
    def _validate_java(self, code: str) -> List[Dict[str, Any]]:
        try:
            import javalang
            javalang.parse.parse(code)
            return []
        except ImportError:
            logger.warning("javalang not installed, skipping Java syntax validation")
            return []
        except Exception as e:
            # javalang raises javalang.parser.JavaSyntaxError or
            # javalang.tokenizer.LexerError
            line = getattr(e, 'at', None)
            if line and hasattr(line, 'lineno'):
                line_num = line.lineno
            elif isinstance(line, tuple) and len(line) >= 1:
                line_num = line[0] if isinstance(line[0], int) else 1
            else:
                # Try to extract line from error message
                line_num = self._extract_line_from_error(str(e))

            desc = str(e).split('\n')[0] if str(e) else "Syntax error"
            return [self._make_issue(line_num, f"Java syntax error: {desc}", "Java")]

    # ---------------------------------------------------------------
    # C — pycparser (already installed)
    # ---------------------------------------------------------------
    def _validate_c(self, code: str) -> List[Dict[str, Any]]:
        try:
            import pycparser
            
            # pycparser needs fake includes for standard headers
            fake_code = self._prepare_c_for_parsing(code)
            parser = pycparser.CParser()
            parser.parse(fake_code)
            return []
        except ImportError:
            logger.warning("pycparser not installed, skipping C syntax validation")
            return []
        except pycparser.c_parser.ParseError as e:
            line_num = self._extract_line_from_error(str(e))
            desc = str(e).split('\n')[0] if str(e) else "Syntax error"
            return [self._make_issue(line_num, f"C syntax error: {desc}", "C")]
        except Exception as e:
            line_num = self._extract_line_from_error(str(e))
            desc = str(e).split('\n')[0]
            return [self._make_issue(line_num, f"C syntax error: {desc}", "C")]

    def _prepare_c_for_parsing(self, code: str) -> str:
        """Strip #include directives and comments since pycparser can't handle them."""
        import re as _re
        # Remove block comments /* ... */
        code = _re.sub(r'/\*.*?\*/', '', code, flags=_re.DOTALL)
        lines = code.split('\n')
        processed = []
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('#include'):
                processed.append('')  # Remove includes
            else:
                # Remove single-line // comments
                comment_idx = line.find('//')
                if comment_idx >= 0:
                    line = line[:comment_idx]
                processed.append(line)
        return '\n'.join(processed)

    # ---------------------------------------------------------------
    # C++ — bracket/brace/paren matching + common pattern checks
    # (No pure-Python C++ parser available; pycparser is C-only)
    # ---------------------------------------------------------------
    def _validate_cpp(self, code: str) -> List[Dict[str, Any]]:
        issues = []
        # Check balanced brackets/braces/parens
        bracket_issue = self._check_balanced(code, "C++")
        if bracket_issue:
            issues.append(bracket_issue)
        # Check for missing semicolons after statements (simple heuristic)
        issues.extend(self._check_cpp_semicolons(code))
        return issues

    def _check_balanced(self, code: str, language: str) -> Optional[Dict[str, Any]]:
        """Check for unbalanced brackets, braces, and parentheses."""
        stack = []
        pairs = {')': '(', ']': '[', '}': '{'}
        openers = set('({[')
        closers = set(')}]')
        in_string = False
        string_char = None
        in_line_comment = False
        in_block_comment = False

        for line_idx, line in enumerate(code.split('\n'), 1):
            i = 0
            while i < len(line):
                ch = line[i]
                # Handle block comment
                if in_block_comment:
                    if ch == '*' and i + 1 < len(line) and line[i + 1] == '/':
                        in_block_comment = False
                        i += 2
                        continue
                    i += 1
                    continue
                # Handle line comment
                if in_line_comment:
                    break
                # Check comment start
                if ch == '/' and i + 1 < len(line):
                    if line[i + 1] == '/':
                        in_line_comment = True
                        break
                    if line[i + 1] == '*':
                        in_block_comment = True
                        i += 2
                        continue
                # Handle strings
                if in_string:
                    if ch == '\\':
                        i += 2  # skip escaped char
                        continue
                    if ch == string_char:
                        in_string = False
                    i += 1
                    continue
                if ch in ('"', "'"):
                    in_string = True
                    string_char = ch
                    i += 1
                    continue
                # Track brackets
                if ch in openers:
                    stack.append((ch, line_idx))
                elif ch in closers:
                    if not stack:
                        return self._make_issue(
                            line_idx,
                            f"{language} syntax error: unmatched closing '{ch}'",
                            language,
                        )
                    top_ch, top_line = stack[-1]
                    if top_ch != pairs[ch]:
                        return self._make_issue(
                            line_idx,
                            f"{language} syntax error: mismatched '{ch}', expected closing for '{top_ch}' opened at line {top_line}",
                            language,
                        )
                    stack.pop()
                i += 1
            in_line_comment = False

        if stack:
            ch, line_num = stack[-1]
            return self._make_issue(
                line_num,
                f"{language} syntax error: unclosed '{ch}'",
                language,
            )
        return None

    def _check_cpp_semicolons(self, code: str) -> List[Dict[str, Any]]:
        """Basic heuristic: detect lines that look like statements but lack semicolons."""
        issues = []
        lines = code.split('\n')
        # Patterns that should end with ; (very conservative)
        stmt_pattern = re.compile(
            r'^\s*(?:return\s+.+|'
            r'(?:int|float|double|char|bool|void|auto|string|std::\w+)\s+\w+\s*=.+|'
            r'\w+\s*\(.*\)\s*'
            r')$'
        )
        for i, line in enumerate(lines, 1):
            stripped = line.rstrip()
            if not stripped or stripped.endswith(('{', '}', ',', ';', '//', '*/', ':')):
                continue
            if stripped.startswith(('#', '//')):
                continue
            # Only flag obvious missing-semicolons on return statements with values
            if re.match(r'^\s*return\s+[^;]+$', stripped) and not stripped.endswith('{'):
                issues.append(self._make_issue(
                    i, f"C++ syntax error: possible missing semicolon", "C++"
                ))
        return issues

    # ---------------------------------------------------------------
    # JavaScript — esprima parser
    # ---------------------------------------------------------------
    def _validate_javascript(self, code: str) -> List[Dict[str, Any]]:
        try:
            import esprima
            tree = esprima.parseScript(code, tolerant=True)
            issues = []
            if getattr(tree, 'errors', None):
                for err in tree.errors:
                    line_num = getattr(err, 'lineNumber', 1)
                    desc = getattr(err, 'description', str(err).split('\n')[0])
                    issues.append(self._make_issue(line_num, f"JavaScript syntax error: {desc}", "JavaScript"))
            return issues
        except ImportError:
            logger.warning("esprima not installed, skipping JavaScript syntax validation")
            return []
        except esprima.Error as e:
            line_num = self._extract_line_from_error(str(e))
            desc = str(e).split('\n')[0]
            return [self._make_issue(line_num, f"JavaScript syntax error: {desc}", "JavaScript")]
        except Exception as e:
            line_num = self._extract_line_from_error(str(e))
            desc = str(e).split('\n')[0]
            return [self._make_issue(line_num, f"JavaScript syntax error: {desc}", "JavaScript")]

    # ---------------------------------------------------------------
    # TypeScript — esprima for JS subset + TS-specific regex checks
    # ---------------------------------------------------------------
    def _validate_typescript(self, code: str) -> List[Dict[str, Any]]:
        issues = []

        # Strip TypeScript-specific annotations for esprima JS parsing
        ts_stripped = self._strip_typescript_annotations(code)
        try:
            import esprima
            tree = esprima.parseScript(ts_stripped, tolerant=True)
            if getattr(tree, 'errors', None):
                for err in tree.errors:
                    line_num = getattr(err, 'lineNumber', 1)
                    desc = getattr(err, 'description', str(err).split('\n')[0])
                    issues.append(self._make_issue(line_num, f"TypeScript syntax error: {desc}", "TypeScript"))
        except ImportError:
            logger.warning("esprima not installed, skipping TypeScript syntax validation")
            return []
        except esprima.Error as e:
            line_num = self._extract_line_from_error(str(e))
            desc = str(e).split('\n')[0]
            issues.append(self._make_issue(line_num, f"TypeScript syntax error: {desc}", "TypeScript"))
        except Exception as e:
            line_num = self._extract_line_from_error(str(e))
            desc = str(e).split('\n')[0]
            issues.append(self._make_issue(line_num, f"TypeScript syntax error: {desc}", "TypeScript"))

        # Check balanced brackets (catches issues esprima might miss after stripping)
        bracket_issue = self._check_balanced(code, "TypeScript")
        if bracket_issue and not issues:
            issues.append(bracket_issue)

        return issues

    def _strip_typescript_annotations(self, code: str) -> str:
        """Remove TypeScript type annotations so esprima can parse the JS subset."""
        # Remove type annotations after : in parameters and declarations
        code = re.sub(r':\s*(?:string|number|boolean|any|void|never|unknown|object|null|undefined)(?:\[\])?', '', code)
        # Remove generic type parameters <T>, <T, U>
        code = re.sub(r'<[A-Z]\w*(?:\s*,\s*[A-Z]\w*)*>', '', code)
        # Remove interface/type declarations (entire blocks)
        code = re.sub(r'(?:export\s+)?(?:interface|type)\s+\w+[^{]*\{[^}]*\}', '', code, flags=re.DOTALL)
        # Remove 'as Type' casts
        code = re.sub(r'\bas\s+\w+', '', code)
        # Remove access modifiers
        code = re.sub(r'\b(?:public|private|protected|readonly)\s+', '', code)
        return code

    # ---------------------------------------------------------------
    # Helpers
    # ---------------------------------------------------------------
    @staticmethod
    def _extract_line_from_error(error_str: str) -> int:
        """Try to extract a line number from a parser error message."""
        # Common patterns: "line 6", "Line 6:", ":6:", "at line 6"
        m = re.search(r'[Ll]ine\s+(\d+)', error_str)
        if m:
            return int(m.group(1))
        m = re.search(r':(\d+):', error_str)
        if m:
            return int(m.group(1))
        m = re.search(r'(\d+)\s*:', error_str)
        if m:
            return int(m.group(1))
        return 1
