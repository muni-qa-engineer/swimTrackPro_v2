import re

with open('swimtrackpro/routes/general.py', 'r') as f:
    content = f.read()

# Replace the dynamic catch-all route with specific routes
old_route = """    @app.route('/<page_slug>')
    def seo_landing(page_slug):
        if page_slug in SEO_PAGES:
            page_data = SEO_PAGES[page_slug]
            return render_template('seo_landing.html', page_data=page_data, page_slug=page_slug)
        # Pass to the next handler if it's not an SEO page
        from werkzeug.exceptions import NotFound
        raise NotFound()"""

new_route = """    def create_seo_route(slug):
        def seo_landing():
            page_data = SEO_PAGES[slug]
            return render_template('seo_landing.html', page_data=page_data, page_slug=slug)
        # Ensure unique function names for flask
        seo_landing.__name__ = f"seo_landing_{slug.replace('-', '_')}"
        app.add_url_rule(f'/{slug}', view_func=seo_landing)

    for slug in SEO_PAGES.keys():
        create_seo_route(slug)"""

content = content.replace(old_route, new_route)

with open('swimtrackpro/routes/general.py', 'w') as f:
    f.write(content)
