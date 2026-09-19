# SwimTrackPro V2 Upgrade Plan

## 1. Audit Summary
The codebase is a Flask application using PostgreSQL and Jinja2 templates, with Bootstrap for the frontend.
The application handles guest bookings, trainer (coach) assignments, feedback, and an admin panel.
It appears to use simple functions in `general.py`, `dashboard.py`, `pages.py`, etc., and manually executes SQL queries.

## 2. Gap Analysis & Proposed Changes

### A. UI/UX Improvements (P1)
- **Homepage:** Optimize hero section padding and mobile responsiveness. Implement a scalable promotional banner system (for Vinayaka Chavithi and future announcements). 
- **Forms & Booking:** Enhance form validation (both client and server side). Add clear loading states for buttons (e.g. replacing text with a spinner on submit to prevent duplicate submissions).
- **Cards & Layouts:** Standardize border radius (`var(--radius-md)`), shadow elevations, and spacing across `login.html` and `dashboard.html`.

### B. Frontend Performance & Accessibility (P2)
- Add aria-labels to icon buttons and close buttons.
- Standardize semantic HTML (`<main>`, `<section>`, `<nav>`).
- Reduce duplicate inline CSS styles across templates by extracting them into `global.css` or `dashboard.css`.

### C. Backend & Database Optimization (P1)
- **Dead Code:** Run a rigorous cleanup for commented-out routes and duplicate logic across the `swimtrackpro/routes` directory.
- **SQL Optimization:** Ensure proper `LOWER()` normalizations are consistently applied across all authentication and query endpoints (like we did in the recent feedback fix).
- **Error Handling:** Standardize generic `500` error catches to flash user-friendly messages rather than just printing to stdout. 

### D. Security (P0)
- Ensure all endpoints verifying ownership actually check `session.get('phone')` or `session.get('user_name')`.
- Validate file upload extensions strictly on the backend to prevent arbitrary file execution.

### E. SEO & Marketing (P3)
- Verify `og:image`, `canonical` links, and structured data on the public landing page (`login.html`).
- Implement the requested Vinayaka Chavithi Banner using a robust, dismissible component.

## 3. Verification Plan
- **Pre-execution:** Backup critical routes.
- **Incremental Implementation:** I will implement these phases iteratively.
- **Post-execution:** Perform full testing of the Booking flow, Trainer flow, and Admin flow.

**Please review this plan. Upon your approval, I will execute the version upgrade in stages without breaking any existing business logic.**
