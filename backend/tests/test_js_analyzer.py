"""Tests for JavaScriptSemanticAnalyzer — Phase 1 rules."""

from app.engine.hybrid_engine import HybridEngine
from app.engine.js_analyzer import JavaScriptSemanticAnalyzer
from app.engine.static_analyzer import StaticAnalyzer

# ═══════════════════════════════════════════════════════════════════
# JS_LOOSE_EQUALITY
# ═══════════════════════════════════════════════════════════════════


class TestLooseEquality:
    """JS_LOOSE_EQUALITY rule."""

    def test_double_equals_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
function check(x) {
    if (x == 0) { return true; }
}
"""
        issues = analyzer.analyze(code)
        le = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(le) == 1
        assert le[0]["severity"] == "Medium"
        assert le[0]["rule_type"] == "Bugs"
        assert "'=='" in le[0]["description"]
        assert "'==='" in le[0]["description"]

    def test_not_equals_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
function check(x) {
    if (x != false) { return x; }
}
"""
        issues = analyzer.analyze(code)
        le = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(le) == 1
        assert "'!='" in le[0]["description"]
        assert "'!=='" in le[0]["description"]

    def test_double_equals_string_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
if (value == "hello") { process(); }
"""
        issues = analyzer.analyze(code)
        le = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(le) == 1

    def test_multiple_loose_equalities(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
if (a == 1 || b != 2) { go(); }
"""
        issues = analyzer.analyze(code)
        le = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(le) == 2

    def test_equals_null_suppressed(self):
        """x == null is the idiomatic null/undefined check — must not fire."""
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
function check(x) {
    if (x == null) { return "nil"; }
}
"""
        issues = analyzer.analyze(code)
        le = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(le) == 0

    def test_not_equals_null_suppressed(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
function check(x) {
    if (x != null) { return x; }
}
"""
        issues = analyzer.analyze(code)
        le = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(le) == 0

    def test_null_on_left_suppressed(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
if (null == x) { return; }
"""
        issues = analyzer.analyze(code)
        le = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(le) == 0

    def test_strict_equality_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
function check(x) {
    if (x === 0) { return true; }
    if (x !== false) { return x; }
}
"""
        issues = analyzer.analyze(code)
        le = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(le) == 0


# ═══════════════════════════════════════════════════════════════════
# JS_DANGEROUS_EVAL
# ═══════════════════════════════════════════════════════════════════


class TestDangerousEval:
    """JS_DANGEROUS_EVAL rule."""

    def test_dynamic_eval_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
var userInput = prompt("Enter:");
var result = eval(userInput);
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if i["rule_name"] == "JS_DANGEROUS_EVAL"]
        assert len(ev) == 1
        assert ev[0]["severity"] == "Critical"
        assert ev[0]["rule_type"] == "Security"
        assert "eval()" in ev[0]["description"]

    def test_dynamic_new_function_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
var body = getUserCode();
var fn = new Function("x", body);
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if i["rule_name"] == "JS_DANGEROUS_EVAL"]
        assert len(ev) == 1
        assert "Function()" in ev[0]["description"]

    def test_eval_no_args_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
eval();
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if i["rule_name"] == "JS_DANGEROUS_EVAL"]
        assert len(ev) == 1

    def test_constant_eval_suppressed(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
var result = eval("1 + 1");
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if i["rule_name"] == "JS_DANGEROUS_EVAL"]
        assert len(ev) == 0

    def test_constant_new_function_suppressed(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
var fn = new Function("x", "return x + 1");
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if i["rule_name"] == "JS_DANGEROUS_EVAL"]
        assert len(ev) == 0

    def test_unrelated_function_calls_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
var x = JSON.parse(data);
var y = parseInt("42");
console.log("hello");
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if i["rule_name"] == "JS_DANGEROUS_EVAL"]
        assert len(ev) == 0

    def test_new_unrelated_constructor_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
