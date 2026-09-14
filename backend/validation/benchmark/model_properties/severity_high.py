"""
User processing module.
"""

def read_user_file(filename: str) -> str:
    """
    Reads a file specified by the user.
    """
    # Missing input validation (path traversal risk)
    filepath = f"/var/data/users/{filename}"
    with open(filepath, 'r') as f:
        return f.read()

def write_user_file(filename: str, data: str) -> None:
    """
    Writes data to a user file.
    """
    filepath = f"/var/data/users/{filename}"
    with open(filepath, 'w') as f:
        f.write(data)
