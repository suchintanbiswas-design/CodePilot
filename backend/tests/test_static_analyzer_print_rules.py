import pytest
from app.engine.static_analyzer import StaticAnalyzer

def test_print_rules_audit():
    analyzer = StaticAnalyzer()

    # 1. Simple print() in small valid Python program
    py_code = "def main():\n    print('Hello world!')\n"
    issues = analyzer.analyze(py_code, "Python")
    assert not any("console output" in i.get("description", "").lower() for i in issues), "Simple print() should not trigger excessive output smell"

    # 2. Simple printf() in C program
    c_code = "int main() {\n    printf(\"Hello\\n\");\n    return 0;\n}"
    issues = analyzer.analyze(c_code, "C")
    assert not any("console output" in i.get("description", "").lower() for i in issues), "Simple printf() should not trigger excessive output smell"

    # 3. Simple System.out.println() in Java program
    java_code = "class Main {\n  public static void main(String[] args) {\n    System.out.println(\"Hello\");\n  }\n}"
    issues = analyzer.analyze(java_code, "Java")
    assert not any("console output" in i.get("description", "").lower() for i in issues), "Simple System.out.println() should not trigger excessive output smell"

    # 4. Simple console.log() in JS
    js_code = "function main() {\n  console.log('Hello');\n}"
    issues = analyzer.analyze(js_code, "JavaScript")
    assert not any("console output" in i.get("description", "").lower() for i in issues), "Simple console.log() should not trigger excessive output smell"

    # 5. Clearly excessive/debug output -> appropriate smell
    excessive_code = "def main():\n    print('Starting')\n    print('Step 1')\n    print('Step 2')\n    print('Done')\n"
    issues = analyzer.analyze(excessive_code, "Python")
    excessive_issues = [i for i in issues if "Excessive console output" in i["description"]]
    assert len(excessive_issues) == 1, "Should aggregate all 4 prints into exactly 1 issue when threshold (3) is exceeded"
    assert excessive_issues[0]["severity"] == "Low", "Excessive prints should be Low severity, not Medium"
    assert "Lines: 2, 3, 4, 5" in excessive_issues[0]["description"], "Description should list the exact line numbers of all matching print statements"

    # 6. Sensitive data printed to console -> detected as a security issue
    sensitive_code = "def debug():\n    print(f'Using api_key: {api_key}')\n"
    issues = analyzer.analyze(sensitive_code, "Python")
    sensitive_issues = [i for i in issues if "Sensitive data printed to console" in i["description"]]
    assert len(sensitive_issues) == 1, "Should flag sensitive console output"
    assert sensitive_issues[0]["severity"] == "High", "Sensitive output should be High severity"
    assert sensitive_issues[0]["rule_type"] == "Security", "Sensitive output should be Security type"
