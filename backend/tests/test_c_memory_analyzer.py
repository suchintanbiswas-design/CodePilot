import pytest
from app.engine.c_memory_analyzer import CMemoryAnalyzer
from app.engine.static_analyzer import StaticAnalyzer
from app.engine.hybrid_engine import HybridEngine


# ---------------------------------------------------------------------------
# Unit-level CMemoryAnalyzer tests
# ---------------------------------------------------------------------------

class TestDoubleFree:
    """C_DOUBLE_FREE rule."""

    def test_double_free_via_alias(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *data = malloc(sizeof(int) * 10);
            int *alias = data;
            free(data);
            free(alias);
        }
        """
        issues = analyzer.analyze(code)
        df = [i for i in issues if i["rule_name"] == "C_DOUBLE_FREE"]
        assert len(df) == 1
        assert "alias" in df[0]["description"]
        assert df[0]["severity"] == "Critical"

    def test_double_free_same_pointer(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *p = malloc(sizeof(int));
            free(p);
            free(p);
        }
        """
        issues = analyzer.analyze(code)
        df = [i for i in issues if i["rule_name"] == "C_DOUBLE_FREE"]
        assert len(df) == 1

    def test_safe_independent_allocations(self):
        """Two separate malloc/free pairs must NOT trigger double free."""
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *a = malloc(sizeof(int));
            int *b = malloc(sizeof(int));
            free(a);
            free(b);
        }
        """
        issues = analyzer.analyze(code)
        df = [i for i in issues if i["rule_name"] == "C_DOUBLE_FREE"]
        assert len(df) == 0

    def test_double_free_chain_of_aliases(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *a = malloc(sizeof(int));
            int *b = a;
            int *c = b;
            free(a);
            free(c);
        }
        """
        issues = analyzer.analyze(code)
        df = [i for i in issues if i["rule_name"] == "C_DOUBLE_FREE"]
        assert len(df) == 1

    def test_safe_multiple_functions(self):
        """Each function has independent state — no cross-function false positives."""
        analyzer = CMemoryAnalyzer()
        code = """
        void func1() {
            int *p = malloc(sizeof(int));
            free(p);
        }
        void func2() {
            int *p = malloc(sizeof(int));
            free(p);
        }
        """
        issues = analyzer.analyze(code)
        df = [i for i in issues if i["rule_name"] == "C_DOUBLE_FREE"]
        assert len(df) == 0


class TestUseAfterFree:
    """C_USE_AFTER_FREE rule."""

    def test_array_access_after_free(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            char *buf = malloc(100);
            free(buf);
            buf[0] = 'A';
        }
        """
        issues = analyzer.analyze(code)
        uaf = [i for i in issues if i["rule_name"] == "C_USE_AFTER_FREE"]
        assert len(uaf) == 1
        assert "buf" in uaf[0]["description"]
        assert uaf[0]["severity"] == "Critical"

    def test_deref_after_free(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *p = malloc(sizeof(int));
            free(p);
            *p = 42;
        }
        """
        issues = analyzer.analyze(code)
        uaf = [i for i in issues if i["rule_name"] == "C_USE_AFTER_FREE"]
        assert len(uaf) == 1

    def test_member_access_after_free(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            struct Node *n = malloc(sizeof(struct Node));
            free(n);
            n->value = 10;
        }
        """
        issues = analyzer.analyze(code)
        uaf = [i for i in issues if i["rule_name"] == "C_USE_AFTER_FREE"]
        assert len(uaf) == 1

    def test_safe_reassignment_after_free(self):
        """Reassignment to a new allocation clears the freed state."""
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            char *buf = malloc(100);
            free(buf);
            buf = malloc(200);
            buf[0] = 'A';
            free(buf);
        }
        """
        issues = analyzer.analyze(code)
        uaf = [i for i in issues if i["rule_name"] == "C_USE_AFTER_FREE"]
        assert len(uaf) == 0
        df = [i for i in issues if i["rule_name"] == "C_DOUBLE_FREE"]
        assert len(df) == 0

    def test_safe_no_use_after_free(self):
        """Normal usage then free — no issue."""
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *arr = malloc(sizeof(int) * 10);
            arr[0] = 1;
            arr[1] = 2;
            free(arr);
        }
        """
        issues = analyzer.analyze(code)
        uaf = [i for i in issues if i["rule_name"] == "C_USE_AFTER_FREE"]
        assert len(uaf) == 0


class TestMallocFreeMismatch:
    """C_MALLOC_FREE_MISMATCH rule."""

    def test_free_stack_pointer(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int x = 42;
            int *ptr = &x;
            free(ptr);
        }
        """
        issues = analyzer.analyze(code)
        mm = [i for i in issues if i["rule_name"] == "C_MALLOC_FREE_MISMATCH"]
        assert len(mm) == 1
        assert "stack" in mm[0]["description"]
        assert mm[0]["severity"] == "Critical"

    def test_free_string_literal(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            char *msg = "hello world";
            free(msg);
        }
        """
        issues = analyzer.analyze(code)
        mm = [i for i in issues if i["rule_name"] == "C_MALLOC_FREE_MISMATCH"]
        assert len(mm) == 1
        assert "static" in mm[0]["description"]

    def test_valid_malloc_free(self):
        """Normal heap allocation and free — no mismatch."""
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *ptr = malloc(sizeof(int));
            *ptr = 42;
            free(ptr);
        }
        """
        issues = analyzer.analyze(code)
        mm = [i for i in issues if i["rule_name"] == "C_MALLOC_FREE_MISMATCH"]
        assert len(mm) == 0

    def test_calloc_free_valid(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *arr = calloc(10, sizeof(int));
            arr[0] = 5;
            free(arr);
        }
        """
        issues = analyzer.analyze(code)
        mm = [i for i in issues if i["rule_name"] == "C_MALLOC_FREE_MISMATCH"]
        assert len(mm) == 0

    def test_free_stack_via_alias(self):
        """Stack pointer passed through an alias — still a mismatch."""
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int x = 10;
            int *p = &x;
            int *q = p;
            free(q);
        }
        """
        issues = analyzer.analyze(code)
        mm = [i for i in issues if i["rule_name"] == "C_MALLOC_FREE_MISMATCH"]
        assert len(mm) == 1

