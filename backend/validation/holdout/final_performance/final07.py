def stream_large_table(cursor):
    """fetchone iteration."""
    cursor.execute("SELECT * FROM massive_log_table")
    processed = 0
    while True:
        row = cursor.fetchone()
        if row is None:
            break
        processed += 1
    return processed
