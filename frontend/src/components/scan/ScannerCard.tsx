"use client";

import { useState } from "react";
import { Play, Settings2 } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function ScannerCard({ onScanStart }: { onScanStart: (id: string) => void }) {
  const [loading, setLoading] = useState(false);

  const handleScan = async () => {
    try {
      setLoading(true);
      const res = await api.startScan();
      onScanStart(res.scan_id);
    } catch (error) {
      console.error(error);
      alert("Failed to start scan");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-card text-card-foreground rounded-xl shadow-sm border p-6 mb-8 flex flex-col md:flex-row items-center justify-between gap-4">
      <div>
        <h2 className="text-2xl font-bold mb-2">Run Screener</h2>
        <p className="text-sm text-gray-500 max-w-xl">
          Fetch the latest stocks from Chartink and analyze their Moneycontrol scores and valuations to filter out the best opportunities.
        </p>
      </div>
      <div className="flex items-center gap-3 w-full md:w-auto">
        <Link 
          href="/settings"
          className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2 border rounded-md hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors font-medium text-sm"
        >
          <Settings2 className="h-4 w-4" />
          Settings
        </Link>
        <button
          onClick={handleScan}
          disabled={loading}
          className="flex-1 md:flex-none flex items-center justify-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-md transition-colors font-medium text-sm disabled:opacity-50"
        >
          {loading ? (
            "Starting..."
          ) : (
            <>
              <Play className="h-4 w-4" /> RUN SCAN
            </>
          )}
        </button>
      </div>
    </div>
  );
}
