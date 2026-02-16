import os
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.database import get_db
from app.models import Invoice, Expense, Client, FinancialInsight
from app.routes import get_current_user, get_active_subscription
from typing import Any
from google import genai
from pydantic import BaseModel
import json

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

class InsightRequest(BaseModel):
    insight_type: str

@router.get("/insights", response_class=HTMLResponse)
async def list_insights(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    # insights are not strictly linked to user_id in the model provided in instructions
    # "requested_by: str — optional, who requested the insight"
    # But for safety, we should probably filter by user if possible, or assume global system insights?
    # The instructions say: "requested_by: str — optional, who requested the insight"
    # I will filter by requested_by == user.email or user.id
    # But wait, User object from viv-auth might have email/id.
    
    # Let's filter by requested_by being the user's ID or email.
    # Viv-auth User usually has 'id' and 'email'.
    
    insights = db.query(FinancialInsight).filter(FinancialInsight.requested_by == str(user.id)).order_by(desc(FinancialInsight.generated_at)).all()
    
    return templates.TemplateResponse("insights/dashboard.html", {"request": request, "user": user, "insights": insights})

@router.get("/insights/{id}", response_class=HTMLResponse)
async def insight_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    insight = db.query(FinancialInsight).filter(FinancialInsight.id == id).first()
    # Check ownership
    if not insight or insight.requested_by != str(user.id):
        raise HTTPException(status_code=404, detail="Insight not found")
        
    return templates.TemplateResponse("insights/detail.html", {"request": request, "user": user, "insight": insight})

@router.post("/api/insights/analyze")
async def analyze_insights(
    request: Request,
    body: InsightRequest,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return JSONResponse(status_code=500, content={"error": "Google API Key not configured"})

    context_data = ""
    
    # Helper to serialize objects
    def serialize_model(obj):
        d = {}
        for c in obj.__table__.columns:
            val = getattr(obj, c.name)
            if hasattr(val, 'isoformat'):
                val = val.isoformat()
            d[c.name] = val
        return d

    if body.insight_type == "revenue_forecast":
        # Get recent invoices
        # User's clients
        client_ids = db.query(Client.id).filter(Client.user_id == str(user.id)).all()
        client_ids = [c[0] for c in client_ids]
        
        invoices = db.query(Invoice).filter(Invoice.client_id.in_(client_ids)).order_by(desc(Invoice.issue_date)).limit(50).all()
        inv_data = [serialize_model(i) for i in invoices]
        context_data = f"Invoices: {json.dumps(inv_data)}"
        
    elif body.insight_type == "expense_analysis":
        expenses = db.query(Expense).filter(Expense.user_id == str(user.id)).order_by(desc(Expense.date)).limit(50).all()
        exp_data = [serialize_model(e) for e in expenses]
        context_data = f"Expenses: {json.dumps(exp_data)}"
        
    elif body.insight_type == "cash_flow":
        client_ids = db.query(Client.id).filter(Client.user_id == str(user.id)).all()
        client_ids = [c[0] for c in client_ids]
        invoices = db.query(Invoice).filter(Invoice.client_id.in_(client_ids)).order_by(desc(Invoice.issue_date)).limit(20).all()
        expenses = db.query(Expense).filter(Expense.user_id == str(user.id)).order_by(desc(Expense.date)).limit(20).all()
        
        inv_data = [serialize_model(i) for i in invoices]
        exp_data = [serialize_model(e) for e in expenses]
        context_data = f"Invoices: {json.dumps(inv_data)}\nExpenses: {json.dumps(exp_data)}"
        
    elif body.insight_type == "client_summary":
        clients = db.query(Client).filter(Client.user_id == str(user.id)).all()
        client_data = []
        for c in clients:
            c_dict = serialize_model(c)
            # Add basic stats
            invs = db.query(Invoice).filter(Invoice.client_id == c.id).all()
            c_dict['total_invoiced'] = sum(i.total for i in invs)
            c_dict['total_paid'] = sum(i.total for i in invs if i.status == 'paid')
            client_data.append(c_dict)
        context_data = f"Clients: {json.dumps(client_data)}"
    
    prompt = f"""
    You are a financial analyst AI for an invoice management application. 
    Analyze the provided data and generate a '{body.insight_type}'. 
    Provide actionable insights, trends, and recommendations. 
    Keep the tone professional but accessible.
    
    Data:
    {context_data}
    """
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        content = response.text
        
        # Save insight
        insight = FinancialInsight(
            insight_type=body.insight_type,
            content=content,
            model_used="gemini-2.5-flash",
            requested_by=str(user.id)
        )
        db.add(insight)
        db.commit()
        db.refresh(insight)
        
        return {"id": insight.id, "content": content}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
