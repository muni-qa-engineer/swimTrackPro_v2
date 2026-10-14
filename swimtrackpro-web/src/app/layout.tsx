import type { Metadata, Viewport } from "next";
import "./globals.css";
import { ServiceWorkerRegister } from "@/components/pwa/ServiceWorkerRegister";
import { InstallPwaPrompt } from "@/components/pwa/InstallPwaPrompt";
import { MobileBottomBar } from "@/components/common/MobileBottomBar";

export const metadata: Metadata = {
  title: "SwimTrackPro - Doorstep Swimming Coaching & Academy",
  description: "Next-generation doorstep swimming academy, multi-swimmer bookings, and attendance tracking.",
  manifest: "/manifest.webmanifest",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "SwimTrackPro",
  },
  icons: {
    icon: "/icons/icon-192.png",
    apple: "/icons/icon-192.png",
  },
};

export const viewport: Viewport = {
  themeColor: "#020617",
  width: "device-width",
  initialScale: 1,
  maximumScale: 1,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark h-full">
      <body className="min-h-full flex flex-col bg-slate-950 text-slate-100 antialiased font-sans pb-20 md:pb-0">
        <ServiceWorkerRegister />
        <InstallPwaPrompt />
        {children}
        <MobileBottomBar />
      </body>
    </html>
  );
}
