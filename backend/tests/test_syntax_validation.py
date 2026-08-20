"""Tests for deterministic syntax validation."""
import pytest
from app.engine.syntax_validator import SyntaxValidator


@pytest.fixture
def validator():
    return SyntaxValidator()


# ---------------------------------------------------------------
# Python
# ---------------------------------------------------------------
class TestPython:
    def test_valid_python(self, validator):
        code = 'def hello():\n    print("hello world")\n'
        issues = validator.validate(code, "Python")
        assert len(issues) == 0

    def test_invalid_python_missing_paren(self, validator):
        code = 'def hello(\n    print("hello")\n'
        issues = validator.validate(code, "Python")
        assert len(issues) >= 1
        assert issues[0]["severity"] == "Critical"
        assert issues[0]["rule_type"] == "Syntax"
        assert "Python syntax error" in issues[0]["description"]

    def test_invalid_python_indent(self, validator):
        code = 'def foo():\nprint("bad")\n'
        issues = validator.validate(code, "Python")
        assert len(issues) >= 1


# ---------------------------------------------------------------
# Java
# ---------------------------------------------------------------
class TestJava:
    def test_valid_java(self, validator):
        code = '''import java.util.*;
public class Hello {
    public static void main(String[] args) {
        System.out.println("hello");
    }
}
'''
        issues = validator.validate(code, "Java")
        assert len(issues) == 0

    def test_invalid_java_string_literal(self, validator):
        code = '''import java.util.*;
public class Getea
{
    public static void main(String args[])
    {
        System.out.println(hello world")
    }
}
'''
        issues = validator.validate(code, "Java")
        assert len(issues) >= 1
        assert issues[0]["severity"] == "Critical"
        assert issues[0]["rule_type"] == "Syntax"

    def test_invalid_java_missing_brace(self, validator):
        code = '''public class Bad {
    public static void main(String[] args) {
        System.out.println("hi");

}
'''
        issues = validator.validate(code, "Java")
        assert len(issues) >= 1


# ---------------------------------------------------------------
# C
# ---------------------------------------------------------------
class TestC:
    def test_valid_c(self, validator):
        code = '''#include <stdio.h>
int main() {
    printf("hello");
    return 0;
}
'''
        issues = validator.validate(code, "C")
        assert len(issues) == 0

    def test_invalid_c_missing_semicolon(self, validator):
        code = '''int main() {
    int x = 5
    return 0;
}
'''
        issues = validator.validate(code, "C")
        assert len(issues) >= 1
        assert issues[0]["severity"] == "Critical"


# ---------------------------------------------------------------
# C++
# ---------------------------------------------------------------
class TestCpp:
    def test_valid_cpp(self, validator):
        code = '''#include <iostream>
int main() {
    std::cout << "hello" << std::endl;
    return 0;
}
'''
        issues = validator.validate(code, "C++")
        assert len(issues) == 0

    def test_invalid_cpp_unclosed_brace(self, validator):
        code = '''#include <iostream>
int main() {
    std::cout << "hello" << std::endl;

'''
        issues = validator.validate(code, "C++")
        assert len(issues) >= 1
        assert issues[0]["severity"] == "Critical"


# ---------------------------------------------------------------
# JavaScript
# ---------------------------------------------------------------
class TestJavaScript:
    def test_valid_js(self, validator):
        code = 'function hello() {\n  console.log("hello");\n}\n'
        issues = validator.validate(code, "JavaScript")
        assert len(issues) == 0

    def test_invalid_js_syntax(self, validator):
        code = 'function hello( {\n  console.log("hello");\n}\n'
        issues = validator.validate(code, "JavaScript")
        assert len(issues) >= 1
        assert issues[0]["severity"] == "Critical"
        assert issues[0]["rule_type"] == "Syntax"


# ---------------------------------------------------------------
# TypeScript
# ---------------------------------------------------------------
class TestTypeScript:
    def test_valid_ts(self, validator):
        code = 'function greet(name: string): void {\n  console.log(name);\n}\n'
        issues = validator.validate(code, "TypeScript")
        assert len(issues) == 0

    def test_invalid_ts_syntax(self, validator):
        code = 'function greet(name: string {\n  console.log(name);\n}\n'
        issues = validator.validate(code, "TypeScript")
        assert len(issues) >= 1
        assert issues[0]["severity"] == "Critical"


# ---------------------------------------------------------------
# Integration: Language Resolution + Syntax Validation
# ---------------------------------------------------------------
class TestLanguageResolutionIntegration:
    """Verify syntax validation uses the final resolved language."""

    def test_selected_python_detected_java_invalid_java(self, validator):
        """Selected Python, Detected Java (89%), Final Java.
        Code is invalid Java → should produce Java syntax error."""
        invalid_java = '''public class Test {
    public static void main(String[] args) {
        System.out.println(hello world")
    }
}'''
        # Validator receives the FINAL language (Java), not the selected (Python)
        issues = validator.validate(invalid_java, "Java")
        assert len(issues) >= 1
        assert "Java" in issues[0]["description"]

    def test_selected_java_detected_python_invalid_python(self, validator):
        """Selected Java, Detected Python (46%), Final Python.
        Code is invalid Python → should produce Python syntax error."""
        invalid_python = 'def hello(\n    print("hello")\n'
        # Validator receives the FINAL language (Python), not the selected (Java)
        issues = validator.validate(invalid_python, "Python")
        assert len(issues) >= 1
        assert "Python" in issues[0]["description"]

    def test_valid_code_no_issues(self, validator):
        """Valid code should produce no syntax issues regardless of language."""
        valid_python = 'def hello():\n    print("hello")\n'
        assert validator.validate(valid_python, "Python") == []

    def test_empty_code(self, validator):
        assert validator.validate("", "Python") == []
        assert validator.validate("   ", "Java") == []

    def test_unsupported_language(self, validator):
        """Unsupported language should return empty list."""
        assert validator.validate("some code", "Rust") == []

    def test_issue_format(self, validator):
        """Verify issue format matches CodePilot's standard."""
        code = 'def hello(\n    print("hello")\n'
        issues = validator.validate(code, "Python")
        assert len(issues) >= 1
        issue = issues[0]
        assert "severity" in issue
        assert "line_number" in issue
        assert "description" in issue
        assert "rule_type" in issue
        assert "confidence" in issue
        assert "source" in issue
        assert issue["severity"] == "Critical"
        assert issue["rule_type"] == "Syntax"
        assert issue["confidence"] == 100
        assert issue["source"] == "static"
        assert isinstance(issue["line_number"], int)
