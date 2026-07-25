import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/footer.html"
with open(file_path, "r") as f:
    content = f.read()

# Replace the whole <script> block at the bottom
script_start = content.find("<script>")
script_end = content.rfind("</script>") + 9

new_script = """<script>
document.addEventListener('DOMContentLoaded', function() {
    const footerLinks = document.querySelectorAll('.footer a');
    const footerModal = new bootstrap.Modal(document.getElementById('footerContentModal'));
    const modalBody = document.getElementById('footerContentModalBody');
    const modalTitle = document.getElementById('footerContentModalLabel');
    
    // 1. Global event delegation for internal navigation inside the modal
    modalBody.addEventListener('click', function(e) {
        const link = e.target.closest('.sidebar-link, .topic-chip');
        if (!link) return;
        
        e.preventDefault(); // Always prevent default if it's a sidebar link
        
        const targetId = link.getAttribute('href');
        if (targetId && targetId.startsWith('#')) {
            const targetElement = modalBody.querySelector(targetId);
            if (targetElement) {
                // Scroll safely inside the modal
                targetElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                // Update active classes
                modalBody.querySelectorAll('.sidebar-link, .topic-chip').forEach(l => l.classList.remove('active'));
                modalBody.querySelectorAll(`[href="${targetId}"]`).forEach(l => l.classList.add('active'));
            }
        }
    });

    // 2. Global scroll spy for the modal
    modalBody.addEventListener('scroll', () => {
        const sections = modalBody.querySelectorAll('.content-section, .legend-card');
        const mobileBar = modalBody.querySelector('#mobileTopicBar');
        
        if (sections.length === 0) return;
        
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.getBoundingClientRect().top;
            const modalTop = modalBody.getBoundingClientRect().top;
            if (sectionTop - modalTop <= 150) {
                current = section.getAttribute('id');
            }
        });
        
        if (current) {
            modalBody.querySelectorAll('.sidebar-link, .topic-chip').forEach(link => {
                link.classList.remove('active');
                if (link.getAttribute('href') === `#${current}`) {
                    link.classList.add('active');
                }
            });
            
            if (mobileBar) {
                const activeChip = mobileBar.querySelector(`.topic-chip[href="#${current}"]`);
                if (activeChip) {
                    const barRect = mobileBar.getBoundingClientRect();
                    const chipRect = activeChip.getBoundingClientRect();
                    if (chipRect.left < barRect.left || chipRect.right > barRect.right) {
                        activeChip.scrollIntoView({ behavior: 'smooth', inline: 'center', block: 'nearest' });
                    }
                }
            }
        }
    });
    
    // 3. Intercept footer links
    footerLinks.forEach(link => {
        if(link.closest('ul')) {
            link.addEventListener('click', function(e) {
                e.preventDefault();
                const href = this.getAttribute('href');
                const titleText = this.textContent.trim();
                
                modalTitle.innerHTML = `<i class="fa-solid fa-circle-info text-primary me-2"></i> ${titleText}`;
                
                if(!href || href === '#' || href.startsWith('/#')) {
                    modalBody.innerHTML = `
                        <div class="text-center py-5">
                            <i class="fa-solid fa-person-digging text-muted" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                            <h4 class="text-white">Coming Soon</h4>
                            <p class="text-secondary">This section is currently under development. Please check back later!</p>
                        </div>
                    `;
                    footerModal.show();
                    return;
                }
                
                // Show loading state
                modalBody.innerHTML = `
                    <div class="text-center py-5">
                        <i class="fa-solid fa-circle-notch fa-spin text-primary" style="font-size: 2rem;"></i>
                        <p class="mt-3 text-muted">Loading content...</p>
                    </div>
                `;
                footerModal.show();
                
                // Fetch the page
                fetch(href)
                    .then(response => response.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        const mainContent = doc.querySelector('.site-main');
                        
                        if (mainContent) {
                            modalBody.innerHTML = mainContent.innerHTML;
                        } else {
                            const container = doc.querySelector('.container.py-4') || doc.body;
                            modalBody.innerHTML = container.innerHTML || 'Failed to load content.';
                        }
                    })
                    .catch(error => {
                        modalBody.innerHTML = `
                            <div class="text-center py-5 text-danger">
                                <i class="fa-solid fa-triangle-exclamation" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                                <h4>Error</h4>
                                <p>Failed to load the content. Please try again later.</p>
                            </div>
                        `;
                    });
            });
        }
    });
});
</script>"""

if script_start != -1 and script_end != -1:
    content = content[:script_start] + new_script + content[script_end:]
    with open(file_path, "w") as f:
        f.write(content)
    print("Rewrote footer script successfully.")
else:
    print("Could not find script block.")
