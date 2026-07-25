import os

source_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/scratch/original_footer.html"
target_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/footer.html"

with open(source_path, "r") as f:
    content = f.read()

modal_and_script = """

<!-- About Swimming Modal -->
<div class="modal fade" id="footerSwimmingModal" tabindex="-1" aria-hidden="true">
    <div class="modal-dialog modal-xl modal-dialog-centered modal-dialog-scrollable">
        <div class="modal-content" style="background: var(--color-bg); border: 1px solid rgba(255,255,255,0.1); border-radius: var(--radius-lg);">
            <div class="modal-header border-0" style="padding: 1.5rem 2rem 0;">
                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close" style="opacity: 0.8;"></button>
            </div>
            <div class="modal-body p-0" id="footerSwimmingModalBody" style="min-height: 50vh;">
                <!-- Content injected here -->
            </div>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', () => {
    const swimmingLink = document.querySelector('a[href="/about-swimming"]');
    if (swimmingLink) {
        swimmingLink.addEventListener('click', (e) => {
            e.preventDefault();
            const modalEl = document.getElementById('footerSwimmingModal');
            const modalBody = document.getElementById('footerSwimmingModalBody');
            
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
            
            fetch('/about-swimming')
                .then(r => r.text())
                .then(html => {
                    const parser = new DOMParser();
                    const doc = parser.parseFromString(html, 'text/html');
                    const mainContent = doc.querySelector('main') || doc.body;
                    modalBody.innerHTML = mainContent.innerHTML;
                })
                .catch(err => {
                    modalBody.innerHTML = '<div class="text-center py-5 text-danger">Failed to load content.</div>';
                });
        });
    }
});
</script>
"""

with open(target_path, "w") as f:
    f.write(content + modal_and_script)

print("Restored footer.html and added specific modal for About Swimming.")
