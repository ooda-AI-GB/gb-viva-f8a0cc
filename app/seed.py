from sqlalchemy.orm import Session
from app.models import Client, Invoice, LineItem, Expense, FinancialInsight
import datetime

def seed_data(db: Session, user_id: str):
    # Check if clients exist for this user
    if db.query(Client).filter(Client.user_id == user_id).first():
        return

    clients_data = [
        {"name": "Acme Corporation", "email": "billing@acme.com", "phone": "+1-555-0201", "address": "123 Business Ave", "city": "San Francisco", "country": "US", "tax_id": "US-94-1234567"},
        {"name": "TechStart Inc", "email": "ap@techstart.io", "phone": "+1-555-0202", "address": "456 Innovation Blvd", "city": "Austin", "country": "US", "tax_id": "US-73-7654321"},
        {"name": "Global Retail Group", "email": "finance@globalretail.com", "phone": "+44-20-5550303", "address": "78 Commerce St", "city": "London", "country": "UK", "tax_id": "GB-123456789"},
        {"name": "Nordic Design Studio", "email": "invoices@nordicdesign.se", "phone": "+46-8-5550404", "address": "15 Kreativ Gatan", "city": "Stockholm", "country": "SE", "tax_id": "SE-559012345601"},
        {"name": "Marina Bay Consulting", "email": "accounts@marinabay.sg", "phone": "+65-5550505", "address": "88 Raffles Place", "city": "Singapore", "country": "SG", "tax_id": "SG-201912345K"},
        {"name": "Cloudworks Solutions", "email": "billing@cloudworks.dev", "phone": "+1-555-0606", "address": "321 Cloud Lane", "city": "Seattle", "country": "US"}
    ]

    client_map = {}
    for i, data in enumerate(clients_data):
        client = Client(user_id=user_id, **data)
        db.add(client)
        db.flush()
        client_map[i + 1] = client

    invoices_data = [
        {"client_id": 1, "invoice_number": "INV-2026-001", "status": "paid", "issue_date": "2026-01-05", "due_date": "2026-01-20", "subtotal": 12500.00, "tax_rate": 10.0, "tax_amount": 1250.00, "total": 13750.00, "currency": "USD", "notes": "Website redesign - Phase 1", "paid_date": "2026-01-18"},
        {"client_id": 1, "invoice_number": "INV-2026-002", "status": "paid", "issue_date": "2026-01-20", "due_date": "2026-02-05", "subtotal": 8500.00, "tax_rate": 10.0, "tax_amount": 850.00, "total": 9350.00, "currency": "USD", "notes": "Website redesign - Phase 2", "paid_date": "2026-02-03"},
        {"client_id": 2, "invoice_number": "INV-2026-003", "status": "sent", "issue_date": "2026-02-01", "due_date": "2026-02-15", "subtotal": 15000.00, "tax_rate": 0.0, "tax_amount": 0.00, "total": 15000.00, "currency": "USD", "notes": "Mobile app development - Sprint 1"},
        {"client_id": 3, "invoice_number": "INV-2026-004", "status": "overdue", "issue_date": "2026-01-10", "due_date": "2026-01-25", "subtotal": 22000.00, "tax_rate": 20.0, "tax_amount": 4400.00, "total": 26400.00, "currency": "GBP", "notes": "E-commerce platform integration"},
        {"client_id": 4, "invoice_number": "INV-2026-005", "status": "draft", "issue_date": "2026-02-10", "due_date": "2026-02-25", "subtotal": 7500.00, "tax_rate": 25.0, "tax_amount": 1875.00, "total": 9375.00, "currency": "SEK", "notes": "Brand identity refresh"},
        {"client_id": 5, "invoice_number": "INV-2026-006", "status": "sent", "issue_date": "2026-02-08", "due_date": "2026-02-22", "subtotal": 18000.00, "tax_rate": 8.0, "tax_amount": 1440.00, "total": 19440.00, "currency": "SGD", "notes": "AI strategy consulting - February"},
        {"client_id": 6, "invoice_number": "INV-2026-007", "status": "paid", "issue_date": "2026-01-15", "due_date": "2026-01-30", "subtotal": 5000.00, "tax_rate": 10.0, "tax_amount": 500.00, "total": 5500.00, "currency": "USD", "notes": "Cloud migration assessment", "paid_date": "2026-01-28"},
        {"client_id": 2, "invoice_number": "INV-2026-008", "status": "viewed", "issue_date": "2026-02-12", "due_date": "2026-02-26", "subtotal": 15000.00, "tax_rate": 0.0, "tax_amount": 0.00, "total": 15000.00, "currency": "USD", "notes": "Mobile app development - Sprint 2"}
    ]

    invoice_map = {}
    for i, data in enumerate(invoices_data):
        cid = data.pop("client_id")
        data["client_id"] = client_map[cid].id
        data["issue_date"] = datetime.datetime.strptime(data["issue_date"], "%Y-%m-%d").date()
        data["due_date"] = datetime.datetime.strptime(data["due_date"], "%Y-%m-%d").date()
        if "paid_date" in data:
            data["paid_date"] = datetime.datetime.strptime(data["paid_date"], "%Y-%m-%d").date()
        
        invoice = Invoice(**data)
        db.add(invoice)
        db.flush()
        invoice_map[i + 1] = invoice

    line_items_data = [
        {"invoice_id": 1, "description": "UX Research & Discovery", "quantity": 40, "unit_price": 150.00, "amount": 6000.00},
        {"invoice_id": 1, "description": "UI Design - Homepage & Landing Pages", "quantity": 25, "unit_price": 175.00, "amount": 4375.00},
        {"invoice_id": 1, "description": "Design System Documentation", "quantity": 12.5, "unit_price": 170.00, "amount": 2125.00},
        {"invoice_id": 2, "description": "Frontend Development", "quantity": 50, "unit_price": 170.00, "amount": 8500.00},
        {"invoice_id": 3, "description": "React Native Development", "quantity": 60, "unit_price": 175.00, "amount": 10500.00},
        {"invoice_id": 3, "description": "API Integration", "quantity": 30, "unit_price": 150.00, "amount": 4500.00},
        {"invoice_id": 4, "description": "Shopify Integration", "quantity": 80, "unit_price": 160.00, "amount": 12800.00},
        {"invoice_id": 4, "description": "Payment Gateway Setup", "quantity": 40, "unit_price": 155.00, "amount": 6200.00},
        {"invoice_id": 4, "description": "Data Migration Scripts", "quantity": 20, "unit_price": 150.00, "amount": 3000.00},
        {"invoice_id": 5, "description": "Brand Strategy Workshop", "quantity": 8, "unit_price": 200.00, "amount": 1600.00},
        {"invoice_id": 5, "description": "Logo & Visual Identity Design", "quantity": 30, "unit_price": 175.00, "amount": 5250.00},
        {"invoice_id": 5, "description": "Brand Guidelines Document", "quantity": 5, "unit_price": 130.00, "amount": 650.00},
        {"invoice_id": 6, "description": "AI Strategy Assessment", "quantity": 40, "unit_price": 250.00, "amount": 10000.00},
        {"invoice_id": 6, "description": "Implementation Roadmap", "quantity": 20, "unit_price": 250.00, "amount": 5000.00},
        {"invoice_id": 6, "description": "Team Training Sessions", "quantity": 12, "unit_price": 250.00, "amount": 3000.00},
        {"invoice_id": 7, "description": "Cloud Architecture Review", "quantity": 20, "unit_price": 175.00, "amount": 3500.00},
        {"invoice_id": 7, "description": "Migration Plan Document", "quantity": 10, "unit_price": 150.00, "amount": 1500.00},
        {"invoice_id": 8, "description": "React Native Development - Sprint 2", "quantity": 60, "unit_price": 175.00, "amount": 10500.00},
        {"invoice_id": 8, "description": "Push Notification System", "quantity": 30, "unit_price": 150.00, "amount": 4500.00}
    ]

    for data in line_items_data:
        iid = data.pop("invoice_id")
        data["invoice_id"] = invoice_map[iid].id
        db.add(LineItem(**data))

    expenses_data = [
        {"category": "software", "description": "GitHub Team Plan", "amount": 44.00, "currency": "USD", "date": "2026-01-01", "vendor": "GitHub", "tax_deductible": True},
        {"category": "software", "description": "Figma Professional", "amount": 15.00, "currency": "USD", "date": "2026-01-01", "vendor": "Figma", "tax_deductible": True},
        {"category": "software", "description": "AWS Monthly", "amount": 287.50, "currency": "USD", "date": "2026-01-31", "vendor": "Amazon Web Services", "tax_deductible": True},
        {"category": "hardware", "description": "Mechanical Keyboard", "amount": 189.00, "currency": "USD", "date": "2026-01-15", "vendor": "Keychron", "tax_deductible": True},
        {"category": "travel", "description": "Client meeting - Flight SFO to AUS", "amount": 385.00, "currency": "USD", "date": "2026-01-22", "vendor": "United Airlines", "tax_deductible": True},
        {"category": "travel", "description": "Hotel 2 nights - Austin", "amount": 420.00, "currency": "USD", "date": "2026-01-22", "vendor": "Hilton", "tax_deductible": True},
        {"category": "marketing", "description": "LinkedIn Ads - January", "amount": 500.00, "currency": "USD", "date": "2026-01-31", "vendor": "LinkedIn", "tax_deductible": True},
        {"category": "professional", "description": "Accounting services Q4", "amount": 750.00, "currency": "USD", "date": "2026-01-10", "vendor": "Smith & Associates CPA", "tax_deductible": True},
        {"category": "office", "description": "Coworking space February", "amount": 350.00, "currency": "USD", "date": "2026-02-01", "vendor": "WeWork", "tax_deductible": True},
        {"category": "software", "description": "Anthropic API usage", "amount": 200.00, "currency": "USD", "date": "2026-02-01", "vendor": "Anthropic", "tax_deductible": True}
    ]

    for data in expenses_data:
        data["date"] = datetime.datetime.strptime(data["date"], "%Y-%m-%d").date()
        db.add(Expense(user_id=user_id, **data))

    insights_data = [
        {"insight_type": "revenue_forecast", "content": "REVENUE TREND: Q1 2026 is tracking strong at $89,815 invoiced across 8 invoices. Based on current pipeline: $15,000 pending from TechStart (Sprint 1), $19,440 from Marina Bay Consulting, and $9,375 draft for Nordic Design. If all outstanding invoices are collected, Q1 revenue will reach $89,815. RISK: Global Retail Group invoice ($26,400 GBP) is overdue by 21 days — recommend immediate follow-up. Cash collection rate: 72% within terms.", "model_used": "seed_data", "requested_by": "system"},
        {"insight_type": "expense_analysis", "content": "EXPENSE BREAKDOWN (Jan-Feb 2026): Total expenses $3,140.50. Software subscriptions: $546.50 (17%). Travel: $805.00 (26%). Marketing: $500.00 (16%). Professional services: $750.00 (24%). Hardware: $189.00 (6%). Office: $350.00 (11%). 100% of expenses are tax-deductible. RECOMMENDATION: Software costs are well-controlled. Travel expenses are high relative to revenue — consider video calls for routine client meetings.", "model_used": "seed_data", "requested_by": "system"}
    ]

    for data in insights_data:
        if data.get("requested_by") == "system":
            data["requested_by"] = str(user_id)
        db.add(FinancialInsight(**data))

    db.commit()
