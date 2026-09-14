import csv
import os

def process_and_upload_data(filepath, destination, file_type, api_client, max_retries, ignore_errors):
    """
    A function that does way too much: parses files, transforms data, 
    applies business logic, and handles uploading.
    Moderate cyclomatic complexity with several if/elif chains.
    """
    if not os.path.exists(filepath):
        print("File does not exist")
        return False
        
    parsed_data = []
    
    # Read file (Task 1)
    if file_type == 'csv':
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                parsed_data.append(row)
    elif file_type == 'tsv':
        with open(filepath, 'r') as f:
            reader = csv.DictReader(f, delimiter='\\t')
            for row in reader:
                parsed_data.append(row)
    elif file_type == 'txt':
        with open(filepath, 'r') as f:
            for line in f:
                parsed_data.append({'raw': line.strip()})
    else:
        print("Unsupported file type")
        return False
        
    # Transform data (Task 2)
    cleaned_data = []
    for item in parsed_data:
        if 'status' in item:
            if item['status'] == 'A':
                item['status'] = 'Active'
            elif item['status'] == 'I':
                item['status'] = 'Inactive'
            elif item['status'] == 'P':
                item['status'] = 'Pending'
                
        if 'amount' in item:
            try:
                val = float(item['amount'])
                if val < 0:
                    item['amount'] = 0.0
                else:
                    item['amount'] = val
            except ValueError:
                if not ignore_errors:
                    return False
                item['amount'] = 0.0
                
        cleaned_data.append(item)
        
    # Upload data (Task 3)
    attempts = 0
    while attempts < max_retries:
        try:
            response = api_client.post(destination, json=cleaned_data)
            if response.status_code in [200, 201]:
                return True
            attempts += 1
        except Exception:
            attempts += 1
            
    return False
