import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/login.html"
with open(file_path, "r") as f:
    content = f.read()

# Replace individual cards
content = re.sub(
    r'(<!-- 3 Months -->\s*)<div class="long-term-card">(.*?)<div class="price-actual mb-0">₹\{\{.*?\}\}</div>\s*</div>',
    r'\1<a href="/booking?package=3_months" class="text-decoration-none d-block">\n                    <div class="long-term-card">\2<div class="price-actual mb-0">₹{{ "{:,}".format(pkg["individual"]["3_months"].final_price) }}</div>\n                    </div>\n                </a>',
    content,
    flags=re.DOTALL
)
content = re.sub(
    r'(<!-- 6 Months -->\s*)<div class="long-term-card">(.*?)<div class="price-actual mb-0">₹\{\{.*?\}\}</div>\s*</div>',
    r'\1<a href="/booking?package=6_months" class="text-decoration-none d-block">\n                    <div class="long-term-card">\2<div class="price-actual mb-0">₹{{ "{:,}".format(pkg["individual"]["6_months"].final_price) }}</div>\n                    </div>\n                </a>',
    content,
    flags=re.DOTALL
)
content = re.sub(
    r'(<!-- 9 Months -->\s*)<div class="long-term-card">(.*?)<div class="price-actual mb-0">₹\{\{.*?\}\}</div>\s*</div>',
    r'\1<a href="/booking?package=9_months" class="text-decoration-none d-block">\n                    <div class="long-term-card">\2<div class="price-actual mb-0">₹{{ "{:,}".format(pkg["individual"]["9_months"].final_price) }}</div>\n                    </div>\n                </a>',
    content,
    flags=re.DOTALL
)
content = re.sub(
    r'(<!-- 1 Year -->\s*)<div class="long-term-card">(.*?)<div class="price-actual mb-0">₹\{\{.*?\}\}</div>\s*</div>',
    r'\1<a href="/booking?package=12_months" class="text-decoration-none d-block">\n                    <div class="long-term-card">\2<div class="price-actual mb-0">₹{{ "{:,}".format(pkg["individual"]["12_months"].final_price) }}</div>\n                    </div>\n                </a>',
    content,
    flags=re.DOTALL
)

with open(file_path, "w") as f:
    f.write(content)

print("Updated login.html successfully.")
