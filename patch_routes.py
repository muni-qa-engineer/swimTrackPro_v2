import re

with open('swimtrackpro/routes/general.py', 'r') as f:
    content = f.read()

# Create the SEO landing pages dictionary and route
seo_routes = """
    # SEO Landing Pages
    SEO_PAGES = {
        'swimming-coaches-hyderabad': {
            'title': 'Swimming Coaches in Hyderabad | SwimTrackPro',
            'h1': 'Find Elite Swimming Coaches in Hyderabad',
            'description': 'Looking for certified swimming coaches in Hyderabad? SwimTrackPro connects you with elite private trainers who teach at your apartment or community pool.',
            'content_html': '<p>Hyderabad has a growing demand for high-quality aquatic fitness. Whether you are a beginner looking to overcome water phobia or an advanced swimmer aiming to perfect your stroke, our verified swimming coaches in Hyderabad are here to help.</p><p>We specialize in doorstep coaching—meaning our trainers travel to your apartment, villa, or community club pool. Skip the traffic and learn in the privacy and comfort of your own facility.</p><ul><li>Certified & background-checked professionals</li><li>Flexible timings for adults and kids</li><li>Personalized 1-on-1 and group coaching</li></ul>'
        },
        'swimming-classes-hyderabad': {
            'title': 'Private Swimming Classes in Hyderabad | SwimTrackPro',
            'h1': 'Premium Swimming Classes in Hyderabad',
            'description': 'Book private swimming classes in Hyderabad. Learn swimming at your own apartment or villa pool with our professional, certified swimming instructors.',
            'content_html': '<p>Finding the right swimming classes in Hyderabad is easier than ever. SwimTrackPro brings the classes to you. Our experienced instructors conduct sessions directly at your residential pool.</p><p>Our structured curriculum covers water safety, basic survival strokes, advanced competitive strokes (freestyle, breaststroke, backstroke, butterfly), and endurance training.</p><ul><li>Monthly and custom coaching packages</li><li>Real-time progress tracking</li><li>Makeup sessions for missed classes</li></ul>'
        },
        'swimming-coach-gachibowli': {
            'title': 'Swimming Coach in Gachibowli, Hyderabad | SwimTrackPro',
            'h1': 'Private Swimming Coach in Gachibowli',
            'description': 'Hire a private swimming coach in Gachibowli. SwimTrackPro offers elite doorstep swimming instruction for residents of Gachibowli and nearby areas.',
            'content_html': '<p>If you live in Gachibowli or the surrounding IT corridor, navigating traffic to reach a public pool can be a hassle. SwimTrackPro provides dedicated swimming coaches in Gachibowli who travel to your residential society pool.</p><p>We partner with residents of major apartment complexes and villas in Gachibowli to provide safe, hygienic, and professional swimming instruction.</p>'
        },
        'private-swimming-coaching': {
            'title': 'Private Swimming Coaching | Doorstep Trainers | SwimTrackPro',
            'h1': 'Exclusive Private Swimming Coaching',
            'description': 'Experience the benefits of private swimming coaching. Our elite trainers provide personalized 1-on-1 instruction at your own pool.',
            'content_html': '<p>Private swimming coaching offers unparalleled focus and rapid skill acquisition. Unlike crowded public batches, our 1-on-1 sessions ensure the coach is entirely focused on your technique, breathing, and safety.</p><p>Our private coaches evaluate your current fitness level and customize a training plan that aligns with your specific goals—whether that is weight loss, triathlon preparation, or basic water survival.</p>'
        },
        'kids-swimming-classes-hyderabad': {
            'title': 'Kids Swimming Classes in Hyderabad | Safe & Fun | SwimTrackPro',
            'h1': 'Kids Swimming Classes in Hyderabad',
            'description': 'Enroll your children in safe, fun kids swimming classes in Hyderabad. Our verified coaches teach water safety and swimming skills at your apartment pool.',
            'content_html': '<p>Water safety is an essential life skill for every child. SwimTrackPro offers specialized kids swimming classes in Hyderabad, conducted safely in the familiar environment of your own community pool.</p><p>Our coaches are trained in child-friendly teaching methodologies, ensuring that your kids overcome their fear of water while having fun. We maintain strict safety standards and encourage parents to watch the sessions from the comfort of their own pool deck.</p><ul><li>Focus on water safety and survival techniques</li><li>Engaging, game-based learning for younger kids</li><li>Strict verification process for all kids coaches</li></ul>'
        }
    }

    @app.route('/<page_slug>')
    def seo_landing(page_slug):
        if page_slug in SEO_PAGES:
            page_data = SEO_PAGES[page_slug]
            return render_template('seo_landing.html', page_data=page_data, page_slug=page_slug)
        # Pass to the next handler if it's not an SEO page
        from werkzeug.exceptions import NotFound
        raise NotFound()

    @app.route('/robots.txt')
    def robots_txt():
        lines = [
            "User-agent: *",
            "Allow: /",
            "Disallow: /admin",
            "Disallow: /dashboard",
            "Disallow: /api/",
            "Disallow: /profile",
            "Sitemap: https://swimtrackpro.onrender.com/sitemap.xml"
        ]
        from flask import Response
        return Response("\\n".join(lines), mimetype="text/plain")

    @app.route('/sitemap.xml')
    def sitemap_xml():
        urls = [
            "https://swimtrackpro.onrender.com/",
            "https://swimtrackpro.onrender.com/about-swimming",
            "https://swimtrackpro.onrender.com/about",
            "https://swimtrackpro.onrender.com/help",
            "https://swimtrackpro.onrender.com/register",
        ]
        # Add SEO landing pages
        for slug in SEO_PAGES.keys():
            urls.append(f"https://swimtrackpro.onrender.com/{slug}")
            
        # Dynamically fetch coaches if possible? We will just keep it static-ish for now to avoid db calls in sitemap unless easy
        xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        for url in urls:
            xml.append(f"  <url>\\n    <loc>{url}</loc>\\n    <changefreq>weekly</changefreq>\\n    <priority>0.8</priority>\\n  </url>")
        xml.append('</urlset>')
        
        from flask import Response
        return Response("\\n".join(xml), mimetype="application/xml")

    # Add dynamic route at the end of register_general_routes
"""

# We need to insert this right before the end of the `register_general_routes` function.
# Let's find the end of the file or the last add_url_rule in general.py
insertion_point = r'        methods=\["POST"\]\n    \)'
content = re.sub(insertion_point, '        methods=["POST"]\n    )\n' + seo_routes, content, count=1)

with open('swimtrackpro/routes/general.py', 'w') as f:
    f.write(content)
