import re

with open('templates/components/footer.html', 'r') as f:
    content = f.read()

# I will insert a new column before Legal
new_col = """            <!-- Services -->
            <div>
                <h4 style="color: white; font-size: 0.95rem; font-weight: 600; margin-bottom: 0.75rem;">Services</h4>
                <ul style="list-style: none; padding: 0; margin: 0; display: flex; flex-direction: column; gap: 0.5rem;">
                    <li><a href="/swimming-coaches-hyderabad" style="color: inherit; text-decoration: none; font-size: 0.82rem; transition: color var(--transition-fast);" onmouseover="this.style.color='white'" onmouseout="this.style.color='var(--color-text-secondary)'">Coaches in Hyderabad</a></li>
                    <li><a href="/swimming-classes-hyderabad" style="color: inherit; text-decoration: none; font-size: 0.82rem; transition: color var(--transition-fast);" onmouseover="this.style.color='white'" onmouseout="this.style.color='var(--color-text-secondary)'">Classes in Hyderabad</a></li>
                    <li><a href="/swimming-coach-gachibowli" style="color: inherit; text-decoration: none; font-size: 0.82rem; transition: color var(--transition-fast);" onmouseover="this.style.color='white'" onmouseout="this.style.color='var(--color-text-secondary)'">Coach in Gachibowli</a></li>
                    <li><a href="/private-swimming-coaching" style="color: inherit; text-decoration: none; font-size: 0.82rem; transition: color var(--transition-fast);" onmouseover="this.style.color='white'" onmouseout="this.style.color='var(--color-text-secondary)'">Private Coaching</a></li>
                    <li><a href="/kids-swimming-classes-hyderabad" style="color: inherit; text-decoration: none; font-size: 0.82rem; transition: color var(--transition-fast);" onmouseover="this.style.color='white'" onmouseout="this.style.color='var(--color-text-secondary)'">Kids Swimming</a></li>
                </ul>
            </div>

            <!-- Legal -->"""

content = re.sub(r'            <!-- Legal -->', new_col, content)

# I should also add these target paths to the modal script, EXCEPT I want them to be normal links so Google can crawl them directly as pages!
# The current JS intercepts links if they are in targetPaths, so since I DID NOT add them to targetPaths, they will load as regular pages. Which is exactly what SEO needs.

with open('templates/components/footer.html', 'w') as f:
    f.write(content)
