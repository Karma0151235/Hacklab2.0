import type { Metadata } from "next";
import { JetBrains_Mono, IBM_Plex_Sans } from "next/font/google";
import { Toaster } from "sonner";
import { AlertNotificationProvider } from "@/components/notifications/alert-notification-provider";
import { BackgroundAlertsProvider } from "@/components/providers/background-alerts-provider";
import { AppShell } from "@/components/layout/app-shell";
import "./globals.css";

const jetbrainsMono = JetBrains_Mono({
  subsets: ["latin"],
  variable: "--font-mono",
  weight: ["400", "500", "700"],
  display: "swap",
});

const ibmPlexSans = IBM_Plex_Sans({
  subsets: ["latin"],
  variable: "--font-sans",
  weight: ["300", "400", "500", "600", "700"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "Financial Intelligence Dashboard | AmBank",
  description:
    "Professional financial intelligence dashboard for compliance officers. Bloomberg Terminal-inspired interface with AI-powered insights.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${jetbrainsMono.variable} ${ibmPlexSans.variable}`}
    >
      <body className="font-sans antialiased">
        <BackgroundAlertsProvider>
          <AlertNotificationProvider
            simulateAlerts={false}
            simulationIntervalMs={45000}
          >
            <AppShell>{children}</AppShell>
          </AlertNotificationProvider>
        </BackgroundAlertsProvider>
        <Toaster
          position="top-right"
          expand={false}
          richColors={false}
          closeButton={false}
          theme="dark"
          toastOptions={{
            style: {
              background: "transparent",
              border: "none",
              padding: 0,
              boxShadow: "none",
            },
          }}
        />
      </body>
    </html>
  );
}
