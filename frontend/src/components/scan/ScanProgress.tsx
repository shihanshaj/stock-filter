"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ScanProgress } from "@/lib/types";
import { Loader2 } from "lucide-react";

export default function ScanProgressTracker({ scanId, onComplete }: { scanId: string, onComplete: () => void }) {
  const [progressData, setProgressData] = useState<any>(null);

  useEffect(() => {
    const sse = api.streamScanProgress(scanId);
    
    sse.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.keepalive) return;
        
        setProgressData(data);
        if (data.status === "COMPLETED" || data.status === "COMPLETED_WITH_WARNINGS" || data.status === "FAILED") {
          sse.close();
          onComplete();
        }
      } catch (e) {
        console.error("Failed to parse SSE", e);
      }
    };

    sse.onerror = (e) => {
      console.error("SSE Error", e);
      sse.close();
      onComplete(); // fallback
    };

    return () => sse.close();
  }, [scanId, onComplete]);

  if (!progressData) return null;

  const percent = progressData.total > 0 ? Math.round((progressData.processed / progressData.total) * 100) : 0;

  return (
    <div className="bg-card border rounded-xl p-6 mb-8 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-bold flex items-center gap-2">
          {progressData.status !== "COMPLETED" && progressData.status !== "FAILED" && (
            <Loader2 className="h-5 w-5 animate-spin text-blue-600" />
          )}
          {progressData.stage || progressData.status}
        </h3>
        {progressData.total > 0 && (
          <span className="text-sm font-medium">
            {progressData.processed} / {progressData.total} ({percent}%)
          </span>
        )}
      </div>
      
      {progressData.total > 0 && (
        <div className="w-full bg-slate-200 dark:bg-slate-700 rounded-full h-2.5 mb-4 overflow-hidden">
          <div className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" style={{ width: `${percent}%` }}></div>
        </div>
      )}
      
      {progressData.recent && progressData.recent.length > 0 && (
        <div className="text-xs text-gray-500 font-mono bg-slate-50 dark:bg-slate-900 p-3 rounded max-h-32 overflow-y-auto space-y-1">
          {progressData.recent.map((item: any, i: number) => (
            <div key={i} className="flex justify-between">
              <span className="font-semibold">{item.symbol}</span>
              <span className={
                item.status === 'match' ? 'text-green-600' :
                item.status === 'error' ? 'text-red-600' :
                item.status === 'review' ? 'text-amber-600' :
                'text-gray-400'
              }>
                {item.status.toUpperCase()}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
