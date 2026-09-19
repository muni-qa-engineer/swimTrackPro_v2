import re

with open('templates/base.html', 'r') as f:
    content = f.read()

meta_block = """    <title>{% block title %}SwimTrackPro v3{% endblock %}</title>
    
    {% block seo_meta %}
    <meta name="description" content="Find swimming coaches and private swimming lessons. Book swimming sessions with SwimTrackPro.">
    <link rel="canonical" href="https://swimtrackpro.onrender.com{{ request.path }}">
    <meta property="og:title" content="SwimTrackPro - Swimming Coaches">
    <meta property="og:description" content="Find swimming coaches and private swimming lessons.">
    <meta property="og:type" content="website">
    <meta property="og:url" content="https://swimtrackpro.onrender.com{{ request.path }}">
    <meta property="og:image" content="https://swimtrackpro.onrender.com/static/images/about_swimming_hero.jpg">
    <meta name="twitter:card" content="summary_large_image">
    {% endblock %}
"""

content = re.sub(r'<title>\{% block title %\}SwimTrackPro v3\{% endblock %\}</title>', meta_block, content)

with open('templates/base.html', 'w') as f:
    f.write(content)
