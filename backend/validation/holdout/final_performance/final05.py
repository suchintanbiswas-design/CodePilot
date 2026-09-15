def export_books_for_authors(db, authors):
    """N+1 query using db.execute in a loop."""
    export_data = []
    for author in authors:
        db.execute("SELECT * FROM books WHERE author_id=?", (author.id,))
        books = db.fetchall()
        export_data.append({"author": author.name, "books": books})
    return export_data
