import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/contexts/AuthContext";
import { GoalProvider } from "@/contexts/GoalContext";

export const metadata: Metadata = {
  title: "Machi Quest",
  description: "Your gamified productivity companion",
  manifest: "/manifest.json", 
  icons: {
    icon: '/Leaf.png',
    apple: '/Leaf.png',
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased font-sans">
        <AuthProvider>
          <GoalProvider>{children}</GoalProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
