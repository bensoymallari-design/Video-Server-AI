import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "Qubit AI Media Server",
  description: "Local control surface for the Qubit AI Media Server.",
  robots: { index: false, follow: false },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="font-sans antialiased">{children}</body>
    </html>
  );
}
