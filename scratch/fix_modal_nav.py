import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/footer.html"
with open(file_path, "r") as f:
    content = f.read()

target = """                        if (mainContent) {
                            modalBody.innerHTML = mainContent.innerHTML;
                        } else {
                            // Fallback if no .site-main
                            const container = doc.querySelector('.container.py-4') || doc.body;
                            modalBody.innerHTML = container.innerHTML || 'Failed to load content.';
                        }"""

replacement = """                        if (mainContent) {
                            modalBody.innerHTML = mainContent.innerHTML;
                        } else {
                            // Fallback if no .site-main
                            const container = doc.querySelector('.container.py-4') || doc.body;
                            modalBody.innerHTML = container.innerHTML || 'Failed to load content.';
                        }
                        
                        // Execute internal navigation scripts (like for about-swimming)
                        const allNavLinks = modalBody.querySelectorAll('.sidebar-link, .topic-chip');
                        const sections = modalBody.querySelectorAll('.content-section, .legend-card');
                        const mobileBar = modalBody.querySelector('#mobileTopicBar');
                        
                        allNavLinks.forEach(link => {
                            link.addEventListener('click', function(e) {
                                e.preventDefault();
                                const targetId = this.getAttribute('href');
                                if (targetId && targetId.startsWith('#')) {
                                    const targetElement = modalBody.querySelector(targetId);
                                    if (targetElement) {
                                        targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                                        allNavLinks.forEach(l => l.classList.remove('active'));
                                        modalBody.querySelectorAll(`[href="${targetId}"]`).forEach(l => l.classList.add('active'));
                                    }
                                }
                            });
                        });
                        
                        // Scroll spy for modalBody
                        modalBody.addEventListener('scroll', () => {
                            let current = '';
                            sections.forEach(section => {
                                const sectionTop = section.getBoundingClientRect().top;
                                const modalTop = modalBody.getBoundingClientRect().top;
                                // Add 150px offset to trigger slightly before it reaches top
                                if (sectionTop - modalTop <= 150) {
                                    current = section.getAttribute('id');
                                }
                            });
                            
                            allNavLinks.forEach(link => {
                                link.classList.remove('active');
                                if (link.getAttribute('href') === `#${current}`) {
                                    link.classList.add('active');
                                }
                            });
                            
                            if (mobileBar) {
                                const activeChip = mobileBar.querySelector('.topic-chip.active');
                                if (activeChip) {
                                    const barRect = mobileBar.getBoundingClientRect();
                                    const chipRect = activeChip.getBoundingClientRect();
                                    if (chipRect.left < barRect.left || chipRect.right > barRect.right) {
                                        activeChip.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                                    }
                                }
                            }
                        });"""

if target in content:
    content = content.replace(target, replacement)
    with open(file_path, "w") as f:
        f.write(content)
    print("Fixed modal internal navigation.")
else:
    print("Could not find the target string in footer.html.")
