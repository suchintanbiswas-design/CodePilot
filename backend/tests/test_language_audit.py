import pytest
from app.engine.syntax_validator import SyntaxValidator
from app.engine.static_analyzer import StaticAnalyzer

def test_python_audit():
    validator = SyntaxValidator()
    analyzer = StaticAnalyzer()
    
    # A. Valid code
    valid = "def main():\n    print('hello')"
    assert not validator.validate(valid, "Python")
    
    # B. One syntax error
    invalid1 = "def main(:\n    pass"
    iss1 = validator.validate(invalid1, "Python")
    assert len(iss1) == 1
    assert iss1[0]["line_number"] == 1
    
    # D. CRLF input
    crlf_valid = "def main():\r\n    print('hello')\r\n"
    assert not validator.validate(crlf_valid, "Python")
    
    # E. Real static-quality issue (Catch-all)
    static1 = "try:\n    pass\nexcept:\n    pass"
    sa_iss = analyzer.analyze(static1, "Python")
    assert any(i["rule_type"] == "Bugs" for i in sa_iss)


def test_java_audit():
    validator = SyntaxValidator()
    analyzer = StaticAnalyzer()
    
    valid = "class Main { public static void main(String[] args) { System.out.println(\"hello\"); } }"
    assert not validator.validate(valid, "Java")
    
    invalid = "class Main { public static void main(String[] args { }"
    iss1 = validator.validate(invalid, "Java")
    assert len(iss1) == 1
    
    crlf_valid = "class Main {\r\n public static void main(String[] args) {} \r\n}"
    assert not validator.validate(crlf_valid, "Java")
    
    static1 = "class Main { void f() { catch (Exception e) { } } }"
    sa_iss = analyzer.analyze(static1, "Java")
    assert any(i["rule_type"] == "Bugs" for i in sa_iss)


def test_c_audit():
    validator = SyntaxValidator()
    analyzer = StaticAnalyzer()
    
    valid = "int main() { return 0; }"
    assert not validator.validate(valid, "C")
    
    invalid = "int main() { return 0 }"
    iss1 = validator.validate(invalid, "C")
    assert len(iss1) == 1
    
    crlf_valid = "int main() {\r\n return 0;\r\n}"
    assert not validator.validate(crlf_valid, "C")
    
    static1 = "int main() { printf(\"test\"); printf(\"2\"); printf(\"3\"); }"
    sa_iss = analyzer.analyze(static1, "C")
    assert any(i["rule_type"] == "Smells" for i in sa_iss)


def test_cpp_audit():
    validator = SyntaxValidator()
    analyzer = StaticAnalyzer()
    
    valid = "int main() { return 0; }"
    assert not validator.validate(valid, "C++")
    
    invalid = "int main() { return 0"
    iss1 = validator.validate(invalid, "C++")
    assert len(iss1) >= 1
    
    crlf_valid = "int main() {\r\n return 0;\r\n}"
    assert not validator.validate(crlf_valid, "C++")
    
    static1 = "int main() { printf(\"test\"); printf(\"2\"); printf(\"3\"); }"
    sa_iss = analyzer.analyze(static1, "C++")
    assert any(i["rule_type"] == "Smells" for i in sa_iss)
    
    # Multiple errors for C++ (heuristic-based)
    invalid2 = "int main() {\n    return 0\n"
    iss2 = validator.validate(invalid2, "C++")
    assert len(iss2) >= 2


def test_javascript_audit():
    validator = SyntaxValidator()
    analyzer = StaticAnalyzer()
    
    valid = "function main() { console.log('hello'); }"
    assert not validator.validate(valid, "JavaScript")
    
    invalid1 = "function main() { console.log('hello' }"
    iss1 = validator.validate(invalid1, "JavaScript")
    assert len(iss1) == 1
    
    crlf_valid = "function main() {\r\n console.log('hello');\r\n}"
    assert not validator.validate(crlf_valid, "JavaScript")
    
    static1 = "function main() { console.log('test'); console.log('2'); console.log('3'); }"
    sa_iss = analyzer.analyze(static1, "JavaScript")
    assert any(i["rule_type"] == "Smells" for i in sa_iss)


def test_typescript_audit():
    validator = SyntaxValidator()
    analyzer = StaticAnalyzer()
    
    valid = "function main(): void { console.log('hello'); }"
    assert not validator.validate(valid, "TypeScript")
    
    invalid1 = "function main(): void { console.log('hello' }"
    iss1 = validator.validate(invalid1, "TypeScript")
    assert len(iss1) == 1
    
    crlf_valid = "function main(): void {\r\n console.log('hello');\r\n}"
    assert not validator.validate(crlf_valid, "TypeScript")
    
    static1 = "function main(): void { console.log('test'); console.log('2'); console.log('3'); }"
    sa_iss = analyzer.analyze(static1, "TypeScript")
    assert any(i["rule_type"] == "Smells" for i in sa_iss)

def test_static_analyzer_multiline_support():
    analyzer = StaticAnalyzer()
    # Test that LARGE_CLASS detects 10+ methods across lines using the normalized multiline support
    code = "class Large {\n" + "".join([f"  def method{i}():\n    pass\n" for i in range(15)])
    sa_iss = analyzer.analyze(code, "Python")
    assert any(i["description"].startswith("Class might be violating") for i in sa_iss)
