import re
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation

RULES = {
    "required": "critical",
    "duplicate": "high",
    "reference": "critical",
    "date_format": "high",
    "money": "high",
    "identifier": "high",
    "range": "high",
    "late": "medium",
}


def validate_orders(rows, customer_ids, product_ids, as_of):
    valid, rejected, counts, seen = [], [], {key: 0 for key in RULES}, set()
    for index, original in enumerate(rows):
        row = {key: str(value).strip() for key, value in original.items()}
        reasons = set()
        if any(
            not row.get(key)
            for key in (
                "order_id",
                "customer_id",
                "product_id",
                "quantity",
                "amount",
                "ordered_at",
            )
        ):
            reasons.add("required")
        if row.get("order_id") in seen:
            reasons.add("duplicate")
        seen.add(row.get("order_id"))
        if not all(
            re.fullmatch(pattern, row.get(key, ""))
            for key, pattern in (
                ("order_id", r"O\d{8}"),
                ("customer_id", r"C\d{5}"),
                ("product_id", r"P\d{5}"),
            )
        ):
            reasons.add("identifier")
        if (
            row.get("customer_id") not in customer_ids
            or row.get("product_id") not in product_ids
        ):
            reasons.add("reference")
        try:
            amount = Decimal(row.get("amount", ""))
            if (
                not amount.is_finite()
                or amount < 0
                or amount > 1000000
                or amount.as_tuple().exponent < -2
            ):
                reasons.add("money")
        except (InvalidOperation, ValueError):
            reasons.add("money")
        try:
            quantity = int(row.get("quantity", ""))
            if not 1 <= quantity <= 1000:
                reasons.add("range")
        except ValueError:
            reasons.add("range")
        try:
            ordered_at = datetime.fromisoformat(row.get("ordered_at", ""))
            if ordered_at.tzinfo is None:
                raise ValueError("Timezone required")
            ordered_at = ordered_at.astimezone(UTC)
            if ordered_at > as_of:
                reasons.add("range")
            if as_of - ordered_at > timedelta(hours=48):
                reasons.add("late")
        except ValueError:
            reasons.add("date_format")
        for reason in reasons:
            counts[reason] += 1
        if reasons:
            rejected.append(
                {"row_number": index, "original": original, "reasons": sorted(reasons)}
            )
        else:
            valid.append(
                {
                    **row,
                    "amount": str(amount),
                    "quantity": quantity,
                    "ordered_at": ordered_at.isoformat(),
                }
            )
    return valid, rejected, counts
