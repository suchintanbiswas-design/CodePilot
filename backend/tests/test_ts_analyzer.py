"""Tests for TypeScriptSemanticAnalyzer — Phase 1 rules."""

from app.engine.hybrid_engine import HybridEngine
from app.engine.static_analyzer import StaticAnalyzer
from app.engine.ts_analyzer import TypeScriptSemanticAnalyzer

# ═══════════════════════════════════════════════════════════════════
# TS_UNSAFE_ANY_DECLARATION
# ═══════════════════════════════════════════════════════════════════


class TestUnsafeAnyDeclaration:
    """TS_UNSAFE_ANY_DECLARATION rule."""

    def test_variable_any_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "let data: any;"
        issues = analyzer.analyze(code)
        any_decl = [i for i in issues if i["rule_name"] == "TS_UNSAFE_ANY_DECLARATION"]
        assert len(any_decl) == 1
        assert any_decl[0]["severity"] == "Medium"
        assert any_decl[0]["rule_type"] == "Type Safety"

    def test_parameter_any_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "function process(payload: any) {}"
        issues = analyzer.analyze(code)
        any_decl = [i for i in issues if i["rule_name"] == "TS_UNSAFE_ANY_DECLARATION"]
        assert len(any_decl) == 1

    def test_return_type_any_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "function getData(): any {}"
        issues = analyzer.analyze(code)
        any_decl = [i for i in issues if i["rule_name"] == "TS_UNSAFE_ANY_DECLARATION"]
        assert len(any_decl) == 1

    def test_class_property_any_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "class Example {\n    value: any;\n}"
        issues = analyzer.analyze(code)
        any_decl = [i for i in issues if i["rule_name"] == "TS_UNSAFE_ANY_DECLARATION"]
        assert len(any_decl) == 1

    def test_unknown_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "let data: unknown;"
        issues = analyzer.analyze(code)
        any_decl = [i for i in issues if i["rule_name"] == "TS_UNSAFE_ANY_DECLARATION"]
        assert len(any_decl) == 0

    def test_normal_typed_declarations_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "let value: string;\nfunction process(payload: MyType) {}"
        issues = analyzer.analyze(code)
        any_decl = [i for i in issues if i["rule_name"] == "TS_UNSAFE_ANY_DECLARATION"]
        assert len(any_decl) == 0

    def test_words_like_company_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "let company: string = 'anyValue';"
        issues = analyzer.analyze(code)
        any_decl = [i for i in issues if i["rule_name"] == "TS_UNSAFE_ANY_DECLARATION"]
        assert len(any_decl) == 0


# ═══════════════════════════════════════════════════════════════════
# TS_EXPLICIT_ANY_CAST
# ═══════════════════════════════════════════════════════════════════


class TestExplicitAnyCast:
    """TS_EXPLICIT_ANY_CAST rule."""

    def test_as_any_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "const data = response as any;"
        issues = analyzer.analyze(code)
        cast = [i for i in issues if i["rule_name"] == "TS_EXPLICIT_ANY_CAST"]
        assert len(cast) == 1
        assert cast[0]["severity"] == "High"
        assert cast[0]["rule_type"] == "Type Safety"

    def test_angle_bracket_any_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "const x = <any>input;"
        issues = analyzer.analyze(code)
        cast = [i for i in issues if i["rule_name"] == "TS_EXPLICIT_ANY_CAST"]
        assert len(cast) == 1

    def test_as_unknown_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "const data = response as unknown;"
        issues = analyzer.analyze(code)
        cast = [i for i in issues if i["rule_name"] == "TS_EXPLICIT_ANY_CAST"]
        assert len(cast) == 0

    def test_as_mytype_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "const data = response as User;\nconst y = <User>input;"
        issues = analyzer.analyze(code)
        cast = [i for i in issues if i["rule_name"] == "TS_EXPLICIT_ANY_CAST"]
        assert len(cast) == 0


# ═══════════════════════════════════════════════════════════════════
# Lexical Safety
# ═══════════════════════════════════════════════════════════════════


class TestLexicalSafety:
    """Verify that comments and strings containing 'any' do not false positive."""

    def test_comments_containing_any_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "// let fake: any;\n/* as any */"
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_strings_containing_any_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "const text = 'this contains any';\nconst x = \"as any\";"
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_template_strings_containing_any_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "const t = `template ${foo} with any and as any`;"
        issues = analyzer.analyze(code)
        assert len(issues) == 0


# ═══════════════════════════════════════════════════════════════════