var d = new Date();
var r = new RegExp("abc");
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if i["rule_name"] == "JS_DANGEROUS_EVAL"]
        assert len(ev) == 0

    def test_eval_with_template_literal_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = "var x = eval(`${userInput}`);"
        issues = analyzer.analyze(code)
        ev = [i for i in issues if i["rule_name"] == "JS_DANGEROUS_EVAL"]
        assert len(ev) == 1

    def test_eval_with_constant_template_suppressed(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = "var x = eval(`1 + 1`);"
        issues = analyzer.analyze(code)
        ev = [i for i in issues if i["rule_name"] == "JS_DANGEROUS_EVAL"]
        assert len(ev) == 0


# ═══════════════════════════════════════════════════════════════════
# JS_INNERHTML_XSS
# ═══════════════════════════════════════════════════════════════════


class TestInnerHTMLXSS:
    """JS_INNERHTML_XSS rule."""

    def test_dynamic_innerhtml_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = 'element.innerHTML = "<b>" + userInput + "</b>";'
        issues = analyzer.analyze(code)
        xss = [i for i in issues if i["rule_name"] == "JS_INNERHTML_XSS"]
        assert len(xss) == 1
        assert xss[0]["severity"] == "High"
        assert xss[0]["rule_type"] == "Security"
        assert "innerHTML" in xss[0]["description"]

    def test_dynamic_outerhtml_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = "container.outerHTML = `<div>${data}</div>`;"
        issues = analyzer.analyze(code)
        xss = [i for i in issues if i["rule_name"] == "JS_INNERHTML_XSS"]
        assert len(xss) == 1
        assert "outerHTML" in xss[0]["description"]

    def test_direct_variable_assignment_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = "element.innerHTML = userInput;"
        issues = analyzer.analyze(code)
        xss = [i for i in issues if i["rule_name"] == "JS_INNERHTML_XSS"]
        assert len(xss) == 1

    def test_constant_string_innerhtml_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = 'element.innerHTML = "<p>Static content</p>";'
        issues = analyzer.analyze(code)
        xss = [i for i in issues if i["rule_name"] == "JS_INNERHTML_XSS"]
        assert len(xss) == 0

    def test_empty_string_innerhtml_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = 'element.innerHTML = "";'
        issues = analyzer.analyze(code)
        xss = [i for i in issues if i["rule_name"] == "JS_INNERHTML_XSS"]
        assert len(xss) == 0

    def test_constant_template_literal_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = "element.innerHTML = `<div>Static template</div>`;"
        issues = analyzer.analyze(code)
        xss = [i for i in issues if i["rule_name"] == "JS_INNERHTML_XSS"]
        assert len(xss) == 0

    def test_textcontent_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = "element.textContent = userInput;"
        issues = analyzer.analyze(code)
        xss = [i for i in issues if i["rule_name"] == "JS_INNERHTML_XSS"]
        assert len(xss) == 0

    def test_unrelated_property_assignment_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = "element.className = userInput;"
        issues = analyzer.analyze(code)
        xss = [i for i in issues if i["rule_name"] == "JS_INNERHTML_XSS"]
        assert len(xss) == 0


# ═══════════════════════════════════════════════════════════════════
# JS_DOCUMENT_WRITE
# ═══════════════════════════════════════════════════════════════════


class TestDocumentWrite:
    """JS_DOCUMENT_WRITE rule."""

    def test_document_write_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = 'document.write("<h1>Hello</h1>");'
        issues = analyzer.analyze(code)
        dw = [i for i in issues if i["rule_name"] == "JS_DOCUMENT_WRITE"]
        assert len(dw) == 1
        assert dw[0]["severity"] == "High"
        assert dw[0]["rule_type"] == "Security"
        assert "document.write" in dw[0]["description"]

    def test_document_writeln_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = "document.writeln(userData);"
        issues = analyzer.analyze(code)
        dw = [i for i in issues if i["rule_name"] == "JS_DOCUMENT_WRITE"]
        assert len(dw) == 1
        assert "document.writeln" in dw[0]["description"]

    def test_dynamic_document_write_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = 'document.write("<h1>" + msg + "</h1>");'
        issues = analyzer.analyze(code)
        dw = [i for i in issues if i["rule_name"] == "JS_DOCUMENT_WRITE"]
        assert len(dw) == 1

    def test_unrelated_object_write_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = 'writer.write("Hello");\nstream.writeln("Hi");'
        issues = analyzer.analyze(code)
        dw = [i for i in issues if i["rule_name"] == "JS_DOCUMENT_WRITE"]
        assert len(dw) == 0

    def test_document_getelementbyid_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = 'document.getElementById("out").textContent = userData;'
        issues = analyzer.analyze(code)
        dw = [i for i in issues if i["rule_name"] == "JS_DOCUMENT_WRITE"]
        assert len(dw) == 0


# ═══════════════════════════════════════════════════════════════════
# JS_SWITCH_FALLTHROUGH
# ═══════════════════════════════════════════════════════════════════


class TestSwitchFallthrough:
    """JS_SWITCH_FALLTHROUGH rule."""

    def test_simple_fallthrough_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
switch (action) {
    case "start":
        initialize();
    case "stop":
        cleanup();
        break;
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 1
        assert ft[0]["severity"] == "Medium"
        assert ft[0]["rule_type"] == "Bugs"
        assert "Switch fallthrough" in ft[0]["description"]

    def test_fallthrough_multiple_statements_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
switch (action) {
    case "start":
        var a = 1;
        initialize();
    case "stop":
        cleanup();
        break;
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 1

    def test_break_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
switch (action) {
    case "start":
        initialize();
        break;
    case "stop":
        cleanup();
        break;
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 0

    def test_return_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
function x() {
    switch (action) {
        case "start":
            initialize();
            return 1;
        case "stop":
            return 0;
    }
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 0

    def test_throw_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
switch (action) {
    case "start":
        throw new Error("bad");
    case "stop":
        break;
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 0

    def test_continue_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
while(true) {
    switch (action) {
        case "start":
            continue;
        case "stop":
            break;
    }
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 0

    def test_intentional_empty_case_grouping_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
switch (action) {
    case "start":
    case "begin":
        initialize();
        break;
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 0

    def test_multiple_independent_fallthrough_cases(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
switch (action) {
    case "1":
        do1();
    case "2":
        do2();
    case "3":
        break;
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 2

    def test_final_case_without_break_not_treated_as_fallthrough(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
switch (action) {
    case "start":
        break;
    case "stop":
        cleanup();
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 0

    def test_unrelated_non_switch_code_not_detected(self):
        analyzer = JavaScriptSemanticAnalyzer()
        code = """
var a = 1;
if (a) {
    b();
} else {
    c();
}
"""
        issues = analyzer.analyze(code)
        ft = [i for i in issues if i["rule_name"] == "JS_SWITCH_FALLTHROUGH"]
        assert len(ft) == 0


# ═══════════════════════════════════════════════════════════════════
# TypeScript isolation
# ═══════════════════════════════════════════════════════════════════


class TestTypeScriptIsolation:
    """Verify that TypeScript does NOT invoke the JavaScript semantic analyzer."""

    def test_typescript_does_not_get_js_semantic_rules(self):
        """The same code analyzed as TypeScript must not produce JS semantic findings."""
        sa = StaticAnalyzer()
        ts_code = """
function check(x) {
    if (x == 0) { return true; }
    var result = eval(userInput);
    document.write("test");
    element.innerHTML = userInput;
}
"""
        ts_issues = sa.analyze(ts_code, "TypeScript")
        js_semantic = [
            i
            for i in ts_issues
            if i.get("rule_name")
            in (
                "JS_LOOSE_EQUALITY",
                "JS_DANGEROUS_EVAL",
                "JS_INNERHTML_XSS",
                "JS_DOCUMENT_WRITE",
                "JS_SWITCH_FALLTHROUGH",
            )
        ]
        assert len(js_semantic) == 0, (
            f"TypeScript must not produce JS semantic findings; got: "
            f"{[i.get('rule_name') for i in js_semantic]}"
        )

    def test_javascript_does_get_js_semantic_rules(self):
        """The same code analyzed as JavaScript MUST produce JS semantic findings."""
        sa = StaticAnalyzer()
        js_code = """
function check(x) {
    if (x == 0) { return true; }
    var result = eval(userInput);
    document.write("test");
    element.innerHTML = userInput;
}
"""
        js_issues = sa.analyze(js_code, "JavaScript")
        js_semantic = [
            i
            for i in js_issues
            if i.get("rule_name")
            in (
                "JS_LOOSE_EQUALITY",
                "JS_DANGEROUS_EVAL",
                "JS_INNERHTML_XSS",
                "JS_DOCUMENT_WRITE",
                "JS_SWITCH_FALLTHROUGH",
            )
        ]
        assert len(js_semantic) >= 4


# ═══════════════════════════════════════════════════════════════════
# End-to-end pipeline tests
# ═══════════════════════════════════════════════════════════════════

FULL_JS_EXAMPLE = """
// Bug: loose equality
function check(x) {
    if (x == 0) { return true; }
}

// Bug: dangerous eval
var userInput = prompt("Code:");
eval(userInput);

// Bug: innerHTML XSS
element.innerHTML = "<b>" + userInput + "</b>";

// Bug: document.write
document.writeln(userInput);

// Bug: switch fallthrough
switch (action) {
    case 1:
        doIt();
    case 2:
        doThat();
        break;
}

// Safe: strict equality
function safe(x) {
    if (x === 0) { return true; }
}

// Safe: null check
function nullCheck(x) {
    if (x == null) { return "nil"; }
}

// Safe: constant eval
var safe2 = eval("1 + 1");

// Safe: constant innerHTML
element.innerHTML = "<b>Static</b>";

// Bug: var usage (existing regex rule)
var oldVar = 42;
"""


class TestE2EJavaScriptPipeline:
    """Verify that JavaScript semantic findings survive the complete pipeline."""

    def _get_fused_issues(self):
        sa = StaticAnalyzer()
        engine = HybridEngine()
        static_issues = sa.analyze(FULL_JS_EXAMPLE, "JavaScript")
        normalised = engine.normalize(static_issues, "Static")
        return engine.fuse(normalised, [])

    def test_loose_equality_in_fused(self):
        fused = self._get_fused_issues()
        le = [i for i in fused if "Loose equality" in i["description"]]
        assert len(le) >= 1

    def test_dangerous_eval_in_fused(self):
        fused = self._get_fused_issues()
        ev = [i for i in fused if "eval()" in i["description"]]
        assert len(ev) >= 1

    def test_innerhtml_xss_in_fused(self):
        fused = self._get_fused_issues()
        xss = [
            i
            for i in fused
            if "Cross-Site Scripting" in i["description"]
            and "innerHTML" in i["description"]
        ]
        assert len(xss) >= 1

    def test_document_write_in_fused(self):
        fused = self._get_fused_issues()
        dw = [i for i in fused if "document.writeln()" in i["description"]]
        assert len(dw) >= 1

    def test_switch_fallthrough_in_fused(self):
        fused = self._get_fused_issues()
        ft = [i for i in fused if "Switch fallthrough" in i["description"]]
        assert len(ft) >= 1

    def test_null_check_not_in_fused(self):
        fused = self._get_fused_issues()
        # The null check should NOT trigger loose equality
        null_le = [i for i in fused if "Loose equality" in i["description"]]
        # Only 1 loose equality finding (x == 0), not nullCheck
        assert len(null_le) == 1

    def test_constant_eval_not_in_fused(self):
        fused = self._get_fused_issues()
        const_eval = [
            i
            for i in fused
            if "eval" in i["description"].lower() and "1 + 1" in i["description"]
        ]
        assert len(const_eval) == 0

    def test_existing_var_usage_still_works(self):
        """The existing VAR_USAGE regex rule must still fire."""
        fused = self._get_fused_issues()
        var = [
            i
            for i in fused
            if "var" in i["description"].lower()
            and "let/const" in i["description"].lower()
        ]
        assert len(var) >= 1

    def test_safe_strict_equality_no_false_positives(self):
        """x === 0 must not appear as a loose equality finding."""
        fused = self._get_fused_issues()
        le = [i for i in fused if "Loose equality" in i["description"]]
        for issue in le:
            assert "===" not in issue["description"] or "'==='" in issue["description"]
