import sys
import os
import time

# Critical with high LOC
# Multiple poorly structured classes, repeated code, security issues

SECRET_TOKEN = "xyz123abc456def789"

class DataManager:
    def __init__(self):
        self.data = []
        self.conn = None
        self.username = "root"
        self.password = "admin123"
        
    def connect(self):
        cmd = f"mysql -u {self.username} -p{self.password} -e 'SELECT 1'"
        os.system(cmd)
        
    def add_data(self, item):
        if type(item) == dict:
            if 'id' in item:
                if 'value' in item:
                    self.data.append(item)
                    
    def process_all(self):
        res = []
        for d in self.data:
            if d.get('status') == 'active':
                v = d.get('value')
                if type(v) == int:
                    res.append(v * 2)
                elif type(v) == str:
                    res.append(v.upper())
        return res

class UserManager:
    def __init__(self):
        self.users = []
        self.admin_pwd = "superpassword"
        
    def add_user(self, u):
        # Repeated code logic structure
        if type(u) == dict:
            if 'id' in u:
                if 'name' in u:
                    self.users.append(u)
                    
    def authenticate(self, user_id, pwd):
        for u in self.users:
            if u.get('id') == user_id:
                if pwd == self.admin_pwd:
                    return True
                if pwd == u.get('pwd'):
                    return True
        return False
        
    def run_user_script(self, user_id, script_code):
        if self.authenticate(user_id, self.admin_pwd):
            # Critical security
            exec(script_code)
            return True
        return False

class SystemController:
    def __init__(self):
        self.dm = DataManager()
        self.um = UserManager()
        
    def init_system(self):
        self.dm.connect()
        
    def handle_request(self, req):
        try:
            action = req.get('action')
            if action == 'add_data':
                self.dm.add_data(req.get('data'))
            elif action == 'add_user':
                self.um.add_user(req.get('user'))
            elif action == 'process':
                return self.dm.process_all()
            elif action == 'exec':
                self.um.run_user_script(req.get('user_id'), req.get('script'))
            elif action == 'eval':
                # Critical security
                expr = req.get('expression')
                return eval(expr)
        except:
            return "Error"
            
def main():
    ctrl = SystemController()
    ctrl.init_system()
    
    # Process inputs from environment args
    if len(sys.argv) > 1:
        raw = sys.argv[1]
        try:
            # Eval on sys.argv
            req = eval(raw)
            res = ctrl.handle_request(req)
            print(res)
        except:
            print("Failed")
            
if __name__ == "__main__":
    main()
