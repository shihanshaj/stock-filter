"use client";

import { ScanDiff } from "@/lib/types";
import StockCard from "./StockCard";

export default function DiffSection({ diff }: { diff: ScanDiff }) {
  if (!diff || (diff.newStocks.length === 0 && diff.removedStocks.length === 0)) return null;

  return (
    <div className="mb-8">
      <h3 className="font-bold text-lg mb-4">Changes Since Last Scan</h3>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {diff.newStocks.length > 0 && (
          <div className="bg-green-50 dark:bg-green-950/20 p-4 rounded-lg border border-green-200 dark:border-green-800">
            <h4 className="font-bold text-green-700 dark:text-green-400 mb-3">New Additions ({diff.newStocks.length})</h4>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
              {diff.newStocks.map(s => <StockCard key={s.symbol} stock={s} />)}
            </div>
          </div>
        )}
        {diff.removedStocks.length > 0 && (
          <div className="bg-red-50 dark:bg-red-950/20 p-4 rounded-lg border border-red-200 dark:border-red-800">
            <h4 className="font-bold text-red-700 dark:text-red-400 mb-3">Removed ({diff.removedStocks.length})</h4>
            <div className="flex flex-wrap gap-2">
              {diff.removedStocks.map(s => (
                <span key={s} className="px-2 py-1 bg-white dark:bg-slate-800 rounded border text-sm">{s}</span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
