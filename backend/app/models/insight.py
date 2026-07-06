from sqlalchemy import Column, Integer, String, Float, DateTime, Text, JSON
from sqlalchemy.sql import func
from app.database import Base


class SeasonalityMetric(Base):
    __tablename__ = "seasonality_metrics"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False, index=True)  # top_products_day, top_products_month, peak_hours, top_clients, category_consumption
    period = Column(String(20), nullable=False)  # day, week, month, year
    period_value = Column(String(50), nullable=True)  # monday, 2024-01, etc.
    data = Column(JSON, nullable=False)
    calculated_at = Column(DateTime, default=func.now())
    created_at = Column(DateTime, default=func.now())


class InsightLog(Base):
    __tablename__ = "insight_logs"

    id = Column(Integer, primary_key=True, index=True)
    insight_type = Column(String(50), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    severity = Column(String(20), default="info")  # info, warning, alert
    data = Column(JSON, nullable=True)
    is_active = Column(Integer, default=1)
    created_at = Column(DateTime, default=func.now())
