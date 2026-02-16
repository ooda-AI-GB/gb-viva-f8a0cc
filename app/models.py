from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Date, Float, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Client(Base):
    __tablename__ = "clients"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False) # who owns this client (from auth)
    name = Column(String(200), nullable=False)
    email = Column(String, nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=True)
    tax_id = Column(String(50), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")

class Invoice(Base):
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=False)
    invoice_number = Column(String(50), unique=True, nullable=False)
    status = Column(String, default="draft") # "draft", "sent", "viewed", "paid", "overdue", "cancelled"
    issue_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    subtotal = Column(Float, default=0.0)
    tax_rate = Column(Float, default=0.0)
    tax_amount = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    currency = Column(String(3), default="USD")
    notes = Column(Text, nullable=True)
    paid_date = Column(Date, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    client = relationship("Client", back_populates="invoices")
    line_items = relationship("LineItem", back_populates="invoice", cascade="all, delete-orphan")

class LineItem(Base):
    __tablename__ = "line_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String(300), nullable=False)
    quantity = Column(Float, default=1.0, nullable=False)
    unit_price = Column(Float, nullable=False)
    amount = Column(Float, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    invoice = relationship("Invoice", back_populates="line_items")

class Expense(Base):
    __tablename__ = "expenses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False) # who logged this expense
    category = Column(String, nullable=True) # "software", "hardware", "travel", "office", "marketing", "professional", "utilities", "other"
    description = Column(String(300), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(3), default="USD")
    date = Column(Date, nullable=False)
    vendor = Column(String(200), nullable=True)
    receipt_ref = Column(String(100), nullable=True)
    tax_deductible = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class FinancialInsight(Base):
    __tablename__ = "financial_insights"

    id = Column(Integer, primary_key=True, index=True)
    insight_type = Column(String, nullable=True) # "revenue_forecast", "expense_analysis", "cash_flow", "client_summary"
    content = Column(Text, nullable=True)
    model_used = Column(String, nullable=True)
    generated_at = Column(DateTime(timezone=True), server_default=func.now())
    requested_by = Column(String, nullable=True)
