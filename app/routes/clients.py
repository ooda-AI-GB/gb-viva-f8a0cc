from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import desc, func
from app.database import get_db
from app.models import Client, Invoice
from app.routes import get_current_user, get_active_subscription
from typing import Any, Optional

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/clients", response_class=HTMLResponse)
async def list_clients(
    request: Request,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    clients = db.query(Client).filter(Client.user_id == str(user.id)).order_by(Client.name).all()
    
    # Calculate stats for each client
    for client in clients:
        invoices = db.query(Invoice).filter(Invoice.client_id == client.id).all()
        client.total_invoiced = sum(inv.total for inv in invoices)
        client.total_paid = sum(inv.total for inv in invoices if inv.status == 'paid')
        client.outstanding_balance = client.total_invoiced - client.total_paid
        
    return templates.TemplateResponse("clients/list.html", {"request": request, "user": user, "clients": clients})

@router.get("/clients/new", response_class=HTMLResponse)
async def new_client_form(
    request: Request,
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    return templates.TemplateResponse("clients/form.html", {"request": request, "user": user})

@router.post("/clients/new")
async def create_client(
    request: Request,
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    tax_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    new_client = Client(
        user_id=str(user.id),
        name=name,
        email=email,
        phone=phone,
        address=address,
        city=city,
        country=country,
        tax_id=tax_id,
        notes=notes
    )
    db.add(new_client)
    db.commit()
    db.refresh(new_client)
    return RedirectResponse(url=f"/clients/{new_client.id}", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/clients/{id}", response_class=HTMLResponse)
async def client_detail(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    client = db.query(Client).filter(Client.id == id, Client.user_id == str(user.id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    invoices = db.query(Invoice).filter(Invoice.client_id == client.id).order_by(desc(Invoice.issue_date)).all()
    
    total_revenue = sum(inv.total for inv in invoices if inv.status == 'paid')
    
    return templates.TemplateResponse("clients/detail.html", {
        "request": request, 
        "user": user, 
        "client": client, 
        "invoices": invoices,
        "total_revenue": total_revenue
    })

@router.get("/clients/{id}/edit", response_class=HTMLResponse)
async def edit_client_form(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    client = db.query(Client).filter(Client.id == id, Client.user_id == str(user.id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    return templates.TemplateResponse("clients/form.html", {"request": request, "user": user, "client": client})

@router.post("/clients/{id}/edit")
async def update_client(
    request: Request,
    id: int,
    name: str = Form(...),
    email: str = Form(...),
    phone: Optional[str] = Form(None),
    address: Optional[str] = Form(None),
    city: Optional[str] = Form(None),
    country: Optional[str] = Form(None),
    tax_id: Optional[str] = Form(None),
    notes: Optional[str] = Form(None),
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    client = db.query(Client).filter(Client.id == id, Client.user_id == str(user.id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
        
    client.name = name
    client.email = email
    client.phone = phone
    client.address = address
    client.city = city
    client.country = country
    client.tax_id = tax_id
    client.notes = notes
    
    db.commit()
    return RedirectResponse(url=f"/clients/{id}", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/clients/{id}/delete")
async def delete_client(
    request: Request,
    id: int,
    db: Session = Depends(get_db),
    user: Any = Depends(get_current_user),
    sub: Any = Depends(get_active_subscription)
):
    client = db.query(Client).filter(Client.id == id, Client.user_id == str(user.id)).first()
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    
    # Invoices will be deleted due to cascade if configured, but let's trust models.py
    # models.py: invoices = relationship(..., cascade="all, delete-orphan")
    
    db.delete(client)
    db.commit()
    return RedirectResponse(url="/clients", status_code=status.HTTP_303_SEE_OTHER)
