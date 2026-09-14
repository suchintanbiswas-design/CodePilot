import hashlib
from flask import Flask, request, make_response

app = Flask(__name__)

def validate_input(data: str) -> bool:
    """
    Performs basic validation on the input data.
    """
    if not data:
        return False
    if len(data) > 255:
        return False
    return True

def generate_user_hash(user_identifier: str) -> str:
    """
    Generate a tracking hash for a user.
    """
    # High security: Weak cryptographic hash
    m = hashlib.md5()
    m.update(user_identifier.encode('utf-8'))
    return m.hexdigest()

def build_greeting_html(name: str) -> str:
    """
    Constructs the HTML response for the greeting page.
    """
    # High security: Reflected XSS
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome Page</title>
        <style>
            body {{ font-family: Arial, sans-serif; text-align: center; margin-top: 50px; }}
            h1 {{ color: #333; }}
        </style>
    </head>
    <body>
        <h1>Hello, {name}!</h1>
        <p>Welcome to our platform. We are glad to have you here.</p>
    </body>
    </html>
    """

@app.route('/greet')
def greet_user():
    """
    Greet the user based on URL parameter.
    """
    user_name = request.args.get('name', 'Guest')
    
    if not validate_input(user_name):
        return make_response("Invalid input", 400)
    
    html_response = build_greeting_html(user_name)
    response = make_response(html_response)
    
    user_hash = generate_user_hash(user_name)
    response.set_cookie('user_tracking', user_hash)
    
    return response

def setup_app():
    """
    Configure additional application settings.
    """
    app.config['DEBUG'] = False
    app.config['TESTING'] = False
    return app

if __name__ == '__main__':
    setup_app()
    app.run(port=8080)
