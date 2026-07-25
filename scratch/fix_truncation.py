import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html"
with open(file_path, "r") as f:
    content = f.read()

truncated_part = """    const todayStr = `${yyyy}-${mm}-${dd}`;
</script>"""

fixed_part = """    const todayStr = `${yyyy}-${mm}-${dd}`;
    
    document.getElementById('renewStartDate').value = todayStr;
    document.getElementById('renewStartDate').min = todayStr;
    
    renewModalObj.show();
};
</script>"""

if truncated_part in content:
    content = content.replace(truncated_part, fixed_part)
    with open(file_path, "w") as f:
        f.write(content)
    print("Fixed truncated script.")
else:
    print("Could not find truncated part.")
