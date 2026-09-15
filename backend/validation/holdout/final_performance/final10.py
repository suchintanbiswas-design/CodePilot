def build_large_string(items):
    """Inefficient string concatenation (CodePilot will likely miss this)."""
    result = ""
    for item in items:
        result += str(item) + ","
    return result
