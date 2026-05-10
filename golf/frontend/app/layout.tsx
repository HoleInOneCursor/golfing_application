import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import Link from "next/link";
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
  title: "Golf Tracker",
  description: "Track golf courses and rounds.",
};

const navigation = [
  { href: "/", label: "Home" },
  { href: "/courses", label: "Courses" },
  { href: "/rounds", label: "Rounds" },
];

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="flex min-h-full flex-col bg-slate-50 text-slate-950">
        <header className="border-b border-slate-200 bg-white">
          <nav
            aria-label="Main navigation"
            className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4"
          >
            <Link href="/" className="text-lg font-semibold tracking-tight">
              Golf Tracker
            </Link>
            <div className="flex items-center gap-4 text-sm font-medium text-slate-600">
              {navigation.map((item) => (
                <Link
                  key={item.href}
                  href={item.href}
                  className="rounded-md px-3 py-2 transition hover:bg-slate-100 hover:text-slate-950"
                >
                  {item.label}
                </Link>
              ))}
            </div>
          </nav>
        </header>
        <main className="mx-auto flex w-full max-w-6xl flex-1 flex-col px-6 py-10">
          {children}
        </main>
      </body>
    </html>
  );
}
