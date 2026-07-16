from app import app
from flask import session

app.testing = True
with app.test_client() as client:
    with client.session_transaction() as sess:
        sess['user_name'] = 'testuser'
        sess['role'] = 'trainer'
        sess['trainer_username'] = 'testuser'
    
    response = client.get('/')
    print("STATUS:", response.status_code)
    html = response.data.decode('utf-8')
    print("DROPDOWN HTML:")
    print(html[html.find('dropdown-menu'):html.find('dropdown-menu')+1000])
