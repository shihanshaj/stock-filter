import os
from datetime import datetime, timezone, timedelta
from typing import Optional, AsyncGenerator

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text

# Timezone info
IST = timezone(timedelta(hours=5, minutes=30))

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./stocklens.db")

engine = create_async_engine(DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

class Setting(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True, index=True)
    value = Column(String)

class ScanRun(Base):
    __tablename__ = "scan_runs"
    id = Column(String, primary_key=True, index=True)
    status = Column(String) # RUNNING, COMPLETED, FAILED
    started_at = Column(DateTime)
    completed_at = Column(DateTime, nullable=True)
    chartink_count = Column(Integer, default=0)
    resolved_count = Column(Integer, default=0)
    qualified_count = Column(Integer, default=0)
    not_qualified_count = Column(Integer, default=0)
    review_count = Column(Integer, default=0)
    duration_seconds = Column(Float, nullable=True)
    screener_url = Column(String, nullable=True)

class ScanResult(Base):
    __tablename__ = "scan_results"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    scan_id = Column(String, ForeignKey("scan_runs.id"), index=True)
    symbol = Column(String, index=True)
    company_name = Column(String)
    exchange = Column(String, nullable=True)
    sector = Column(String, nullable=True)
    industry = Column(String, nullable=True)
    bse_code = Column(String, nullable=True)
    
    chartink_matched = Column(Boolean, default=True)
    moneycontrol_resolved = Column(Boolean, default=False)
    moneycontrol_url = Column(String, nullable=True)
    moneycontrol_sc_id = Column(String, nullable=True)
    
    price = Column(Float, nullable=True)
    day_change_percent = Column(Float, nullable=True)
    
    mc_score = Column(Integer, nullable=True)
    q_factor = Column(String, nullable=True)
    g_factor = Column(String, nullable=True)
    v_factor = Column(String, nullable=True)
    
    raw_classification = Column(Text, nullable=True)
    financial_strength = Column(String, nullable=True)
    growth_trend = Column(String, nullable=True)
    valuation = Column(String, nullable=True)
    matched_category = Column(String, nullable=True)
    
    qualified = Column(Boolean, default=False)
    status = Column(String) # SUCCESS, ERROR
    error_message = Column(Text, nullable=True)
    checked_at = Column(DateTime)

class MoneycontrolCache(Base):
    __tablename__ = "moneycontrol_cache"
    symbol = Column(String, primary_key=True, index=True)
    sc_id = Column(String)
    company_name = Column(String)
    slug = Column(String)
    sector = Column(String, nullable=True)
    link_src = Column(String, nullable=True)
    isin = Column(String, nullable=True)
    bse_code = Column(String, nullable=True)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

class ClassificationCache(Base):
    __tablename__ = "classification_cache"
    sc_id = Column(String, primary_key=True, index=True)
    raw_classification = Column(Text)
    financial_strength = Column(String, nullable=True)
    growth_trend = Column(String, nullable=True)
    valuation = Column(String, nullable=True)
    mc_score = Column(Integer, nullable=True)
    checked_at = Column(DateTime)

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session
