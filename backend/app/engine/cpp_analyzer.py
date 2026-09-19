import re
from typing import Any, Dict, List


class CppLifetimeAnalyzer:
    """
    Deterministic C++-specific analysis for lifetime bugs.
    Tracks symbols and relationships across the whole source using
    multi-pass discovery:

      Pass 1 (iterative fixpoint):
        - Discover std::vector<T> declarations
        - Track range-for references (auto& x : container)
        - Track return &element patterns (both indexed and range-for vars)
        - Map function names to vectors whose elements they return
        - Track assignments from those functions into variables
        - Track pointer-to-pointer copies that propagate vector aliases

      Pass 2 (linear):
        - Emit findings for vector mutations that invalidate tracked aliases
        - Emit findings for returning raw pointers to vector elements
        - Track new/delete for double-free detection
    """

    # C++ keywords that must never be mistaken for function declarations
    _CPP_KEYWORDS = frozenset(
        {
            "if",
            "else",
            "for",
            "while",
            "do",
            "switch",
            "case",
            "catch",
            "return",
            "sizeof",
            "alignof",
            "decltype",
            "static_assert",
            "throw",
            "try",
            "delete",
            "new",
            "typeid",
        }
    )

    def _is_function_decl(self, name: str) -> bool:
        """Return True if *name* looks like a real function/method name."""
        return name not in self._CPP_KEYWORDS

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []

        vectors: set[str] = set()
        vector_aliases: dict[str, str] = {}  # alias_name -> vector_name
        functions_returning_vector: dict[str, str] = {}  # func_name -> vector_name
        range_for_aliases: dict[str, str] = {}  # loop_var -> container_name

        raw_pointers: dict[str, str] = {}  # dest_ptr -> src_ptr | "allocated"
        deleted_pointers: set[str] = set()

        lines = code.split("\n")

        # ── Pass 1: multi-pass fixpoint discovery ──────────────────────
        changed = True
        while changed:
            changed = False
            current_function = None
            for line in lines:
                clean = re.sub(r"//.*", "", line)
                if "shared_ptr" in clean or "weak_ptr" in clean:
                    continue

                # Discover vector declarations
                m_vec = re.search(r"std::vector<[^>]+>\s+(\w+)", clean)
                if m_vec and m_vec.group(1) not in vectors:
                    vectors.add(m_vec.group(1))

                # Track current function name
                m_func = re.search(
                    r"(?:[\w:]+\s*\*?\s+)?([\w:]+)\s*\([^)]*\)\s*(?:const\s*)?\{",
                    clean,
                )
                if m_func:
                    candidate = m_func.group(1).split(":")[-1]
                    if self._is_function_decl(candidate):
                        current_function = candidate

                # Range-for: for (auto& book : inventory)
                m_range = re.search(
                    r"for\s*\(\s*(?:const\s+)?(?:auto|[\w:]+)\s*&\s*(\w+)\s*:\s*(\w+)\s*\)",
                    clean,
                )
                if m_range:
                    alias = m_range.group(1)
                    container = m_range.group(2)
                    if alias not in range_for_aliases:
                        range_for_aliases[alias] = container

                # return &element: indexed form  return &inventory[i];
                m_ret_idx = re.search(
                    r"return\s+&(\w+)(?:\[.*?\]|\.at\(.*?\))\s*;", clean
                )
                if m_ret_idx and current_function:
                    vec = m_ret_idx.group(1)
                    if current_function not in functions_returning_vector:
                        functions_returning_vector[current_function] = vec
                        changed = True

                # return &element: range-for form  return &book;
                m_ret_bare = re.search(r"return\s+&(\w+)\s*;", clean)
                if m_ret_bare and current_function:
                    var = m_ret_bare.group(1)
                    if var in range_for_aliases:
                        container = range_for_aliases[var]
                        if current_function not in functions_returning_vector:
                            functions_returning_vector[current_function] = container
                            changed = True

                # Assignment from a function call: dest = obj.func(...)
                m_assign = re.search(
                    r"(?:[\w:]+\s*\*\s+)?([\w:]+)\s*=\s*(?:[\w:]+\.)?([\w:]+)\s*\(",
                    clean,
                )
                if m_assign:
                    dest = m_assign.group(1).split(":")[-1]
                    func_called = m_assign.group(2).split(":")[-1]
                    if func_called in functions_returning_vector:
                        vec = functions_returning_vector[func_called]
                        if dest not in vector_aliases:
                            vector_aliases[dest] = vec
                            changed = True

                # Direct alias: Book* b = &inventory[i]
                m_alias = re.search(
                    r"(?:[\w:]+\s*\*\s+)?([\w:]+)\s*=\s*&(\w+)(?:\[.*?\]|\.at\(.*?\))\s*;",
                    clean,
                )
                if m_alias:
                    dest = m_alias.group(1).split(":")[-1]
                    vec = m_alias.group(2)
                    if dest not in vector_aliases:
                        vector_aliases[dest] = vec
                        changed = True

                # Pointer-to-pointer copy: user.currentBook = book;
                # This propagates vector aliases through assignment chains.
                m_ptr_copy = re.search(
                    r"(?:[\w:]+\s*\*\s+)?(?:(\w+)\.)?(\w+)\s*=\s*(\w+)\s*;",
                    clean,
                )
                if m_ptr_copy:
                    dest = m_ptr_copy.group(2)
                    src = m_ptr_copy.group(3)
                    if src in vector_aliases and dest not in vector_aliases:
                        vector_aliases[dest] = vector_aliases[src]
                        changed = True

        # ── Pass 2: emit findings ──────────────────────────────────────
        current_function = None
        for i, line in enumerate(lines):
            line_num = i + 1
            clean = re.sub(r"//.*", "", line)

            if "shared_ptr" in clean or "weak_ptr" in clean:
                continue

            m_func = re.search(
                r"(?:[\w:]+\s*\*?\s+)?([\w:]+)\s*\([^)]*\)\s*(?:const\s*)?\{",
                clean,
            )
            if m_func:
                candidate = m_func.group(1).split(":")[-1]
                if self._is_function_decl(candidate):
                    current_function = candidate

            # 1. Returning raw pointer to vector element (indexed)
            m_ret_idx = re.search(r"return\s+&(\w+)(?:\[.*?\]|\.at\(.*?\))\s*;", clean)
            if m_ret_idx:
                vec_name = m_ret_idx.group(1)
                issues.append(
                    {
                        "severity": "Critical",
                        "category": "Memory/Lifetime",
                        "line_number": line_num,
                        "description": (
                            f"Returning a raw pointer to an element of vector "
                            f"'{vec_name}'. This pointer will dangle if the "
                            f"vector reallocates."
                        ),
                        "confidence": "High",
                        "rule_type": "Memory/Lifetime",
                    }
                )

            # 1b. Returning raw pointer via range-for alias
            m_ret_bare = re.search(r"return\s+&(\w+)\s*;", clean)
            if m_ret_bare and not m_ret_idx:
                var = m_ret_bare.group(1)
                if var in range_for_aliases:
                    container = range_for_aliases[var]
                    issues.append(
                        {
                            "severity": "Critical",
                            "category": "Memory/Lifetime",
                            "line_number": line_num,
                            "description": (
                                f"Returning a raw pointer to an element of "
                                f"vector '{container}' via range-for reference "
                                f"'{var}'. This pointer will dangle if the "
                                f"vector reallocates."
                            ),
                            "confidence": "High",
                            "rule_type": "Memory/Lifetime",
                        }
                    )

            # 2 & 3. Vector mutations that invalidate aliases
            m_mut = re.search(
                r"(\w+)\.(push_back|emplace_back|insert|resize|erase|clear)\(",
                clean,
            )
            if m_mut:
                vec_name = m_mut.group(1)
                op = m_mut.group(2)

                aliases_for_vec = [
                    a for a, v in vector_aliases.items() if v == vec_name
                ]
                if aliases_for_vec:
                    alias_list = ", ".join(f"'{a}'" for a in aliases_for_vec)
                    if op in ("erase", "clear"):
                        issues.append(
                            {
                                "severity": "High",
                                "category": "Memory/Lifetime",
                                "line_number": line_num,
                                "description": (
                                    f"Container erasure '{vec_name}.{op}()' can "
                                    f"invalidate externally stored "
                                    f"aliases/pointers such as {alias_list}."
                                ),
                                "confidence": "High",
                                "rule_type": "Memory/Lifetime",
                            }
                        )
                    else:
                        issues.append(
                            {
                                "severity": "Critical",
                                "category": "Memory/Lifetime",
                                "line_number": line_num,
                                "description": (
                                    f"Vector reallocation "
                                    f"'{vec_name}.{op}()' invalidates previously "
                                    f"stored raw pointers/aliases like "
                                    f"{alias_list}."
                                ),
                                "confidence": "High",
                                "rule_type": "Memory/Lifetime",
                            }
                        )

            # 4. Double free
            m_alloc = re.search(r"(?:[\w:]+\s*\*\s+)?([\w:]+)\s*=\s*new\s+", clean)
            if m_alloc:
                ptr = m_alloc.group(1).split(":")[-1]
                raw_pointers[ptr] = "allocated"

            m_copy = re.search(r"(?:[\w:]+\s*\*\s+)?([\w:]+)\s*=\s*([\w:]+)\s*;", clean)
            if m_copy:
                dest = m_copy.group(1).split(":")[-1]
                src = m_copy.group(2).split(":")[-1]
                if src in raw_pointers:
                    raw_pointers[dest] = src

            m_delete = re.search(r"delete\s+(?:\[\]\s+)?([\w:]+)\s*;", clean)
            if m_delete:
                ptr = m_delete.group(1).split(":")[-1]
                root = ptr
                visited: set[str] = set()
                while (
                    root in raw_pointers
                    and raw_pointers[root] != "allocated"
                    and root not in visited
                ):
                    visited.add(root)
                    root = raw_pointers[root]

                if root in deleted_pointers:
                    issues.append(
                        {
                            "severity": "Critical",
                            "category": "Memory/Lifetime",
                            "line_number": line_num,
                            "description": (
                                f"Double free or use-after-free detected on "
                                f"pointer alias '{ptr}'."
                            ),
                            "confidence": "High",
                            "rule_type": "Memory/Lifetime",
                        }
                    )
                else:
                    if root in raw_pointers or ptr in raw_pointers:
                        deleted_pointers.add(root)

        return issues
