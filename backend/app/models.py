from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any
from datetime import datetime

class SettingsResponse(BaseModel):
    settings: Dict[str, str]

class SettingsUpdate(BaseModel):
    settings: Dict[str, str]

class ScanRunBase(BaseModel):
    id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    chartink_count: int
    resolved_count: int
    qualified_count: int
    not_qualified_count: int
    review_count: int
    duration_seconds: Optional[float] = None
    screener_url: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)

class ScanResultBase(BaseModel):
    id: int
    scan_id: str
    symbol: str
    company_name: str
    exchange: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    bse_code: Optional[str] = None
    
    chartink_matched: bool
    moneycontrol_resolved: bool
    moneycontrol_url: Optional[str] = None
    moneycontrol_sc_id: Optional[str] = None
    
    price: Optional[float] = None
    day_change_percent: Optional[float] = None
    
    mc_score: Optional[int] = None
    q_factor: Optional[str] = None
    g_factor: Optional[str] = None
    v_factor: Optional[str] = None
    
    raw_classification: Optional[str] = None
    financial_strength: Optional[str] = None
    growth_trend: Optional[str] = None
    valuation: Optional[str] = None
    matched_category: Optional[str] = None
    
    qualified: bool
    status: str
    error_message: Optional[str] = None
    checked_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ScanDetailResponse(BaseModel):
    run: ScanRunBase
    results: List[ScanResultBase]

class ScansListResponse(BaseModel):
    scans: List[ScanRunBase]
