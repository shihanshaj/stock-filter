"use client";

export default function StatusBadge({ status }: { status: "Match" | "Not Selected" | "Needs Review" }) {
  const styles = {
    "Match": "bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400 border-green-200",
    "Not Selected": "bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-400 border-slate-200",
    "Needs Review": "bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400 border-amber-200"
  };

  return (
    <span className={`px-2 py-1 rounded text-xs font-medium border ${styles[status]}`}>
      {status}
    </span>
  );
}
