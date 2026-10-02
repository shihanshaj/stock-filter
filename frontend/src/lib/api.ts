import { Settings, ScanResult, ScanSummary, ScanDiff, StockDetail } from './types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAPI(endpoint: string, options: RequestInit = {}) {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  });
  if (!response.ok) {
    throw new Error(`API Error: ${response.statusText}`);
  }
  return response.json();
}

export const api = {
  startScan: (): Promise<{ scanId: string }> => fetchAPI('/api/scans', { method: 'POST' }),
  getScan: (id: string): Promise<ScanResult> => fetchAPI(`/api/scans/${id}`),
  getLatestScan: (): Promise<ScanResult> => fetchAPI('/api/scans/latest'),
  getScans: (): Promise<ScanSummary[]> => fetchAPI('/api/scans').then(res => res.scans),
  getScanDiff: (id: string): Promise<ScanDiff> => fetchAPI(`/api/scans/${id}/diff`),
  getStock: (symbol: string): Promise<StockDetail> => fetchAPI(`/api/stocks/${symbol}`),
  refreshStock: (symbol: string): Promise<StockDetail> => fetchAPI(`/api/stocks/${symbol}/refresh`, { method: 'POST' }),
  getSettings: (): Promise<Settings> => fetchAPI('/api/settings'),
  updateSettings: (data: Settings): Promise<Settings> => fetchAPI('/api/settings', { method: 'PUT', body: JSON.stringify(data) }),
  streamScanProgress: (scanId: string) => new EventSource(`${API_BASE_URL}/api/scans/${scanId}/stream`),
  exportCSV: (scanId: string) => { window.location.href = `${API_BASE_URL}/api/scans/${scanId}/export/csv`; },
  exportJSON: (scanId: string) => { window.location.href = `${API_BASE_URL}/api/scans/${scanId}/export/json`; },
};
