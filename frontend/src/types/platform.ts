export type Row = Record<string, unknown>;
export interface Metrics {
  processed_records:number; data_quality_score:number|null; valid_percent:number|null;
  duplicate_percent:number|null; pipeline_success_percent:number|null;
  average_duration_seconds:number|null; sla_percent:number|null;
}
