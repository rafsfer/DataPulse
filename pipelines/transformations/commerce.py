import pandas as pd


def transform(valid, customers, products):
    columns = [
        "order_id",
        "customer_id",
        "product_id",
        "quantity",
        "amount",
        "ordered_at",
    ]
    frame = pd.DataFrame(valid, columns=columns)
    frame = frame.merge(
        pd.DataFrame(customers), on="customer_id", validate="many_to_one"
    )
    frame = frame.merge(pd.DataFrame(products), on="product_id", validate="many_to_one")
    frame["amount"] = pd.to_numeric(frame["amount"])
    gold = frame.groupby(["region", "category"], as_index=False).agg(
        revenue=("amount", "sum"),
        orders=("order_id", "count"),
        units=("quantity", "sum"),
    )
    return frame, gold
