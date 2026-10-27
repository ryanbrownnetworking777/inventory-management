from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Literal, Optional
from datetime import date, datetime, timedelta
from pydantic import BaseModel, Field
from mock_data import inventory_items, orders, demand_forecasts, backlog_items, spending_summary, monthly_spending, category_spending, recent_transactions, purchase_orders

app = FastAPI(title="Factory Inventory Management System")

# Quarter mapping for date filtering
QUARTER_MAP = {
    'Q1-2025': ['2025-01', '2025-02', '2025-03'],
    'Q2-2025': ['2025-04', '2025-05', '2025-06'],
    'Q3-2025': ['2025-07', '2025-08', '2025-09'],
    'Q4-2025': ['2025-10', '2025-11', '2025-12']
}

def filter_by_month(items: list, month: Optional[str]) -> list:
    """Filter items by month/quarter based on order_date field"""
    if not month or month == 'all':
        return items

    if month.startswith('Q'):
        # Handle quarters
        if month in QUARTER_MAP:
            months = QUARTER_MAP[month]
            return [item for item in items if any(m in item.get('order_date', '') for m in months)]
    else:
        # Direct month match
        return [item for item in items if month in item.get('order_date', '')]

    return items

def apply_filters(items: list, warehouse: Optional[str] = None, category: Optional[str] = None,
                 status: Optional[str] = None) -> list:
    """Apply common filters to a list of items"""
    filtered = items

    if warehouse and warehouse != 'all':
        filtered = [item for item in filtered if item.get('warehouse') == warehouse]

    if category and category != 'all':
        filtered = [item for item in filtered if item.get('category', '').lower() == category.lower()]

    if status and status != 'all':
        filtered = [item for item in filtered if item.get('status', '').lower() == status.lower()]

    return filtered

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Data models
class InventoryItem(BaseModel):
    id: str
    sku: str
    name: str
    category: str
    warehouse: str
    quantity_on_hand: int
    reorder_point: int
    unit_cost: float
    location: str
    last_updated: str

class Order(BaseModel):
    id: str
    order_number: str
    customer: str
    items: List[dict]
    status: str
    order_date: str
    expected_delivery: str
    total_value: float
    actual_delivery: Optional[str] = None
    warehouse: Optional[str] = None
    category: Optional[str] = None

class DemandForecast(BaseModel):
    id: str
    item_sku: str
    item_name: str
    current_demand: int
    forecasted_demand: int
    trend: str
    period: str
    unit_cost: float
    lead_time_days: int

class BacklogItem(BaseModel):
    id: str
    order_id: str
    item_sku: str
    item_name: str
    quantity_needed: int
    quantity_available: int
    days_delayed: int
    priority: str
    has_purchase_order: Optional[bool] = False
    purchase_order_id: Optional[str] = None

class PurchaseOrder(BaseModel):
    id: str
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    status: str
    created_date: str
    notes: Optional[str] = None

class CreatePurchaseOrderRequest(BaseModel):
    backlog_item_id: str
    supplier_name: str
    quantity: int
    unit_cost: float
    expected_delivery_date: str
    notes: Optional[str] = None

class RestockRecommendation(BaseModel):
    item_sku: str
    item_name: str
    trend: str
    current_demand: int
    forecasted_demand: int
    quantity: int
    recommended_quantity: int
    partial: bool
    unit_cost: float
    subtotal: float
    lead_time_days: int

class RestockRecommendationResponse(BaseModel):
    items: List[RestockRecommendation]
    total_cost: float
    budget: float
    max_budget: float

class RestockOrderItem(BaseModel):
    item_sku: str
    item_name: str
    quantity: int
    unit_cost: float
    lead_time_days: int

class RestockOrderLine(BaseModel):
    item_sku: str
    quantity: int = Field(gt=0)

class CreateRestockOrderRequest(BaseModel):
    # Only SKU and quantity are trusted from the client; name, unit cost and lead time come from the forecast data
    items: List[RestockOrderLine]

class RestockOrder(BaseModel):
    id: str
    order_number: str
    items: List[RestockOrderItem]
    total_value: float
    status: str
    order_date: str
    expected_delivery: str
    lead_time_days: int

class Task(BaseModel):
    id: str
    title: str
    priority: str
    dueDate: str
    status: str

class CreateTaskRequest(BaseModel):
    title: str
    priority: Literal["high", "medium", "low"] = "medium"
    dueDate: str

# Submitted restock orders live in memory only, consistent with the rest of the app (no database)
restock_orders: List[dict] = []

# Tasks created through the API (the profile's built-in mock tasks live in the client)
tasks: List[dict] = []
# Monotonic counter so ids stay unique after deletions; "api-" prefix avoids clashing with the client's numeric mock task ids
task_id_counter = 0

