import re

with open('templates/login.html', 'r') as f:
    content = f.read()

seo_block = """{% block title %}SwimTrackPro - Swimming Coaches & Private Swimming Lessons in Hyderabad{% endblock %}

{% block seo_meta %}
<meta name="description" content="Find swimming coaches and private swimming lessons in Hyderabad. Discover coaches, compare options and book swimming sessions with SwimTrackPro at your apartment or community pool.">
<link rel="canonical" href="https://swimtrackpro.onrender.com/">
<meta property="og:title" content="SwimTrackPro - Swimming Coaches & Private Swimming Lessons in Hyderabad">
<meta property="og:description" content="Find swimming coaches and private swimming lessons in Hyderabad. Discover coaches, compare options and book swimming sessions with SwimTrackPro at your apartment or community pool.">
<meta property="og:type" content="website">
<meta property="og:url" content="https://swimtrackpro.onrender.com/">
<meta property="og:image" content="https://swimtrackpro.onrender.com/static/images/about_swimming_hero.jpg">
<meta name="twitter:card" content="summary_large_image">
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SportsActivityLocation",
  "name": "SwimTrackPro",
  "description": "Premium platform connecting learners with verified, elite swimming coaches for doorstep training in Hyderabad.",
  "url": "https://swimtrackpro.onrender.com/",
  "address": {
    "@type": "PostalAddress",
    "addressLocality": "Hyderabad",
    "addressRegion": "Telangana",
    "addressCountry": "IN"
  }
}
</script>
{% endblock %}
"""

content = re.sub(r'\{% block title %\}Personal Swimming Coaches for Your Pool \| SwimTrackPro\{% endblock %\}', seo_block, content)

with open('templates/login.html', 'w') as f:
    f.write(content)
