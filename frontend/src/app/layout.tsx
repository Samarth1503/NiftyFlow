import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from "@/context/AuthContext";
import { GlobalDataProvider } from "@/context/GlobalDataContext";
import TopNav from "@/components/TopNav";
import Sidebar from "@/components/Sidebar";
import CreatePortfolioModal from "@/components/CreatePortfolioModal";

export const metadata: Metadata = {
  title: "NiftyFlow",
  description: "Event-driven portfolio analytics platform",
};

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
              
              <TopNav />
              <CreatePortfolioModal />
              
              <div className="flex flex-1 w-full">
                <Sidebar />
                <main className="flex-1 w-full overflow-hidden">
                  {children}
                </main>
              </div>

            </div>
          </GlobalDataProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
