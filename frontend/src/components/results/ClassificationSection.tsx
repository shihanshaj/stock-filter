"use client";

import { useState } from "react";
import { Category, StockDetail } from "@/lib/types";
import StockCard from "./StockCard";
import { cn } from "@/lib/utils";
import { TrendingUp, Filter } from "lucide-react";

const categoryConfig = {
  [Category.AVERAGE_DISCOUNTED]: {
    title: "AVERAGE GROWTH / DISCOUNTED",
    color: "border-blue-500",
    bg: "bg-blue-50 dark:bg-blue-950/20",
    text: "text-blue-700 dark:text-blue-400"
  },
  [Category.AVERAGE_ATTRACTIVE]: {
    title: "AVERAGE GROWTH / ATTRACTIVE",
    color: "border-green-500",
    bg: "bg-green-50 dark:bg-green-950/20",
    text: "text-green-700 dark:text-green-400"
  },
  [Category.HIGH_ATTRACTIVE]: {
    title: "HIGH GROWTH / ATTRACTIVE",
    color: "border-purple-500",
    bg: "bg-purple-50 dark:bg-purple-950/20",
    text: "text-purple-700 dark:text-purple-400"
  },
  [Category.HIGH_REASONABLE]: {
    title: "HIGH GROWTH / REASONABLE",
    color: "border-teal-500",
    bg: "bg-teal-50 dark:bg-teal-950/20",
    text: "text-teal-700 dark:text-teal-400"
  },
  [Category.HIGH_HIGH_VALUATION]: {
    title: "HIGH GROWTH / HIGH VALUATION",
    color: "border-amber-500",
    bg: "bg-amber-50 dark:bg-amber-950/20",
    text: "text-amber-700 dark:text-amber-400"
  }
};

export default function ClassificationSection({ 
  category, 
  stocks, 
  onStockClick 
}: { 
  category: Category; 
  stocks: StockDetail[]; 
  onStockClick: (stock: StockDetail) => void;
}) {
  const [positiveOnly, setPositiveOnly] = useState(false);

  if (stocks.length === 0) return null;

  const config = categoryConfig[category];
  
  const filteredStocks = positiveOnly 
    ? stocks.filter(s => (s.dayChange || 0) > 0)
    : stocks;

  return (
    <div id={category} className={cn("mb-8 border-l-4 pl-4 scroll-mt-24", config.color, config.bg, "py-4 pr-4 rounded-r-xl transition-all")}>
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
        <div className="flex items-center gap-3">
          <h3 className={cn("font-bold text-lg", config.text)}>{config.title}</h3>
          <span className="bg-white dark:bg-slate-800 text-xs font-bold px-2 py-1 rounded-full shadow-sm">
            {filteredStocks.length} {positiveOnly && `/ ${stocks.length}`}
          </span>
        </div>
        
        <button 
          onClick={() => setPositiveOnly(!positiveOnly)}
          className={cn(
            "flex items-center gap-1.5 text-xs font-medium px-3 py-1.5 rounded-md transition-colors border",
            positiveOnly 
              ? "bg-green-100 border-green-200 text-green-700 dark:bg-green-900/40 dark:border-green-800 dark:text-green-400" 
              : "bg-white border-gray-200 text-gray-600 hover:bg-gray-50 dark:bg-slate-800 dark:border-slate-700 dark:text-gray-300 dark:hover:bg-slate-700"
          )}
        >
          <TrendingUp className="h-3.5 w-3.5" />
          {positiveOnly ? "Showing Positive Only" : "Filter Positive Growth"}
        </button>
      </div>
      
      {filteredStocks.length === 0 ? (
        <div className="text-sm text-gray-500 italic py-4">No stocks match the current filters.</div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {filteredStocks.map(stock => (
            <StockCard key={stock.symbol} stock={stock} onClick={() => onStockClick(stock)} />
          ))}
        </div>
      )}
    </div>
  );
}
