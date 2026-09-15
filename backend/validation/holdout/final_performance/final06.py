def get_all_books(db, author_ids):
    """Batched query."""
    if not author_ids: return []
    placeholders = ",".join(["?"] * len(author_ids))
    db.execute(f"SELECT * FROM books WHERE author_id IN ({placeholders})", author_ids)
    return db.fetchall()
