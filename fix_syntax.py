with open('swimtrackpro/routes/general.py', 'r') as f:
    content = f.read()

content = content.replace('return Response("\\n".join(lines), mimetype="text/plain")', 'return Response("\\n".join(lines), mimetype="text/plain")')
content = content.replace('return Response("{\\n}".join(xml), mimetype="application/xml")', 'return Response("\\n".join(xml), mimetype="application/xml")')
# Let's just fix it completely by reading lines and replacing the bad ones
import re
content = re.sub(r'return Response\("\n"\.join\(lines\)', r'return Response("\\n".join(lines)', content)
content = re.sub(r'return Response\("\n"\.join\(xml\)', r'return Response("\\n".join(xml)', content)
content = re.sub(r'<url>\n    <loc>\{url\}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0\.8</priority>\n  </url>', r'<url>\\n    <loc>{url}</loc>\\n    <changefreq>weekly</changefreq>\\n    <priority>0.8</priority>\\n  </url>', content)

with open('swimtrackpro/routes/general.py', 'w') as f:
    f.write(content)
