/**
 * SwimTrackPro - Modern Interactive Guided Product Tour & Welcome Experience
 * Designed with modern SaaS UX standards (inspired by Linear, Stripe, Driver.js)
 * High-precision SVG spotlight overlay anchored directly at specific options/elements/tags.
 * Covers both Dashboard features and Mobile/Desktop Menu Bar navigation.
 */

(function() {
    'use strict';

    // Inject self-contained CSS styles into head so tour renders flawlessly without caching issues
    function injectTourStyles() {
        if (document.getElementById('swimtrack-tour-injected-styles')) return;

        const style = document.createElement('style');
        style.id = 'swimtrack-tour-injected-styles';
        style.textContent = `
            #tourBackdropOverlay {
                position: fixed;
                inset: 0;
                width: 100vw;
                height: 100vh;
                z-index: 100010;
                pointer-events: auto;
                cursor: pointer;
            }
            #tourSvgOverlay {
                position: fixed;
                inset: 0;
                width: 100vw;
                height: 100vh;
                z-index: 100011;
                pointer-events: none;
            }
            #tourPopoverCard {
                position: fixed;
                z-index: 100020;
                background: linear-gradient(145deg, #0f172a, #1e293b);
                border: 1px solid rgba(6, 182, 212, 0.45);
                border-radius: 18px;
                box-shadow: 0 25px 60px rgba(0, 0, 0, 0.9), 0 0 35px rgba(6, 182, 212, 0.25);
                color: #ffffff;
                width: 340px;
                max-width: calc(100vw - 32px);
                padding: 1.25rem 1.35rem;
                pointer-events: auto;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                transition: opacity 0.25s ease, transform 0.25s ease;
                box-sizing: border-box;
            }
            .tour-pointer-arrow {
                position: absolute;
                width: 14px;
                height: 14px;
                background: #172338;
                border: 1px solid rgba(6, 182, 212, 0.45);
                transform: rotate(45deg);
                z-index: -1;
            }
            .tour-pointer-arrow.arrow-top {
                top: -8px;
                border-bottom: none;
                border-right: none;
            }
            .tour-pointer-arrow.arrow-bottom {
                bottom: -8px;
                border-top: none;
                border-left: none;
            }
            .tour-step-badge {
                background: rgba(6, 182, 212, 0.2);
                color: #38bdf8;
                border: 1px solid rgba(6, 182, 212, 0.45);
                font-size: 0.72rem;
                font-weight: 700;
                padding: 0.2rem 0.55rem;
                border-radius: 6px;
                letter-spacing: 0.3px;
            }
            .tour-category-badge {
                background: rgba(255, 255, 255, 0.08);
                color: #94a3b8;
                font-size: 0.72rem;
                padding: 0.2rem 0.55rem;
                border-radius: 6px;
            }
            .tour-category-badge.menu-badge {
                background: rgba(16, 185, 129, 0.15);
                color: #34d399;
                border: 1px solid rgba(16, 185, 129, 0.35);
            }
            .tour-close-btn {
                background: rgba(255, 255, 255, 0.08);
                border: 1px solid rgba(255, 255, 255, 0.12);
                color: #94a3b8;
                font-size: 0.85rem;
                cursor: pointer;
                width: 28px;
                height: 28px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: all 0.2s;
            }
            .tour-close-btn:hover {
                color: #ffffff;
                background: rgba(255, 255, 255, 0.2);
                transform: scale(1.05);
            }
            .tour-progress-bar-container {
                height: 4px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 4px;
                overflow: hidden;
                margin: 0.75rem 0 0.9rem 0;
            }
            .tour-progress-bar {
                height: 100%;
                background: linear-gradient(90deg, #06b6d4, #10b981);
                transition: width 0.3s ease;
            }
            .tour-celebrate-toast {
                position: fixed;
                top: 30px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 100030;
                background: linear-gradient(135deg, rgba(16, 185, 129, 0.98), rgba(6, 182, 212, 0.98));
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.3);
                box-shadow: 0 15px 40px rgba(0, 0, 0, 0.7), 0 0 30px rgba(16, 185, 129, 0.3);
                padding: 0.9rem 1.6rem;
                border-radius: 18px;
                color: white;
                transition: all 0.35s ease;
                display: flex;
                align-items: center;
                gap: 0.8rem;
                font-family: inherit;
            }
        `;
        document.head.appendChild(style);
    }

    class SwimTrackTour {
        constructor() {
            this.currentStep = 0;
            this.steps = [];
            this.overlay = null;
            this.svgOverlay = null;
            this.popover = null;
            this.currentTarget = null;
            this.role = 'guest';
            this.userName = '';
            this.onKeyDown = this.handleKeyDown.bind(this);
            this.onResizeOrScroll = this.handleResizeOrScroll.bind(this);
            this.rafId = null;
        }

        init(options = {}) {
            injectTourStyles();
            this.role = options.role || (window.__SWIMTRACK_USER_ROLE || 'guest');
            this.userName = options.userName || (window.__SWIMTRACK_USER_NAME || '');
            this.steps = options.steps || this.getDefaultSteps(this.role);
        }

        getDefaultSteps(role) {
            if (role === 'trainer') {
                return [
                    // Dashboard Core Features (5 steps)
                    {
                        element: '#tourCoachActiveBookings',
                        fallback: '.metrics-grid .metric-card.primary',
                        title: '👥 Active Bookings',
                        badge: 'Dashboard',
                        description: 'View and manage all swimmers currently assigned to your coaching sessions.'
                    },
                    {
                        element: '#coachEarningsMetricCard',
                        fallback: '#coachEarningsCarousel',
                        title: '💰 Earnings Carousel',
                        badge: 'Dashboard',
                        description: 'Swipe to view real-time monthly, yearly, and lifetime earnings.'
                    },
                    {
                        element: '#tourCoachUpcomingSessions',
                        fallback: '.dashboard-main .glass-panel',
                        title: '📋 Daily Sessions',
                        badge: 'Dashboard',
                        description: 'Mark student attendance with one tap right after class finishes.'
                    },
                    {
                        element: '#tourCoachTimeSlots',
                        fallback: '.glass-panel.mb-6',
                        title: '⏰ Manage Time Slots',
                        badge: 'Dashboard',
                        description: 'Set your morning and evening availability for student bookings.'
                    },
                    {
                        element: '#tourCoachNoticeBoard',
                        fallback: '#coachNoticeBoard',
                        title: '📢 Notice Board',
                        badge: 'Dashboard',
                        description: 'Stay updated on academy announcements and reschedule requests.'
                    },
                    // Menu Bar Navigation Options (3 steps)
                    {
                        element: ['#mobileNavBookings', '#desktopNavBookings', 'a[href="/my-bookings"]'],
                        title: '📋 All Bookings',
                        badge: 'Menu Bar',
                        description: 'View your complete calendar of upcoming and past coaching sessions.'
                    },
                    {
                        element: ['#mobileNavPayments', '#desktopNavPayments', 'a[href="/payments"]'],
                        title: '💳 Payments',
                        badge: 'Menu Bar',
                        description: 'Track student fee collections, receipts, and pending payments.'
                    },
                    {
                        element: ['#mobileNavProfile', '#desktopNavProfile', 'a[href*="profile"]'],
                        title: '👤 Coach Profile',
                        badge: 'Menu Bar',
                        description: 'Update your coaching bio, specialties, and contact details.'
                    }
                ];
            } else {
                // Swimmer / Guest Steps
                return [
                    // Dashboard Core Features (5 steps)
                    {
                        element: '#tourNextSessionCard',
                        fallback: '.metrics-grid .metric-card.primary',
                        title: '📅 Next Session',
                        badge: 'Dashboard',
                        description: 'Check your upcoming class timing, lane assignment, and coach details.'
                    },
                    {
                        element: '#tourProgressTracker',
                        fallback: '.glass-panel:has(.progress-circle)',
                        title: '📈 Progress Tracker',
                        badge: 'Dashboard',
                        description: 'Track attended classes against your total package.'
                    },
                    {
                        element: '#tourMembershipCard',
                        fallback: '.glass-panel:has(.fa-circle-pause)',
                        title: '💳 Membership Freeze',
                        badge: 'Dashboard',
                        description: 'Pause your package during travel or illness so sessions never expire.'
                    },
                    {
                        element: '#tourMySwimmersCard',
                        fallback: '.glass-panel:has(.fa-users)',
                        title: '🏊 Swimmer Profiles',
                        badge: 'Dashboard',
                        description: 'Manage family member profiles and track individual stroke milestones.'
                    },
                    {
                        element: '#tourMiniCalendar',
                        fallback: '.mini-calendar',
                        title: '🗓️ Training Calendar',
                        badge: 'Dashboard',
                        description: 'View monthly scheduled dates and attendance history at a glance.'
                    },
                    // Menu Bar Navigation Options (4 steps)
                    {
                        element: ['#mobileNavBookSession', '#desktopNavBookSession', 'a[href="/booking"]'],
                        title: '➕ Book Session',
                        badge: 'Menu Bar',
                        description: 'Book new swimming classes and select your preferred coach or slot.'
                    },
                    {
                        element: ['#mobileNavBookings', '#desktopNavBookings', 'a[href="/my-bookings"]'],
                        title: '📋 My Bookings',
                        badge: 'Menu Bar',
                        description: 'Track upcoming classes, skip dates, or reschedule sessions.'
                    },
                    {
                        element: ['#mobileNavPayments', '#desktopNavPayments', 'a[href="/payments"]'],
                        title: '💳 Payments',
                        badge: 'Menu Bar',
                        description: 'View package invoices, receipts, and pending fees.'
                    },
                    {
                        element: ['#mobileNavProfile', '#desktopNavProfile', 'a[href*="trainer"]'],
                        title: '🏅 About Coach',
                        badge: 'Menu Bar',
                        description: 'Learn about your assigned coach’s certifications and background.'
                    }
                ];
            }
        }

        findTargetElement(step) {
            const selectors = Array.isArray(step.element) ? step.element : (step.element ? [step.element] : []);
            if (step.fallback) {
                selectors.push(step.fallback);
            }

            // First check visible elements (e.g. mobile bottom nav on mobile, desktop nav on desktop)
            for (const sel of selectors) {
                try {
                    const matches = document.querySelectorAll(sel);
                    for (const el of matches) {
                        const style = window.getComputedStyle(el);
                        if (style.display !== 'none' && style.visibility !== 'hidden' && el.offsetWidth > 0 && el.offsetHeight > 0) {
                            return el;
                        }
                    }
                } catch(e) {}
            }

            // Fallback to first existing element if visibility check was too strict
            for (const sel of selectors) {
                try {
                    const el = document.querySelector(sel);
                    if (el) return el;
                } catch(e) {}
            }
            return null;
        }

        start(customSteps = null) {
            injectTourStyles();

            if (customSteps) {
                this.steps = customSteps;
            } else if (!this.steps || this.steps.length === 0) {
                this.steps = this.getDefaultSteps(this.role);
            }

            if (!this.steps || this.steps.length === 0) return;

            // Dismiss first-time welcome modal if currently open
            const welcomeModal = document.getElementById('welcomeModalFTUE');
            if (welcomeModal) {
                welcomeModal.style.opacity = '0';
                welcomeModal.style.transform = 'scale(0.96)';
                setTimeout(() => welcomeModal.remove(), 250);
            }

            this.createOverlay();
            this.createSvgMask();
            this.createPopover();
            this.currentStep = 0;
            this.goToStep(0);

            window.addEventListener('keydown', this.onKeyDown);
            window.addEventListener('resize', this.onResizeOrScroll, { passive: true });
            window.addEventListener('scroll', this.onResizeOrScroll, { passive: true });
        }

        createOverlay() {
            if (document.getElementById('tourBackdropOverlay')) return;
            const overlay = document.createElement('div');
            overlay.id = 'tourBackdropOverlay';
            overlay.onclick = () => this.close();
            document.body.appendChild(overlay);
            this.overlay = overlay;
        }

        createSvgMask() {
            if (document.getElementById('tourSvgOverlay')) return;
            const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            svg.setAttribute('id', 'tourSvgOverlay');
            svg.setAttribute('width', '100%');
            svg.setAttribute('height', '100%');

            svg.innerHTML = `
                <defs>
                    <mask id="tour-spotlight-mask">
                        <rect x="0" y="0" width="100%" height="100%" fill="white" />
                        <rect id="tourMaskHole" x="0" y="0" width="0" height="0" rx="16" ry="16" fill="black" />
                    </mask>
                </defs>
                <rect x="0" y="0" width="100%" height="100%" fill="rgba(0, 0, 0, 0.78)" mask="url(#tour-spotlight-mask)" />
                <rect id="tourSpotlightBorder" x="0" y="0" width="0" height="0" rx="16" ry="16" fill="none" stroke="#06b6d4" stroke-width="3" stroke-dasharray="6,4">
                    <animate attributeName="stroke-dashoffset" from="0" to="20" dur="1.2s" repeatCount="indefinite" />
                </rect>
            `;
            document.body.appendChild(svg);
            this.svgOverlay = svg;
        }

        createPopover() {
            if (document.getElementById('tourPopoverCard')) return;
            const popover = document.createElement('div');
            popover.id = 'tourPopoverCard';
            popover.setAttribute('role', 'dialog');
            popover.setAttribute('aria-modal', 'true');
            popover.innerHTML = `
                <div class="tour-pointer-arrow" id="tourPointerArrow"></div>
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.4rem;">
                    <div style="display: flex; align-items: center; gap: 0.45rem;">
                        <span class="tour-step-badge" id="tourStepBadge">Step 1 of 5</span>
                        <span class="tour-category-badge" id="tourCategoryBadge">Dashboard</span>
                    </div>
                    <button type="button" class="tour-close-btn" onclick="SwimTrackTourInstance.close()" aria-label="Close tour">
                        <i class="fa-solid fa-xmark"></i>
                    </button>
                </div>
                <div class="tour-progress-bar-container">
                    <div class="tour-progress-bar" id="tourProgressBar" style="width: 20%;"></div>
                </div>
                <h4 style="font-size: 1.1rem; font-weight: 800; color: #ffffff; margin-bottom: 0.35rem; letter-spacing: -0.2px;" id="tourStepTitle"></h4>
                <p style="font-size: 0.86rem; color: #94a3b8; line-height: 1.45; margin-bottom: 1.15rem;" id="tourStepDesc"></p>
                <div style="display: flex; align-items: center; justify-content: space-between; padding-top: 0.75rem; border-top: 1px solid rgba(255, 255, 255, 0.08);">
                    <button type="button" onclick="SwimTrackTourInstance.close()" style="background: transparent; border: none; color: #64748b; font-size: 0.82rem; cursor: pointer; padding: 0.2rem 0; text-decoration: none; transition: color 0.2s;">Skip tour</button>
                    <div style="display: flex; align-items: center; gap: 0.45rem;">
                        <button type="button" id="tourPrevBtn" onclick="SwimTrackTourInstance.prev()" style="background: rgba(255, 255, 255, 0.08); border: 1px solid rgba(255, 255, 255, 0.15); color: #e2e8f0; font-size: 0.8rem; font-weight: 600; padding: 0.35rem 0.85rem; border-radius: 9999px; cursor: pointer; display: flex; align-items: center; gap: 0.3rem; transition: all 0.2s;">
                            <i class="fa-solid fa-arrow-left"></i> Back
                        </button>
                        <button type="button" id="tourNextBtn" onclick="SwimTrackTourInstance.next()" style="background: linear-gradient(135deg, #06b6d4, #0284c7); border: none; color: #020617; font-size: 0.8rem; font-weight: 700; padding: 0.35rem 0.95rem; border-radius: 9999px; cursor: pointer; display: flex; align-items: center; gap: 0.3rem; box-shadow: 0 4px 14px rgba(6, 182, 212, 0.35); transition: all 0.2s;">
                            Next <i class="fa-solid fa-arrow-right"></i>
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

            // Find target element on page
            const target = this.findTargetElement(step);
            this.currentTarget = target;

            // Update Popover content
            const badge = document.getElementById('tourStepBadge');
            const catBadge = document.getElementById('tourCategoryBadge');
            const title = document.getElementById('tourStepTitle');
            const desc = document.getElementById('tourStepDesc');
            const progBar = document.getElementById('tourProgressBar');
            const prevBtn = document.getElementById('tourPrevBtn');
            const nextBtn = document.getElementById('tourNextBtn');

            if (badge) badge.textContent = `Step ${index + 1} of ${this.steps.length}`;
            if (catBadge) {
                catBadge.textContent = step.badge || 'Feature';
                if (step.badge === 'Menu Bar') {
                    catBadge.className = 'tour-category-badge menu-badge';
                } else {
                    catBadge.className = 'tour-category-badge';
                }
            }
            if (title) title.innerHTML = step.title;
            if (desc) desc.textContent = step.description;
            if (progBar) progBar.style.width = `${((index + 1) / this.steps.length) * 100}%`;

            if (prevBtn) {
                prevBtn.style.visibility = (index === 0) ? 'hidden' : 'visible';
            }

            if (nextBtn) {
                if (index === this.steps.length - 1) {
                    nextBtn.style.background = 'linear-gradient(135deg, #10b981, #059669)';
                    nextBtn.style.color = '#ffffff';
                    nextBtn.innerHTML = 'Got It! Finish 🎉';
                } else {
                    nextBtn.style.background = 'linear-gradient(135deg, #06b6d4, #0284c7)';
                    nextBtn.style.color = '#020617';
                    nextBtn.innerHTML = 'Next <i class="fa-solid fa-arrow-right"></i>';
                }
            }

            if (target) {
                // If element is not fixed in place (like bottom nav), scroll it into center view
                const isFixed = target.closest('.mobile-bottom-nav') || target.closest('header') || window.getComputedStyle(target).position === 'fixed';
                if (!isFixed) {
                    target.scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'nearest' });
                    setTimeout(() => {
                        this.updateSpotlightAndPopover(target);
                    }, 240);
                } else {
                    this.updateSpotlightAndPopover(target);
                }
            } else {
                this.centerPopover();
            }
        }

        updateSpotlightAndPopover(target) {
            if (!target) return;
            const rect = target.getBoundingClientRect();
            const pad = 8;
            const x = Math.max(0, rect.left - pad);
            const y = Math.max(0, rect.top - pad);
            const w = rect.width + (pad * 2);
            const h = rect.height + (pad * 2);

            // Update SVG spotlight hole and animated glowing border
            const hole = document.getElementById('tourMaskHole');
            const border = document.getElementById('tourSpotlightBorder');
            if (hole) {
                hole.setAttribute('x', x);
                hole.setAttribute('y', y);
                hole.setAttribute('width', w);
                hole.setAttribute('height', h);
                hole.setAttribute('rx', 14);
                hole.setAttribute('ry', 14);
            }
            if (border) {
                border.setAttribute('x', x);
                border.setAttribute('y', y);
                border.setAttribute('width', w);
                border.setAttribute('height', h);
                border.setAttribute('rx', 14);
                border.setAttribute('ry', 14);
                border.style.display = 'block';
            }

            // Position popover card
            this.positionPopover(rect);
        }

        positionPopover(rect) {
            if (!this.popover) return;
            const popRect = this.popover.getBoundingClientRect();
            const arrow = document.getElementById('tourPointerArrow');
            const vw = window.innerWidth;
            const vh = window.innerHeight;
            const margin = 16;

            let top, left;
            let arrowClass = 'arrow-top';

            // Check if there is enough room below target
            const spaceBelow = vh - rect.bottom;
            const spaceAbove = rect.top;

            if (spaceBelow >= popRect.height + margin + 10 || spaceBelow >= spaceAbove) {
                // Place Below
                top = rect.bottom + margin;
                arrowClass = 'arrow-top';
            } else {
                // Place Above (especially for mobile bottom nav)
                top = rect.top - popRect.height - margin;
                arrowClass = 'arrow-bottom';
            }

            // Align horizontally with target center
            left = rect.left + (rect.width / 2) - (popRect.width / 2);

            // Constrain within viewport boundaries
            left = Math.max(16, Math.min(left, vw - popRect.width - 16));
            top = Math.max(16, Math.min(top, vh - popRect.height - 16));

            this.popover.style.top = `${top}px`;
            this.popover.style.bottom = 'auto';
            this.popover.style.left = `${left}px`;
            this.popover.style.transform = 'none';

            // Position arrow pointing at target center
            if (arrow) {
                arrow.style.display = 'block';
                arrow.className = `tour-pointer-arrow ${arrowClass}`;
                const targetCenter = rect.left + (rect.width / 2);
                const arrowLeft = Math.max(18, Math.min(targetCenter - left - 7, popRect.width - 25));
                arrow.style.left = `${arrowLeft}px`;
                arrow.style.right = 'auto';
            }
        }

        centerPopover() {
            if (!this.popover) return;
            const hole = document.getElementById('tourMaskHole');
            const border = document.getElementById('tourSpotlightBorder');
            if (hole) {
                hole.setAttribute('width', 0);
                hole.setAttribute('height', 0);
            }
            if (border) {
                border.style.display = 'none';
            }
            const arrow = document.getElementById('tourPointerArrow');
            if (arrow) {
                arrow.style.display = 'none';
            }
            this.popover.style.top = '50%';
            this.popover.style.left = '50%';
            this.popover.style.transform = 'translate(-50%, -50%)';
        }

        handleResizeOrScroll() {
            if (!this.currentTarget) return;
            if (this.rafId) cancelAnimationFrame(this.rafId);
            this.rafId = requestAnimationFrame(() => {
                this.updateSpotlightAndPopover(this.currentTarget);
            });
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

        close() {
            if (this.overlay) {
                this.overlay.remove();
                this.overlay = null;
            }
            if (this.svgOverlay) {
                this.svgOverlay.remove();
                this.svgOverlay = null;
            }
            if (this.popover) {
                this.popover.remove();
                this.popover = null;
            }
            this.currentTarget = null;
            window.removeEventListener('keydown', this.onKeyDown);
            window.removeEventListener('resize', this.onResizeOrScroll);
            window.removeEventListener('scroll', this.onResizeOrScroll);
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
            toast.className = 'tour-celebrate-toast';
            toast.innerHTML = `
                <span style="font-size: 1.7rem;">🎉</span>
                <div>
                    <div style="font-weight: 800; font-size: 0.95rem; color: #ffffff;">Tour Completed!</div>
                    <div style="font-size: 0.8rem; color: rgba(255, 255, 255, 0.88); line-height: 1.3;">You're ready to use SwimTrackPro!</div>
                </div>
            `;
            document.body.appendChild(toast);
            setTimeout(() => {
                toast.style.opacity = '0';
                toast.style.transform = 'translate(-50%, -20px)';
                setTimeout(() => toast.remove(), 400);
            }, 3000);
        }
    }

    // Expose global instance
    window.SwimTrackTourInstance = new SwimTrackTour();

    window.startAppTour = function(role, userName) {
        // Dismiss first-time welcome modal if open
        const modal = document.getElementById('welcomeModalFTUE');
        if (modal) {
            modal.style.opacity = '0';
            modal.style.transform = 'scale(0.96)';
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
            modal.style.transform = 'scale(0.96)';
            setTimeout(() => modal.remove(), 250);
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
