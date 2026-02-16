from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, extract
from app.database import get_db
from app.models import Invoice, Client, Expense
from app.routes import get_current_user, get_active_subscription
from typing import Any
from datetime import date, timedelta
import datetime
from app.seed import seed_data

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/", response_class=HTMLResponse)
async def dashboard(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    # Seed data check
    seed_data(db, user.id)

    # 1. Revenue Summary (This Month)
    today = date.today()
    first_day_of_month = date(today.year, today.month, 1)
    
    # Invoices for this user
    user_clients_subquery = db.query(Client.id).filter(Client.user_id == user.id).subquery()
    
    invoices_this_month = db.query(Invoice).filter(
        Invoice.client_id.in_(user_clients_subquery),
        Invoice.issue_date >= first_day_of_month
    ).all()
    
    total_invoiced_month = sum(inv.total for inv in invoices_this_month)
    
    paid_invoices_month = [inv for inv in invoices_this_month if inv.status == 'paid']
    total_paid_month = sum(inv.total for inv in paid_invoices_month)
    
    # Total Outstanding (All time)
    outstanding_invoices = db.query(Invoice).filter(
        Invoice.client_id.in_(user_clients_subquery),
        Invoice.status.in_(['sent', 'viewed', 'overdue'])
    ).all()
    total_outstanding = sum(inv.total for inv in outstanding_invoices)
    
    # 2. Invoice Status Breakdown
    status_counts = db.query(
        Invoice.status, func.count(Invoice.id)
    ).filter(
        Invoice.client_id.in_(user_clients_subquery)
    ).group_by(Invoice.status).all()
    
    status_dict = {s: c for s, c in status_counts}
    
    # 3. Recent Invoices
    recent_invoices = db.query(Invoice).filter(
        Invoice.client_id.in_(user_clients_subquery)
    ).order_by(desc(Invoice.created_at)).limit(10).all()
    
    # 4. Quick Stats
    total_clients = db.query(Client).filter(Client.user_id == user.id).count()
    invoice_count_month = len(invoices_this_month)
    
    # Revenue YTD
    first_day_year = date(today.year, 1, 1)
    revenue_ytd_invoices = db.query(Invoice).filter(
        Invoice.client_id.in_(user_clients_subquery),
        Invoice.issue_date >= first_day_year,
        Invoice.status == 'paid'
    ).all()
    revenue_ytd = sum(inv.total for inv in revenue_ytd_invoices)
    
    # Expenses YTD
    expenses_ytd_records = db.query(Expense).filter(
        Expense.user_id == user.id,
        Expense.date >= first_day_year
    ).all()
    expenses_ytd = sum(exp.amount for exp in expenses_ytd_records)
    
    # 5. Overdue Alerts
    overdue_invoices = db.query(Invoice).filter(
        Invoice.client_id.in_(user_clients_subquery),
        Invoice.status != 'paid',
        Invoice.status != 'cancelled',
        Invoice.status != 'draft',
        Invoice.due_date < today
    ).all()
    
    # Calculate days overdue for display
    for inv in overdue_invoices:
        inv.days_overdue = (today - inv.due_date).days
        
    # 6. Monthly Chart Data (Last 6 months)
    chart_data = []
    for i in range(5, -1, -1):
        # Calculate month start and end
        month_date = today - timedelta(days=i*30) # Approx
        m_start = date(month_date.year, month_date.month, 1)
        if m_start.month == 12:
            m_end = date(m_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            m_end = date(m_start.year, m_start.month + 1, 1) - timedelta(days=1)
            
        # Revenue
        m_revenue = db.query(func.sum(Invoice.total)).filter(
            Invoice.client_id.in_(user_clients_subquery),
            Invoice.paid_date >= m_start,
            Invoice.paid_date <= m_end,
            Invoice.status == 'paid'
        ).scalar() or 0.0
        
        # Expenses
        m_expenses = db.query(func.sum(Expense.amount)).filter(
            Expense.user_id == user.id,
            Expense.date >= m_start,
            Expense.date <= m_end
        ).scalar() or 0.0
        
        chart_data.append({
            "month": m_start.strftime("%b"),
            "revenue": m_revenue,
            "expenses": m_expenses
        })

    # Find max value for chart scaling
    max_val = 0
    for d in chart_data:
        max_val = max(max_val, d["revenue"], d["expenses"])
    
    if max_val == 0:
        max_val = 100 # Prevent division by zero
        
    for d in chart_data:
        d["revenue_pct"] = (d["revenue"] / max_val) * 100
        d["expenses_pct"] = (d["expenses"] / max_val) * 100

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "total_invoiced_month": total_invoiced_month,
        "total_paid_month": total_paid_month,
        "total_outstanding": total_outstanding,
        "status_counts": status_dict,
        "recent_invoices": recent_invoices,
        "total_clients": total_clients,
        "invoice_count_month": invoice_count_month,
        "revenue_ytd": revenue_ytd,
        "expenses_ytd": expenses_ytd,
        "overdue_invoices": overdue_invoices,
        "chart_data": chart_data
    })
