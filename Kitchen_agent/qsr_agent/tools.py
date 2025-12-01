
# import json
# import os
# import datetime
# import pandas as pd

# # Base path to project directory
# BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # blogger_agent root
# # DATA_DIR = os.path.join(BASE_DIR, "data")
# DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# # ----------------------------------------------------------
# # ORDER MANAGEMENT TOOLS
# # ----------------------------------------------------------

# def get_order_details(order_id: str) -> dict:
#     """Fetch order details from orders.json."""
#     with open(os.path.join(DATA_DIR, "orders.json"), "r") as f:
#         orders = json.load(f)
#     for order in orders:
#         if order["order_id"] == order_id:
#             return order
#     return {}  # empty if not found

# def update_order_status(order_id: str, status: str) -> dict:
#     """Update order status."""
#     with open(os.path.join(DATA_DIR, "orders.json"), "r") as f:
#         orders = json.load(f)

#     updated = False
#     for order in orders:
#         if order["order_id"] == order_id:
#             order["status"] = status
#             updated = True
#             break

#     with open(os.path.join(DATA_DIR, "orders.json"), "w") as f:
#         json.dump(orders, f, indent=2)

#     return {"updated": updated, "order_id": order_id, "new_status": status}

# def fetch_pending_orders() -> dict:
#     """Return all orders that are not completed."""
#     with open(os.path.join(DATA_DIR, "orders.json"), "r") as f:
#         orders = json.load(f)

#     pending = [o for o in orders if o["status"] != "completed"]
#     return {"pending_orders": pending}

# # ----------------------------------------------------------
# # INVENTORY TOOLS
# # ----------------------------------------------------------

# def fetch_inventory() -> dict:
#     """Load the current inventory."""
#     with open(os.path.join(DATA_DIR, "inventory.json"), "r") as f:
#         return json.load(f)

# def update_inventory_changes(item: str, qty: int) -> dict:
#     """Deduct or add stock."""
#     with open(os.path.join(DATA_DIR, "inventory.json"), "r") as f:
#         inventory = json.load(f)

#     inventory[item] = max(0, inventory.get(item, 0) + qty)

#     with open(os.path.join(DATA_DIR, "inventory.json"), "w") as f:
#         json.dump(inventory, f, indent=2)

#     return {"item": item, "updated_qty": inventory[item]}

# def get_ingredient_requirements(order_id: str) -> dict:
#     """Return ingredient list for the order."""
#     with open(os.path.join(DATA_DIR, "recipes.json"), "r") as f:
#         recipes = json.load(f)
#     order = get_order_details(order_id)
#     recipe_id = order.get("recipe")
#     return recipes.get(recipe_id, {}) if recipe_id else {}

# def trigger_low_stock_alert(item: str) -> dict:
#     """Triggered when any item is below threshold."""
#     return {"alert": True, "item": item, "message": "Low stock detected"}

# # ----------------------------------------------------------
# # LOYALTY TOOLS
# # ----------------------------------------------------------

# def fetch_loyalty_profile(user_id: str) -> dict:
#     with open(os.path.join(DATA_DIR, "loyalty.json"), "r") as f:
#         profiles = json.load(f)
#     return profiles.get(user_id, {})

# def update_loyalty_points(user_id: str, points: int) -> dict:
#     with open(os.path.join(DATA_DIR, "loyalty.json"), "r") as f:
#         profiles = json.load(f)
#     profiles[user_id] = profiles.get(user_id, 0) + points
#     with open(os.path.join(DATA_DIR, "loyalty.json"), "w") as f:
#         json.dump(profiles, f, indent=2)
#     return {"user": user_id, "points": profiles[user_id]}

# # ----------------------------------------------------------
# # FEEDBACK TOOLS
# # ----------------------------------------------------------

# def save_feedback(user_id: str, feedback: str) -> dict:
#     timestamp = datetime.datetime.now().isoformat()
#     feedback_file = os.path.join(DATA_DIR, "feedback.json")
#     with open(feedback_file, "r") as f:
#         fb = json.load(f)
#     fb.append({"user": user_id, "feedback": feedback, "time": timestamp})
#     with open(feedback_file, "w") as f:
#         json.dump(fb, f, indent=2)
#     return {"saved": True}