class TestNullDerefAfterMalloc:
    """C_NULL_DEREF_AFTER_MALLOC rule."""

    def test_unchecked_malloc(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *arr = malloc(100 * sizeof(int));
            arr[0] = 42;
            free(arr);
        }
        """
        issues = analyzer.analyze(code)
        nd = [i for i in issues if i["rule_name"] == "C_NULL_DEREF_AFTER_MALLOC"]
        assert len(nd) == 1

    def test_unchecked_calloc(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *ptr = calloc(10, sizeof(int));
            *ptr = 10;
            free(ptr);
        }
        """
        issues = analyzer.analyze(code)
        nd = [i for i in issues if i["rule_name"] == "C_NULL_DEREF_AFTER_MALLOC"]
        assert len(nd) == 1

    def test_safe_if_ptr_equals_null_return(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *arr = malloc(100 * sizeof(int));
            if (arr == NULL) {
                return;
            }
            arr[0] = 42;
            free(arr);
        }
        """
        issues = analyzer.analyze(code)
        nd = [i for i in issues if i["rule_name"] == "C_NULL_DEREF_AFTER_MALLOC"]
        assert len(nd) == 0

    def test_safe_if_not_ptr_return(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *arr = calloc(10, sizeof(int));
            if (!arr) return;
            *arr = 10;
            free(arr);
        }
        """
        issues = analyzer.analyze(code)
        nd = [i for i in issues if i["rule_name"] == "C_NULL_DEREF_AFTER_MALLOC"]
        assert len(nd) == 0

    def test_safe_if_ptr_check(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *ptr = malloc(10);
            if (ptr) {
                *ptr = 10;
            }
            free(ptr);
        }
        """
        issues = analyzer.analyze(code)
        nd = [i for i in issues if i["rule_name"] == "C_NULL_DEREF_AFTER_MALLOC"]
        assert len(nd) == 0

    def test_safe_if_ptr_not_equals_null(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *ptr = malloc(10);
            if (ptr != NULL) {
                *ptr = 10;
            }
            free(ptr);
        }
        """
        issues = analyzer.analyze(code)
        nd = [i for i in issues if i["rule_name"] == "C_NULL_DEREF_AFTER_MALLOC"]
        assert len(nd) == 0

    def test_reassignment_followed_by_new_check(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *ptr = malloc(10);
            if (!ptr) return;
            *ptr = 1;
            free(ptr);
            ptr = malloc(20);
            *ptr = 2; // Should trigger here!
            free(ptr);
        }
        """
        issues = analyzer.analyze(code)
        nd = [i for i in issues if i["rule_name"] == "C_NULL_DEREF_AFTER_MALLOC"]
        assert len(nd) == 1

    def test_stack_pointer_safe_case(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int x = 42;
            int *ptr = &x;
            *ptr = 10;
        }
        """
        issues = analyzer.analyze(code)
        nd = [i for i in issues if i["rule_name"] == "C_NULL_DEREF_AFTER_MALLOC"]
        assert len(nd) == 0

    def test_multiple_allocations_different_checks(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *a = malloc(10);
            int *b = malloc(10);
            if (a == NULL) return;
            *a = 1;
            *b = 2; // b is unchecked!
        }
        """
        issues = analyzer.analyze(code)
        nd = [i for i in issues if i["rule_name"] == "C_NULL_DEREF_AFTER_MALLOC"]
        assert len(nd) == 1
        assert "b" in nd[0]["description"]


class TestMemoryLeak:
    """C_MEMORY_LEAK rule."""

    def test_obvious_malloc_leak(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *data = malloc(100);
            data[0] = 42;
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 1
        assert "data" in leaks[0]["description"]

    def test_obvious_calloc_leak(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *data = calloc(10, sizeof(int));
            data[0] = 42;
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 1

    def test_overwritten_pointer_leak(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *data = malloc(100);
            data = malloc(200);
            free(data);
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 1
        assert "overwritten" in leaks[0]["description"]

    def test_proper_malloc_free(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *data = malloc(100);
            data[0] = 42;
            free(data);
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 0

    def test_returned_allocation(self):
        analyzer = CMemoryAnalyzer()
        code = """
        int* create_buffer() {
            int *data = malloc(100);
            return data;
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 0

    def test_passed_to_function_allocation(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void consume(int *ptr);
        void process() {
            int *data = malloc(100);
            consume(data);
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 0

    def test_properly_freed_on_all_paths(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process(int err) {
            int *data = malloc(100);
            if (err) {
                free(data);
                return;
            }
            data[0] = 1;
            free(data);
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 0

    def test_multiple_independent_allocations_leak_one(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *a = malloc(10);
            int *b = malloc(10);
            free(a);
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 1
        assert "b" in leaks[0]["description"]

    def test_interaction_with_double_free_use_after_free(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *a = malloc(10);
            free(a);
            free(a); // Double free
            
            int *b = malloc(10);
            // leaks b
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 1
        df = [i for i in issues if i["rule_name"] == "C_DOUBLE_FREE"]
        assert len(df) == 1

    def test_branch_early_return_leak(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process(int err) {
            int *data = malloc(100);
            if (err) {
                return; // Leak here!
            }
            free(data);
        }
        """
        issues = analyzer.analyze(code)
        leaks = [i for i in issues if i["rule_name"] == "C_MEMORY_LEAK"]
        assert len(leaks) == 1
        # The line reported should ideally be the return line or function exit.
        assert leaks[0]["line_number"] == 5

class TestMultiplePointers:
    """Tests with multiple independent pointers to verify no cross-contamination."""

    def test_multiple_independent_pointers(self):
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *a = malloc(sizeof(int));
            int *b = malloc(sizeof(int));
            int *c = malloc(sizeof(int));
            *a = 1;
            *b = 2;
            *c = 3;
            free(a);
            free(b);
            free(c);
        }
        """
        issues = analyzer.analyze(code)
        issues = [i for i in issues if "NULL_DEREF" not in i["rule_name"]]
        assert len(issues) == 0

    def test_mixed_safe_and_buggy(self):
        """One pointer is buggy (double free), others are safe."""
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *safe1 = malloc(sizeof(int));
            int *safe2 = malloc(sizeof(int));
            int *buggy = malloc(sizeof(int));
            int *alias = buggy;
            free(safe1);
            free(buggy);
            free(alias);
            free(safe2);
        }
        """
        issues = analyzer.analyze(code)
        df = [i for i in issues if i["rule_name"] == "C_DOUBLE_FREE"]
        assert len(df) == 1
        assert "alias" in df[0]["description"]
        # safe1 and safe2 should not trigger anything
        mm = [i for i in issues if i["rule_name"] == "C_MALLOC_FREE_MISMATCH"]
        assert len(mm) == 0
        uaf = [i for i in issues if i["rule_name"] == "C_USE_AFTER_FREE"]
        assert len(uaf) == 0
        assert len(uaf) == 0

    def test_safe_usage_with_null_check_early_return(self):
        """Exact test_safe_usage regression — no false positives from early returns."""
        analyzer = CMemoryAnalyzer()
        code = """
        void test_safe_usage() {
            int *a = malloc(sizeof(int));
            int *b = malloc(sizeof(int));

            if (a == NULL || b == NULL) {
                free(a);
                free(b);
                return;
            }

            *a = 10;
            *b = 20;

            printf("%d %d\\n", *a, *b);

            free(a);
            free(b);
        }
        """
        issues = analyzer.analyze(code)
        assert len(issues) == 0, f"Expected 0 issues, got {issues}"

    def test_mixed_branch_safe_and_buggy(self):
        """Ensure state tracking remains independent across branches for multiple pointers."""
        analyzer = CMemoryAnalyzer()
        code = """
        void process() {
            int *safe = malloc(10);
            int *buggy = malloc(10);

            if (safe == NULL) {
                free(safe);
                free(buggy);
                return;
            }
            
            free(buggy);
            *buggy = 5;  // Real UAF
            
            *safe = 10;  // Safe use
            free(safe);
        }
        """
        issues = analyzer.analyze(code)
        # Should only report UAF for 'buggy' (and possibly NULL deref, so filter)
        uaf = [i for i in issues if i["rule_name"] == "C_USE_AFTER_FREE"]
        assert len(uaf) == 1
        assert "buggy" in uaf[0]["description"]


# ---------------------------------------------------------------------------
# Full end-to-end integration test
# ---------------------------------------------------------------------------

FULL_C_EXAMPLE = r"""
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

struct Node {
    int value;
    struct Node *next;
};

void double_free_bug() {
    int *data = malloc(sizeof(int) * 10);
    int *alias = data;
    free(data);
    free(alias);
}

void use_after_free_bug() {
    char *buffer = malloc(256);
    strcpy(buffer, "hello");
    free(buffer);
    buffer[0] = 'X';
}

void stack_free_bug() {
    int local = 42;
    int *ptr = &local;
    free(ptr);
}

void string_free_bug() {
    char *msg = "constant string";
    free(msg);
}

void unchecked_deref_bug() {
    int *nums = malloc(10 * sizeof(int));
    nums[0] = 5; // Bug: no null check
    free(nums);
}

void memory_leak_bug() {
    int *leak = malloc(100);
    if (!leak) return;
    leak[0] = 5;
    // Bug: no free
}

void safe_function() {
    int *a = malloc(sizeof(int));
    int *b = malloc(sizeof(int));
    if (a == NULL || b == NULL) {
        free(a);
        free(b);
        return;
    }
    *a = 10;
    *b = 20;
    printf("a=%d b=%d\\n", *a, *b);
    free(a);
    free(b);
}

void safe_reassign() {
    char *buf = malloc(100);
    free(buf);
    buf = malloc(200);
    if (!buf) {
        free(buf);
        return;
    }
    buf[0] = 'A';
    free(buf);
}

int main() {
    double_free_bug();
    use_after_free_bug();
    stack_free_bug();
    string_free_bug();
    unchecked_deref_bug();
    memory_leak_bug();
    safe_function();
    safe_reassign();
    return 0;
}
"""


class TestE2EFullCPipeline:
    """Verify that C memory findings survive the complete pipeline."""

    def _get_fused_issues(self):
        sa = StaticAnalyzer()
        engine = HybridEngine()
        static_issues = sa.analyze(FULL_C_EXAMPLE, "C")
        normalised = engine.normalize(static_issues, "Static")
        return engine.fuse(normalised, [])

    def test_double_free_in_fused(self):
        fused = self._get_fused_issues()
        df = [i for i in fused if "Double free" in i["description"]]
        assert len(df) >= 1, (
            f"Expected double-free finding; got: "
            f"{[i['description'] for i in fused]}"
        )

    def test_use_after_free_in_fused(self):
        fused = self._get_fused_issues()
        uaf = [i for i in fused if "Use-after-free" in i["description"]]
        assert len(uaf) >= 1

    def test_stack_free_mismatch_in_fused(self):
        fused = self._get_fused_issues()
        mm = [i for i in fused if "stack pointer" in i["description"]]
        assert len(mm) >= 1

    def test_static_free_mismatch_in_fused(self):
        fused = self._get_fused_issues()
        mm = [i for i in fused if "static" in i["description"].lower()
              and "free()" in i["description"]]
        assert len(mm) >= 1

    def test_null_deref_in_fused(self):
        fused = self._get_fused_issues()
        nd = [i for i in fused if "before being checked for NULL" in i["description"]]
        assert len(nd) >= 1

    def test_memory_leak_in_fused(self):
        fused = self._get_fused_issues()
        ml = [i for i in fused if "Memory leak:" in i["description"]]
        assert len(ml) >= 1

    def test_safe_functions_no_false_positives(self):
        """safe_function and safe_reassign should not produce Memory/Safety findings."""
        fused = self._get_fused_issues()
        mem = [i for i in fused if i.get("rule_type") == "Memory/Safety"]
        # 7 real bugs — no false positives from safe functions
        assert len(mem) == 7, (
            f"Expected exactly 7 Memory/Safety findings; got {len(mem)}: "
            f"{[i['description'][:60] for i in mem]}"
        )
