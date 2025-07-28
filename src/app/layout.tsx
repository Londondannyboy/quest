import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Quest Core V2 - Earn Your Quest Through Story",
  description: "A revolutionary professional development platform where you must earn your Quest through story.",
};

// Force dynamic rendering for all pages
export const dynamic = 'force-dynamic'

import { ClerkProvider } from '@clerk/nextjs'
import { MonitoringProvider } from './providers'

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <ClerkProvider>
      <html lang="en">
        <body
          className={`${geistSans.variable} ${geistMono.variable} antialiased`}
        >
          <MonitoringProvider>
            {children}
          </MonitoringProvider>
        </body>
      </html>
    </ClerkProvider>
  );
}