def find_purchase_order(backlog_item_id: str) -> Optional[dict]:
    return next((po for po in purchase_orders if po["backlog_item_id"] == backlog_item_id), None)

def build_restock_candidates() -> List[dict]:
    """Items whose forecast exceeds current demand, largest demand growth first.
    The recommended quantity is the growth itself, so items with zero or negative growth are excluded."""
    candidates = []
    for forecast in demand_forecasts:
        growth = forecast["forecasted_demand"] - forecast["current_demand"]
        if growth <= 0:
            continue
        candidates.append({
            "item_sku": forecast["item_sku"],
            "item_name": forecast["item_name"],
            "trend": forecast["trend"],
            "current_demand": forecast["current_demand"],
            "forecasted_demand": forecast["forecasted_demand"],
            "quantity": growth,
            "recommended_quantity": growth,
            "partial": False,
            "unit_cost": forecast["unit_cost"],
            "subtotal": round(growth * forecast["unit_cost"], 2),
            "lead_time_days": forecast["lead_time_days"],
        })
    candidates.sort(key=lambda c: c["recommended_quantity"], reverse=True)
    return candidates

def to_cents(amount: float) -> int:
    return round(amount * 100)

def default_restock_budget(max_budget: float) -> float:
    """Half of the full restock cost, rounded down to the slider's $50 step."""
    return float(int(max_budget / 2 // 50) * 50)

def parse_iso_date(value: str) -> date:
    """Accept YYYY-MM-DD or a full ISO datetime; reject anything with trailing garbage."""
    try:
        return date.fromisoformat(value)
    except ValueError:
        return datetime.fromisoformat(value).date()

# API endpoints
@app.get("/")
def root():
    return {"message": "Factory Inventory Management System API", "version": "1.0.0"}

@app.get("/api/inventory", response_model=List[InventoryItem])
def get_inventory(
    warehouse: Optional[str] = None,
    category: Optional[str] = None
):
    """Get all inventory items with optional filtering"""
    return apply_filters(inventory_items, warehouse, category)

@app.get("/api/inventory/{item_id}", response_model=InventoryItem)
def get_inventory_item(item_id: str):
    """Get a specific inventory item"""
    item = next((item for item in inventory_items if item["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item

@app.get("/api/orders", response_model=List[Order])
def get_orders(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get all orders with optional filtering"""
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)
    return filtered_orders

@app.get("/api/orders/{order_id}", response_model=Order)
def get_order(order_id: str):
    """Get a specific order"""
    order = next((order for order in orders if order["id"] == order_id), None)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

@app.get("/api/demand", response_model=List[DemandForecast])
def get_demand_forecasts():
    """Get demand forecasts"""
    return demand_forecasts

@app.get("/api/backlog", response_model=List[BacklogItem])
def get_backlog():
    """Get backlog items with purchase order status"""
    # Add has_purchase_order flag to each backlog item
    result = []
    for item in backlog_items:
        item_dict = dict(item)
        # Check if this backlog item has a purchase order
        po = find_purchase_order(item["id"])
        item_dict["has_purchase_order"] = po is not None
        item_dict["purchase_order_id"] = po["id"] if po else None
        result.append(item_dict)
    return result

@app.get("/api/dashboard/summary")
def get_dashboard_summary(
    warehouse: Optional[str] = None,
    category: Optional[str] = None,
    status: Optional[str] = None,
    month: Optional[str] = None
):
    """Get summary statistics for dashboard with optional filtering"""
    # Filter inventory
    filtered_inventory = apply_filters(inventory_items, warehouse, category)

    # Filter orders
    filtered_orders = apply_filters(orders, warehouse, category, status)
    filtered_orders = filter_by_month(filtered_orders, month)

    total_inventory_value = sum(item["quantity_on_hand"] * item["unit_cost"] for item in filtered_inventory)
    low_stock_items = len([item for item in filtered_inventory if item["quantity_on_hand"] <= item["reorder_point"]])
    pending_orders = len([order for order in filtered_orders if order["status"] in ["Processing", "Backordered"]])
    total_backlog_items = len(backlog_items)

    return {
        "total_inventory_value": round(total_inventory_value, 2),
        "low_stock_items": low_stock_items,
        "pending_orders": pending_orders,
        "total_backlog_items": total_backlog_items,
        "total_orders_value": sum(order["total_value"] for order in filtered_orders)
    }

@app.get("/api/spending/summary")
def get_spending_summary():
    """Get spending summary statistics"""
    return spending_summary

@app.get("/api/spending/monthly")
def get_monthly_spending():
    """Get monthly spending breakdown"""
    return monthly_spending

@app.get("/api/spending/categories")
def get_category_spending():
    """Get spending by category"""
    return category_spending

@app.get("/api/spending/transactions")
def get_recent_transactions():
    """Get recent transactions"""
    return recent_transactions

@app.get("/api/reports/quarterly")
def get_quarterly_reports():
    """Get quarterly performance reports"""
    # Calculate quarterly statistics from orders
    quarters = {}

    for order in orders:
        order_date = order.get('order_date', '')
        # Determine quarter
        if '2025-01' in order_date or '2025-02' in order_date or '2025-03' in order_date:
            quarter = 'Q1-2025'
        elif '2025-04' in order_date or '2025-05' in order_date or '2025-06' in order_date:
            quarter = 'Q2-2025'
        elif '2025-07' in order_date or '2025-08' in order_date or '2025-09' in order_date:
            quarter = 'Q3-2025'
        elif '2025-10' in order_date or '2025-11' in order_date or '2025-12' in order_date:
            quarter = 'Q4-2025'
        else:
            continue

        if quarter not in quarters:
            quarters[quarter] = {
                'quarter': quarter,
                'total_orders': 0,
                'total_revenue': 0,
                'delivered_orders': 0,
                'avg_order_value': 0
            }

        quarters[quarter]['total_orders'] += 1
        quarters[quarter]['total_revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            quarters[quarter]['delivered_orders'] += 1

    # Calculate averages and fulfillment rate
    result = []
    for q, data in quarters.items():
        if data['total_orders'] > 0:
            data['avg_order_value'] = round(data['total_revenue'] / data['total_orders'], 2)
            data['fulfillment_rate'] = round((data['delivered_orders'] / data['total_orders']) * 100, 1)
        result.append(data)

    # Sort by quarter
    result.sort(key=lambda x: x['quarter'])
    return result

@app.get("/api/reports/monthly-trends")
def get_monthly_trends():
    """Get month-over-month trends"""
    months = {}

    for order in orders:
        order_date = order.get('order_date', '')
        if not order_date:
            continue

        # Extract month (format: YYYY-MM-DD)
        month = order_date[:7]  # Gets YYYY-MM

        if month not in months:
            months[month] = {
                'month': month,
                'order_count': 0,
                'revenue': 0,
                'delivered_count': 0
            }

        months[month]['order_count'] += 1
        months[month]['revenue'] += order.get('total_value', 0)
        if order.get('status') == 'Delivered':
            months[month]['delivered_count'] += 1

    # Convert to list and sort
    result = list(months.values())
    result.sort(key=lambda x: x['month'])
    return result

@app.get("/api/restocking/recommendations", response_model=RestockRecommendationResponse)
def get_restock_recommendations(budget: Optional[float] = None):
    """Recommend restock items from the demand forecast that fit within the budget.
    Omitting budget uses a default (half the full restock cost) so the client needs one request on load."""
    candidates = build_restock_candidates()
    max_budget = round(sum(c["subtotal"] for c in candidates), 2)
    if budget is None:
        budget = default_restock_budget(max_budget)
    if budget < 0:
        raise HTTPException(status_code=400, detail="Budget must be non-negative")
    # Priority-first: fill each item in growth order, ordering as many units as the remaining budget allows,
    # so the highest-growth item is never skipped just because its full quantity doesn't fit. Money is in cents to avoid float drift.
    selected = []
    remaining_cents = to_cents(budget)
    for candidate in candidates:
        unit_cents = to_cents(candidate["unit_cost"])
        quantity = min(candidate["recommended_quantity"], remaining_cents // unit_cents)
        if quantity <= 0:
            continue
        remaining_cents -= quantity * unit_cents
        selected.append({
            **candidate,
            "quantity": quantity,
            "partial": quantity < candidate["recommended_quantity"],
            "subtotal": quantity * unit_cents / 100,
        })
    return {
        "items": selected,
        "total_cost": sum(to_cents(c["subtotal"]) for c in selected) / 100,
        "budget": budget,
        "max_budget": max_budget,
    }

@app.get("/api/restocking/orders", response_model=List[RestockOrder])
def get_restock_orders():
    """Get submitted restock orders, newest first"""
    return list(reversed(restock_orders))

@app.post("/api/restocking/orders", response_model=RestockOrder, status_code=201)
def create_restock_order(request: CreateRestockOrderRequest):
    """Submit a restock order; delivery is driven by the slowest item's lead time"""
    if not request.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")
    skus = [line.item_sku for line in request.items]
    if len(set(skus)) != len(skus):
        raise HTTPException(status_code=400, detail="Each SKU may appear only once per order")
    forecasts_by_sku = {f["item_sku"]: f for f in demand_forecasts}
    unknown = [sku for sku in skus if sku not in forecasts_by_sku]
    if unknown:
        raise HTTPException(status_code=400, detail=f"Unknown SKU(s): {', '.join(unknown)}")
    items = [
        {
            "item_sku": line.item_sku,
            "item_name": forecasts_by_sku[line.item_sku]["item_name"],
            "quantity": line.quantity,
            "unit_cost": forecasts_by_sku[line.item_sku]["unit_cost"],
            "lead_time_days": forecasts_by_sku[line.item_sku]["lead_time_days"],
        }
        for line in request.items
    ]
    order_date = datetime.now().replace(microsecond=0)
    lead_time_days = max(item["lead_time_days"] for item in items)
    order_id = str(len(restock_orders) + 1)
    order = {
        "id": order_id,
        "order_number": f"RST-{int(order_id):04d}",
        "items": items,
        "total_value": sum(item["quantity"] * to_cents(item["unit_cost"]) for item in items) / 100,
        "status": "Submitted",
        "order_date": order_date.isoformat(),
        "expected_delivery": (order_date + timedelta(days=lead_time_days)).isoformat(),
        "lead_time_days": lead_time_days,
    }
    restock_orders.append(order)
    return order

@app.get("/api/tasks", response_model=List[Task])
def get_tasks():
    """Get tasks created through the API, newest first"""
    return list(reversed(tasks))

@app.post("/api/tasks", response_model=Task, status_code=201)
def create_task(request: CreateTaskRequest):
    """Create a pending task"""
    global task_id_counter
    title = request.title.strip()
    if not title:
        raise HTTPException(status_code=400, detail="Task title is required")
    try:
        date.fromisoformat(request.dueDate)
    except ValueError:
        raise HTTPException(status_code=400, detail="dueDate must be an ISO date (YYYY-MM-DD)")
    task_id_counter += 1
    task = {
        "id": f"api-{task_id_counter}",
        "title": title,
        "priority": request.priority,
        "dueDate": request.dueDate,
        "status": "pending",
    }
    tasks.append(task)
    return task

@app.patch("/api/tasks/{task_id}", response_model=Task)
def toggle_task(task_id: str):
    """Toggle a task between pending and completed"""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    task["status"] = "completed" if task["status"] == "pending" else "pending"
    return task

@app.delete("/api/tasks/{task_id}")
def delete_task(task_id: str):
    """Delete a task"""
    task = next((t for t in tasks if t["id"] == task_id), None)
    if not task:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
    tasks.remove(task)
    return {"deleted": task_id}

@app.post("/api/purchase-orders", response_model=PurchaseOrder, status_code=201)
def create_purchase_order(request: CreatePurchaseOrderRequest):
    """Create a purchase order for a backlog item (one PO per backlog item)"""
    if not any(item["id"] == request.backlog_item_id for item in backlog_items):
        raise HTTPException(status_code=404, detail=f"Backlog item {request.backlog_item_id} not found")
    if find_purchase_order(request.backlog_item_id):
        raise HTTPException(status_code=409, detail="A purchase order already exists for this backlog item")
    if not request.supplier_name.strip():
        raise HTTPException(status_code=400, detail="Supplier name is required")
    if request.quantity <= 0 or request.unit_cost <= 0:
        raise HTTPException(status_code=400, detail="Quantity and unit cost must be positive")
    try:
        delivery_date = parse_iso_date(request.expected_delivery_date)
    except ValueError:
        raise HTTPException(status_code=400, detail="expected_delivery_date must be an ISO date (YYYY-MM-DD)")
    if delivery_date < date.today():
        raise HTTPException(status_code=400, detail="expected_delivery_date cannot be in the past")
    po = {
        "id": f"PO-{len(purchase_orders) + 1:04d}",
        "backlog_item_id": request.backlog_item_id,
        "supplier_name": request.supplier_name.strip(),
        "quantity": request.quantity,
        "unit_cost": request.unit_cost,
        "expected_delivery_date": request.expected_delivery_date,
        "status": "Pending",
        "created_date": datetime.now().replace(microsecond=0).isoformat(),
        "notes": request.notes,
    }
    purchase_orders.append(po)
    return po

@app.get("/api/purchase-orders/{backlog_item_id}", response_model=PurchaseOrder)
def get_purchase_order_by_backlog_item(backlog_item_id: str):
    """Get the purchase order for a backlog item"""
    po = find_purchase_order(backlog_item_id)
    if not po:
        raise HTTPException(status_code=404, detail=f"No purchase order for backlog item {backlog_item_id}")
    return po

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
