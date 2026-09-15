def find_duplicates(items):
    """Nested-loop inefficiency O(N^2)."""
    duplicates = []
    for i in range(len(items)):
        for j in range(i + 1, len(items)):
            if items[i].name == items[j].name:
                duplicates.append((items[i], items[j]))
    return duplicates