# def load_feedback_history() -> dict:
#     with open(os.path.join(DATA_DIR, "feedback.json"), "r") as f:
#         return json.load(f)

# def analyze_feedback_sentiment(text: str) -> dict:
#     """Mock sentiment tool."""
#     score = 1 if "good" in text.lower() else -1
#     return {"sentiment_score": score}

# # ----------------------------------------------------------
# # SYSTEM TOOLS
# # ----------------------------------------------------------

# def send_notification(msg: str, to: str) -> dict:
#     return {"sent": True, "message": msg, "to": to}

# def save_system_logs(event: str) -> dict:
#     with open(os.path.join(DATA_DIR, "system_logs.txt"), "a") as f:
#         f.write(event + "\n")
#     return {"logged": True}

# def message_bus(sender: str, receiver: str, payload: dict) -> dict:
#     return {"from": sender, "to": receiver, "payload": payload}


# def run_prophet_forecast(periods: int = 7) -> dict:
#     """
#     Runs a time-series forecast using internal sales history data.
    
#     Parameters:
#         periods (int): Future days to forecast. Default is 7.
#     """
#     # 1. Load data internally (Solving the Agent asking for data)
#     sales_path = os.path.join(DATA_DIR, "sales_history.json")
    
#     if not os.path.exists(sales_path):
#         return {"error": "sales_history.json not found in data directory."}
        
#     try:
#         with open(sales_path, "r") as f:
#             data = json.load(f)
#     except Exception as e:
#         return {"error": f"Failed to load sales history: {e}"}

#     # 2. Run Logic (Same as before)
#     try:
#         df = pd.DataFrame(data)
#         df["ds"] = pd.to_datetime(df["ds"])
#     except Exception as e:
#         return {"error": f"Invalid input format in file: {e}"}

#     df = df.sort_values("ds")
#     if len(df) < 2:
#         return {"error": "Not enough data points to forecast."}

#     last_value = df["y"].iloc[-1]
#     second_last_value = df["y"].iloc[-2]
#     daily_change = last_value - second_last_value
#     last_date = df["ds"].iloc[-1]

#     forecast_list = []
#     current_value = last_value
#     for i in range(1, periods + 1):
#         next_date = last_date + pd.Timedelta(days=i)
#         current_value += daily_change
#         forecast_list.append({"ds": next_date.strftime("%Y-%m-%d"), "yhat": float(current_value)})

#     return {"forecast": forecast_list}


# blogger_agent/tools.py

import json
import os
import datetime
import uuid  # <--- Added for ID generation
import pandas as pd

# Base path to project directory
BASE_DIR = os.path.dirname(os.path.dirname(__file__))  # blogger_agent root
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


# ==========================================================
# 1. RECEPTION / MENU TOOLS (New for Aura)
# ==========================================================

def get_menu() -> dict:
    """
    Fetches the menu items from the database.
    Used by the Reception Agent to show options to the user.
    """
    menu_path = os.path.join(DATA_DIR, "menu.json")
    if not os.path.exists(menu_path):
        return {"error": "Menu file (menu.json) not found in data directory."}
        
    try:
        with open(menu_path, "r") as f:
            return json.load(f)
    except Exception as e:
        return {"error": f"Failed to load menu: {e}"}


