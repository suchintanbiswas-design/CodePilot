def execute_custom_query(db_conn, table_name, filters, user_id):
    """
    Executes a query based on filters.
    Contains mild security issues and performance inefficiencies.
    """
    # Security smell: string concatenation for query building
    # This might be vulnerable if table_name or filter keys come from untrusted sources
    query = "SELECT * FROM " + table_name + " WHERE user_id = " + str(user_id)
    
    if filters:
        for key, value in filters.items():
            # Potential injection point depending on how `value` is formed
            query += f" AND {key} = '{value}'"
            
    print(f"Executing: {query}")
    cursor = db_conn.cursor()
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Performance issue: repeated list scanning
    # Suppose results is a list of dicts: [{'id': 1, 'category': 'A'}, ...]
    categories = ['Electronics', 'Books', 'Clothing', 'Home', 'Toys']
    
    categorized_results = {c: [] for c in categories}
    
    # O(N*M) where it could be O(N) by just using the dictionary key lookup directly
    for row in results:
        row_category = row.get('category')
        
        # Inefficiently scanning the categories list repeatedly
        for cat in categories:
            if row_category == cat:
                categorized_results[cat].append(row)
                break
                
        if row_category not in categories:
            if 'Other' not in categorized_results:
                categorized_results['Other'] = []
            categorized_results['Other'].append(row)
            
    return categorized_results
