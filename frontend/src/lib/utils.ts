import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";
import { format, formatDistanceToNow } from "date-fns";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value?: number) {
  if (value === undefined || value === null) return "N/A";
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    minimumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value?: number) {
  if (value === undefined || value === null) return "N/A";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

export function formatDate(dateString?: string) {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  return format(date, "dd MMM yyyy • hh:mm a");
}

export function formatRelative(dateString?: string) {
  if (!dateString) return "N/A";
  const date = new Date(dateString);
  return formatDistanceToNow(date, { addSuffix: true });
}
