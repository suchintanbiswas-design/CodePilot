def aggregate_stats(transactions):
    """Sequential loops O(N) + O(N)."""
    total_sales = 0
    for t in transactions:
        if t.type == "sale":
            total_sales += t.amount
            
    total_refunds = 0
    for t in transactions:
        if t.type == "refund":
            total_refunds += t.amount
            
    return total_sales, total_refunds
