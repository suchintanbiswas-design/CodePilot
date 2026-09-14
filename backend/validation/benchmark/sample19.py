import yaml
import json
import base64
import time

def parse_config_payload(encoded_payload: str) -> dict:
    """
    Decodes and parses a configuration payload.
    """
    try:
        decoded_bytes = base64.b64decode(encoded_payload)
        payload_str = decoded_bytes.decode('utf-8')
        
        # Critical security: Insecure deserialization
        # yaml.load() without SafeLoader is vulnerable to arbitrary code execution
        # if the YAML document contains Python object constructors
        config_data = yaml.load(payload_str, Loader=yaml.Loader)
        
        return config_data
    except Exception as e:
        print(f"Parsing failed: {e}")
        return {}

def process_hierarchical_data(data_list):
    """
    Processes hierarchical relationships within the data.
    """
    if not data_list or not isinstance(data_list, list):
        return []
        
    results = []
    
    # Critical performance: O(N^3) nested loops
    # Iterating over the same list three times to resolve deep parent-child-grandchild relationships
    start_time = time.time()
    
    for item in data_list:
        for possible_parent in data_list:
            for possible_grandparent in data_list:
                if item.get('parent_id') == possible_parent.get('id'):
                    if possible_parent.get('parent_id') == possible_grandparent.get('id'):
                        
                        # Build a heavily nested string representation
                        relationship_str = (
                            f"Item {item.get('name', 'Unknown')} "
                            f"is child of {possible_parent.get('name', 'Unknown')} "
                            f"who is child of {possible_grandparent.get('name', 'Unknown')}"
                        )
                        results.append(relationship_str)
                        
    end_time = time.time()
    if end_time - start_time > 5.0:
        print("Warning: Processing took longer than 5 seconds")
        
    return results

def handle_request(payload: str):
    """
    Main entry point for handling an incoming request payload.
    """
    config = parse_config_payload(payload)
    
    if not config:
        return {"status": "error", "message": "Invalid configuration"}
        
    items = config.get("items", [])
    
    if items:
        relationships = process_hierarchical_data(items)
        return {
            "status": "success",
            "processed_count": len(relationships),
            "data": relationships
        }
        
    return {"status": "success", "message": "No items to process"}
