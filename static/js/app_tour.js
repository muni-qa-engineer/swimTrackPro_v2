/**
 * SwimTrackPro - Modern Interactive Guided Product Tour & Welcome Experience
 * Designed with modern SaaS UX standards (inspired by Linear, Stripe, Notion)
 */

(function() {
    'use strict';

    class SwimTrackTour {
        constructor() {
            this.currentStep = 0;
            this.steps = [];
            this.overlay = null;
            this.popover = null;
            this.highlightedEl = null;
            this.role = 'guest';
            this.userName = '';
            this.onKeyDown = this.handleKeyDown.bind(this);
            this.onResize = this.handleResize.bind(this);
        }

        init(options = {}) {
            this.role = options.role || 'guest';
            this.userName = options.userName || '';
            this.steps = options.steps || this.getDefaultSteps(this.role);
        }

        getDefaultSteps(role) {
            if (role === 'trainer') {
                return [
                    {
                        element: '#tourCoachActiveBookings',
                        fallback: '.metrics-grid .metric-card.primary',
                        title: '👥 Active Bookings',
                        badge: 'Students',
                        description: 'See all swimmers currently assigned to you for private or doorstep sessions. Tap to view student details and contacts.'
                    },
                    {
                        element: '#coachEarningsMetricCard',
                        fallback: '#coachEarningsCarousel',
                        title: '💰 Earnings Carousel',
                        badge: 'Finances',
                        description: 'Swipe or use the arrows to cycle between Monthly, Yearly, and Overall earnings. Track revenue from every session you conduct in real time!'
                    },
                    {
                        element: '#tourCoachUpcomingSessions',
                        fallback: 'section.dashboard-main h3:has(.fa-calendar-check)',
                        title: '📋 Daily Sessions & Attendance',
                        badge: 'Schedule',
                        description: 'Your upcoming schedule is organized by date and time. Confirm swimmer attendance with one tap right after completing each session.'
                    },
                    {
                        element: '#tourCoachTimeSlots',
                        fallback: 'section.dashboard-main h3:has(.fa-clock)',
                        title: '⏰ Manage Time Slots',
                        badge: 'Availability',
                        description: 'Define and update your weekly working hours so students and admins can book sessions during your active availability.'
                    },
                    {
                        element: '#tourCoachNoticeBoard',
                        fallback: 'section.dashboard-main h3:has(.fa-bullhorn)',
                        title: '📢 Notice Board & Approvals',
                        badge: 'Updates',
                        description: 'Check official academy announcements, student pause notices, and session rescheduling requests that need your review.'
                    }
                ];
            } else {
                // Swimmer / Guest Steps
                return [
                    {
                        element: '#tourNextSessionCard',
                        fallback: '.metrics-grid .metric-card.primary',
                        title: '📅 Next Swim Session',
                        badge: 'Upcoming',
                        description: 'Quickly see your next scheduled class, timing, assigned coach, and lane info. Eligible sessions can be skipped or rescheduled directly.'
                    },
                    {
                        element: '#tourProgressTracker',
                        fallback: '.glass-panel:has(.progress-circle)',
                        title: '📈 Progress & Class Tracker',
                        badge: 'Attendance',
                        description: 'Track how many classes you have completed against your package total. Progress updates automatically as your coach confirms each session.'
                    },
                    {
                        element: '#tourMembershipCard',
                        fallback: '.glass-panel:has(.fa-circle-pause)',
                        title: '💳 Membership & Flexibility',
                        badge: 'Package',
                        description: 'Review active membership validity dates, remaining classes, and doorstep perks. Freeze long-term passes during travel or illness with one click.'
                    },
                    {
                        element: '#tourMySwimmersCard',
                        fallback: '.glass-panel:has(.fa-users)',
                        title: '🏊 Swimmer Profiles & Learning',
                        badge: 'Students',
                        description: 'Manage family swimmer profiles, track individual skill levels, and watch learning milestones grow over time.'
                    },
                    {
                        element: '#tourMiniCalendar',
                        fallback: '.mini-calendar',
                        title: '🗓️ Training Calendar',
                        badge: 'Calendar',
                        description: 'Get a bird’s-eye view of your monthly training days. Click Full View to explore comprehensive class histories and dates.'
                    }
                ];
            }
        }

        start(customSteps = null) {
            if (customSteps) {
                this.steps = customSteps;
            } else if (!this.steps || this.steps.length === 0) {
                this.steps = this.getDefaultSteps(this.role);
            }

            if (!this.steps || this.steps.length === 0) return;

            // Remove any existing welcome modal
            const welcomeModal = document.getElementById('welcomeModalFTUE');
            if (welcomeModal) {
                welcomeModal.style.opacity = '0';
                setTimeout(() => welcomeModal.remove(), 250);
            }

            this.createOverlay();
            this.createPopover();
            this.currentStep = 0;
            this.goToStep(0);

            window.addEventListener('keydown', this.onKeyDown);
            window.addEventListener('resize', this.onResize);
        }

        createOverlay() {
            if (document.getElementById('tourBackdropOverlay')) return;
            const overlay = document.createElement('div');
            overlay.id = 'tourBackdropOverlay';
            overlay.className = 'tour-backdrop-overlay';
            overlay.innerHTML = '';
            overlay.onclick = () => this.close();
            document.body.appendChild(overlay);
            this.overlay = overlay;
        }

        createPopover() {
            if (document.getElementById('tourPopoverCard')) return;
            const popover = document.createElement('div');
            popover.id = 'tourPopoverCard';
            popover.className = 'tour-popover-card';
            popover.setAttribute('role', 'dialog');
            popover.setAttribute('aria-modal', 'true');
            popover.innerHTML = `
                <div class="tour-popover-header d-flex align-items-center justify-content-between mb-2">
                    <div class="d-flex align-items-center gap-2">
                        <span class="badge tour-step-badge" id="tourStepBadge">Step 1 of 5</span>
                        <span class="badge tour-category-badge" id="tourCategoryBadge">Overview</span>
                    </div>
                    <button type="button" class="tour-close-btn" onclick="SwimTrackTourInstance.close()" aria-label="Close tour">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
                <div class="tour-progress-bar-container">
                    <div class="tour-progress-bar" id="tourProgressBar" style="width: 20%;"></div>
                </div>
                <h4 class="tour-step-title fw-bold text-white mb-2" id="tourStepTitle"></h4>
                <p class="tour-step-desc text-secondary small mb-4" id="tourStepDesc"></p>
                <div class="tour-popover-footer d-flex align-items-center justify-content-between pt-2 border-top border-white-10">
                    <button type="button" class="btn btn-link btn-sm text-muted text-decoration-none p-0" onclick="SwimTrackTourInstance.close()">Skip tour</button>
                    <div class="d-flex align-items-center gap-2">
                        <button type="button" class="btn btn-outline-light btn-sm rounded-pill px-3" id="tourPrevBtn" onclick="SwimTrackTourInstance.prev()">
                            <i class="fa-solid fa-arrow-left me-1"></i> Back
                        </button>
                        <button type="button" class="btn btn-primary btn-sm rounded-pill px-3 fw-bold" id="tourNextBtn" onclick="SwimTrackTourInstance.next()">
                            Next <i class="fa-solid fa-arrow-right ms-1"></i>
                        </button>
                    </div>
                </div>
            `;
            document.body.appendChild(popover);
            this.popover = popover;
        }

        goToStep(index) {
            if (index < 0 || index >= this.steps.length) return;
            this.currentStep = index;
            const step = this.steps[index];

            // Clean up previous highlight
            if (this.highlightedEl) {
                this.highlightedEl.classList.remove('tour-highlighted-element');
            }

            // Find target element
            let target = null;
            if (step.element) {
                target = document.querySelector(step.element);
            }
            if (!target && step.fallback) {
                try {
                    target = document.querySelector(step.fallback);
                } catch(e) {}
            }

            // Update Popover content
            const badge = document.getElementById('tourStepBadge');
            const catBadge = document.getElementById('tourCategoryBadge');
            const title = document.getElementById('tourStepTitle');
            const desc = document.getElementById('tourStepDesc');
            const progBar = document.getElementById('tourProgressBar');
            const prevBtn = document.getElementById('tourPrevBtn');
            const nextBtn = document.getElementById('tourNextBtn');

            if (badge) badge.textContent = `Step ${index + 1} of ${this.steps.length}`;
            if (catBadge) catBadge.textContent = step.badge || 'Feature';
            if (title) title.innerHTML = step.title;
            if (desc) desc.textContent = step.description;
            if (progBar) progBar.style.width = `${((index + 1) / this.steps.length) * 100}%`;

            if (prevBtn) {
                prevBtn.style.visibility = (index === 0) ? 'hidden' : 'visible';
            }

            if (nextBtn) {
                if (index === this.steps.length - 1) {
                    nextBtn.className = 'btn btn-success btn-sm rounded-pill px-3 fw-bold';
                    nextBtn.innerHTML = 'Got It! Finish 🎉';
                } else {
                    nextBtn.className = 'btn btn-primary btn-sm rounded-pill px-3 fw-bold';
                    nextBtn.innerHTML = 'Next <i class="fa-solid fa-arrow-right ms-1"></i>';
                }
            }

            if (target) {
                this.highlightedEl = target;
                target.classList.add('tour-highlighted-element');

                // Smooth scroll into center view
                target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });

                // Position popover
                setTimeout(() => this.positionPopover(target), 300);
            } else {
                // If element is not present on page, center popover
                this.centerPopover();
            }
        }

        positionPopover(target) {
            if (!this.popover) return;
            const rect = target.getBoundingClientRect();
            const popRect = this.popover.getBoundingClientRect();
            const viewportWidth = window.innerWidth;
            const viewportHeight = window.innerHeight;

            // On mobile viewports (< 768px), keep popover fixed at bottom for optimal touch ergonomics
            if (viewportWidth < 768) {
                this.popover.style.top = 'auto';
                this.popover.style.bottom = '20px';
                this.popover.style.left = '50%';
                this.popover.style.transform = 'translateX(-50%)';
                return;
            }

            // Desktop smart positioning (Prefer Bottom, then Top, then Right)
            let top, left;
            const margin = 16;

            if (rect.bottom + popRect.height + margin < viewportHeight) {
                // Place Below target
                top = rect.bottom + margin;
                left = rect.left + (rect.width / 2) - (popRect.width / 2);
            } else if (rect.top - popRect.height - margin > 0) {
                // Place Above target
                top = rect.top - popRect.height - margin;
                left = rect.left + (rect.width / 2) - (popRect.width / 2);
            } else {
                // Center vertically
                top = (viewportHeight / 2) - (popRect.height / 2);
                left = (viewportWidth / 2) - (popRect.width / 2);
            }

            // Constrain within viewport boundaries
            left = Math.max(16, Math.min(left, viewportWidth - popRect.width - 16));
            top = Math.max(16, Math.min(top, viewportHeight - popRect.height - 16));

            this.popover.style.top = `${top}px`;
            this.popover.style.bottom = 'auto';
            this.popover.style.left = `${left}px`;
            this.popover.style.transform = 'none';
        }

        centerPopover() {
            if (!this.popover) return;
            this.popover.style.top = '50%';
            this.popover.style.bottom = 'auto';
            this.popover.style.left = '50%';
            this.popover.style.transform = 'translate(-50%, -50%)';
        }

        next() {
            if (this.currentStep < this.steps.length - 1) {
                this.goToStep(this.currentStep + 1);
            } else {
                this.finish();
            }
        }

        prev() {
            if (this.currentStep > 0) {
                this.goToStep(this.currentStep - 1);
            }
        }

        handleKeyDown(e) {
            if (e.key === 'Escape') {
                this.close();
            } else if (e.key === 'ArrowRight') {
                this.next();
            } else if (e.key === 'ArrowLeft') {
                this.prev();
            }
        }

        handleResize() {
            if (this.highlightedEl) {
                this.positionPopover(this.highlightedEl);
            } else {
                this.centerPopover();
            }
        }

        close() {
            if (this.highlightedEl) {
                this.highlightedEl.classList.remove('tour-highlighted-element');
                this.highlightedEl = null;
            }
            if (this.overlay) {
                this.overlay.remove();
                this.overlay = null;
            }
            if (this.popover) {
                this.popover.remove();
                this.popover = null;
            }
            window.removeEventListener('keydown', this.onKeyDown);
            window.removeEventListener('resize', this.onResize);
            this.markTourCompletedOnBackend();
        }

        finish() {
            this.close();
            this.showCelebrationToast();
            this.markTourCompletedOnBackend();
        }

        markTourCompletedOnBackend() {
            try {
                fetch('/api/complete_tour', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                }).catch(() => {});
            } catch (err) {}
        }

        showCelebrationToast() {
            const toast = document.createElement('div');
            toast.className = 'tour-celebrate-toast animate-bounce-in';
            toast.innerHTML = `
                <div class="d-flex align-items-center gap-3">
                    <span style="font-size: 1.8rem;">🎉</span>
                    <div>
                        <div class="fw-bold text-white">Tour Completed!</div>
                        <div class="small text-white-50">You're all set to explore and enjoy SwimTrackPro.</div>
                    </div>
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translate(-50%, -20px)';
                setTimeout(() => toast.remove(), 400);
            }, 3500);
        }
    }

    // Expose global instance
    window.SwimTrackTourInstance = new SwimTrackTour();

    window.startAppTour = function(role, userName) {
        // Dismiss first-time welcome modal if open
        const modal = document.getElementById('welcomeModalFTUE');
        if (modal) {
            modal.style.opacity = '0';
            setTimeout(() => modal.remove(), 250);
        }
        window.SwimTrackTourInstance.init({
            role: role || (window.__SWIMTRACK_USER_ROLE || 'guest'),
            userName: userName || (window.__SWIMTRACK_USER_NAME || '')
        });
        window.SwimTrackTourInstance.start();
    };

    window.dismissWelcomeModal = function() {
        const modal = document.getElementById('welcomeModalFTUE');
        if (modal) {
            modal.style.opacity = '0';
            modal.style.transform = 'translate(-50%, -40%) scale(0.95)';
            setTimeout(() => modal.remove(), 300);
        }
        // Mark tour as completed / dismissed in backend
        try {
            fetch('/api/complete_tour', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            }).catch(() => {});
        } catch(e) {}
    };

})();
