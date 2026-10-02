"use client";

import { useState } from "react";
import { StockDetail } from "@/lib/types";
import { ChevronDown, ChevronUp } from "lucide-react";
import StockCard from "./StockCard";

export default function OtherStocks({ stocks }: { stocks: StockDetail[] }) {
  const [open, setOpen] = useState(false);

  if (stocks.length === 0) return null;

  return (
    <div className="mb-8 border rounded-xl overflow-hidden">
      <button 
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between p-4 bg-slate-50 dark:bg-slate-900 hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors"
      >
        <div className="flex items-center gap-3">
          <h3 className="font-bold">Other Chartink Stocks</h3>
          <span className="bg-slate-200 dark:bg-slate-700 text-xs font-bold px-2 py-1 rounded-full">
            {stocks.length}
          </span>
        </div>
        {open ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
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
