def find_similar_users(db, threshold):
    """Batch query then O(N^2) in-memory comparison."""
    db.execute("SELECT * FROM users")
    all_users = db.fetchall()
    
    similar = []
    for u1 in all_users:
        for u2 in all_users:
            if u1.id < u2.id and abs(u1.score - u2.score) < threshold:
                similar.append((u1, u2))
    return similar
