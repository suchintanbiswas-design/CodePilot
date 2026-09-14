import subprocess
import sys

def ping_host(hostname):
    """
    Pings a host to check if it is alive.
    Has a medium security concern: uses user input in subprocess 
    without strict sanitization, though it checks for some characters.
    """
    # Incomplete sanitization
    if ';' in hostname or '|' in hostname:
        print("Invalid characters in hostname")
        return False
        
    if '&' in hostname:
        print("Invalid characters in hostname")
        return False
        
    try:
        # shell=True is dangerous with user input, even with the basic checks above
        # it might still be vulnerable to other shell injections
        command = f"ping -c 1 {hostname}"
        result = subprocess.run(
            command, 
            shell=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            text=True
        )
        
        if result.returncode == 0:
            return True
        else:
            return False
            
    except Exception as e:
        print(f"Error pinging host: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        is_up = ping_host(target)
        print(f"Host {target} is {'up' if is_up else 'down'}")
