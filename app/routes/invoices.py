from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models import Invoice, LineItem, Client
from app.routes import get_current_user, get_active_subscription
from typing import Any, List, Optional
from datetime import date
import datetime

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/invoices", response_class=HTMLResponse)
async def list_invoices(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    clients = db.query(Client.id).filter(Client.user_id == str(user.id)).subquery()
    invoices = db.query(Invoice).filter(Invoice.client_id.in_(clients)).order_by(desc(Invoice.issue_date)).all()
    return templates.TemplateResponse("invoices/list.html", {"request": request, "user": user, "invoices": invoices})

@router.get("/invoices/new", response_class=HTMLResponse)
async def new_invoice_form(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    clients = db.query(Client).filter(Client.user_id == str(user.id)).all()
    
    # Auto-generate invoice number
    today = date.today()
    year_prefix = f"INV-{today.year}-"
    last_invoice = db.query(Invoice).filter(Invoice.invoice_number.like(f"{year_prefix}%")).order_by(desc(Invoice.id)).first()
    
    if last_invoice:
        try:
            last_seq = int(last_invoice.invoice_number.split("-")[-1])
            new_seq = last_seq + 1
        except:
            new_seq = 1
    else:
        new_seq = 1
        
    next_invoice_number = f"{year_prefix}{new_seq:03d}"
    
    return templates.TemplateResponse("invoices/form.html", {
        "request": request, 
        "user": user, 
        "clients": clients,
        "next_invoice_number": next_invoice_number,
        "today": today
    })

@router.post("/invoices/new")
async def create_invoice(
    request: Request,
    client_id: int = Form(...),
    invoice_number: str = Form(...),
    issue_date: str = Form(...),
    due_date: str = Form(...),
    tax_rate: float = Form(0.0),
    currency: str = Form("USD"),
    notes: Optional[str] = Form(None),
    descriptions: List[str] = Form([]),
    quantities: List[float] = Form([]),
    unit_prices: List[float] = Form([]),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    # Verify client belongs to user
    client = db.query(Client).filter(Client.id == client_id, Client.user_id == str(user.id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    # Calculate totals
    subtotal = 0.0
    line_items_data = []
    
    # Handle line items
    # descriptions, quantities, unit_prices should have same length
    count = min(len(descriptions), len(quantities), len(unit_prices))
    
    new_invoice = Invoice(
        client_id=client_id,
        invoice_number=invoice_number,
        issue_date=datetime.datetime.strptime(issue_date, "%Y-%m-%d").date(),
        due_date=datetime.datetime.strptime(due_date, "%Y-%m-%d").date(),
        tax_rate=tax_rate,
        currency=currency,
        notes=notes,
        status="draft"
    )
    db.add(new_invoice)
    db.flush() # get ID
    
    for i in range(count):
        desc = descriptions[i]
        qty = quantities[i]
        price = unit_prices[i]
        if desc and qty > 0:
            amt = qty * price
            subtotal += amt
            li = LineItem(
                invoice_id=new_invoice.id,
                description=desc,
                quantity=qty,
                unit_price=price,
                amount=amt
            )
            db.add(li)
            
    new_invoice.subtotal = subtotal
    new_invoice.tax_amount = subtotal * (tax_rate / 100)
    new_invoice.total = subtotal + new_invoice.tax_amount
    
    db.commit()
    return RedirectResponse(url=f"/invoices/{new_invoice.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/invoices/{id}", response_class=HTMLResponse)
async def invoice_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    # Join with Client to ensure ownership
    invoice = db.query(Invoice).join(Client).filter(Invoice.id == id, Client.user_id == str(user.id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    return templates.TemplateResponse("invoices/detail.html", {"request": request, "user": user, "invoice": invoice})

@router.get("/invoices/{id}/edit", response_class=HTMLResponse)
async def edit_invoice_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    invoice = db.query(Invoice).join(Client).filter(Invoice.id == id, Client.user_id == str(user.id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    clients = db.query(Client).filter(Client.user_id == str(user.id)).all()
    
    return templates.TemplateResponse("invoices/form.html", {
        "request": request, 
        "user": user, 
        "invoice": invoice,
        "clients": clients
    })

@router.post("/invoices/{id}/edit")
async def update_invoice(
    request: Request,
    id: int,
    client_id: int = Form(...),
    invoice_number: str = Form(...),
    issue_date: str = Form(...),
    due_date: str = Form(...),
    tax_rate: float = Form(0.0),
    currency: str = Form("USD"),
    notes: Optional[str] = Form(None),
    descriptions: List[str] = Form([]),
    quantities: List[float] = Form([]),
    unit_prices: List[float] = Form([]),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    invoice = db.query(Invoice).join(Client).filter(Invoice.id == id, Client.user_id == str(user.id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")

    # Update fields
    invoice.client_id = client_id
    invoice.invoice_number = invoice_number
    invoice.issue_date = datetime.datetime.strptime(issue_date, "%Y-%m-%d").date()
    invoice.due_date = datetime.datetime.strptime(due_date, "%Y-%m-%d").date()
    invoice.tax_rate = tax_rate
    invoice.currency = currency
    invoice.notes = notes
    
    # Clear existing line items
    db.query(LineItem).filter(LineItem.invoice_id == id).delete()
    
    # Re-add line items
    subtotal = 0.0
    count = min(len(descriptions), len(quantities), len(unit_prices))
    
    for i in range(count):
        desc = descriptions[i]
        qty = quantities[i]
        price = unit_prices[i]
        if desc and qty > 0:
            amt = qty * price
            subtotal += amt
            li = LineItem(
                invoice_id=invoice.id,
                description=desc,
                quantity=qty,
                unit_price=price,
                amount=amt
            )
            db.add(li)
            
    invoice.subtotal = subtotal
    invoice.tax_amount = subtotal * (tax_rate / 100)
    invoice.total = subtotal + invoice.tax_amount
    
    db.commit()
    return RedirectResponse(url=f"/invoices/{id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/invoices/{id}/status")
async def update_invoice_status(
    request: Request,
    id: int,
    status_val: str = Form(...), # 'sent', 'paid', 'cancelled', etc.
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    invoice = db.query(Invoice).join(Client).filter(Invoice.id == id, Client.user_id == str(user.id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    if status_val in ["draft", "sent", "viewed", "paid", "overdue", "cancelled"]:
        invoice.status = status_val
        if status_val == 'paid':
            invoice.paid_date = date.today()
        elif status_val != 'paid' and invoice.paid_date:
            invoice.paid_date = None
            
        db.commit()
        
    return RedirectResponse(url=f"/invoices/{id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/invoices/{id}/delete")
async def delete_invoice(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    invoice = db.query(Invoice).join(Client).filter(Invoice.id == id, Client.user_id == str(user.id)).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Invoice not found")
        
    db.delete(invoice)
    db.commit()
    return RedirectResponse(url="/invoices", status_code=status.HTTP_303_SEE_OTHER)
