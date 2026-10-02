"use client";

import { StockDetail } from "@/lib/types";
import { formatCurrency, formatPercent, cn } from "@/lib/utils";

export default function StockCard({ stock, onClick }: { stock: StockDetail; onClick?: () => void }) {
  return (
    <div 
      onClick={onClick}
      className={cn(
        "bg-card border rounded-lg p-4 shadow-sm hover:shadow-md transition-shadow cursor-pointer",
        stock.needsReview ? "border-amber-300 dark:border-amber-700/50" : ""
      )}
    >
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="font-bold text-lg">{stock.symbol}</h4>
          <p className="text-xs text-gray-500 truncate max-w-[150px]">{stock.companyName || "Unknown"}</p>
        </div>
        <div className="text-right">
          <div className="font-semibold">{formatCurrency(stock.price)}</div>
          <div className={cn("text-xs font-medium", (stock.dayChange || 0) >= 0 ? "text-green-600" : "text-red-500")}>
            {formatPercent(stock.dayChange)}
          </div>
        </div>
      </div>
      
      <div className="flex gap-2 mt-3 text-xs">
        {stock.mcScore !== undefined && (
          <span className="bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300 px-2 py-1 rounded">
            MC: {stock.mcScore}
          </span>
        )}
        {stock.qFactor !== undefined && (
          <span className="bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300 px-2 py-1 rounded">
            Q: {stock.qFactor}
          </span>
        )}
        {stock.vFactor !== undefined && (
          <span className="bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-300 px-2 py-1 rounded">
            V: {stock.vFactor}
          </span>
        )}
      </div>
      
      {stock.classification && (
        <div className="mt-3 text-[10px] text-gray-500 line-clamp-2 leading-tight">
          {stock.classification}
        </div>
      )}
    </div>
  );
}
