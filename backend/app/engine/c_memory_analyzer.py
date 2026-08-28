import re
from typing import Any, Dict, List, Set


class CMemoryAnalyzer:
    """
    Deterministic C-specific memory-safety analysis.

    Uses per-function pointer-state tracking to detect:
      - C_DOUBLE_FREE:           two free() calls resolving to the same allocation
      - C_USE_AFTER_FREE:        dereference / use of a pointer after free()
      - C_MALLOC_FREE_MISMATCH:  free() called on stack or static memory

    Architecture
    ------------
    Single linear pass per function body:
      1. Track pointer origins  (heap / stack / static / unknown)
      2. Track pointer aliases  (dest → src chain)
      3. Track freed pointers   (set of root allocation names)
      4. Emit findings on violations
    """

    # C keywords that must not be confused with function definitions
    _C_KEYWORDS = frozenset({
        "if", "else", "for", "while", "do", "switch", "case",
        "return", "sizeof", "typedef", "struct", "enum", "union",
        "goto", "break", "continue", "default",
    })

    # ── Public API ────────────────────────────────────────────────────

    def analyze(self, code: str) -> List[Dict[str, Any]]:
        issues: List[Dict[str, Any]] = []
        lines = code.split("\n")

        # Per-function state — reset at each function boundary
        ptr_origin: dict[str, str] = {}       # ptr_name → "heap" | "stack" | "static"
        ptr_alias: dict[str, str] = {}        # ptr_name → source ptr_name
        freed_roots: set[str] = set()         # root allocation names already freed
        freed_ptrs: set[str] = set()          # direct pointer names passed to free()
        unchecked_ptrs: set[str] = set()      # heap pointers not yet null-checked
        live_allocs: set[str] = set()         # root pointer names holding active heap allocations
        escaped_allocs: set[str] = set()      # root pointer names that have escaped
        leaked_allocs: set[str] = set()       # root pointer names already reported as leaked

        # Branch tracking to handle early returns
        brace_depth = 0
        state_snapshots = {}                  # depth -> (freed_roots, freed_ptrs, unchecked_ptrs, live_allocs, escaped_allocs)
        diverging_depths = set()              # depths that have seen return/break/continue

        for i, line in enumerate(lines):
            line_num = i + 1
            clean = self._strip_comments(line)

            # Detect function boundaries — reset state
            if self._is_function_def(clean):
                # Check for leaks from the PREVIOUS function
                for root in live_allocs:
                    if root not in freed_roots and root not in escaped_allocs and root not in leaked_allocs:
                        issues.append(self._make_issue(
                            line_num - 1,
                            "High",
                            f"Memory leak: allocation '{root}' is not freed before function exit.",
                            "C_MEMORY_LEAK",
                        ))

                ptr_origin.clear()
                ptr_alias.clear()
                freed_roots.clear()
                freed_ptrs.clear()
                unchecked_ptrs.clear()
                live_allocs.clear()
                escaped_allocs.clear()
                leaked_allocs.clear()
                brace_depth = 0
                state_snapshots.clear()
                diverging_depths.clear()
                # A function definition usually ends with {
                if "{" in clean:
                    brace_depth = 1
                continue

            # Track brace depth for branch isolation
            # Track brace depth for branch isolation
            if "{" in clean:
                state_snapshots[brace_depth] = (
                    freed_roots.copy(), freed_ptrs.copy(), unchecked_ptrs.copy(),
                    live_allocs.copy(), escaped_allocs.copy()
                )
                brace_depth += clean.count("{")
            
            if re.search(r'\b(return|break|continue)\b', clean):
                if brace_depth > 0:
                    diverging_depths.add(brace_depth)

            if "}" in clean:
                brace_depth -= clean.count("}")
                if brace_depth < 0:
                    brace_depth = 0
                # If we are closing a block that had an early return, restore state
                # to what it was before this block opened
                if (brace_depth + 1) in diverging_depths:
                    if brace_depth in state_snapshots:
                        saved_roots, saved_ptrs, _, saved_live, saved_escaped = state_snapshots[brace_depth]
                        freed_roots.intersection_update(saved_roots)
                        freed_roots.update(saved_roots)
                        freed_ptrs.intersection_update(saved_ptrs)
                        freed_ptrs.update(saved_ptrs)
                        live_allocs.intersection_update(saved_live)
                        live_allocs.update(saved_live)
                        escaped_allocs.intersection_update(saved_escaped)
                        escaped_allocs.update(saved_escaped)
                    diverging_depths.discard(brace_depth + 1)
                else:
                    # Non-diverging block closes: restore unchecked_ptrs so checks inside don't leak outside
                    if brace_depth in state_snapshots:
                        _, _, saved_unchecked, _, _ = state_snapshots[brace_depth]
                        unchecked_ptrs.intersection_update(saved_unchecked)
                        unchecked_ptrs.update(saved_unchecked)
                
                # Cleanup snapshots for depths we've left
                keys_to_remove = [k for k in state_snapshots.keys() if k >= brace_depth]
                for k in keys_to_remove:
                    state_snapshots.pop(k, None)
                    diverging_depths.discard(k + 1)

            # ── 0.5 Track escapes (returned, passed to function, assigned to struct/global)
            for root in list(live_allocs):
                if root not in escaped_allocs and self._escapes_on_line(root, ptr_alias, clean):
                    escaped_allocs.add(root)

            # ── 1. Track heap allocations ─────────────────────────────
            #   int *p = malloc(...)  /  calloc(...)  /  realloc(...)
            m_alloc = re.search(
                r'(\w+)\s*=\s*(?:\(\s*\w[\w\s*]*\s*\)\s*)?'
                r'(malloc|calloc|realloc)\s*\(',
                clean,
            )
            if m_alloc:
                ptr = m_alloc.group(1).strip()
                # Overwrite leak check
                if ptr in live_allocs and ptr not in freed_roots and ptr not in escaped_allocs and ptr not in leaked_allocs:
                    issues.append(self._make_issue(
                        line_num,
                        "High",
                        f"Memory leak: pointer '{ptr}' is overwritten by a new allocation before being freed.",
                        "C_MEMORY_LEAK",
                    ))
                    leaked_allocs.add(ptr)

                # New allocation clears any previous freed state
                freed_ptrs.discard(ptr)
                freed_roots.discard(ptr)  # old root no longer valid
                unchecked_ptrs.add(ptr)
                live_allocs.add(ptr)
                escaped_allocs.discard(ptr)
                leaked_allocs.discard(ptr)
                ptr_origin[ptr] = "heap"
                # Remove old alias chain — this is a fresh allocation
                ptr_alias.pop(ptr, None)
                continue  # allocation line — skip further checks

            # ── 2. Track stack-pointer assignments ────────────────────
            #   int *p = &local_var;
            m_stack = re.search(
                r'(\w+)\s*=\s*&(\w+)\s*;', clean,
            )
            if m_stack:
                ptr = m_stack.group(1).strip()
                ptr_origin[ptr] = "stack"
                ptr_alias.pop(ptr, None)
                freed_ptrs.discard(ptr)
                unchecked_ptrs.discard(ptr)
                continue

            # ── 3. Track string-literal / static assignments ──────────
            #   char *p = "hello";
            m_static = re.search(
                r'(\w+)\s*=\s*"[^"]*"\s*;', clean,
            )
            if m_static:
                ptr = m_static.group(1).strip()
                ptr_origin[ptr] = "static"
                ptr_alias.pop(ptr, None)
                freed_ptrs.discard(ptr)
                unchecked_ptrs.discard(ptr)
                continue

            # ── 4. Track pointer-to-pointer copies ────────────────────
            #   int *alias = data;   or   alias = data;
            #   Skip dereference assignments: *p = value;  (star at start of expr)
            m_copy = re.search(
                r'(?:[\w\s*]+\*\s+)?(\w+)\s*=\s*(\w+)\s*;', clean,
            )
            is_deref_assign = bool(re.match(r'^\s*\*\s*\w+\s*=', clean))
            if m_copy and not is_deref_assign:
                dest = m_copy.group(1).strip()
                src = m_copy.group(2).strip()
                # Only track if src is a known pointer
                if src in ptr_origin or src in ptr_alias:
                    ptr_alias[dest] = src
                    # Inherit origin
                    root_src = self._resolve_root(src, ptr_alias)
                    if root_src in ptr_origin:
                        ptr_origin[dest] = ptr_origin[root_src]
                    # If the source was freed, the alias is also freed
                    if src in freed_ptrs:
                        freed_ptrs.add(dest)
                    else:
                        freed_ptrs.discard(dest)
                    # Inherit unchecked state
                    if src in unchecked_ptrs:
                        unchecked_ptrs.add(dest)
                    else:
                        unchecked_ptrs.discard(dest)
                    continue
                # If src is not known, this might be a generic assignment
                # that clears freed state (e.g., ptr = some_function())
                if dest in freed_ptrs:
                    freed_ptrs.discard(dest)
                if dest in unchecked_ptrs:
                    unchecked_ptrs.discard(dest)
                ptr_alias.pop(dest, None)

            # ── 5. Track free() calls ─────────────────────────────────
            m_free = re.search(r'\bfree\s*\(\s*(\w+)\s*\)', clean)
            if m_free:
                ptr = m_free.group(1).strip()

                # Resolve to root allocation
                root = self._resolve_root(ptr, ptr_alias)

                # Rule: C_MALLOC_FREE_MISMATCH
                origin = ptr_origin.get(root, ptr_origin.get(ptr))
                if origin == "stack":
                    issues.append(self._make_issue(
                        line_num,
                        "Critical",
                        f"free() called on stack pointer '{ptr}'. "
                        f"Only heap-allocated memory (malloc/calloc/realloc) "
                        f"may be freed.",
                        "C_MALLOC_FREE_MISMATCH",
                    ))
                    continue
                if origin == "static":
                    issues.append(self._make_issue(
                        line_num,
                        "Critical",
                        f"free() called on static/string-literal pointer "
                        f"'{ptr}'. Only heap-allocated memory may be freed.",
                        "C_MALLOC_FREE_MISMATCH",
                    ))
                    continue

                # Rule: C_DOUBLE_FREE
                if root in freed_roots:
                    issues.append(self._make_issue(
                        line_num,
                        "Critical",
                        f"Double free detected: '{ptr}' has already been "
                        f"freed (directly or via an alias).",
                        "C_DOUBLE_FREE",
                    ))
                else:
                    freed_roots.add(root)
                    freed_ptrs.add(ptr)
                    # Also mark all known aliases of this root as freed
                    for alias_name, alias_src in list(ptr_alias.items()):
                        alias_root = self._resolve_root(alias_name, ptr_alias)
                        if alias_root == root:
                            freed_ptrs.add(alias_name)
                continue

            # ── 6. Detect use-after-free ──────────────────────────────
            # Check if any freed pointer is used on this line
            for fptr in list(freed_ptrs):
                if self._is_used_on_line(fptr, clean):
                    issues.append(self._make_issue(
                        line_num,
                        "Critical",
                        f"Use-after-free: pointer '{fptr}' is used after "
                        f"being freed.",
                        "C_USE_AFTER_FREE",
                    ))
                    break  # one finding per line

            # ── 6b. Null checks and deref detection ───────────────────
            m_cond = re.search(r'\b(if|while|for)\s*\((.*)\)', clean)
            if m_cond:
                cond = m_cond.group(2)
                for uptr in list(unchecked_ptrs):
                    if re.search(rf'\b{re.escape(uptr)}\b', cond):
                        unchecked_ptrs.discard(uptr)

            for uptr in list(unchecked_ptrs):
                if self._is_used_on_line(uptr, clean):
                    issues.append(self._make_issue(
                        line_num,
                        "High",
                        f"Pointer '{uptr}' is dereferenced or used before being checked for NULL. "
                        f"Memory allocation (malloc/calloc) may fail and return NULL.",
                        "C_NULL_DEREF_AFTER_MALLOC",
                    ))
                    unchecked_ptrs.discard(uptr)  # report once

            # ── 7. Handle pointer reassignment clearing freed state ───
            #   ptr = malloc(...)  is handled above (step 1)
            #   ptr = other_func()  or  ptr = NULL;
            m_reassign = re.search(
                r'\b(\w+)\s*=\s*(?!.*free)', clean,
            )
            if m_reassign:
                ptr = m_reassign.group(1).strip()
                if ptr in freed_ptrs:
                    # Check this isn't part of a declaration we already handled
                    if not re.search(r'(malloc|calloc|realloc)\s*\(', clean):
                        freed_ptrs.discard(ptr)
                if ptr in unchecked_ptrs:
                    if not re.search(r'(malloc|calloc|realloc)\s*\(', clean):
                        unchecked_ptrs.discard(ptr)

            # ── 8. Check for leaks on early return ────────────────────
            if re.search(r'\breturn\b', clean):
                for root in list(live_allocs):
                    if root not in freed_roots and root not in escaped_allocs and root not in leaked_allocs:
                        # Suppress leak reporting on early return if the pointer was checked for NULL.
                        # This prevents false positives on `if (!ptr) return;` error paths.
                        if root not in unchecked_ptrs:
                            continue
                        issues.append(self._make_issue(
                            line_num,
                            "High",
                            f"Memory leak: allocation '{root}' is not freed before returning.",
                            "C_MEMORY_LEAK",
                        ))
                        leaked_allocs.add(root)

        # ── Final check for the last function in the file ─────────────
        for root in live_allocs:
            if root not in freed_roots and root not in escaped_allocs and root not in leaked_allocs:
                issues.append(self._make_issue(
                    len(lines),
                    "High",
                    f"Memory leak: allocation '{root}' is not freed before function exit.",
                    "C_MEMORY_LEAK",
                ))

        return issues

    # ── Private helpers ───────────────────────────────────────────────

    def _escapes_on_line(self, root: str, ptr_alias: dict[str, str], line: str) -> bool:
        """Check if the root allocation escapes on this line (returned, passed to func, or assigned to struct/global)."""
        aliases = [k for k, v in ptr_alias.items() if self._resolve_root(k, ptr_alias) == root]
        aliases.append(root)
        
        for a in aliases:
            # 1. Returned (handles `return data;`, `return (data);`, `return(data);`)
            if re.search(rf'\breturn\b[^;]*\b{re.escape(a)}\b', line):
                return True
            # 2. Passed to function (excluding C keywords)
            for m in re.finditer(rf'([a-zA-Z_]\w*)\s*\([^)]*\b{re.escape(a)}\b[^)]*\)', line):
                if m.group(1) not in self._C_KEYWORDS:
                    return True
            # 3. Assigned to struct/array/global or out-parameter pointer deref
            m_assign = re.search(rf'([^=\s]+)\s*=\s*[^;]*\b{re.escape(a)}\b', line)
            if m_assign:
                left = m_assign.group(1).strip()
                if '->' in left or '.' in left or '[' in left or left.startswith('*'):
                    return True
        return False

    def _resolve_root(self, ptr: str, aliases: dict[str, str]) -> str:
        """Follow alias chain to the root allocation name."""
        visited: set[str] = set()
        current = ptr
        while current in aliases and current not in visited:
            visited.add(current)
            current = aliases[current]
        return current

    def _is_function_def(self, line: str) -> bool:
        """Detect C function definitions (heuristic)."""
        m = re.search(
            r'(?:[\w\s*]+\s+)?([\w]+)\s*\([^)]*\)\s*\{', line,
        )
        if m:
            name = m.group(1)
            if name not in self._C_KEYWORDS:
                return True
        return False

    def _is_used_on_line(self, ptr: str, line: str) -> bool:
        """Check if ptr is dereferenced or passed to a function on this line."""
        # Skip free() lines — handled separately
        if re.search(rf'\bfree\s*\(\s*{re.escape(ptr)}\s*\)', line):
            return False
        # Skip pure assignment to ptr (reassignment clears state)
        if re.match(rf'^\s*{re.escape(ptr)}\s*=\s', line):
            return False
        # Dereference: *ptr
        if re.search(rf'\*\s*{re.escape(ptr)}\b', line):
            return True
        # Array access: ptr[...]
        if re.search(rf'\b{re.escape(ptr)}\s*\[', line):
            return True
        # Member access: ptr->...
        if re.search(rf'\b{re.escape(ptr)}\s*->', line):
            return True
        # Passed as function argument: func(ptr) or func(a, ptr, b)
        for m in re.finditer(rf'([a-zA-Z_]\w*)\s*\([^)]*\b{re.escape(ptr)}\b[^)]*\)', line):
            if m.group(1) not in self._C_KEYWORDS:
                return True
        return False

    @staticmethod
    def _strip_comments(line: str) -> str:
        """Remove single-line // comments."""
        idx = line.find("//")
        return line[:idx] if idx >= 0 else line

    @staticmethod
    def _make_issue(
        line_number: int,
        severity: str,
        description: str,
        rule_name: str,
    ) -> Dict[str, Any]:
        return {
            "severity": severity,
            "line_number": line_number,
            "description": description,
            "rule_type": "Memory/Safety",
            "confidence": "High",
            "category": "Memory/Safety",
            "rule_name": rule_name,
        }
