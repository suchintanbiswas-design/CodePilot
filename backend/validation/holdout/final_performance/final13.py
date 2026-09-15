def map_items(items, reference_list):
    """O(N^2) via repeated .index() calls."""
    results = []
    for item in items:
        # index() is O(N), making this loop O(N^2) overall
        if item in reference_list:
            idx = reference_list.index(item)
            results.append(idx)
    return results
