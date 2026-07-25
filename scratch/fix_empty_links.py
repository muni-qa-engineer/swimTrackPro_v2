import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/footer.html"
with open(file_path, "r") as f:
    content = f.read()

# Replace the existing link handling logic inside footer.html script
target_script = """    const footerLinks = document.querySelectorAll('footer a');
    footerLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && targetPaths.includes(href)) {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const modalEl = document.getElementById('footerDynamicModal');
                const modalBody = document.getElementById('footerDynamicModalBody');
                
                modalBody.innerHTML = `
                    <div class="d-flex justify-content-center align-items-center py-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                `;
                
                if (typeof bootstrap !== 'undefined') {
                    const modal = new bootstrap.Modal(modalEl);
                    modal.show();
                }
                
                fetch(href)
                    .then(r => r.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        
                        // Extract the main content. Prioritize <main>, then a main container, then body.
                        let contentToInject = doc.querySelector('main');
                        if (!contentToInject) {
                            contentToInject = doc.querySelector('.container.py-4') || doc.body;
                        }
                        
                        modalBody.innerHTML = contentToInject.innerHTML;
                    })
                    .catch(err => {
                        modalBody.innerHTML = '<div class="text-center py-5 text-danger">Failed to load content.</div>';
                    });
            });
        }
    });"""

replacement_script = """    const footerLinks = document.querySelectorAll('footer a');
    footerLinks.forEach(link => {
        const href = link.getAttribute('href');
        
        if (href && targetPaths.includes(href)) {
            // Handle internal pages with fetch
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const modalEl = document.getElementById('footerDynamicModal');
                const modalBody = document.getElementById('footerDynamicModalBody');
                
                modalBody.innerHTML = `
                    <div class="d-flex justify-content-center align-items-center py-5">
                        <div class="spinner-border text-primary" role="status">
                            <span class="visually-hidden">Loading...</span>
                        </div>
                    </div>
                `;
                
                if (typeof bootstrap !== 'undefined') {
                    const modal = new bootstrap.Modal(modalEl);
                    modal.show();
                }
                
                fetch(href)
                    .then(r => r.text())
                    .then(html => {
                        const parser = new DOMParser();
                        const doc = parser.parseFromString(html, 'text/html');
                        
                        // Extract the main content. Prioritize <main>, then a main container, then body.
                        let contentToInject = doc.querySelector('main');
                        if (!contentToInject) {
                            contentToInject = doc.querySelector('.container.py-4') || doc.body;
                        }
                        
                        modalBody.innerHTML = contentToInject.innerHTML;
                    })
                    .catch(err => {
                        modalBody.innerHTML = '<div class="text-center py-5 text-danger">Failed to load content.</div>';
                    });
            });
        } 
        else if (href === '#' || !href) {
            // Handle empty links like Privacy, Press, Social Media
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const modalEl = document.getElementById('footerDynamicModal');
                const modalBody = document.getElementById('footerDynamicModalBody');
                
                modalBody.innerHTML = `
                    <div class="text-center py-5" style="color: var(--color-text-secondary);">
                        <i class="fa-solid fa-person-digging mb-3" style="font-size: 3.5rem; color: var(--color-primary); opacity: 0.8;"></i>
                        <h3 style="color: white; margin-bottom: 0.5rem;">Under Construction</h3>
                        <p style="font-size: 1.1rem;">We will update this soon!</p>
                        <button type="button" class="btn btn-outline-light mt-3 px-4" data-bs-dismiss="modal">Okay</button>
                    </div>
                `;
                
                if (typeof bootstrap !== 'undefined') {
                    const modal = new bootstrap.Modal(modalEl);
                    modal.show();
                }
            });
        }
    });"""

content = content.replace(target_script, replacement_script)

with open(file_path, "w") as f:
    f.write(content)

print("Updated footer.html for empty links.")
