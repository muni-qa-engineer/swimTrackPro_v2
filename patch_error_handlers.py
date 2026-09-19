import re

with open('app.py', 'r') as f:
    content = f.read()

handlers_code = """
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403
"""

# We'll put it right before if __name__ == '__main__':
content = content.replace("if __name__ == '__main__':", handlers_code + "\nif __name__ == '__main__':")

with open('app.py', 'w') as f:
    f.write(content)

print("Error handlers added to app.py")
