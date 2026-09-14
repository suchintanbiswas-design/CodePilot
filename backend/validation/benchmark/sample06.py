def check_access_permission(user_role, resource_type, is_active, department):
    """
    Check if a user has access to a specific resource.
    """
    # Unused variable
    audit_log_level = 3
    
    has_access = False
    
    # Mildly complex condition
    if (user_role == "admin" and is_active) or (
        user_role == "manager" and 
        is_active and 
        department in ["HR", "Finance", "IT"] and 
        resource_type != "system_config"
    ):
        has_access = True
    elif user_role == "employee" and is_active and resource_type == "public":
        has_access = True
        
    return has_access

def process_login(username, role, active, dept):
    """Process a login attempt."""
    allowed = check_access_permission(role, "dashboard", active, dept)
    if allowed:
        return f"Welcome {username}"
    return "Access Denied"
