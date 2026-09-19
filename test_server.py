from app import app
with app.test_client() as client:
    resp = client.get('/robots.txt')
    print("ROBOTS.TXT STATUS:", resp.status_code)
    
    resp = client.get('/sitemap.xml')
    print("SITEMAP STATUS:", resp.status_code)
    
    resp = client.get('/swimming-coaches-hyderabad')
    print("SEO PAGE STATUS:", resp.status_code)
    if resp.status_code == 200:
        print("H1 PRESENT:", b'Find Elite Swimming Coaches in Hyderabad' in resp.data)
        print("CANONICAL PRESENT:", b'rel="canonical"' in resp.data)
