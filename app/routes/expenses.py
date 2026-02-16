from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models import Expense
from app.routes import get_current_user, get_active_subscription
from typing import Any, Optional
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/expenses", response_class=HTMLResponse)
async def list_expenses(
    request: Request,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    query = db.query(Expense).filter(Expense.user_id == user.id)
    if category:
        query = query.filter(Expense.category == category)
        
    expenses = query.order_by(desc(Expense.date)).all()
    
    total_amount = sum(e.amount for e in expenses)
    
    return templates.TemplateResponse("expenses/list.html", {
        "request": request, 
        "user": user, 
        "expenses": expenses, 
        "total_amount": total_amount,
        "selected_category": category
    })

@router.get("/expenses/new", response_class=HTMLResponse)
async def new_expense_form(
    request: Request,
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    return templates.TemplateResponse("expenses/form.html", {
        "request": request, 
        "user": user,
        "today": datetime.date.today()
    })

@router.post("/expenses/new")
async def create_expense(
    request: Request,
    description: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...),
    category: str = Form("other"),
    vendor: Optional[str] = Form(None),
    tax_deductible: bool = Form(False),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    new_expense = Expense(
        user_id=user.id,
        description=description,
        amount=amount,
        date=datetime.datetime.strptime(date, "%Y-%m-%d").date(),
        category=category,
        vendor=vendor,
        tax_deductible=tax_deductible
    )
    db.add(new_expense)
    db.commit()
    return RedirectResponse(url="/expenses", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/expenses/{id}/edit", response_class=HTMLResponse)
async def edit_expense_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    expense = db.query(Expense).filter(Expense.id == id, Expense.user_id == user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    return templates.TemplateResponse("expenses/form.html", {"request": request, "user": user, "expense": expense})

@router.post("/expenses/{id}/edit")
async def update_expense(
    request: Request,
    id: int,
    description: str = Form(...),
    amount: float = Form(...),
    date: str = Form(...),
    category: str = Form("other"),
    vendor: Optional[str] = Form(None),
    tax_deductible: bool = Form(False),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    expense = db.query(Expense).filter(Expense.id == id, Expense.user_id == user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    expense.description = description
    expense.amount = amount
    expense.date = datetime.datetime.strptime(date, "%Y-%m-%d").date()
    expense.category = category
    expense.vendor = vendor
    expense.tax_deductible = tax_deductible
    
    db.commit()
    return RedirectResponse(url="/expenses", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/expenses/{id}/delete")
async def delete_expense(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    expense = db.query(Expense).filter(Expense.id == id, Expense.user_id == user.id).first()
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    db.delete(expense)
    db.commit()
    return RedirectResponse(url="/expenses", status_code=status.HTTP_303_SEE_OTHER)
