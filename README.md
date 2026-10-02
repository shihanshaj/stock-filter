# StockLens

**Chartink × Moneycontrol Stock Filter**

StockLens is a focused screening utility that combines [Chartink](https://chartink.com) screener results with [Moneycontrol](https://www.moneycontrol.com) stock classifications to identify stocks matching specific growth and valuation criteria.

## What It Does

1. **Runs a Chartink screener** — fetches stocks from the [Intrinsic Value Stock Screener](https://chartink.com/screener/copy-intrinsic-value-stock-134?src=wassup)
2. **Resolves each stock on Moneycontrol** — maps NSE symbols to Moneycontrol company pages
3. **Extracts MC Stock Score classification** — retrieves the growth trend and valuation assessment
4. **Filters and categorizes** — keeps stocks matching four specific conditions:

| Category | Growth Trend | Valuation |
|----------|-------------|-----------|
| 🔵 Average + Discounted | Average Growth Trend | Discounted Valuations |
| 🟢 Average + Attractive | Average Growth Trend | Attractive Valuations |
| 🟣 High + Attractive | High Growth Trend | Attractive Valuations |
| 🟠 High + High | High Growth Trend | High Valuations |

Financial Strength classification is intentionally **ignored** — only Growth Trend and Valuation matter.

## Architecture

```
stocklens/
├── backend/          # Python FastAPI server
│   ├── app/
│   │   ├── main.py           # FastAPI app, routes, SSE
│   │   ├── database.py       # SQLite via SQLAlchemy async
│   │   ├── models.py         # Pydantic schemas
│   │   └── services/
│   │       ├── chartink.py       # Chartink screener extraction
│   │       ├── moneycontrol.py   # MC search + classification
│   │       ├── resolver.py       # Symbol resolution
│   │       ├── classifier.py     # Classification parser
│   │       └── scanner.py        # Scan orchestration
│   └── requirements.txt
├── frontend/         # Next.js React app
│   └── src/
│       ├── app/              # Pages (dashboard, history, settings)
│       ├── components/       # UI components
│       └── lib/              # API client, types, utilities
├── scripts/          # Development scripts
├── docker/           # Docker configuration
├── .env.example      # Environment template
└── README.md
```

## Requirements

- **Python 3.10+** (backend)
- **Node.js 18+** (frontend)
- **npm** (package manager)

## Quick Start

### 1. Clone and configure

```bash
cd stocklens
cp .env.example .env
```

### 2. Start the backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

### 3. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

### 4. Open StockLens

Visit **http://localhost:3000** and click **Run Scan**.

### Alternative: Use the dev script

```bash
chmod +x scripts/dev.sh
./scripts/dev.sh
```

## How Scans Work

### Chartink Extraction

StockLens uses Chartink's internal scan processing API:

1. **GET** the screener page to obtain a CSRF token and session cookies
2. **Extract** the `atlas_query` (scan clause) from the page HTML
3. **POST** to `https://chartink.com/screener/process` with the scan clause
4. **Parse** the JSON response containing stock symbols, names, prices, and volumes

Each stock in the response includes: NSE symbol (`nsecode`), BSE code (`bsecode`), company name (`name`), closing price (`close`), and percentage change (`per_chg`).

### Moneycontrol Extraction

For each Chartink stock:

1. **Search** using Moneycontrol's autocomplete API with the NSE symbol
2. **Verify** the match by checking the NSE ticker in the search results
3. **Fetch** the MC Stock Score page for the resolved company
4. **Extract** the classification text from the page HTML
5. **Parse** the classification into Financial Strength, Growth Trend, and Valuation components

### Classification Parsing

Raw classification text like:

```
Superior Financial Strength, Average Growth Trend Stock at Attractive Valuations
```

Is parsed into:

```json
{
  "financialStrength": "Superior",
  "growthTrend": "Average",
  "valuation": "Attractive",
  "matchedCategory": "AVERAGE_ATTRACTIVE",
  "qualified": true
}
```

The parser normalizes whitespace, case, and HTML entities before matching.

## Cache Behavior

| Data | Cache Duration | Rationale |
|------|---------------|-----------|
| Company mappings (symbol → MC ID) | 7 days | Rarely changes |
| Classification data | 1 hour | Can change with market conditions |

Confirmed mappings are cached in SQLite to avoid redundant resolution on subsequent scans. Classifications are refreshed during each scan unless recently cached.

Use **Refresh** to force re-fetch of all data.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/scans` | Start a new scan |
| `GET` | `/api/scans` | List all scans |
| `GET` | `/api/scans/latest` | Get most recent scan |
| `GET` | `/api/scans/{id}` | Get scan details |
| `GET` | `/api/scans/{id}/stream` | SSE progress stream |
| `GET` | `/api/scans/{id}/diff` | Compare with previous scan |
| `GET` | `/api/scans/{id}/export/csv` | Export results as CSV |
| `GET` | `/api/scans/{id}/export/json` | Export results as JSON |
| `GET` | `/api/stocks/{symbol}` | Get stock details |
| `POST` | `/api/stocks/{symbol}/refresh` | Refresh a stock |
| `GET` | `/api/settings` | Get settings |
| `PUT` | `/api/settings` | Update settings |
| `GET` | `/api/health` | Health check |

## Testing

```bash
cd backend
source venv/bin/activate

# Run all tests
python -m pytest app/tests/ -v

# Run classifier tests specifically
python -m pytest app/tests/test_classifier.py -v
```

## Development Commands

```bash
# Backend
cd backend && source venv/bin/activate
uvicorn app.main:app --reload                # Dev server
python -m pytest app/tests/ -v               # Tests
python -m pytest app/tests/ -v --tb=short    # Tests (short output)

# Frontend
cd frontend
npm run dev          # Dev server
npm run build        # Production build
npm run lint         # Lint check
```

## Known Limitations

1. **Chartink CSRF tokens** expire — the backend fetches a fresh token for each scan
2. **Moneycontrol rate limits** — concurrent requests are limited to 3 with exponential backoff
3. **Classification extraction** depends on Moneycontrol's page structure — if they change the stock score page layout, the parser may need updating
4. **Symbol resolution** may fail for recently listed stocks not yet in Moneycontrol's search index
5. **No authentication** — this is a local development tool, not a public service

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "CSRF token not found" | Chartink may have changed their page structure. Check `services/chartink.py`. |
| "Moneycontrol temporarily prevented this request" | Rate limited. Wait a few minutes and retry. The stock is placed in "Needs Review". |
| No stocks found | Market may be closed and Chartink returns empty results. Try during market hours. |
| Classification not found | Moneycontrol may not have MC Stock Score for that company. Check manually. |
| Frontend can't connect | Ensure backend is running on port 8000. Check CORS settings. |

## Disclaimer

StockLens is a screening and research utility. Source data is provided by third-party financial websites. Verify market information independently before making financial decisions.

## License

Private use only. Not for redistribution.
