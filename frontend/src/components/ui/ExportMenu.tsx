"use client";

import { Download, Copy, FileJson, FileSpreadsheet, ChevronDown } from "lucide-react";
import { useState, useRef, useEffect } from "react";
import { api } from "@/lib/api";

export default function ExportMenu({ scanId, symbols }: { scanId: string, symbols: string[] }) {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, []);

  const handleCopy = () => {
    navigator.clipboard.writeText(symbols.join(","));
    setOpen(false);
    alert("Copied " + symbols.length + " symbols");
  };

  return (
    <div className="relative" ref={ref}>
      <button 
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 px-3 py-1.5 border rounded-md hover:bg-slate-50 dark:hover:bg-slate-800 text-sm font-medium"
      >
        <Download className="h-4 w-4" /> Export <ChevronDown className="h-3 w-3" />
      </button>
      
      {open && (
        <div className="absolute right-0 mt-1 w-48 bg-card border rounded-md shadow-lg z-10 py-1">
          <button onClick={handleCopy} className="w-full flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-800 text-left">
            <Copy className="h-4 w-4" /> Copy Symbols
          </button>
          <button onClick={() => api.exportCSV(scanId)} className="w-full flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-800 text-left">
            <FileSpreadsheet className="h-4 w-4" /> Export CSV
          </button>
          <button onClick={() => api.exportJSON(scanId)} className="w-full flex items-center gap-2 px-4 py-2 text-sm hover:bg-slate-50 dark:hover:bg-slate-800 text-left">
            <FileJson className="h-4 w-4" /> Export JSON
          </button>
        </div>
      )}
    </div>
  );
}
