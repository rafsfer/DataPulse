# Data dictionary and quality contract

| Dataset | Key | Fields | Owner |
| --- | --- | --- | --- |
| customers | customer_id: C plus 5 digits | region | Atlas Customer Analytics |
| products | product_id: P plus 5 digits | category | Atlas Merchandising |
| orders | order_id: O plus 8 digits | customer_id, product_id, quantity, amount, ordered_at | Atlas Data Operations |

All identities are synthetic. No real personal data is used. Update frequency: daily.
Amounts are complete order totals. Quantity must be an integer between 1 and 1000.
Dates must be timezone-aware ISO8601; future dates fail. Values older than 48 hours
relative to validation_as_of fail the freshness rule and enter quarantine.
Amounts must be finite, nonnegative, at most 1,000,000 with at most two decimals.
Required, identifier, duplicate and reference rules are independently recorded.
Each invalid row retains the original data and every violated rule identifier.
Dimension duplicate/missing keys fail the pipeline; malformed dimension schemas
are rejected rather than silently accepted.

Execution IDs identify attempts; SHA256 of source CSV bytes identifies batches.
Bronze Parquet preserves raw CSV strings plus source, ingestion time and run ID.
Silver contains validated joins; Gold contains region/category aggregates.
PostgreSQL stores executions, rule outcomes, quarantine, facts, incidents and catalog.
