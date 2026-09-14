import sqlite3
import pickle
import base64
import json

def process_remote_data(encoded_data_payload, db_path, user_id):
    """
    Process incoming data and store it in the database.
    Contains both performance issues and security flaws.
    """
    try:
        # High security: unpickling untrusted data
        # If encoded_data_payload comes from a user, this is a remote code execution vulnerability
        decoded_bytes = base64.b64decode(encoded_data_payload)
        data_objects = pickle.loads(decoded_bytes)
    except Exception as e:
        print(f"Failed to decode data: {e}")
        return False
        
    if not isinstance(data_objects, list):
        return False
        
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    results = []
    
    # Performance issue + Security issue
    for item in data_objects:
        item_type = item.get('type', 'unknown')
        item_val = item.get('value', '')
        
        # Security: SQL Injection vulnerability via string formatting
        query = f"SELECT * FROM user_settings WHERE user_id = {user_id} AND type = '{item_type}'"
        cursor.execute(query)
        existing = cursor.fetchall()
        
        # High Performance Issue: Nested loops doing inefficient cross-referencing
        for db_row in existing:
            row_id = db_row[0]
            row_val = db_row[2]
            
            # Another nested query inside a loop (N+1 query problem)
            audit_query = f"SELECT log_entry FROM audit_logs WHERE target_id = {row_id}"
            cursor.execute(audit_query)
            logs = cursor.fetchall()
            
            for log in logs:
                if item_val in str(log[0]):
                    results.append({
                        'id': row_id,
                        'matched_val': item_val,
                        'history': log[0]
                    })
                    
    conn.close()
    return results
