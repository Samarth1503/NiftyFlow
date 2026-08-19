import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { GlobalDataProvider } from "@/context/GlobalDataContext";
import Image from "next/image";

export const metadata: Metadata = {
  title: "NiftyFlow",
  description: "Event-driven portfolio analytics platform",
};

import Link from "next/link";
import LogoutButton from "@/components/LogoutButton";

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className="antialiased bg-[var(--background)] min-h-screen">
        <AuthProvider>
          <GlobalDataProvider>
            <div className="flex flex-col min-h-screen max-w-[1600px] w-full mx-auto px-4 sm:px-6 lg:px-8">
              <header className="py-4 flex justify-between items-center border-b border-[var(--gf-border)] mb-6">
                <div className="flex items-center gap-6">
                  <Link href="/dashboard" className="flex items-center gap-2 hover:opacity-90 transition-opacity">
                    <Image src="/icon.jpg" width={32} height={32} className="rounded-full" alt="NiftyFlow Logo" />
                    <h1 className="text-xl font-medium tracking-tight">NiftyFlow</h1>
                  </Link>
                  <nav className="hidden md:flex gap-4 text-sm font-medium text-[var(--gf-gray-text)]">
                    <Link href="/dashboard" className="hover:text-white transition-colors">Portfolios</Link>
                    <Link href="/securities" className="hover:text-white transition-colors">Market Data & ML</Link>
                  </nav>
                </div>
                <div>
                  <LogoutButton />
                </div>
              </header>
              <main className="flex-1 w-full">
                {children}
              </main>
              <footer className="py-8 mt-12 border-t border-[var(--gf-border)] flex flex-col md:flex-row justify-between items-center text-sm text-[var(--gf-gray-text)] gap-4">
                <div>&copy; {new Date().getFullYear()} NiftyFlow. All rights reserved.</div>
                <div className="flex gap-6">
                  <Link href="/about" className="hover:text-[var(--foreground)] transition-colors">About</Link>
                  <Link href="/contact" className="hover:text-[var(--foreground)] transition-colors">Contact</Link>
                  <Link href="/terms" className="hover:text-[var(--foreground)] transition-colors">Terms of Service</Link>
                </div>
              </footer>
            </div>
          </GlobalDataProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
