# KPI definitions

All API values come from PostgreSQL; undefined denominators return null.

- Data Quality Score / valid percentage: 100 × valid rows / total input orders
  in the latest successful execution. A row violating multiple rules counts once.
- Processed records: total orders in the latest successful execution (not all attempts).
- Duplicate percentage: 100 × repeated order keys after first occurrence / total
  input orders in the latest successful execution. Invalid keys remain auditable.
- Pipeline success: 100 × successful attempts / all attempts, including running ones.
- Average processing time: mean duration_seconds across completed attempts.
- SLA compliance: 100 × successful attempts lasting at most 120 seconds / all attempts.
- Incident severity: count of unresolved incidents grouped by severity.
- Freshness: seconds since the last successful ingestion/publication per dataset.
  This operational timestamp differs from order event timestamps.
- Revenue: sum of validated order amount; amount is the whole order amount, not
  a unit price. Units are summed quantities. Serving SQL uses numeric(16,2).

Analytics includes distinct content-addressed batches. Reprocessing identical
CSV content replaces the same batch's facts without adding duplicates. Different
seeds/volumes are separate demonstration batches and their facts are additive.
Quality trends retain individual attempts rather than fabricated time series.
