from fastapi import APIRouter, Depends, Request, status, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
import app.routes as routes_module
from app.routes import get_current_user
from typing import Any
import os

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/pricing", response_class=HTMLResponse)
async def pricing_page(request: Request):
    # Public page, no auth required, but we can try to get user to show logged in state in nav
    # But get_current_user raises HTTPException if not authenticated?
    # Usually dependencies raise errors.
    # So we pass user=None. The base template handles user check via request.state or similar if available, 
    # but here we just pass None for now.
    return templates.TemplateResponse("billing/pricing.html", {"request": request, "user": None})

@router.post("/subscribe")
async def subscribe(request: Request, user: Any = Depends(get_current_user)):
    if not routes_module.create_checkout:
        raise HTTPException(status_code=500, detail="Billing not configured")
        
    price_id = os.environ.get("STRIPE_PRICE_ID")
    if not price_id:
        # Fallback for dev/test if allowed, but instructions say "ALWAYS read STRIPE_PRICE_ID"
        # I'll raise error if missing to be safe
        raise HTTPException(status_code=500, detail="STRIPE_PRICE_ID not configured")

    try:
        # Call create_checkout (synchronous wrapper from viv-pay usually)
        url = routes_module.create_checkout(user_id=user.id, email=user.email, price_id=price_id)
        return RedirectResponse(url=url, status_code=status.HTTP_303_SEE_OTHER)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Checkout failed: {str(e)[:200]}")
