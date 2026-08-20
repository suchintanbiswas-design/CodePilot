"""CodePilot Language Detector.

Deterministic, fingerprint-based language detection for source code.
Supports the six languages seeded in CodePilot: Python, Java, C, C++,
JavaScript, and TypeScript.

No LLM or external API is used.  Detection is based on syntax-pattern
fingerprints; each fingerprint contributes a weighted score.  The language
with the highest total score wins.

A filename extension (if provided) acts as an additional signal but
cannot override strongly contradictory source-code evidence.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Detection result
# ---------------------------------------------------------------------------

@dataclass
class DetectionResult:
    """Result returned by ``LanguageDetector.detect()``."""

    detected_language: str          # e.g. "Python", "Java", "Unknown"
    confidence: int                 # 0-100
    evidence: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "detected_language": self.detected_language,
            "confidence": self.confidence,
            "evidence": self.evidence,
        }


# ---------------------------------------------------------------------------
# Fingerprint definitions
# ---------------------------------------------------------------------------

@dataclass
class _Fingerprint:
    """A single syntax fingerprint."""
    pattern: re.Pattern[str]
    weight: float
    label: str


def _fp(pattern: str, weight: float, label: str, flags: int = 0) -> _Fingerprint:
    return _Fingerprint(re.compile(pattern, flags | re.MULTILINE), weight, label)


# Each language has a list of (compiled-regex, weight, human-readable label).
# Weights are additive.  The language with the highest total wins.

_PYTHON_FINGERPRINTS: List[_Fingerprint] = [
    _fp(r"^\s*def\s+\w+\s*\(", 3, "Python def/function syntax detected"),
    _fp(r"^\s*class\s+\w+.*:", 2, "Python class definition detected"),
    _fp(r"^\s*import\s+\w+", 2, "Python import statement detected"),
    _fp(r"^\s*from\s+\w+\s+import\s+", 3, "Python from-import syntax detected"),
    _fp(r"\bprint\s*\(", 1.5, "Python print() call detected"),
    _fp(r"\bif\s+.*:\s*$", 1, "Python if-colon block detected"),
    _fp(r"\bfor\s+\w+\s+in\s+", 2, "Python for-in loop detected"),
    _fp(r"\bself\.\w+", 2.5, "Python self attribute access detected"),
    _fp(r"\b(None|True|False)\b", 1, "Python keyword (None/True/False) detected"),
    _fp(r"^\s*elif\s+", 2, "Python elif keyword detected"),
    _fp(r"\braise\s+\w+", 1.5, "Python raise statement detected"),
    _fp(r"\bexcept\s+\w+", 1.5, "Python except clause detected"),
    _fp(r"^\s*@\w+", 1.5, "Python decorator syntax detected"),
    _fp(r"\bdef\s+__\w+__", 2, "Python dunder method detected"),
    _fp(r"\blambda\s+", 1, "Python lambda expression detected"),
]

_JAVA_FINGERPRINTS: List[_Fingerprint] = [
    _fp(r"\bpublic\s+class\s+\w+", 4, "Java public class declaration detected"),
    _fp(r"\bprivate\s+(static\s+)?\w+\s+\w+", 2.5, "Java private field/method detected"),
    _fp(r"\bstatic\s+void\s+main\s*\(", 4, "Java main method detected"),
    _fp(r"\bSystem\.out\.print(ln)?\s*\(", 3, "Java System.out.println detected"),
    _fp(r"\bnew\s+[A-Z]\w*\s*\(", 1.5, "Java new-object instantiation detected"),
    _fp(r"\bimport\s+java\.", 4, "Java java.* import detected"),
    _fp(r"\bpackage\s+[\w.]+;", 3.5, "Java package declaration detected"),
    _fp(r"\bpublic\s+static\s+", 2, "Java public static modifier detected"),
    _fp(r"\b(String|int|boolean|double|float|void)\b", 1.5, "Java type keyword detected"),
    _fp(r"\b(extends|implements)\s+\w+", 2, "Java extends/implements detected"),
    _fp(r"\b(try|catch|finally)\s*\{?", 1, "Java try/catch/finally detected"),
    _fp(r"@Override", 2, "Java @Override annotation detected"),
]

_JAVASCRIPT_FINGERPRINTS: List[_Fingerprint] = [
    _fp(r"\b(const|let|var)\s+\w+\s*=", 2, "JavaScript variable declaration detected"),
    _fp(r"\bfunction\s+\w+\s*\(", 2, "JavaScript function declaration detected"),
    _fp(r"=>\s*(\{|[^{])", 2, "Arrow function expression detected"),
    _fp(r"\bconsole\.(log|warn|error)\s*\(", 2.5, "JavaScript console.log detected"),
    _fp(r"\brequire\s*\(\s*['\"]", 3, "Node.js require() detected"),
    _fp(r"\bmodule\.exports\b", 3, "Node.js module.exports detected"),
    _fp(r"\b(document|window)\.\w+", 2, "Browser DOM API access detected"),
    _fp(r"===|!==", 1.5, "JavaScript strict equality detected"),
    _fp(r"\basync\s+function\b", 2, "JavaScript async function detected"),
    _fp(r"\bawait\s+", 1, "JavaScript await keyword detected"),
    _fp(r"\bexport\s+(default\s+)?function\b", 2, "JavaScript/ES6 export function detected"),
    _fp(r"\bimport\s+.*\s+from\s+['\"]", 2, "ES6 import-from syntax detected"),
]

_TYPESCRIPT_FINGERPRINTS: List[_Fingerprint] = [
    # TS-specific patterns (on top of JS patterns)
    _fp(r"\binterface\s+\w+\s*\{", 4, "TypeScript interface declaration detected"),
    _fp(r":\s*(string|number|boolean|any|void|never|unknown)\b", 3, "TypeScript type annotation detected"),
    _fp(r"\btype\s+\w+\s*=", 3.5, "TypeScript type alias detected"),
    _fp(r"\benum\s+\w+\s*\{", 3.5, "TypeScript enum declaration detected"),
    _fp(r"<\w+(\s*,\s*\w+)*>", 1.5, "TypeScript/Java generic syntax detected"),
    _fp(r"\bas\s+\w+", 1.5, "TypeScript type assertion detected"),
    _fp(r"\bimport\s+.*\s+from\s+['\"]", 1.5, "ES6/TS import-from detected"),
    # Also include common JS patterns to build score
    _fp(r"\b(const|let)\s+\w+\s*[:=]", 1.5, "const/let variable with type annotation detected"),
    _fp(r"=>\s*(\{|[^{])", 1.5, "Arrow function expression detected"),
    _fp(r"\bconsole\.(log|warn|error)\s*\(", 1, "console.log detected"),
    _fp(r"\basync\s+", 1, "async keyword detected"),
    _fp(r"\bexport\s+(default\s+)?(class|function|const|interface|type)\b", 2, "TypeScript export detected"),
]

_C_FINGERPRINTS: List[_Fingerprint] = [
    _fp(r"#include\s*<\w+\.h>", 4, "C #include <header.h> detected"),
    _fp(r"\bprintf\s*\(", 3, "C printf() call detected"),
    _fp(r"\bscanf\s*\(", 2.5, "C scanf() call detected"),
    _fp(r"\bmalloc\s*\(", 2.5, "C malloc() call detected"),
    _fp(r"\bfree\s*\(", 2, "C free() call detected"),
    _fp(r"\bint\s+main\s*\(", 3.5, "C main function detected"),
    _fp(r"\btypedef\s+", 2, "C typedef detected"),
    _fp(r"\bstruct\s+\w+\s*\{", 2, "C struct definition detected"),
    _fp(r"\bsizeof\s*\(", 1.5, "C sizeof operator detected"),
    _fp(r"\bNULL\b", 1.5, "C NULL macro detected"),
    _fp(r"->\w+", 1, "C pointer dereference detected"),
]

_CPP_FINGERPRINTS: List[_Fingerprint] = [
    _fp(r"#include\s*<\w+>", 2, "C++ #include <header> detected"),
    _fp(r"\bstd::\w+", 4, "C++ std:: namespace detected"),
    _fp(r"\bcout\s*<<", 3.5, "C++ cout detected"),
    _fp(r"\bcin\s*>>", 3, "C++ cin detected"),
    _fp(r"\bclass\s+\w+\s*(\{|:)", 2, "C++ class definition detected"),
    _fp(r"\bnamespace\s+\w+", 3, "C++ namespace declaration detected"),
    _fp(r"\busing\s+namespace\s+", 3, "C++ using namespace detected"),
    _fp(r"\btemplate\s*<", 3, "C++ template detected"),
    _fp(r"\bnew\s+\w+", 1.5, "C++ new operator detected"),
    _fp(r"\bdelete\s+", 1.5, "C++ delete operator detected"),
    _fp(r"\bvirtual\s+", 2, "C++ virtual keyword detected"),
    _fp(r"\bnullptr\b", 2, "C++ nullptr keyword detected"),
    _fp(r"\bauto\s+\w+\s*=", 1.5, "C++ auto keyword detected"),
]

# Map language name -> fingerprints
_LANGUAGE_FINGERPRINTS: Dict[str, List[_Fingerprint]] = {
    "Python": _PYTHON_FINGERPRINTS,
    "Java": _JAVA_FINGERPRINTS,
    "JavaScript": _JAVASCRIPT_FINGERPRINTS,
    "TypeScript": _TYPESCRIPT_FINGERPRINTS,
    "C": _C_FINGERPRINTS,
    "C++": _CPP_FINGERPRINTS,
}

# Extension -> language mapping
_EXTENSION_MAP: Dict[str, str] = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".jsx": "JavaScript",
    ".c": "C",
    ".h": "C",       # could be C or C++, treated as C signal
    ".cpp": "C++",
    ".cxx": "C++",
    ".cc": "C++",
    ".hpp": "C++",
}


# ---------------------------------------------------------------------------
# LanguageDetector
# ---------------------------------------------------------------------------

class LanguageDetector:
    """Deterministic fingerprint-based language detector for CodePilot."""

    # Extension signal weight (additive, same scale as fingerprints)
    EXTENSION_WEIGHT = 3.0

    def detect(
        self,
        source_code: str,
        filename: Optional[str] = None,
    ) -> DetectionResult:
        """Detect the programming language of *source_code*.

        Parameters
        ----------
        source_code : str
            The source code to analyze.
        filename : str, optional
            The original filename (used for extension-based signal).

        Returns
        -------
        DetectionResult
            Contains the detected language, confidence (0-100), and evidence list.
        """
        if not source_code or not source_code.strip():
            return DetectionResult(
                detected_language="Unknown",
                confidence=0,
                evidence=["Empty or whitespace-only source code"],
            )

        # Strip comments-only check: if after removing all single-line and
        # multi-line comments the remaining non-whitespace is empty, it's ambiguous.
        stripped = self._strip_comments(source_code)
        if not stripped.strip():
            return DetectionResult(
                detected_language="Unknown",
                confidence=10,
                evidence=["Source code contains only comments"],
            )

        scores: Dict[str, float] = {}
        evidence_map: Dict[str, List[str]] = {}

        for lang, fingerprints in _LANGUAGE_FINGERPRINTS.items():
            lang_score = 0.0
            lang_evidence: List[str] = []
            for fp in fingerprints:
                matches = fp.pattern.findall(source_code)
                if matches:
                    # Score is weight * min(match_count, 3) to avoid one repeated
                    # pattern dominating.
                    count_factor = min(len(matches), 3)
                    lang_score += fp.weight * count_factor
                    lang_evidence.append(fp.label)
            scores[lang] = lang_score
            evidence_map[lang] = lang_evidence

        # Extension signal
        ext_lang = self._language_from_extension(filename)
        if ext_lang and ext_lang in scores:
            scores[ext_lang] += self.EXTENSION_WEIGHT
            evidence_map.setdefault(ext_lang, []).append(
                f"File extension matches {ext_lang}"
            )

        # Find the winner
        if not scores or max(scores.values()) == 0:
            return DetectionResult(
                detected_language="Unknown",
                confidence=0,
                evidence=["No recognized syntax patterns found"],
            )

        best_lang = max(scores, key=scores.get)  # type: ignore[arg-type]
        best_score = scores[best_lang]

        # Runner-up for confidence gap calculation
        sorted_scores = sorted(scores.values(), reverse=True)
        runner_up_score = sorted_scores[1] if len(sorted_scores) > 1 else 0

        confidence = self._calculate_confidence(best_score, runner_up_score)

        return DetectionResult(
            detected_language=best_lang,
            confidence=confidence,
            evidence=evidence_map.get(best_lang, []),
        )

    def validate_language(
        self,
        selected_language: str,
        source_code: str,
        filename: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Compare the user-selected language against detected language.

        Returns a dict suitable for JSONB metadata storage.
        """
        result = self.detect(source_code, filename)
        is_match = (
            result.detected_language.lower() == selected_language.lower()
            or result.detected_language == "Unknown"
        )

        return {
            "selected_language": selected_language,
            "detected_language": result.detected_language,
            "confidence": result.confidence,
            "is_match": is_match,
            "evidence": result.evidence,
        }

    # -- private helpers --

    @staticmethod
    def _language_from_extension(filename: Optional[str]) -> Optional[str]:
        if not filename:
            return None
        # Extract extension
        dot_idx = filename.rfind(".")
        if dot_idx == -1:
            return None
        ext = filename[dot_idx:].lower()
        return _EXTENSION_MAP.get(ext)

    @staticmethod
    def _calculate_confidence(best_score: float, runner_up_score: float) -> int:
        """Map the absolute score and the gap to the runner-up into 0-100.

        Strategy:
        * A high absolute score means many fingerprints fired.
        * A large gap to the runner-up means little ambiguity.
        * We blend both signals.

        Thresholds (tuned for ~5-50 line code snippets):
        * best_score >=20 with gap >= 10  -> 90-100  (strong multi-signal)
        * best_score >=12 with gap >= 5   -> 75-89   (good match)
        * best_score >= 5                 -> 50-74   (weak match)
        * below                           -> 10-49   (ambiguous)
        """
        gap = best_score - runner_up_score

        if best_score >= 20 and gap >= 10:
            raw = 90 + min(10, int(gap / 3))
        elif best_score >= 12 and gap >= 5:
            raw = 75 + min(14, int(gap))
        elif best_score >= 5:
            raw = 50 + min(24, int(best_score))
        else:
            raw = 10 + min(39, int(best_score * 8))

        return max(0, min(100, raw))

    @staticmethod
    def _strip_comments(code: str) -> str:
        """Remove common comment patterns (C-style and Python-style)."""
        # Remove multi-line comments  /* ... */
        code = re.sub(r"/\*.*?\*/", "", code, flags=re.DOTALL)
        # Remove single-line //
        code = re.sub(r"//[^\n]*", "", code)
        # Remove single-line #
        code = re.sub(r"#[^\n]*", "", code)
        # Remove Python triple-quoted strings used as docstrings
        code = re.sub(r'""".*?"""', "", code, flags=re.DOTALL)
        code = re.sub(r"'''.*?'''", "", code, flags=re.DOTALL)
        return code
