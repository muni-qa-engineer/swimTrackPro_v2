import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/static/booking.js"
with open(file_path, "r") as f:
    content = f.read()

# Replace renew flow trainer selection
old_renew = """        // 6. Pre-fill Trainer Card
        if (window.renewBookingData.trainer_username) {
            const selectTrainer = () => {
                const card = document.getElementById(`trainer-card-${window.renewBookingData.trainer_username}`);
                if (card) {
                    toggleTrainerSelection(window.renewBookingData.trainer_username);
                } else {
                    setTimeout(selectTrainer, 100);
                }
            };
            selectTrainer();
        }"""
new_renew = """        // 6. Pre-fill Trainer Dropdown
        if (window.renewBookingData.trainer_username) {
            const selectTrainer = () => {
                const coachSelect = document.getElementById('coachSelect');
                if (coachSelect) {
                    coachSelect.value = window.renewBookingData.trainer_username;
                    coachSelect.dispatchEvent(new Event('change', { bubbles: true }));
                } else {
                    setTimeout(selectTrainer, 100);
                }
            };
            selectTrainer();
        }"""
content = content.replace(old_renew, new_renew)

with open(file_path, "w") as f:
    f.write(content)
print("booking.js renew flow updated")
