"use client";

import Link from "next/link";
import { useTheme } from "@/components/ThemeProvider";
import { Moon, Sun, History, Settings, Activity } from "lucide-react";

export default function Header() {
  const { theme, setTheme } = useTheme();

  return (
    <header className="border-b bg-background sticky top-0 z-10">
      <div className="container mx-auto px-4 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity className="h-6 w-6 text-blue-600 dark:text-blue-400" />
          <div>
            <Link href="/" className="font-bold text-xl tracking-tight block leading-tight">
              StockLens
            </Link>
            <span className="text-[10px] text-muted-foreground uppercase tracking-wider font-semibold">
              Chartink × Moneycontrol
            </span>
          </div>
        </div>

        <nav className="hidden md:flex items-center gap-6">
          <Link href="/" className="text-sm font-medium hover:text-blue-600 transition-colors">
            Dashboard
          </Link>
          <Link href="/history" className="text-sm font-medium hover:text-blue-600 transition-colors flex items-center gap-1">
            <History className="h-4 w-4" /> History
          </Link>
          <Link href="/settings" className="text-sm font-medium hover:text-blue-600 transition-colors flex items-center gap-1">
            <Settings className="h-4 w-4" /> Settings
          </Link>
        </nav>

        <div className="flex items-center gap-4">
          <button
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="p-2 rounded-full hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
            aria-label="Toggle theme"
          >
            {theme === "dark" ? <Sun className="h-5 w-5" /> : <Moon className="h-5 w-5" />}
          </button>
        </div>
      </div>
    </header>
  );
}
