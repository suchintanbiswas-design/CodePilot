def complex_but_efficient_router(request):
    """High cyclomatic complexity, but O(N) performance."""
    path = request.path
    method = request.method
    if path == "/api/v1/users":
        if method == "GET":
            return "get_users"
        elif method == "POST":
            return "create_user"
    elif path == "/api/v1/posts":
        if method == "GET":
            return "get_posts"
        elif method == "DELETE":
            return "delete_post"
    elif path == "/status":
        return "ok"
    # Imagine 50 more elif blocks here...
    return "not_found"
