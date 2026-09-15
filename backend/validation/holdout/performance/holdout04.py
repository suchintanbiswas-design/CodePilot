def get_user_orders(cursor, user_ids):
    """Batched database access that should NOT be flagged as N+1."""
    if not user_ids:
        return []
        
    placeholders = ",".join(["?"] * len(user_ids))
    query = f"SELECT * FROM orders WHERE user_id IN ({placeholders})"
    
    cursor.execute(query, user_ids)
    rows = cursor.fetchall()
    
    results = []
    for row in rows:
        results.append(row)
        
    return results
