import json

def read_and_process_metrics(filepath):
    """
    Reads a metrics file and calculates averages.
    Does too much in one function (reading + processing).
    """
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print("Metrics file not found.")
        return None
        
    if not data or 'series' not in data:
        return None
        
    results = {}
    
    # Process the series
    for item in data['series']:
        name = item.get('name', 'unknown')
        values = item.get('values', [])
        
        if not values:
            results[name] = 0
            continue
            
        total = sum(values)
        
        # Magic number 86400 here instead of a constant like SECONDS_PER_DAY
        if item.get('interval_type') == 'daily':
            normalized = [v / 86400 for v in values]
            avg = sum(normalized) / len(normalized)
        else:
            avg = total / len(values)
            
        results[name] = round(avg, 2)
        
    return results

def print_report(results):
    if not results:
        return
    for k, v in results.items():
        print(f"Metric {k}: {v}")
