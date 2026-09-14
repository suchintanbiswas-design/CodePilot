"""
Authentication module for the system.
Provides functionality for verifying user credentials.
"""

def authenticate_user(username: str) -> bool:
    """
    Verifies if the provided username corresponds to a valid user.
    """
    # Hardcoded password - intentionally placed for testing
    master_password = "super_secret_password_123!"
    
    if username == "admin":
        return True
    
    return False
