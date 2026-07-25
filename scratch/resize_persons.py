import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/booking.html"
with open(file_path, "r") as f:
    content = f.read()

target = """<div class="input-group input-group-lg" style="height: 100%;">
                            <button class="btn btn-outline-secondary px-4" type="button" id="btn-minus-person" style="background-color: var(--color-bg-alt); border-color: rgba(255,255,255,0.1); color: white;"><i class="fa-solid fa-minus"></i></button>
                            <input type="text" id="personsInput" name="persons" class="form-control text-center fw-bold" value="1" readonly style="background-color: rgba(0,0,0,0.4); color: white; pointer-events: none;">
                            <button class="btn btn-outline-secondary" type="button" id="btn-plus-person" class="btn btn-outline-secondary px-4" style="background-color: var(--color-bg-alt); border-color: rgba(255,255,255,0.1); color: white;"><i class="fa-solid fa-plus"></i></button>
                        </div>"""

replacement = """<div class="d-flex align-items-center">
                            <div class="input-group input-group-sm" style="width: 120px;">
                                <button class="btn btn-outline-secondary" type="button" id="btn-minus-person" style="background-color: var(--color-bg-alt); border-color: rgba(255,255,255,0.1); color: white; width: 36px;"><i class="fa-solid fa-minus"></i></button>
                                <input type="text" id="personsInput" name="persons" class="form-control text-center fw-bold px-0" value="1" readonly style="background-color: rgba(0,0,0,0.4); color: white; pointer-events: none; min-width: 40px;">
                                <button class="btn btn-outline-secondary" type="button" id="btn-plus-person" style="background-color: var(--color-bg-alt); border-color: rgba(255,255,255,0.1); color: white; width: 36px;"><i class="fa-solid fa-plus"></i></button>
                            </div>
                        </div>"""

content = content.replace(target, replacement)

with open(file_path, "w") as f:
    f.write(content)

print("Resized persons input.")
