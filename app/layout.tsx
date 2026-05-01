import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "The Operating Brief",
  description: "Your daily AI-powered business briefing for Australian operators.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
