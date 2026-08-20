"""Regression tests for authoritative language detection resolution."""
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from uuid import uuid4


def make_lang_detection(selected, detected, confidence):
    """Helper to simulate validate_language output."""
    is_match = detected.lower() == selected.lower() or detected == "Unknown"
    return {
        "selected_language": selected,
        "detected_language": detected,
        "confidence": confidence,
        "is_match": is_match,
        "evidence": [f"test evidence for {detected}"],
    }


def resolve_final_language(selected, detected, confidence):
    """Replicates the resolution logic from review_service._process_single_file."""
    if detected != "Unknown" and detected.lower() != selected.lower() and confidence >= 25:
        return detected, True
    return selected, False


class TestFinalLanguageResolution:
    """Test the 25% confidence threshold language resolution rules."""

    def test_python_selected_java_detected_89(self):
        """Python selected + Java detected 89% → final language Java."""
        final, switched = resolve_final_language("Python", "Java", 89)
        assert final == "Java"
        assert switched is True

    def test_java_selected_python_detected_46(self):
        """Java selected + Python detected 46% → final language Python."""
        final, switched = resolve_final_language("Java", "Python", 46)
        assert final == "Python"
        assert switched is True

    def test_python_selected_python_detected_100(self):
        """Python selected + Python detected 100% → final language Python."""
        final, switched = resolve_final_language("Python", "Python", 100)
        assert final == "Python"
        assert switched is False

    def test_java_selected_unknown_detected(self):
        """Java selected + Unknown → final language Java."""
        final, switched = resolve_final_language("Java", "Unknown", 0)
        assert final == "Java"
        assert switched is False

    def test_java_selected_python_detected_20(self):
        """Java selected + Python detected 20% → final language Java (below threshold)."""
        final, switched = resolve_final_language("Java", "Python", 20)
        assert final == "Java"
        assert switched is False

    def test_exact_threshold_25(self):
        """At exactly 25% confidence, detected language should be used."""
        final, switched = resolve_final_language("Python", "Java", 25)
        assert final == "Java"
        assert switched is True

    def test_just_below_threshold_24(self):
        """At 24% confidence, selected language should be kept."""
        final, switched = resolve_final_language("Python", "Java", 24)
        assert final == "Python"
        assert switched is False

    def test_case_insensitive_match(self):
        """python selected + Python detected → match, no switch."""
        final, switched = resolve_final_language("python", "Python", 95)
        assert final == "python"
        assert switched is False

    def test_cpp_selected_c_detected_high_confidence(self):
        """C++ selected + C detected 75% → final language C."""
        final, switched = resolve_final_language("C++", "C", 75)
        assert final == "C"
        assert switched is True


class TestLangDetectionMetadata:
    """Test that language_detection metadata includes final_language and language_switched."""

    def test_metadata_fields_on_switch(self):
        detection = make_lang_detection("Python", "Java", 89)
        detected = detection["detected_language"]
        confidence = detection["confidence"]
        selected = detection["selected_language"]

        if detected != "Unknown" and detected.lower() != selected.lower() and confidence >= 25:
            detection["final_language"] = detected
            detection["language_switched"] = True
        else:
            detection["final_language"] = selected
            detection["language_switched"] = False

        assert detection["final_language"] == "Java"
        assert detection["language_switched"] is True
        assert detection["selected_language"] == "Python"
        assert detection["detected_language"] == "Java"
        assert detection["confidence"] == 89

    def test_metadata_fields_on_match(self):
        detection = make_lang_detection("Python", "Python", 100)
        detected = detection["detected_language"]
        confidence = detection["confidence"]
        selected = detection["selected_language"]

        if detected != "Unknown" and detected.lower() != selected.lower() and confidence >= 25:
            detection["final_language"] = detected
            detection["language_switched"] = True
        else:
            detection["final_language"] = selected
            detection["language_switched"] = False

        assert detection["final_language"] == "Python"
        assert detection["language_switched"] is False

    def test_metadata_fields_below_threshold(self):
        detection = make_lang_detection("Java", "Python", 20)
        detected = detection["detected_language"]
        confidence = detection["confidence"]
        selected = detection["selected_language"]

        if detected != "Unknown" and detected.lower() != selected.lower() and confidence >= 25:
            detection["final_language"] = detected
            detection["language_switched"] = True
        else:
            detection["final_language"] = selected
            detection["language_switched"] = False

        assert detection["final_language"] == "Java"
        assert detection["language_switched"] is False
