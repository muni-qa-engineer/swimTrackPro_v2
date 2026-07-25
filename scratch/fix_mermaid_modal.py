import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/components/footer.html"
with open(file_path, "r") as f:
    content = f.read()

# 1. Add mermaid script tag right before the existing <script> tag
target_script = "<script>\ndocument.addEventListener('DOMContentLoaded', () => {"

replacement_script = """<!-- Dynamic Mermaid Support for Modals -->
<script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    window.mermaid = mermaid;
    mermaid.initialize({ 
        startOnLoad: false, 
        theme: 'dark',
        fontFamily: 'Inter, sans-serif'
    });
</script>

<script>
document.addEventListener('DOMContentLoaded', () => {"""

content = content.replace(target_script, replacement_script)

# 2. Add mermaid.run() after injecting innerHTML
target_inject = """                        modalBody.innerHTML = contentToInject.innerHTML;"""
replacement_inject = """                        modalBody.innerHTML = contentToInject.innerHTML;
                        
                        // Re-render Mermaid graphs if any exist in the injected content
                        if (window.mermaid && modalBody.querySelector('.mermaid')) {
                            // Give the DOM a tiny bit of time to settle before rendering
                            setTimeout(() => {
                                try {
                                    window.mermaid.run({
                                        nodes: modalBody.querySelectorAll('.mermaid')
                                    });
                                } catch (e) {
                                    console.error('Mermaid render error:', e);
                                }
                            }, 50);
                        }"""
content = content.replace(target_inject, replacement_inject)

with open(file_path, "w") as f:
    f.write(content)

print("Updated footer.html to support dynamic Mermaid rendering.")
