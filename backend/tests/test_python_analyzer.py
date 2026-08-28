"""Tests for PythonSemanticAnalyzer — Phase 1 rules."""
import pytest
from app.engine.python_analyzer import PythonSemanticAnalyzer
from app.engine.static_analyzer import StaticAnalyzer
from app.engine.hybrid_engine import HybridEngine


# ═══════════════════════════════════════════════════════════════════
# PY_MUTABLE_DEFAULT_ARG
# ═══════════════════════════════════════════════════════════════════

class TestMutableDefaultArg:
    """PY_MUTABLE_DEFAULT_ARG rule."""

    def test_list_default_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def add_item(item, items=[]):
    items.append(item)
    return items
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 1
        assert "items" in md[0]["description"] or "[]" in md[0]["description"]
        assert md[0]["severity"] == "High"
        assert md[0]["rule_type"] == "Bugs"

    def test_dict_default_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def config(options={}):
    options["key"] = "value"
    return options
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 1
        assert "{}" in md[0]["description"]

    def test_set_constructor_default_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def values(items=set()):
    items.add(1)
    return items
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 1
        assert "set()" in md[0]["description"]

    def test_list_constructor_default_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def process(data=list()):
    data.append(1)
    return data
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 1
        assert "list()" in md[0]["description"]

    def test_dict_constructor_default_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def process(cache=dict()):
    return cache
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 1
        assert "dict()" in md[0]["description"]

    def test_bytearray_constructor_default_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def process(buf=bytearray()):
    buf.extend(b'data')
    return buf
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 1
        assert "bytearray()" in md[0]["description"]

    def test_none_sentinel_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 0

    def test_immutable_int_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def process(x=10):
    return x + 1
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 0

    def test_immutable_string_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def greet(name="world"):
    return f"Hello, {name}!"
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 0

    def test_immutable_tuple_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def f(x=(1, 2, 3)):
    return sum(x)
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 0

    def test_immutable_bool_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def f(verbose=False):
    pass
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 0

    def test_async_function_default_handled(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
async def fetch(headers={}):
    pass
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 1
        assert "{}" in md[0]["description"]
        assert "fetch" in md[0]["description"]

    def test_kwonly_default_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def process(*, cache={}):
    return cache
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 1

    def test_multiple_mutable_defaults(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
def process(a=[], b={}, c=set()):
    pass
"""
        issues = analyzer.analyze(code)
        md = [i for i in issues if i["rule_name"] == "PY_MUTABLE_DEFAULT_ARG"]
        assert len(md) == 3


# ═══════════════════════════════════════════════════════════════════
# PY_DANGEROUS_EVAL
# ═══════════════════════════════════════════════════════════════════

class TestDangerousEval:
    """PY_DANGEROUS_EVAL rule."""

    def test_dynamic_eval_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
user_input = input("Expression: ")
result = eval(user_input)
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if "PY_DANGEROUS" in i["rule_name"]]
        assert len(ev) == 1
        assert ev[0]["severity"] == "Critical"
        assert ev[0]["rule_type"] == "Security"
        assert "eval" in ev[0]["description"].lower()

    def test_dynamic_exec_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
code = input("Code: ")
exec(code)
"""
        issues = analyzer.analyze(code)
        ex = [i for i in issues if "PY_DANGEROUS" in i["rule_name"]]
        assert len(ex) == 1
        assert ex[0]["severity"] == "Critical"
        assert "exec" in ex[0]["description"].lower()

    def test_constant_string_eval_suppressed(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
result = eval("1 + 2")
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if "PY_DANGEROUS" in i["rule_name"]]
        assert len(ev) == 0

    def test_constant_string_exec_suppressed(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
exec("print('hello')")
"""
        issues = analyzer.analyze(code)
        ex = [i for i in issues if "PY_DANGEROUS" in i["rule_name"]]
        assert len(ex) == 0

    def test_unrelated_function_calls_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
import math
x = math.sqrt(16)
y = len([1, 2, 3])
z = print("hello")
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if "PY_DANGEROUS" in i["rule_name"]]
        assert len(ev) == 0

    def test_eval_no_args(self):
        """eval() with no arguments should still be flagged."""
        analyzer = PythonSemanticAnalyzer()
        code = """
eval()
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if "PY_DANGEROUS" in i["rule_name"]]
        assert len(ev) == 1

    def test_eval_with_variable_arg(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
expr = get_expression()
val = eval(expr)
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if "PY_DANGEROUS" in i["rule_name"]]
        assert len(ev) == 1

    def test_eval_with_fstring_arg(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
x = 5
result = eval(f"{x} + 1")
"""
        issues = analyzer.analyze(code)
        ev = [i for i in issues if "PY_DANGEROUS" in i["rule_name"]]
        assert len(ev) == 1


# ═══════════════════════════════════════════════════════════════════
# PY_BROAD_EXCEPTION
# ═══════════════════════════════════════════════════════════════════

class TestBroadException:
    """PY_BROAD_EXCEPTION rule."""

    def test_except_exception_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
try:
    process_data()
except Exception:
    pass
"""
        issues = analyzer.analyze(code)
        be = [i for i in issues if i["rule_name"] == "PY_BROAD_EXCEPTION"]
        assert len(be) == 1
        assert be[0]["severity"] == "High"
        assert "Exception" in be[0]["description"]

    def test_except_exception_as_e_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
try:
    process_data()
except Exception as e:
    logger.error(e)
"""
        issues = analyzer.analyze(code)
        be = [i for i in issues if i["rule_name"] == "PY_BROAD_EXCEPTION"]
        assert len(be) == 1

    def test_except_baseexception_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
try:
    process_data()
except BaseException:
    handle_error()
"""
        issues = analyzer.analyze(code)
        be = [i for i in issues if i["rule_name"] == "PY_BROAD_EXCEPTION"]
        assert len(be) == 1
        assert "BaseException" in be[0]["description"]

    def test_except_tuple_containing_exception_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
try:
    process_data()
except (ValueError, Exception):
    pass
"""
        issues = analyzer.analyze(code)
        be = [i for i in issues if i["rule_name"] == "PY_BROAD_EXCEPTION"]
        assert len(be) == 1
        assert "Exception" in be[0]["description"]

    def test_explicit_reraise_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
try:
    process_data()
except Exception:
    logger.exception("error")
    raise
"""
        issues = analyzer.analyze(code)
        be = [i for i in issues if i["rule_name"] == "PY_BROAD_EXCEPTION"]
        assert len(be) == 0

    def test_bare_except_handled_by_existing_rule(self):
        """Bare except: should not be handled here, avoiding duplicate findings."""
        analyzer = PythonSemanticAnalyzer()
        code = """
try:
    process_data()
except:
    pass
"""
        issues = analyzer.analyze(code)
        be = [i for i in issues if i["rule_name"] == "PY_BROAD_EXCEPTION"]
        assert len(be) == 0

    def test_specific_exception_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
try:
    process_data()
except ValueError:
    pass
"""
        issues = analyzer.analyze(code)
        be = [i for i in issues if i["rule_name"] == "PY_BROAD_EXCEPTION"]
        assert len(be) == 0


# ═══════════════════════════════════════════════════════════════════
# PY_IS_LITERAL_COMPARISON
# ═══════════════════════════════════════════════════════════════════

class TestIsLiteralComparison:
    """PY_IS_LITERAL_COMPARISON rule."""

    def test_is_zero_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
if x is 0:
    pass
"""
        issues = analyzer.analyze(code)
        ilc = [i for i in issues if i["rule_name"] == "PY_IS_LITERAL_COMPARISON"]
        assert len(ilc) == 1
        assert ilc[0]["severity"] == "Medium"
        assert "0" in ilc[0]["description"]

    def test_is_text_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
if name is "admin":
    pass
"""
        issues = analyzer.analyze(code)
        ilc = [i for i in issues if i["rule_name"] == "PY_IS_LITERAL_COMPARISON"]
        assert len(ilc) == 1
        assert "admin" in ilc[0]["description"]

    def test_is_list_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
if values is []:
    pass
"""
        issues = analyzer.analyze(code)
        ilc = [i for i in issues if i["rule_name"] == "PY_IS_LITERAL_COMPARISON"]
        assert len(ilc) == 1
        assert "[]" in ilc[0]["description"]

    def test_is_dict_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
if data is {}:
    pass
"""
        issues = analyzer.analyze(code)
        ilc = [i for i in issues if i["rule_name"] == "PY_IS_LITERAL_COMPARISON"]
        assert len(ilc) == 1
        assert "{}" in ilc[0]["description"]

    def test_is_none_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
if x is None:
    pass
"""
        issues = analyzer.analyze(code)
        ilc = [i for i in issues if i["rule_name"] == "PY_IS_LITERAL_COMPARISON"]
        assert len(ilc) == 0

    def test_is_not_none_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
if x is not None:
    pass
"""
        issues = analyzer.analyze(code)
        ilc = [i for i in issues if i["rule_name"] == "PY_IS_LITERAL_COMPARISON"]
        assert len(ilc) == 0

    def test_is_true_false_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
if flag is True:
    pass
if done is False:
    pass
"""
        issues = analyzer.analyze(code)
        ilc = [i for i in issues if i["rule_name"] == "PY_IS_LITERAL_COMPARISON"]
        assert len(ilc) == 0

    def test_valid_equality_comparisons_not_detected(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
if x == 0:
    pass
if name == "admin":
    pass
if values == []:
    pass
"""
        issues = analyzer.analyze(code)
        ilc = [i for i in issues if i["rule_name"] == "PY_IS_LITERAL_COMPARISON"]
        assert len(ilc) == 0


# ═══════════════════════════════════════════════════════════════════
# PY_OS_SYSTEM_INJECTION
# ═══════════════════════════════════════════════════════════════════

class TestOsSystemInjection:
    """PY_OS_SYSTEM_INJECTION rule."""

    def test_os_system_with_user_input(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
import os
filename = input("Enter filename: ")
os.system(filename)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 1
        assert osi[0]["severity"] == "Critical"
        assert osi[0]["rule_type"] == "Security"
        assert "os.system" in osi[0]["description"]

    def test_os_popen_with_user_input(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
import os
os.popen(cmd)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 1
        assert "os.popen" in osi[0]["description"]

    def test_subprocess_run_shell_true_with_user_input(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
import subprocess
subprocess.run(command, shell=True)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 1
        assert "subprocess.run" in osi[0]["description"]

    def test_subprocess_call_shell_true(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
import subprocess
subprocess.call(args=cmd, shell=True)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 1
        assert "subprocess.call" in osi[0]["description"]

    def test_subprocess_popen_shell_true(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
import subprocess
subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 1
        assert "subprocess.Popen" in osi[0]["description"]

    def test_concatenated_command(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
import os
os.system("rm " + filename)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 1

    def test_fstring_command(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
import os
os.system(f"rm {filename}")
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 1

    def test_safe_list_argument_subprocess(self):
        """Standard safe usage of subprocess with a list of arguments and shell=False (default)."""
        analyzer = PythonSemanticAnalyzer()
        code = """
import subprocess
subprocess.run(["rm", filename], check=True)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 0

    def test_subprocess_without_shell_true(self):
        """Even if the command is dynamic, without shell=True it shouldn't trigger this rule."""
        analyzer = PythonSemanticAnalyzer()
        code = """
import subprocess
subprocess.run(cmd)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 0

    def test_unrelated_system_function(self):
        analyzer = PythonSemanticAnalyzer()
        code = """
my_obj.system(cmd)
system(cmd)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 0

    def test_suppress_static_command(self):
        """Ensure static strings don't trigger the rule, even with shell=True or os.system."""
        analyzer = PythonSemanticAnalyzer()
        code = """
import os
import subprocess
os.system("ls -la")
subprocess.run("ls -la", shell=True)
subprocess.run(["ls", "-la"], shell=True)
"""
        issues = analyzer.analyze(code)
        osi = [i for i in issues if i["rule_name"] == "PY_OS_SYSTEM_INJECTION"]
        assert len(osi) == 0


# ═══════════════════════════════════════════════════════════════════
# End-to-end pipeline tests
# ═══════════════════════════════════════════════════════════════════

FULL_PYTHON_EXAMPLE = """
import os

# Bug: mutable default
def add_item(item, items=[]):
    items.append(item)
    return items

# Bug: dangerous eval
user_input = input("Enter expression: ")
result = eval(user_input)

# Bug: broad exception
try:
    process()
except Exception as e:
    print(e)

# Bug: is literal comparison
if user_input is "":
    pass

# Bug: os system injection
command = input("Command: ")
os.system(f"run {command}")

# Safe: None sentinel
def safe_add(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items

# Safe: constant eval
safe_result = eval("1 + 2")

# Bug: bare except (existing regex rule)
try:
    process()
except:
    pass

# Safe: singleton comparison
if user_input is None:
    pass
"""


class TestE2EPythonPipeline:
    """Verify that Python semantic findings survive the complete pipeline."""

    def _get_fused_issues(self):
        sa = StaticAnalyzer()
        engine = HybridEngine()
        static_issues = sa.analyze(FULL_PYTHON_EXAMPLE, "Python")
        normalised = engine.normalize(static_issues, "Static")
        return engine.fuse(normalised, [])

    def test_mutable_default_in_fused(self):
        fused = self._get_fused_issues()
        md = [i for i in fused if "Mutable default" in i["description"]]
        assert len(md) >= 1, (
            f"Expected mutable default finding; got: "
            f"{[i['description'][:60] for i in fused]}"
        )

    def test_dangerous_eval_in_fused(self):
        fused = self._get_fused_issues()
        ev = [i for i in fused if "eval()" in i["description"]]
        assert len(ev) >= 1, (
            f"Expected dangerous eval finding; got: "
            f"{[i['description'][:60] for i in fused]}"
        )

    def test_broad_exception_in_fused(self):
        fused = self._get_fused_issues()
        be = [i for i in fused if "Catch-all exception" in i["description"]]
        assert len(be) >= 1, (
            f"Expected broad exception finding; got: "
            f"{[i['description'][:60] for i in fused]}"
        )

    def test_is_literal_comparison_in_fused(self):
        fused = self._get_fused_issues()
        ilc = [i for i in fused if "Identity comparison" in i["description"]]
        assert len(ilc) >= 1, (
            f"Expected is literal comparison finding; got: "
            f"{[i['description'][:60] for i in fused]}"
        )

    def test_os_system_injection_in_fused(self):
        fused = self._get_fused_issues()
        osi = [i for i in fused if "Dangerous OS command execution" in i["description"]]
        assert len(osi) >= 1, (
            f"Expected OS command injection finding; got: "
            f"{[i['description'][:60] for i in fused]}"
        )

    def test_constant_eval_not_in_fused(self):
        fused = self._get_fused_issues()
        # The constant eval("1 + 2") should NOT appear
        const_eval = [
            i for i in fused
            if "eval" in i["description"].lower()
            and "1 + 2" in i["description"]
        ]
        assert len(const_eval) == 0

    def test_existing_catch_all_still_works(self):
        """The existing CATCH_ALL_PY regex rule must still fire."""
        fused = self._get_fused_issues()
        ca = [i for i in fused if "masks bugs" in i["description"]]
        assert len(ca) >= 1

    def test_safe_functions_no_false_positives(self):
        """safe_add with None sentinel should not trigger mutable default."""
        fused = self._get_fused_issues()
        md = [i for i in fused if "Mutable default" in i["description"]]
        # Only 1 mutable default (add_item), not safe_add
        assert len(md) == 1
        assert "add_item" in md[0]["description"]

