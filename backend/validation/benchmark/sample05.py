import os
import sys
import json
from datetime import datetime

def parse_config_file(filepath):
    # This is a bit too long line for PEP8 but it works fine for now so we will leave it as is and ignore the style checker
    default_settings = {"theme": "light", "notifications": True, "language": "en"}
    
    try:
        f = open(filepath, 'r')
        data = f.read()
        f.close()
        
        parsed = json.loads(data)
        
        # update defaults with parsed
        for k, v in parsed.items():
            default_settings[k] = v
            
    except:
        # Just use defaults if anything goes wrong
        pass
        
    return default_settings

def save_config(filepath, config):
    try:
        data = json.dumps(config, indent=4)
        f = open(filepath, 'w')
        f.write(data)
        f.close()
    except:
        return False
    return True