def save_new_order(
    items: str,  
    eta: str,
    table_number: int = None,
    num_people: int = None,
    customer_name: str = "Guest"
) -> dict:
    """
    Generates IDs, creates a structured order, saves it to orders.json, 
    and returns the order object for the pipeline.
    
    Parameters:
      items: List of dicts like [{"name": "Burger", "quantity": 1, "addons": []}]
      delivery_mode: "dining" or "takeaway"
      eta: String (e.g., "10 mins", "now")
    """
    # 1. Generate IDs
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    customer_id = f"CUST-{uuid.uuid4().hex[:6].upper()}"
    
    # 2. Build the Order Object
    new_order = {
        "order_id": order_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "table": table_number,
        "num_people": num_people,
        "time": datetime.datetime.now().isoformat(),
        "delivery_mode": delivery_mode,
        "estimated_arrival": eta,
        "status": "QUEUED",
        "loyalty_points_awarded": 0,
        "items": []
    }

    # 3. Process Items (Try to map to IDs from menu.json if possible)
    menu = get_menu()
    flat_menu = {}
    if "error" not in menu:
        for category in menu.values():
            if isinstance(category, list):
                for m_item in category:
                    flat_menu[m_item.get('name', '').lower()] = m_item.get('id')

    for item in items:
        item_name = item.get("name", "Unknown")
        # Lookup ID or generate temporary one
        item_id = flat_menu.get(item_name.lower(), f"ITEM-{uuid.uuid4().hex[:4]}")
        
        new_order["items"].append({
            "item_id": item_id,
            "name": item_name,
            "quantity": item.get("quantity", 1),
            "addons": item.get("addons", [])
        })

    # 4. Save to orders.json
    orders_path = os.path.join(DATA_DIR, "orders.json")
    current_orders = []
    
    if os.path.exists(orders_path):
        try:
            with open(orders_path, "r") as f:
                content = f.read().strip()
                if content:
                    current_orders = json.loads(content)
        except json.JSONDecodeError:
            current_orders = []

    # Ensure it's a list
    if not isinstance(current_orders, list):
        current_orders = []

    current_orders.append(new_order)

    with open(orders_path, "w") as f:
        json.dump(current_orders, f, indent=2)

    # Return structured dict for the next agent
    return {"order": new_order}


# ==========================================================
# 2. ORDER MANAGEMENT TOOLS (Existing)
# ==========================================================

def get_order_details(order_id: str) -> dict:
    """Fetch order details from orders.json."""
    with open(os.path.join(DATA_DIR, "orders.json"), "r") as f:
        orders = json.load(f)
    for order in orders:
        if order["order_id"] == order_id:
            return order
    return {}  # empty if not found

def update_order_status(order_id: str, status: str) -> dict:
    """Update order status."""
    with open(os.path.join(DATA_DIR, "orders.json"), "r") as f:
        orders = json.load(f)

    updated = False
    for order in orders:
        if order["order_id"] == order_id:
            order["status"] = status
            updated = True
            break

    with open(os.path.join(DATA_DIR, "orders.json"), "w") as f:
        json.dump(orders, f, indent=2)

    return {"updated": updated, "order_id": order_id, "new_status": status}

def fetch_pending_orders() -> dict:
    """Return all orders that are not completed."""
    with open(os.path.join(DATA_DIR, "orders.json"), "r") as f:
        orders = json.load(f)

    pending = [o for o in orders if o["status"] != "completed"]
    return {"pending_orders": pending}


# ==========================================================
# 3. INVENTORY TOOLS
# ==========================================================

def fetch_inventory() -> dict:
    """Load the current inventory."""
    with open(os.path.join(DATA_DIR, "inventory.json"), "r") as f:
        return json.load(f)

def update_inventory_changes(item: str, qty: int) -> dict:
    """Deduct or add stock."""
    with open(os.path.join(DATA_DIR, "inventory.json"), "r") as f:
        inventory = json.load(f)

    inventory[item] = max(0, inventory.get(item, 0) + qty)

    with open(os.path.join(DATA_DIR, "inventory.json"), "w") as f:
        json.dump(inventory, f, indent=2)

    return {"item": item, "updated_qty": inventory[item]}

def get_ingredient_requirements(order_id: str) -> dict:
    """Return ingredient list for the order."""
    with open(os.path.join(DATA_DIR, "recipes.json"), "r") as f:
        recipes = json.load(f)
    order = get_order_details(order_id)
    # Be careful: ensure your orders actually have a 'recipe' field or logic to map items to recipes
    # Assuming basic items have recipes:
    if order and "items" in order and order["items"]:
        # Just getting the first item's recipe for this simplified logic
        # In a real app, you'd aggregate all items
        first_item = order["items"][0]["name"]
        return recipes.get(first_item, {}) 
    return {}

