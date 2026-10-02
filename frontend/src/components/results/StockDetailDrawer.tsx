"use client";

import { StockDetail } from "@/lib/types";
import { formatCurrency, formatPercent, formatDate } from "@/lib/utils";
import { X, ExternalLink, Copy } from "lucide-react";

export default function StockDetailDrawer({ stock, onClose }: { stock: StockDetail | null, onClose: () => void }) {
  if (!stock) return null;

  return (
    <>
      <div className="fixed inset-0 bg-black/50 z-40" onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 w-full max-w-md bg-background border-l z-50 shadow-2xl overflow-y-auto">
        <div className="p-6">
          <div className="flex justify-between items-start mb-6">
            <div>
              <h2 className="text-2xl font-bold">{stock.symbol}</h2>
              <p className="text-gray-500">{stock.companyName}</p>
            </div>
            <button onClick={onClose} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-full">
              <X className="h-5 w-5" />
            </button>
          </div>

          <div className="flex gap-4 mb-6">
            <div>
              <div className="text-sm text-gray-500">Price</div>
              <div className="text-xl font-bold">{formatCurrency(stock.price)}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">Day Change</div>
              <div className={`text-xl font-bold ${(stock.dayChange || 0) >= 0 ? "text-green-600" : "text-red-500"}`}>
                {formatPercent(stock.dayChange)}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 mb-6">
            <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded-lg border">
              <div className="text-xs text-gray-500">Sector</div>
              <div className="font-medium">{stock.sector || "N/A"}</div>
            </div>
            <div className="bg-slate-50 dark:bg-slate-900 p-3 rounded-lg border">
              <div className="text-xs text-gray-500">Industry</div>
              <div className="font-medium">{stock.industry || "N/A"}</div>
            </div>
          </div>

          <div className="space-y-4 mb-8">
            <h3 className="font-bold border-b pb-2">Scores</h3>
            <div className="flex justify-between items-center">
              <span>MC Score</span>
              <span className="font-bold">{stock.mcScore ?? "N/A"}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Quality (Q)</span>
              <span className="font-bold">{stock.qFactor ?? "N/A"}</span>
            </div>
            <div className="flex justify-between items-center">
              <span>Valuation (V)</span>
              <span className="font-bold">{stock.vFactor ?? "N/A"}</span>
            </div>
          </div>

          <div className="space-y-3">
            <button onClick={() => window.open(`https://www.moneycontrol.com/mccode/${stock.symbol}`, "_blank")} className="w-full flex items-center justify-center gap-2 border py-2 rounded-md hover:bg-slate-50 dark:hover:bg-slate-800">
              <ExternalLink className="h-4 w-4" /> Open Moneycontrol
            </button>
            <button onClick={() => window.open(`https://chartink.com/stocks/${stock.symbol}.html`, "_blank")} className="w-full flex items-center justify-center gap-2 border py-2 rounded-md hover:bg-slate-50 dark:hover:bg-slate-800">
              <ExternalLink className="h-4 w-4" /> Open Chartink
            </button>
            <button onClick={() => navigator.clipboard.writeText(stock.symbol)} className="w-full flex items-center justify-center gap-2 border py-2 rounded-md hover:bg-slate-50 dark:hover:bg-slate-800">
              <Copy className="h-4 w-4" /> Copy Symbol
            </button>
          </div>
          
          <div className="mt-8 text-xs text-gray-400 text-center">
            Last checked: {formatDate(stock.lastChecked)}
          </div>
        </div>
      </div>
    </>
  );
}
