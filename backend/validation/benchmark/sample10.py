def find_duplicate_users(user_list, previous_users):
    """
    Identifies duplicate users between two lists.
    Has a medium performance issue (O(N*M) time complexity).
    """
    duplicates = []
    
    try:
        # Inefficient nested loop approach.
        # Should convert previous_users to a set of IDs for O(1) lookups
        for user in user_list:
            user_id = user.get('id')
            
            # This is O(N) inside a loop, making it O(N^2) overall
            for prev in previous_users:
                if prev.get('id') == user_id:
                    duplicates.append({
                        'id': user_id,
                        'name': user.get('name'),
                        'last_seen': prev.get('last_seen')
                    })
                    break
                    
        return duplicates
        
    except Exception:
        # Broad exception handler swallowing all errors silently
        return []

def format_duplicates_report(dups):
    if not dups:
        return "No duplicates found."
        
    lines = ["Duplicate Users:"]
    for d in dups:
        lines.append(f" - {d['name']} (ID: {d['id']})")
        
    return "\\n".join(lines)