def trigger_low_stock_alert(item: str) -> dict:
    """Triggered when any item is below threshold."""
    return {"alert": True, "item": item, "message": "Low stock detected"}


# ==========================================================
# 4. LOYALTY TOOLS
# ==========================================================

def fetch_loyalty_profile(user_id: str) -> dict:
    with open(os.path.join(DATA_DIR, "loyalty.json"), "r") as f:
        profiles = json.load(f)
    return profiles.get(user_id, {})

def update_loyalty_points(user_id: str, points: int) -> dict:
    with open(os.path.join(DATA_DIR, "loyalty.json"), "r") as f:
        profiles = json.load(f)
    profiles[user_id] = profiles.get(user_id, 0) + points
    with open(os.path.join(DATA_DIR, "loyalty.json"), "w") as f:
        json.dump(profiles, f, indent=2)
    return {"user": user_id, "points": profiles[user_id]}


# ==========================================================
# 5. FEEDBACK TOOLS
# ==========================================================

def save_feedback(user_id: str, feedback: str) -> dict:
    timestamp = datetime.datetime.now().isoformat()
    feedback_file = os.path.join(DATA_DIR, "feedback.json")
    with open(feedback_file, "r") as f:
        fb = json.load(f)
    fb.append({"user": user_id, "feedback": feedback, "time": timestamp})
    with open(feedback_file, "w") as f:
        json.dump(fb, f, indent=2)
    return {"saved": True}

def load_feedback_history() -> dict:
    with open(os.path.join(DATA_DIR, "feedback.json"), "r") as f:
        return json.load(f)

def analyze_feedback_sentiment(text: str) -> dict:
    """Mock sentiment tool."""
    score = 1 if "good" in text.lower() else -1
    return {"sentiment_score": score}


# ==========================================================
# 6. SYSTEM TOOLS
# ==========================================================

def send_notification(msg: str, to: str) -> dict:
    return {"sent": True, "message": msg, "to": to}

def save_system_logs(event: str) -> dict:
    with open(os.path.join(DATA_DIR, "system_logs.txt"), "a") as f:
        f.write(event + "\n")
    return {"logged": True}

def message_bus(sender: str, receiver: str, payload: dict) -> dict:
    return {"from": sender, "to": receiver, "payload": payload}


# ==========================================================
# 7. PROPHET FORECASTING TOOL
# ==========================================================

def run_prophet_forecast(periods: int = 7) -> dict:
    """
    Runs a time-series forecast using internal sales history data.
    
    Parameters:
        periods (int): Future days to forecast. Default is 7.
    """
    # 1. Load data internally (Solving the Agent asking for data)
    sales_path = os.path.join(DATA_DIR, "sales_history.json")
    
    if not os.path.exists(sales_path):
        return {"error": "sales_history.json not found in data directory."}
        
    try:
        with open(sales_path, "r") as f:
            data = json.load(f)
    except Exception as e:
        return {"error": f"Failed to load sales history: {e}"}

    # 2. Run Logic
    try:
        df = pd.DataFrame(data)
        df["ds"] = pd.to_datetime(df["ds"])
    except Exception as e:
        return {"error": f"Invalid input format in file: {e}"}

    df = df.sort_values("ds")
    if len(df) < 2:
        return {"error": "Not enough data points to forecast."}

    last_value = df["y"].iloc[-1]
    second_last_value = df["y"].iloc[-2]
    daily_change = last_value - second_last_value
    last_date = df["ds"].iloc[-1]

    forecast_list = []
    current_value = last_value
    for i in range(1, periods + 1):
        next_date = last_date + pd.Timedelta(days=i)
        current_value += daily_change
        forecast_list.append({"ds": next_date.strftime("%Y-%m-%d"), "yhat": float(current_value)})

    return {"forecast": forecast_list}