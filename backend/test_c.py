import pytest
from app.engine.syntax_validator import SyntaxValidator

def test_c_validation_crlf():
    validator = SyntaxValidator()
    code = "int main() {\r\n    return 0;\r\n}\r\n"
    issues = validator.validate(code, "C")
    assert not issues, f"Expected no issues, got: {issues}"

def test_c_validation_malformed():
    validator = SyntaxValidator()
    code = "int main() {\r\n    return 0\r\n}\r\n" # Missing semicolon
    issues = validator.validate(code, "C")
    assert issues, "Expected issues for malformed C code"

if __name__ == '__main__':
    import sys
    sys.exit(pytest.main(['-v', 'test_c.py']))
