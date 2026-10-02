"use client";

import { useState } from "react";
import { StockDetail } from "@/lib/types";
import { ChevronDown, ChevronUp, RefreshCw } from "lucide-react";
import StockCard from "./StockCard";

export default function NeedsReview({ stocks }: { stocks: StockDetail[] }) {
  const [open, setOpen] = useState(true);

  if (stocks.length === 0) return null;

  return (
    <div className="mb-8 border border-amber-200 dark:border-amber-800 rounded-xl overflow-hidden">
      <button 
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 bg-amber-50 dark:bg-amber-950/30 hover:bg-amber-100 dark:hover:bg-amber-900/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <h3 className="font-bold text-amber-800 dark:text-amber-400">Needs Review</h3>
          <span className="bg-amber-200 dark:bg-amber-800 text-xs font-bold px-2 py-1 rounded-full">
            {stocks.length}
          </span>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-sm text-amber-700 dark:text-amber-500 hidden md:inline">Failed to parse classification</span>
          {open ? <ChevronUp className="h-5 w-5 text-amber-700" /> : <ChevronDown className="h-5 w-5 text-amber-700" />}
        </div>
      </button>
      
      {open && (
        <div className="p-4 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 bg-background">
          {stocks.map(stock => (
            <StockCard key={stock.symbol} stock={stock} />
          ))}
        </div>
      )}
    </div>
  );
}
