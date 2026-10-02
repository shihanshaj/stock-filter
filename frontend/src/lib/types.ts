export enum Category {
  AVERAGE_DISCOUNTED = "AVERAGE_DISCOUNTED",
  AVERAGE_ATTRACTIVE = "AVERAGE_ATTRACTIVE",
  HIGH_ATTRACTIVE = "HIGH_ATTRACTIVE",
  HIGH_REASONABLE = "HIGH_REASONABLE",
  HIGH_HIGH_VALUATION = "HIGH_HIGH_VALUATION"
}

export interface Settings {
  screenerUrl: string;
  cacheDuration: number;
  categories: Category[];
  theme?: string;
}

export interface StockDetail {
  symbol: string;
  companyName?: string;
  sector?: string;
  industry?: string;
  price?: number;
  dayChange?: number;
  mcScore?: number;
  qFactor?: number;
  gFactor?: number;
  vFactor?: number;
  classification?: string;
  parsedClassification?: any;
  category?: Category;
  verified?: boolean;
  needsReview?: boolean;
  error?: string;
  lastChecked?: string;
}

export interface ScanRun {
  id: string;
  startTime: string;
  endTime?: string;
  status: "running" | "completed" | "failed";
  chartinkCount: number;
  resolvedCount: number;
  qualifiedCount: number;
  notQualifiedCount: number;
  needsReviewCount: number;
}

export interface ScanSummary extends ScanRun {}

export interface ScanResult {
  scan: ScanRun;
  stocks: StockDetail[];
}

export interface ScanProgress {
  scanId: string;
  stage: "chartink" | "resolving" | "moneycontrol" | "classifying" | "completed" | "failed";
  progress: number;
  total: number;
  current: number;
  logs: string[];
}

export interface ScanDiff {
  newStocks: StockDetail[];
  removedStocks: string[];
  changedStocks: StockDetail[];
  unchangedStocks: StockDetail[];
}
