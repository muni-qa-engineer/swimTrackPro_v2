import os

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/login.html"
with open(file_path, "r") as f:
    content = f.read()

# 1. Update grid classes
content = content.replace(
    '<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">',
    '<div class="grid grid-cols-2 md:grid-cols-4 gap-2 md:gap-4">'
)

# 2. Add "Buy Now" text. We can append it right before closing </div> of long-term-card
# Let's find: `<div class="price-actual mb-0">₹{{ "{:,}".format(pkg["individual"]["3_months"].final_price) }}</div>` and so on.
# It might be easier to replace `</div>\n                </a>` with `<div class="mt-2 text-center" style="font-size: 0.8rem; color: var(--color-primary); font-weight: 600;">Buy Now <i class="fa-solid fa-arrow-right fa-sm ms-1"></i></div></div>\n                </a>`
# BUT that might match other places too.
# Let's look for `class="long-term-card"` and replace `</div>\n                </a>` only in those blocks.

import re

# Split by `class="long-term-card"`
parts = content.split('class="long-term-card">')

new_content = parts[0]
buy_now_html = '\n                    <div class="mt-2 text-center" style="font-size: 0.8rem; color: var(--color-primary); font-weight: 600;">Buy Now <i class="fa-solid fa-arrow-right fa-sm ms-1"></i></div>'

for part in parts[1:]:
    # Find the FIRST occurrence of `</div>\n                </a>` in this part
    # Actually, `price-actual` is the last element before closing `long-term-card`.
    # Let's just find `</div>\n                </a>` which closes the card.
    
    # We can replace the first occurrence of `\n                    </div>\n                </a>`
    # or just use regex to insert after `price-actual` block.
    
    # Find `price-actual mb-0">...</div>`
    match = re.search(r'(<div class="price-actual mb-0">.*?</div>)', part)
    if match:
        replaced_part = part[:match.end()] + buy_now_html + part[match.end():]
        new_content += 'class="long-term-card">' + replaced_part
    else:
        new_content += 'class="long-term-card">' + part

with open(file_path, "w") as f:
    f.write(new_content)

print("Updated login.html with mobile grid-cols-2 and Buy Now text")
