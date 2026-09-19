import re

with open('templates/login.html', 'r') as f:
    content = f.read()

hero_replacement = """    <div class="container">
        <div class="hero-content animate-slide-up">
            <span class="badge badge-success mb-3" style="font-size: 0.85rem; padding: 0.4rem 1rem;">DOORSTEP SWIMMING COACHES IN HYDERABAD</span>
            <h1 class="font-display text-white mb-3" style="font-size: 3.5rem; font-weight: 800; line-height: 1.15;">Private Swimming Coaches at Your Pool</h1>
            <p class="text-white fw-bold mb-2" style="font-size: 1.4rem;">Your Pool. Our Coaches.</p>
            <p class="text-muted mb-5" style="font-size: 1.1rem; line-height: 1.6;">Have access to a swimming pool in your apartment complex, community club, or villa in Hyderabad? We match you with verified, elite swimming coaches who travel to your location. Discover private swimming classes in Gachibowli and surrounding areas in the comfort of your own facility.</p>
            <div class="d-flex flex-column flex-sm-row gap-3 mt-4">
                <button type="button" class="btn btn-primary px-5 py-3 w-100" onclick="document.getElementById('coaches').scrollIntoView({ behavior: 'smooth' })">Find a Swimming Coach</button>
                <button type="button" class="btn btn-secondary px-5 py-3 w-100" onclick="openLoginModal()">Track Progress</button>
            </div>
        </div>
    </div>"""

content = re.sub(r'    <div class="container">\s*<div class="hero-content animate-slide-up">.*?</div>\s*</div>\s*</div>', hero_replacement + '\n</div>', content, flags=re.DOTALL)

with open('templates/login.html', 'w') as f:
    f.write(content)
