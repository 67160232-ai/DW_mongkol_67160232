import pandas as pd
from .config import PROVINCE_MAP

def transform_data(raw):
    """
    Transform raw data:
    1. Clean Customers
    2. Clean Products
    3. Clean & Validate Orders
    4. Calculate financial metrics for sales
    """
    # 1. Customers
    cust = raw["customers"].drop_duplicates(subset=["customer_id"], keep="first").copy()
    cust["province"] = (
        cust["province"]
        .astype(str)
        .str.strip()
        .str.lower()
        .map(PROVINCE_MAP)
        .fillna("Unknown")
    )
    cust["email"] = cust["email"].fillna("Unknown")
    cust["name"] = cust["name"].fillna("Unknown")
    clean_customers = cust[["customer_id", "name", "province", "email"]].copy()

    # 2. Products
    prod = raw["products"].copy()
    if "category.name" in prod.columns:
        prod.rename(columns={"category.name": "category"}, inplace=True)
    if "pricing.price" in prod.columns:
        prod.rename(columns={"pricing.price": "price"}, inplace=True)

    prod["price"] = pd.to_numeric(
        prod["price"].astype(str).str.replace(",", "").str.strip(),
        errors="coerce"
    )
    prod["category"] = prod["category"].fillna("Unknown")
    prod["product_name"] = prod["product_name"].fillna("Unknown")
    clean_products = prod[["product_id", "product_name", "category", "price"]].copy()

    # 3. Orders
    orders = raw["orders"].drop_duplicates(subset=["order_id"], keep="first").copy()
    orders["parsed_date"] = pd.to_datetime(orders["order_date"], format="mixed", errors="coerce")
    orders["status"] = orders["status"].astype(str).str.strip().str.lower()
    orders["qty"] = pd.to_numeric(orders["qty"], errors="coerce")
    orders["unit_price"] = pd.to_numeric(orders["unit_price"], errors="coerce")
    orders["discount_pct"] = pd.to_numeric(orders["discount_pct"], errors="coerce")

    # Reject conditions
    invalid_qty = orders["qty"].isna() | (orders["qty"] <= 0)
    invalid_unit_price = orders["unit_price"].isna() | (orders["unit_price"] <= 0)
    invalid_discount = (
        orders["discount_pct"].isna()
        | (orders["discount_pct"] < 0)
        | (orders["discount_pct"] > 100)
    )
    invalid_date = orders["parsed_date"].isna()
    invalid_cust = ~orders["customer_id"].isin(clean_customers["customer_id"])
    invalid_prod = ~orders["product_id"].isin(clean_products["product_id"])

    invalid_mask = (
        invalid_qty
        | invalid_unit_price
        | invalid_discount
        | invalid_date
        | invalid_cust
        | invalid_prod
    )

    rejects = orders[invalid_mask].copy()

    # 4. Valid Sales (paid or completed)
    valid_orders = orders[~invalid_mask].copy()
    sales = valid_orders[valid_orders["status"].isin(["paid", "completed"])].copy()

    sales["order_date"] = sales["parsed_date"].dt.strftime("%Y-%m-%d")
    sales["gross_amount"] = sales["qty"] * sales["unit_price"]
    sales["discount_amount"] = sales["gross_amount"] * sales["discount_pct"] / 100.0
    sales["sales_amount"] = sales["gross_amount"] - sales["discount_amount"]

    sales_cols = [
        "order_id",
        "customer_id",
        "product_id",
        "order_date",
        "qty",
        "unit_price",
        "discount_pct",
        "sales_amount",
    ]
    sales = sales[sales_cols].copy()

    return clean_customers, clean_products, sales, rejects