class TestNonNullAssertion:
    def test_non_null_property_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "const name = user!.profile!.name;"
        issues = analyzer.analyze(code)
        assert len(issues) == 2
        assert issues[0]["rule_name"] == "TS_NON_NULL_ASSERTION"
        assert issues[1]["rule_name"] == "TS_NON_NULL_ASSERTION"

    def test_non_null_array_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "const value = users![0];"
        issues = analyzer.analyze(code)
        assert len(issues) == 1
        assert issues[0]["rule_name"] == "TS_NON_NULL_ASSERTION"

    def test_non_null_function_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = 'const element = document.getElementById("app")!;'
        issues = analyzer.analyze(code)
        assert len(issues) == 1
        assert issues[0]["rule_name"] == "TS_NON_NULL_ASSERTION"

    def test_logical_not_ignored(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "if (!value) { return; }"
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_inequality_ignored(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "if (a != null && b !== undefined && a! == b) { return; }"
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_comments_and_strings_ignored(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = """
        // The factorial is 5!
        const msg = "Error!";
        """
        issues = analyzer.analyze(code)
        assert len(issues) == 0


class TestBannedTypes:
    def test_banned_types_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = """
        let name: String;
        let enabled: Boolean;
        let count: Number;
        let data: Object;
        let key: Symbol;
        """
        issues = analyzer.analyze(code)
        assert len(issues) == 5
        types = [i["description"] for i in issues]
        assert any("'string'" in t for t in types)
        assert any("'boolean'" in t for t in types)
        assert any("'number'" in t for t in types)
        assert any("'object'" in t for t in types)
        assert any("'symbol'" in t for t in types)

    def test_banned_types_in_function_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "function check(name: String, enabled: Boolean): Number { return 1; }"
        issues = analyzer.analyze(code)
        assert len(issues) == 3

    def test_banned_types_in_class_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "class Example { value: Number; }"
        issues = analyzer.analyze(code)
        assert len(issues) == 1

    def test_lowercase_primitives_ignored(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = """
        let name: string;
        let enabled: boolean;
        let count: number;
        let data: object;
        let key: symbol;
        """
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_unrelated_identifiers_ignored(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = """
        let String = 5;
        const obj = { String: 12 };
        const myString = String("hello");
        """
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_comments_and_strings_ignored(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = """
        // let x: String;
        const msg = "value: Number";
        """
        issues = analyzer.analyze(code)
        assert len(issues) == 0


class TestCompilerIgnore:
    def test_ts_ignore_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "// @ts-ignore\nconst value: any = getValue();"
        issues = analyzer.analyze(code)
        assert len(issues) == 2
        ignore_issues = [i for i in issues if i["rule_name"] == "TS_COMPILER_IGNORE"]
        assert len(ignore_issues) == 1
        assert ignore_issues[0]["line_number"] == 1

    def test_ts_ignore_explanation_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "// @ts-ignore some explanation\nconst x = 1;"
        issues = analyzer.analyze(code)
        assert len(issues) == 1
        assert issues[0]["rule_name"] == "TS_COMPILER_IGNORE"

    def test_ts_nocheck_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "// @ts-nocheck\nconst x = 1;"
        issues = analyzer.analyze(code)
        assert len(issues) == 1
        assert issues[0]["rule_name"] == "TS_COMPILER_IGNORE"

    def test_whitespace_variations_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = """
        //    @ts-ignore
        //@ts-ignore
        // @ts-nocheck
        """
        issues = analyzer.analyze(code)
        assert len(issues) == 3

    def test_multiple_directives_detected_separately(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = """
        // @ts-ignore
        const value: any = getValue();

        // @ts-nocheck
        """
        issues = analyzer.analyze(code)
        ignore_issues = [i for i in issues if i["rule_name"] == "TS_COMPILER_IGNORE"]
        assert len(ignore_issues) == 2
        assert ignore_issues[0]["line_number"] == 2
        assert ignore_issues[1]["line_number"] == 5

    def test_ts_expect_error_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "// @ts-expect-error: API typing is temporarily incorrect\nconst x = 1;"
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_string_containing_ignore_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = 'const text = "// @ts-ignore";'
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_template_literal_containing_ignore_not_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "const text = `// @ts-ignore`;"
        issues = analyzer.analyze(code)
        assert len(issues) == 0

    def test_ordinary_comment_text_not_falsely_detected(self):
        analyzer = TypeScriptSemanticAnalyzer()
        code = "// Please ignore this ts-ignore thing\n// do not @ts-ignore it\n// @ts-ignoring"
        issues = analyzer.analyze(code)
        assert len(issues) == 0


# ═══════════════════════════════════════════════════════════════════
# Language Isolation & E2E
# ═══════════════════════════════════════════════════════════════════


class TestLanguageIsolation:
    """Verify JS/TS isolation."""

    def test_typescript_receives_ts_analyzer(self):
        sa = StaticAnalyzer()
        code = "let data: any;"
        issues = sa.analyze(code, "TypeScript")
        ts_issues = [i for i in issues if i["rule_name"] == "TS_UNSAFE_ANY_DECLARATION"]
        assert len(ts_issues) == 1

    def test_javascript_analyzer_rules_do_not_appear_for_typescript(self):
        sa = StaticAnalyzer()
        # Loose equality is a JS rule. TS analyzer should not flag it.
        code = "if (x == 0) { return true; }"
        issues = sa.analyze(code, "TypeScript")
        js_issues = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(js_issues) == 0

    def test_javascript_still_receives_js_analyzer(self):
        sa = StaticAnalyzer()
        code = "function check(x) { if (x == 0) { return true; } }"
        issues = sa.analyze(code, "JavaScript")
        js_issues = [i for i in issues if i["rule_name"] == "JS_LOOSE_EQUALITY"]
        assert len(js_issues) == 1


FULL_TS_EXAMPLE = """
// @ts-ignore
// Bug: unsafe any declaration
let data: any;

// Bug: explicit any cast
const value = input as any;

// Safe: unknown
let safe: unknown;

// Safe lexical:
const msg = "no as any inside here";
"""


class TestE2ETypescriptPipeline:
    def test_e2e_findings_reach_unified_list(self):
        sa = StaticAnalyzer()
        engine = HybridEngine()

        static_issues = sa.analyze(FULL_TS_EXAMPLE, "TypeScript")
        normalised = engine.normalize(static_issues, "Static")
        fused = engine.fuse(normalised, [])

        any_decl = [i for i in fused if "Unsafe 'any' declaration" in i["description"]]
        assert len(any_decl) >= 1

        any_cast = [i for i in fused if "Explicit 'any' cast" in i["description"]]
        assert len(any_cast) >= 1

        lexical_fp = [i for i in fused if "no as any inside here" in i["description"]]
        assert len(lexical_fp) == 0

        ts_ignore = [i for i in fused if "Compiler Suppression" in i["description"]]
        assert len(ts_ignore) >= 1
