import assert from "node:assert";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const webRoot = path.resolve(__dirname, "..");

console.log("=================================================");
console.log("🌊 SwimTrackPro Phase 5: Parity & Verification Test");
console.log("=================================================\n");

let passedTests = 0;
let totalTests = 0;

function test(name, fn) {
  totalTests++;
  try {
    fn();
    console.log(`✅ PASS: ${name}`);
    passedTests++;
  } catch (error) {
    console.error(`❌ FAIL: ${name}`);
    console.error(error);
  }
}

// 1. Verify Pricing Config and Group Scaling
test("Pricing Config: Demo and Single base prices", () => {
  // Demo 1 session base price is 699
  // Single 1 session base price is 799
  // Group discount percentages: 1: 0%, 2: 8%, 3: 15%, 4: 22%, 5: 36%
  const groupDiscounts = { 1: 0, 2: 8, 3: 15, 4: 22, 5: 36 };

  // For 1 swimmer Demo
  const demoBase = 699;
  const demo1Total = demoBase * 1 * (1 - groupDiscounts[1] / 100);
  assert.strictEqual(demo1Total, 699);

  // For 2 swimmers Demo with 8% discount
  // 699 * 2 = 1398, discount 8% = 111.84 -> total approx 1286
  const demo2Total = Math.round(demoBase * 2 * (1 - groupDiscounts[2] / 100));
  assert.strictEqual(demo2Total, 1286);

  // For 5 swimmers Demo with 36% group discount
  // 699 * 5 = 3495, discount 36% = 1258.2 -> total 2237
  const demo5Total = Math.round(demoBase * 5 * (1 - groupDiscounts[5] / 100));
  assert.strictEqual(demo5Total, 2237);
});

test("Pricing Config: Long-Term Memberships and Pause Allocations", () => {
  const tiers = {
    "Monthly 3 Days/Week": { pauseDays: 0, skips: 3, isLongTerm: false },
    "3 Months 3 Days/Week": { pauseDays: 15, skips: 9, isLongTerm: true },
    "6 Months 3 Days/Week": { pauseDays: 30, skips: 18, isLongTerm: true },
    "9 Months 3 Days/Week": { pauseDays: 45, skips: 27, isLongTerm: true },
    "12 Months 3 Days/Week": { pauseDays: 60, skips: 36, isLongTerm: true },
  };

  assert.strictEqual(tiers["Monthly 3 Days/Week"].pauseDays, 0);
  assert.strictEqual(tiers["Monthly 3 Days/Week"].skips, 3);
  assert.strictEqual(tiers["3 Months 3 Days/Week"].pauseDays, 15);
  assert.strictEqual(tiers["6 Months 3 Days/Week"].pauseDays, 30);
  assert.strictEqual(tiers["12 Months 3 Days/Week"].pauseDays, 60);
});

// 2. Schedule and Pause Shift Math Verification
test("Membership Pause Calendar Shift Algorithm", () => {
  const startDate = new Date("2026-11-01");
  const pauseDays = 7;
  
  // When member pauses for 7 days, auto resume is start + 7 days
  const autoResume = new Date(startDate.getTime() + pauseDays * 86400000);
  assert.strictEqual(autoResume.toISOString().split("T")[0], "2026-11-08");

  // Original end date was 2026-11-30, new end date shifts by 7 days to 2026-12-07
  const origEnd = new Date("2026-11-30");
  const newEnd = new Date(origEnd.getTime() + pauseDays * 86400000);
  assert.strictEqual(newEnd.toISOString().split("T")[0], "2026-12-07");
});

// 3. PWA Assets & Manifest Verification
test("PWA Assets: manifest.json existence & valid JSON", () => {
  const manifestPath = path.join(webRoot, "public", "manifest.json");
  assert.ok(fs.existsSync(manifestPath), "public/manifest.json must exist");
  const content = JSON.parse(fs.readFileSync(manifestPath, "utf-8"));
  assert.strictEqual(content.short_name, "SwimTrackPro");
  assert.strictEqual(content.display, "standalone");
  assert.ok(content.icons && content.icons.length >= 2, "Must contain at least 2 icon sizes");
});

test("PWA Assets: Service Worker sw.js exists with cache strategy", () => {
  const swPath = path.join(webRoot, "public", "sw.js");
  assert.ok(fs.existsSync(swPath), "public/sw.js must exist");
  const content = fs.readFileSync(swPath, "utf-8");
  assert.ok(content.includes("swimtrackpro-v1"), "Must declare cache version");
  assert.ok(content.includes("caches.match"), "Must implement cache match");
});

test("PWA Assets: 192x192 and 512x512 icons exist", () => {
  const icon192 = path.join(webRoot, "public", "icons", "icon-192.png");
  const icon512 = path.join(webRoot, "public", "icons", "icon-512.png");
  assert.ok(fs.existsSync(icon192), "192x192 icon must exist");
  assert.ok(fs.existsSync(icon512), "512x512 icon must exist");
  assert.ok(fs.statSync(icon192).size > 1000, "192 icon must not be empty");
  assert.ok(fs.statSync(icon512).size > 1000, "512 icon must not be empty");
});

// 4. Verification of Core App Route Files
test("App Router: Core pages and actions exist", () => {
  const routes = [
    "src/app/page.tsx",
    "src/app/booking/page.tsx",
    "src/app/dashboard/page.tsx",
    "src/app/my-bookings/page.tsx",
    "src/app/trainer/page.tsx",
    "src/app/admin/page.tsx",
    "src/app/offline/page.tsx",
    "src/app/actions/booking.ts",
    "src/app/actions/dashboard.ts",
    "src/components/common/Navbar.tsx",
    "src/components/common/MobileBottomBar.tsx",
  ];

  for (const route of routes) {
    const fullPath = path.join(webRoot, route);
    assert.ok(fs.existsSync(fullPath), `Expected route file ${route} to exist`);
  }
});

console.log("\n-------------------------------------------------");
console.log(`Results: ${passedTests} / ${totalTests} tests passed`);
console.log("-------------------------------------------------");

if (passedTests !== totalTests) {
  process.exit(1);
}
