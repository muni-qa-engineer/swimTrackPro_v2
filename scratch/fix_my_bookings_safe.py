import re

file_path = "/Users/munisekhar/Desktop/swimTrackPro_v2/templates/my_bookings.html"
with open(file_path, "r") as f:
    content = f.read()

# Fix block title
old_title_block = content[content.find("{% block title %}"):content.find("{% endblock %}", content.find("{% block title %}")) + 14]
new_title_block = "{% block title %}My Bookings | SwimTrack Pro{% endblock %}"
content = content.replace(old_title_block, new_title_block)

# Fix block page_title
old_page_title_block = content[content.find("{% block page_title %}"):content.find("{% endblock %}", content.find("{% block page_title %}")) + 14]
new_page_title_block = "{% block page_title %}Bookings{% endblock %}"
content = content.replace(old_page_title_block, new_page_title_block)

# Replace the OLD filter script block logic safely
# The old script starts with document.addEventListener('DOMContentLoaded', function() { \n const filterBtns = document.querySelectorAll('.filter-btn');
# I will find that exact function body and replace it.

old_logic = """    document.addEventListener('DOMContentLoaded', function() {
        const filterBtns = document.querySelectorAll('.filter-btn');
        const cards = document.querySelectorAll('.booking-card');
        const emptyState = document.getElementById('filter-empty-state');
        const emptyText = document.getElementById('filter-empty-text');
        
        filterBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const isCurrentlyActive = this.classList.contains('active');
                
                // Remove active class from all buttons
                filterBtns.forEach(b => {
                    b.classList.remove('active');
                });
                
                let activeFilter = null;
                
                if (!isCurrentlyActive) {
                    this.classList.add('active');
                    activeFilter = this.dataset.filter;
                }
                
                let totalVisible = 0;
                
                // Filter the cards
                cards.forEach(card => {
                    if (!activeFilter || card.dataset.bookingStatus === activeFilter) {
                        card.style.display = '';
                        totalVisible++;
                    } else {
                        card.style.display = 'none';
                    }
                });
                
                // Show empty state if no cards are visible
                if (totalVisible === 0) {
                    emptyState.style.display = 'block';
                    if (activeFilter === 'booked') {
                        emptyText.textContent = 'No booked bookings found.';
                    } else if (activeFilter === 'active') {
                        emptyText.textContent = 'No active bookings found.';
                    } else if (activeFilter === 'completed') {
                        emptyText.textContent = 'No completed bookings found.';
                    } else {
                        emptyText.textContent = 'No bookings found.';
                    }
                } else {
                    emptyState.style.display = 'none';
                }
                
                // Hide empty groups
                document.querySelectorAll('.col-12.mb-4').forEach(groupContainer => {
                    const grid = groupContainer.querySelector('.grid');
                    if (grid) {
                        const visibleCards = grid.querySelectorAll('.booking-card:not([style*="display: none"])');
                        const addCard = grid.querySelector('.border-dashed'); // Renew card
                        
                        // If there are no visible cards, hide the group
                        if (visibleCards.length === 0 && !addCard) {
                            groupContainer.style.display = 'none';
                        } else {
                            groupContainer.style.display = '';
                        }
                    }
                });
            });
        });
    });"""

new_logic = """    document.addEventListener('DOMContentLoaded', function() {
        const filterBtns = document.querySelectorAll('.filter-btn');
        const cards = document.querySelectorAll('.booking-card');
        const emptyState = document.getElementById('filter-empty-state');
        const emptyText = document.getElementById('filter-empty-text');
        
        filterBtns.forEach(btn => {
            btn.addEventListener('click', function() {
                const isCurrentlyActive = this.classList.contains('active');
                
                // Remove active class from all buttons
                filterBtns.forEach(b => {
                    b.classList.remove('active');
                    b.style.backgroundColor = '';
                    b.style.color = '';
                });
                
                let activeFilter = null;
                
                if (!isCurrentlyActive) {
                    this.classList.add('active');
                    activeFilter = this.dataset.filter;
                    // Add solid background to active button
                    if (activeFilter === 'booked') {
                        this.style.backgroundColor = '#0d6efd';
                        this.style.color = 'white';
                    } else if (activeFilter === 'active') {
                        this.style.backgroundColor = '#0dcaf0';
                        this.style.color = 'black';
                    } else if (activeFilter === 'completed') {
                        this.style.backgroundColor = '#6c757d';
                        this.style.color = 'white';
                    }
                }
                
                let totalVisible = 0;
                
                // Filter the cards
                cards.forEach(card => {
                    if (!activeFilter || card.dataset.bookingStatus === activeFilter) {
                        card.style.display = '';
                        totalVisible++;
                    } else {
                        card.style.display = 'none';
                    }
                });
                
                // Show empty state if no cards are visible
                if (totalVisible === 0) {
                    emptyState.style.display = 'block';
                    if (activeFilter === 'booked') {
                        emptyText.textContent = 'No booked bookings found.';
                    } else if (activeFilter === 'active') {
                        emptyText.textContent = 'No active bookings found.';
                    } else if (activeFilter === 'completed') {
                        emptyText.textContent = 'No completed bookings found.';
                    } else {
                        emptyText.textContent = 'No bookings found.';
                    }
                } else {
                    emptyState.style.display = 'none';
                }
                
                // Hide empty groups
                document.querySelectorAll('.col-12.mb-4').forEach(groupContainer => {
                    const grid = groupContainer.querySelector('.grid');
                    if (grid) {
                        const visibleCards = grid.querySelectorAll('.booking-card:not([style*="display: none"])');
                        const addCard = grid.querySelector('.border-dashed'); // Renew card
                        
                        // If there are no visible cards, hide the group
                        if (visibleCards.length === 0) {
                            groupContainer.style.display = 'none';
                        } else {
                            groupContainer.style.display = '';
                        }
                    }
                });
            });
        });
    });"""

if old_logic in content:
    content = content.replace(old_logic, new_logic)
else:
    print("WARNING: Could not find old_logic for tab filtering!")

with open(file_path, "w") as f:
    f.write(content)
print("Done fixing my_bookings.html safely.")
