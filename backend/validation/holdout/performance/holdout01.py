def process_items(items):
    """Clean efficient code, single loop."""
    results = []
    for item in items:
        if item.is_active:
            results.append(item.process())
    return results
