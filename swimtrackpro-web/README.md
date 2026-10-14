# SwimTrackPro - Modern Web Platform (Next.js 15 + Prisma)

Welcome to the modern Next.js 15 rewrite of **SwimTrackPro**. This full-stack application replaces the legacy Jinja/Flask frontend with modern React 19 Server Components, TypeScript type safety, dynamic pricing engine, responsive PWA support, and Prisma ORM against the existing PostgreSQL database.

---

## 🚀 Tech Stack

- **Framework**: [Next.js 15 (App Router)](https://nextjs.org/)
- **UI & Components**: [React 19](https://react.dev/), [Tailwind CSS v4](https://tailwindcss.com/), [Lucide React](https://lucide.dev/)
- **Database & ORM**: [PostgreSQL](https://www.postgresql.org/) via [Prisma ORM v6](https://www.prisma.io/)
- **Mobile First**: PWA with Web App Manifest, Service Worker (`/sw.js`), native bottom navigation bar, and offline fallback route (`/offline`).

---

## 📁 Application Structure

```
swimtrackpro-web/
├── public/
│   ├── icons/               # 192x192 & 512x512 maskable app icons
│   ├── manifest.json        # PWA manifest fallback
│   └── sw.js                # Offline caching service worker
├── prisma/
│   └── schema.prisma        # 12 Prisma models mapped to Postgres tables
├── scripts/
│   └── verify-parity.mjs    # Parity & pricing unit test suite
├── src/
│   ├── app/
│   │   ├── actions/         # Server Actions (booking.ts, dashboard.ts)
│   │   ├── admin/           # Admin command center & analytics
│   │   ├── booking/         # 3-step booking wizard with single Pool Location
│   │   ├── dashboard/       # Guest portal with interactive calendar & pause
│   │   ├── my-bookings/     # Subscriptions sorted latest active first
│   │   ├── offline/         # Offline fallback screen
│   │   ├── trainer/         # Trainer attendance tracker & roster
│   │   ├── layout.tsx       # Root layout with PWA meta & bottom bar
│   │   ├── manifest.ts      # Next.js Metadata Route for Web Manifest
│   │   └── page.tsx         # Modern hero landing page
│   ├── components/
│   │   ├── booking/         # Stepper, Map modal, Swimmer cards
│   │   ├── common/          # Navbar & MobileBottomBar
│   │   ├── dashboard/       # Calendar, Flexibility card, Swimmers card
│   │   ├── pwa/             # ServiceWorkerRegister, InstallPwaPrompt
│   │   └── trainer/         # TrainerAttendanceTracker
│   └── lib/
│       ├── pricingEngine.ts # Dynamic pricing & multi-swimmer discount logic
│       └── prisma.ts        # Prisma client singleton
```

---

## 🧪 Testing & Verification

Run the automated parity verification test suite:
```bash
npm run build
node scripts/verify-parity.mjs
```

---

## 🚢 Deployment & Staging Cutover

### Option 1: Vercel (Recommended for Best Performance)
1. Import your GitHub repository into Vercel.
2. Set **Root Directory** to `swimtrackpro-web`.
3. Under Environment Variables, add:
   ```env
   DATABASE_URL="postgresql://user:password@host/dbname?sslmode=require"
   ```
4. Deploy! Vercel will build the Next.js App Router and deploy to edge locations globally.

### Option 2: Render Multi-Service
In `render.yaml` at repository root, add the `swimtrackpro-web` service:
```yaml
services:
  - type: web
    name: swimtrackpro-web
    env: node
    rootDir: swimtrackpro-web
    buildCommand: npm install && npx prisma generate && npm run build
    startCommand: npm start
    envVars:
      - key: DATABASE_URL
        sync: false
```

### Option 3: Docker Container
```bash
docker build -t swimtrackpro-web .
docker run -p 3000:3000 -e DATABASE_URL="your-postgres-url" swimtrackpro-web
```
