def process_queue(cursor):
    """N+1 query pattern inside a while loop."""
    processed = 0
    while True:
        cursor.execute("SELECT * FROM jobs WHERE status = 'PENDING' LIMIT 1")
        job = cursor.fetchone()
        if not job:
            break
            
        # Do work
        processed += 1
        cursor.execute("UPDATE jobs SET status = 'DONE' WHERE id = ?", (job.id,))
        
    return processed
