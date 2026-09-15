def stream_results(cursor):
    """Cursor iteration fetching one by one. Should not be N+1."""
    cursor.execute("SELECT * FROM massive_table")
    
    count = 0
    while True:
        row = cursor.fetchone()
        if not row:
            break
        count += 1
        
    return count
