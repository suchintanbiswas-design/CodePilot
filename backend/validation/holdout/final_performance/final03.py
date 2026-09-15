def find_matching_schedules(students):
    """O(N^2) Nested loops."""
    matches = []
    for s1 in students:
        for s2 in students:
            if s1.id != s2.id and s1.schedule == s2.schedule:
                matches.append((s1, s2))
    return matches
