"use client";

import { ScanRun } from "@/lib/types";

export default function SummaryCards({ scan }: { scan: ScanRun }) {
  return (
    <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-8">
      <div className="bg-card border rounded-lg p-4 shadow-sm">
        <div className="text-sm text-gray-500 mb-1">Chartink Stocks</div>
        <div className="text-2xl font-bold">{scan.chartinkCount}</div>
      </div>
      <div className="bg-card border rounded-lg p-4 shadow-sm">
        <div className="text-sm text-gray-500 mb-1">Resolved</div>
        <div className="text-2xl font-bold text-blue-600">{scan.resolvedCount}</div>
      </div>
      <div className="bg-card border rounded-lg p-4 shadow-sm">
        <div className="text-sm text-gray-500 mb-1">Qualified</div>
        <div className="text-2xl font-bold text-green-600">{scan.qualifiedCount}</div>
      </div>
      <div className="bg-card border rounded-lg p-4 shadow-sm">
        <div className="text-sm text-gray-500 mb-1">Not Qualified</div>
        <div className="text-2xl font-bold text-red-500">{scan.notQualifiedCount}</div>
      </div>
      <div className="bg-card border rounded-lg p-4 shadow-sm">
        <div className="text-sm text-gray-500 mb-1">Needs Review</div>
        <div className="text-2xl font-bold text-amber-500">{scan.needsReviewCount}</div>
      </div>
    </div>
  );
}
