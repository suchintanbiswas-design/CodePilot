def handle_request(payload):
    """Clean Flask-style route processing O(N)."""
    import json
    data = json.loads(payload)
    results = [item * 2 for item in data.get("items", []) if item > 0]
    return {"status": "ok", "processed": results}
