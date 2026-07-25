import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/booking.html"
with open(file_path, "r") as f:
    content = f.read()

target = """                        <label for="personsInput" class="form-label">Number of Persons</label>
                        <input type="number" id="personsInput" name="persons" class="form-control" min="1" max="5" value="1">"""

replacement = """                        <label for="personsInput" class="form-label">Number of Persons</label>
                        <div class="input-group">
                            <button class="btn btn-outline-secondary" type="button" id="btn-minus-person" style="background-color: var(--color-bg-alt); border-color: rgba(255,255,255,0.1); color: white;"><i class="fa-solid fa-minus"></i></button>
                            <input type="text" id="personsInput" name="persons" class="form-control text-center fw-bold" value="1" readonly style="background-color: rgba(0,0,0,0.4); color: white; pointer-events: none;">
                            <button class="btn btn-outline-secondary" type="button" id="btn-plus-person" style="background-color: var(--color-bg-alt); border-color: rgba(255,255,255,0.1); color: white;"><i class="fa-solid fa-plus"></i></button>
                        </div>
                        <script>
                            document.addEventListener('DOMContentLoaded', function() {
                                const minusBtn = document.getElementById('btn-minus-person');
                                const plusBtn = document.getElementById('btn-plus-person');
                                const personsInput = document.getElementById('personsInput');
                                
                                minusBtn.addEventListener('click', () => {
                                    let val = parseInt(personsInput.value) || 1;
                                    if (val > 1) {
                                        personsInput.value = val - 1;
                                        personsInput.dispatchEvent(new Event('input', { bubbles: true }));
                                    }
                                });
                                
                                plusBtn.addEventListener('click', () => {
                                    let val = parseInt(personsInput.value) || 1;
                                    if (val < 5) {
                                        personsInput.value = val + 1;
                                        personsInput.dispatchEvent(new Event('input', { bubbles: true }));
                                    }
                                });
                            });
                        </script>"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Updated persons input successfully.")
