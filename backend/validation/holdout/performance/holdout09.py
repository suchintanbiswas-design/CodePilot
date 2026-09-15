def merge_data(cursor, user_ids, group_ids):
    """Realistic mixed code: batched query, but O(N^2) in-memory join."""
    cursor.execute("SELECT * FROM users WHERE id IN (...)")
    users = cursor.fetchall()
    
    cursor.execute("SELECT * FROM groups WHERE id IN (...)")
    groups = cursor.fetchall()
    
    # Inefficient in-memory join
    memberships = []
    for u in users:
        for g in groups:
            if u.group_id == g.id:
                memberships.append((u, g))
                
    return memberships
