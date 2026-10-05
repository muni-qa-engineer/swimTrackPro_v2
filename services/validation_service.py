"""Contact number and password validation service."""

import re

def validate_contact_number(phone):
    """
    Validates contact number (which also acts as guest password/credential).
    Enforces rules:
    1. Consecutive numbers more than 6 digits not allowed (ascending or descending, e.g. 1234567, 9876543).
    2. Cannot start with 0, 1, 2, 3, 4, 5 (must start with 6, 7, 8, 9).
    3. Repetitive digits more than 6 times not allowed (neither consecutive nor total frequency).
    4. Cannot start with two same digits: 00, 11, 22, 33, 44, 55.
    
    Additional robust checks implemented:
    5. Must be exactly 10 digits (digits only).
    6. Cannot be all identical digits (e.g. 9999999999, 8888888888).
    7. Cannot be common dummy/placeholder numbers (e.g. 9876543210, 1234567890).
    """
    if not phone:
        return False, "Contact number is required."
        
    cleaned = "".join(character for character in str(phone) if character.isdigit())
    
    # Check 5: Exactly 10 digits
    if len(cleaned) != 10:
        return False, "Contact number must be exactly 10 digits."
        
    # Rule 2: Cannot start with 0, 1, 2, 3, 4, 5 (must start with 6, 7, 8, 9)
    if cleaned[0] in "012345":
        return False, f"Contact number cannot start with '{cleaned[0]}'. Must start with 6, 7, 8, or 9."
        
    # Rule 4: Cannot start with repeated digits 00, 11, 22, 33, 44, 55
    if cleaned[:2] in ("00", "11", "22", "33", "44", "55"):
        return False, f"Contact number cannot start with repeated digits '{cleaned[:2]}'."
        
    # Rule 3: Repetitive digits more than 6 times not allowed
    if re.search(r'(\d)\1{6,}', cleaned):
        return False, "Repetitive digits appearing consecutively more than 6 times are not allowed."
    if any(cleaned.count(digit) > 6 for digit in set(cleaned)):
        return False, "Any single digit cannot appear more than 6 times in the number."
        
    # Rule 1: Consecutive numbers more than 6 digits not allowed (ascending or descending)
    inc_count = 1
    dec_count = 1
    for index in range(len(cleaned) - 1):
        curr_digit = int(cleaned[index])
        next_digit = int(cleaned[index + 1])
        
        # Ascending consecutive (e.g. 1-2-3-4-5-6-7)
        if next_digit == curr_digit + 1:
            inc_count += 1
            if inc_count > 6:
                return False, "Consecutive numbers of more than 6 digits (e.g. sequential numbers) are not allowed."
        else:
            inc_count = 1
            
        # Descending consecutive (e.g. 7-6-5-4-3-2-1)
        if next_digit == curr_digit - 1:
            dec_count += 1
            if dec_count > 6:
                return False, "Consecutive numbers of more than 6 digits (e.g. sequential numbers) are not allowed."
        else:
            dec_count = 1
            
    # Check 6: All identical digits
    if len(set(cleaned)) == 1:
        return False, "Contact number cannot consist of all identical digits."
        
    # Check 7: Known test/dummy phone numbers
    dummy_numbers = {
        "9876543210",
        "1234567890",
        "0123456789",
        "9898989898",
        "9000000000",
        "9999999999",
        "8888888888",
        "7777777777",
        "6666666666"
    }
    if cleaned in dummy_numbers:
        return False, "Please enter a genuine, active mobile number (test sequence detected)."
        
    return True, ""
