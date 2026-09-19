import re

with open('templates/base.html', 'r') as f:
    content = f.read()

banner_html = """
    <!-- Reusable Promotional Banner -->
    <div id="promoBanner" class="promo-banner" style="display: none; background: linear-gradient(90deg, var(--color-primary), #005f73); color: white; padding: 0.5rem 1rem; text-align: center; position: relative; z-index: 1050; font-size: 0.9rem; font-weight: 600;">
        <span id="promoBannerText"></span>
        <button type="button" class="btn-close btn-close-white" style="position: absolute; right: 1rem; top: 50%; transform: translateY(-50%); font-size: 0.7rem;" onclick="dismissPromoBanner()" aria-label="Close"></button>
    </div>
    
    <script>
        // Check for active promotions (mocked via localStorage/JS for now, or backend injected)
        document.addEventListener('DOMContentLoaded', function() {
            const promoConfig = {
                active: true,
                id: 'promo_vinayaka_2026',
                text: '🎉 Happy Vinayaka Chavithi! Book 3 months & get 15% off. <a href="/#plans" class="text-white text-decoration-underline">View Plans</a>'
            };
            
            if (promoConfig.active && localStorage.getItem('dismissed_promo') !== promoConfig.id) {
                document.getElementById('promoBannerText').innerHTML = promoConfig.text;
                document.getElementById('promoBanner').style.display = 'block';
            }
        });
        
        function dismissPromoBanner() {
            document.getElementById('promoBanner').style.display = 'none';
            // Save the current promo ID so we don't show it again
            localStorage.setItem('dismissed_promo', 'promo_vinayaka_2026');
        }
    </script>
"""

# Insert right after <body> tag
content = re.sub(r'(<body[^>]*>)', r'\1\n' + banner_html, content)

with open('templates/base.html', 'w') as f:
    f.write(content)

print("Banner added to base.html")
