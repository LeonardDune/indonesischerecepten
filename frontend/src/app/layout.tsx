import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Sidebar } from "@/components/Sidebar";
import { MobileNav } from "@/components/MobileNav";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "SpiceRoute | Authentieke Wereldrecepten",
  description: "Ontdek authentieke smaken van over de hele wereld met onze AI-gestuurde culinaire assistent.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="nl">
      <body className={`${inter.className} bg-background text-foreground antialiased`}>
        <div className="flex min-h-screen">
          <Sidebar />
          <MobileNav />
          <main className="flex-1 w-full md:ml-64 min-h-screen relative transition-all duration-300">
            <div className="max-w-7xl mx-auto px-4 md:px-8 py-20 md:py-10">
              {children}
            </div>

            {/* Background Decorative Elements */}
            <div className="fixed top-0 right-0 -z-10 w-[500px] h-[500px] bg-primary/10 blur-[120px] rounded-full" />
            <div className="fixed bottom-0 left-0 md:left-64 -z-10 w-[400px] h-[400px] bg-secondary/5 blur-[100px] rounded-full" />
          </main>
        </div>
      </body>
    </html>
  );
}
