"use client";

import { useEffect, useState } from "react";
import ScannerCard from "@/components/scan/ScannerCard";
import ScanProgressTracker from "@/components/scan/ScanProgress";
import SummaryCards from "@/components/scan/SummaryCards";
import ClassificationSection from "@/components/results/ClassificationSection";
import { api } from "@/lib/api";
import { Category, ScanResult, StockDetail } from "@/lib/types";

import { Search } from "lucide-react";

export default function Home() {
  const [data, setData] = useState<ScanResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeScanId, setActiveScanId] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState("");

  const fetchLatest = async () => {
    try {
      setLoading(true);
      const res = await api.getLatestScan();
      setData(res);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLatest();
  }, []);

  const handleScanStart = (scanId: string) => {
    setActiveScanId(scanId);
  };

  if (loading) return <div className="text-center py-20 animate-pulse">Loading...</div>;

  // Helper to filter and sort stocks
  const getSectionStocks = (category: Category) => {
    if (!data) return [];
    
    // First, filter by category and search query
    const filtered = data.stocks.filter(s => {
      if (s.category !== category) return false;
      if (!searchQuery) return true;
      
      const q = searchQuery.toLowerCase();
      return (
        s.symbol.toLowerCase().includes(q) || 
        (s.companyName || "").toLowerCase().includes(q)
      );
    });

    // Then, sort by day change percentage (highest first)
    return filtered.sort((a, b) => (b.dayChange || -999) - (a.dayChange || -999));
  };

  return (
    <div>
      <ScannerCard onScanStart={handleScanStart} />
      
      {activeScanId && (
        <ScanProgressTracker 
          scanId={activeScanId} 
          onComplete={() => {
            setActiveScanId(null);
            fetchLatest();
          }} 
        />
      )}

      {data ? (
        <>
          <SummaryCards scan={data.scan} />
          
          <div className="bg-card border rounded-lg p-4 mb-8 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4 sticky top-4 z-10">
            <div className="flex flex-wrap gap-2">
              <span className="text-sm font-medium text-gray-500 mr-2 flex items-center">Jump to:</span>
              <a href={`#${Category.AVERAGE_DISCOUNTED}`} className="text-xs font-semibold px-3 py-1.5 bg-blue-100 text-blue-700 hover:bg-blue-200 dark:bg-blue-900/40 dark:text-blue-300 rounded-full transition-colors">Avg / Discounted</a>
              <a href={`#${Category.AVERAGE_ATTRACTIVE}`} className="text-xs font-semibold px-3 py-1.5 bg-green-100 text-green-700 hover:bg-green-200 dark:bg-green-900/40 dark:text-green-300 rounded-full transition-colors">Avg / Attractive</a>
              <a href={`#${Category.HIGH_ATTRACTIVE}`} className="text-xs font-semibold px-3 py-1.5 bg-purple-100 text-purple-700 hover:bg-purple-200 dark:bg-purple-900/40 dark:text-purple-300 rounded-full transition-colors">High / Attractive</a>
              <a href={`#${Category.HIGH_REASONABLE}`} className="text-xs font-semibold px-3 py-1.5 bg-teal-100 text-teal-700 hover:bg-teal-200 dark:bg-teal-900/40 dark:text-teal-300 rounded-full transition-colors">High / Reasonable</a>
              <a href={`#${Category.HIGH_HIGH_VALUATION}`} className="text-xs font-semibold px-3 py-1.5 bg-amber-100 text-amber-700 hover:bg-amber-200 dark:bg-amber-900/40 dark:text-amber-300 rounded-full transition-colors">High / High Val</a>
            </div>
            
            <div className="relative w-full md:w-64">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-gray-500" />
              <input
                type="text"
                placeholder="Search stocks..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-9 pr-4 py-2 bg-transparent border rounded-md text-sm focus:outline-none focus:ring-1 focus:ring-blue-500 dark:border-slate-700"
              />
            </div>
          </div>
          
          <div className="mt-4">
            <ClassificationSection 
              category={Category.AVERAGE_DISCOUNTED} 
              stocks={getSectionStocks(Category.AVERAGE_DISCOUNTED)} 
              onStockClick={() => {}}
            />
            <ClassificationSection 
              category={Category.AVERAGE_ATTRACTIVE} 
              stocks={getSectionStocks(Category.AVERAGE_ATTRACTIVE)} 
              onStockClick={() => {}}
            />
            <ClassificationSection 
              category={Category.HIGH_ATTRACTIVE} 
              stocks={getSectionStocks(Category.HIGH_ATTRACTIVE)} 
              onStockClick={() => {}}
            />
            <ClassificationSection 
              category={Category.HIGH_REASONABLE} 
              stocks={getSectionStocks(Category.HIGH_REASONABLE)} 
              onStockClick={() => {}}
            />
            <ClassificationSection 
              category={Category.HIGH_HIGH_VALUATION} 
              stocks={getSectionStocks(Category.HIGH_HIGH_VALUATION)} 
              onStockClick={() => {}}
            />
          </div>
        </>
      ) : (
        <div className="text-center py-20 text-gray-500">
          No scans run yet. Click RUN SCAN to begin.
        </div>
      )}
    </div>
  );
}
