"use client";

export default function EmptyState({ message = "No data available." }: { message?: string }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 bg-slate-50 dark:bg-slate-900/50 rounded-xl border border-dashed">
      <div className="text-4xl mb-4">📊</div>
      <h3 className="text-lg font-medium text-slate-600 dark:text-slate-400">{message}</h3>
    </div>
  );
}
