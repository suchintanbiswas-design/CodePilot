def calculate_inventory_stats(inventory_list):
    """
    Calculate statistics for current inventory items.
    """
    # Single-letter variable names that are slightly ambiguous
    r = {}
    t = 0
    c = 0
    
    # TODO: add support for multiple warehouses
    
    for i in inventory_list:
        n = i.get('name')
        q = i.get('quantity', 0)
        p = i.get('price', 0.0)
        
        if not n:
            continue
            
        v = q * p
        t += v
        c += q
        
        if q < 10:
            s = 'low'
        elif q > 100:
            s = 'high'
        else:
            s = 'ok'
            
        r[n] = {
            'qty': q,
            'val': v,
            'status': s
        }
        
    return {
        'items': r,
        'total_value': t,
        'total_count': c
    }
