"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { ScanSummary } from "@/lib/types";
import { formatDate } from "@/lib/utils";
import Link from "next/link";

export default function HistoryPage() {
  const [scans, setScans] = useState<ScanSummary[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.getScans().then(setScans).finally(() => setLoading(false));
  }, []);

  if (loading) return <div className="text-center py-10">Loading history...</div>;

  return (
    <div className="max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">Scan History</h1>
      {scans.length === 0 ? (
        <p className="text-gray-500">No scans found.</p>
      ) : (
        <div className="bg-card border rounded-lg overflow-hidden shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-50 dark:bg-slate-900 border-b">
              <tr>
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium text-right">Stocks</th>
                <th className="px-4 py-3 font-medium text-right">Qualified</th>
              </tr>
            </thead>
            <tbody className="divide-y">
              {scans.map(scan => (
                <tr key={scan.id} className="hover:bg-slate-50 dark:hover:bg-slate-900/50">
                  <td className="px-4 py-3">
                    <Link href={`/?scan=${scan.id}`} className="text-blue-600 hover:underline">
                      {formatDate(scan.startTime)}
                    </Link>
                  </td>
                  <td className="px-4 py-3">
                    <span className={`px-2 py-1 rounded text-xs ${scan.status === 'completed' ? 'bg-green-100 text-green-800' : 'bg-amber-100 text-amber-800'}`}>
                      {scan.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-right">{scan.chartinkCount}</td>
                  <td className="px-4 py-3 text-right">{scan.qualifiedCount}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
