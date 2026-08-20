from __future__ import annotations

import re
from typing import Any, Dict, List


class Rule:
    def __init__(
        self,
        name: str,
        pattern: str,
        severity: str,
        description: str,
        rule_type: str,
        languages: List[str] = None,
        threshold: int = 1,
        aggregate: bool = False,
    ):
        self.name = name
        self.pattern = re.compile(pattern)
        self.severity = severity
        self.description = description
        self.rule_type = rule_type
        self.languages = languages or ["ALL"]
        self.threshold = threshold
        self.aggregate = aggregate


class StaticAnalyzer:
    """Basic static analysis engine using regex rules."""

    def __init__(self) -> None:
        self.rules: List[Rule] = [
            Rule(
                "TODO_COMMENTS",
                r"(?i)#\s*todo|//\s*todo",
                "Low",
                "TODO comments indicate incomplete code",
                "Best Practices",
                ["ALL"],
            ),
            Rule(
                "SENSITIVE_CONSOLE_OUTPUT",
                r"(?i)\b(?:print|console\.log|System\.out\.println|printf)\s*\([^)]*(?:password|secret|token|api_key|credential)[^)]*\)",
                "High",
                "Sensitive data printed to console",
                "Security",
                ["ALL"],
            ),
            Rule(
                "EXCESSIVE_CONSOLE_OUTPUT",
                r"\b(?:print|console\.log|System\.out\.println|printf)\s*\(",
                "Low",
                "Excessive console output (likely debugging statements left in code)",
                "Smells",
                ["ALL"],
                threshold=3,
                aggregate=True,
            ),
            Rule(
                "HARDCODED_SECRETS",
                r"(?i)(password|secret|api_key|token)\s*=\s*['\"][a-zA-Z0-9]+['\"]",
                "Critical",
                "Possible hardcoded secret",
                "Security",
                ["ALL"],
            ),
            Rule(
                "MAGIC_NUMBERS",
                r"\s*=\s*\d{3,}\b",
                "Low",
                "Potential magic number used without constant",
                "Maintainability",
                ["ALL"],
            ),
            Rule(
                "CATCH_ALL_PY",
                r"\bexcept\s*:",
                "High",
                "Catch-all exception handling masks bugs",
                "Bugs",
                ["Python"],
            ),
            Rule(
                "CATCH_ALL_JAVA",
                r"\bcatch\s*\(Exception\s+[a-zA-Z_]+\)\s*\{",
                "High",
                "Catch-all exception handling masks bugs",
                "Bugs",
                ["Java", "C++", "JavaScript", "TypeScript"],
            ),
            Rule(
                "EMPTY_BLOCK_C",
                r"\{\s*\}",
                "Low",
                "Empty block found",
                "Smells",
                ["Java", "C", "C++", "JavaScript", "TypeScript"],
            ),
            Rule(
                "EMPTY_BLOCK_PY",
                r":\s+pass\b",
                "Low",
                "Empty block found",
                "Smells",
                ["Python"],
            ),
            Rule(
                "VAR_USAGE",
                r"\bvar\s+[a-zA-Z_]",
                "Medium",
                "Use of 'var' instead of let/const in JS/TS",
                "Best Practices",
                ["JavaScript", "TypeScript"],
            ),
            Rule(
                "COMPLEX_CONDITION",
                r"(\&\&|\|\||and|or).*(\&\&|\|\||and|or).*(\&\&|\|\||and|or)",
                "Medium",
                "Complex condition, refactor into smaller methods",
                "Complexity",
                ["ALL"],
            ),
            Rule(
                "DUPLICATE_IMPORT",
                r"import\s+.*\bfrom\s+['\"].*['\"]",
                "Low",
                "Check for duplicate imports (heuristic)",
                "Optimization",
                ["ALL"],
            ),
            Rule(
                "LARGE_CLASS",
                r"(class\s+[a-zA-Z_]+)(?:(?s:.*?)(?:class\s+[a-zA-Z_]+|def\s+|function\s+)){10,}",
                "Medium",
                "Class might be violating Single Responsibility (SOLID)",
                "SOLID",
                ["ALL"],
            ),
        ]

    def calculate_cyclomatic_complexity(self, code: str) -> int:
        complexity = 1
        keywords = [
            r"\bif\b",
            r"\belse\b",
            r"\belif\b",
            r"\bfor\b",
            r"\bwhile\b",
            r"\bcase\b",
            r"\bcatch\b",
            r"\&\&",
            r"\|\|",
            r"\?",
        ]
        for keyword in keywords:
            complexity += len(re.findall(keyword, code))
        return complexity

    def analyze(self, code: str, language: str) -> List[Dict[str, Any]]:
        """
        Analyze code and return a list of issues.
        language: Java, Python, C, C++, JavaScript, TypeScript.
        """
        issues = []
        
        # Normalize analyzer input (CRLF/CR -> LF, remove BOM)
        normalized_code = code.replace("\r\n", "\n").replace("\r", "\n").lstrip("\ufeff")
        
        for rule in self.rules:
            if "ALL" in rule.languages or language in rule.languages:
                # Search across the entire normalized string to support multiline rules like LARGE_CLASS
                matches = list(rule.pattern.finditer(normalized_code))
                
                # Only report if threshold is met
                if len(matches) >= getattr(rule, 'threshold', 1):
                    if getattr(rule, 'aggregate', False):
                        # Aggregate all matches into a single issue
                        line_numbers = []
                        for match in matches:
                            line_number = normalized_code.count("\n", 0, match.start()) + 1
                            line_numbers.append(str(line_number))
                        
                        issues.append(
                            {
                                "severity": rule.severity,
                                "line_number": int(line_numbers[0]),
                                "description": f"{rule.description}. Lines: {', '.join(line_numbers)}",
                                "rule_type": rule.rule_type,
                            }
                        )
                    else:
                        for match in matches:
                            # Calculate line number by counting newlines before the match
                            line_number = normalized_code.count("\n", 0, match.start()) + 1
                            issues.append(
                                {
                                    "severity": rule.severity,
                                    "line_number": line_number,
                                    "description": rule.description,
                                    "rule_type": rule.rule_type,
                                }
                            )

        return issues
