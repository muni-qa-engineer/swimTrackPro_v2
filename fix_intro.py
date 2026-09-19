import re

with open('templates/about_swimming.html', 'r') as f:
    content = f.read()

intro_replacement = """<h3>🏊🏼‍♂️ What is Swimming?</h3>
                    <p class="lead" style="color: var(--color-text-primary); font-size: 1.1rem; font-weight: 500;"><strong>Swimming</strong> is the self-propulsion of a person through water, usually for recreation, sport, exercise, or survival.</p>
                    <p>Locomotion is achieved through coordinated movement of the limbs and the body to achieve hydrodynamic thrust which results in directional motion.</p>
                    
                    <div class="row g-4 mt-2">
                        <div class="col-md-6">
                            <div class="info-card h-100" style="border-left-color: var(--color-primary); background: rgba(6, 182, 212, 0.05);">
                                <h5 class="fw-bold text-white"><i class="fa-solid fa-heart-pulse text-primary me-2"></i> Unmatched Versatility</h5>
                                <p class="mb-0 text-muted small mt-2">Whether you want to build strength, lose weight, or find a moving meditation, swimming offers something for everyone.</p>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="info-card h-100" style="border-left-color: var(--color-success); background: rgba(16, 185, 129, 0.05);">
                                <h5 class="fw-bold text-white"><i class="fa-solid fa-leaf text-success me-2"></i> Low Impact</h5>
                                <p class="mb-0 text-muted small mt-2">Unlike many other exercises, swimming is completely low-impact, taking stress off your joints for a sustainable lifetime workout.</p>
                            </div>
                        </div>
                    </div>"""

content = re.sub(r'<h3>🏊🏼‍♂️ What is Swimming\?</h3>.*?find a moving meditation, swimming offers unmatched versatility\.</p>', intro_replacement, content, flags=re.DOTALL)

with open('templates/about_swimming.html', 'w') as f:
    f.write(content)
