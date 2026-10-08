import type { Row } from '../types/platform';
export function display(value:unknown,column = ""):string {
  if (value == null) return '—';
  if (column.endsWith('_at') && typeof value === 'string') return new Date(value).toLocaleString();
  if (column.endsWith('_seconds') && typeof value === 'number') return value.toFixed(2);
  if (column === 'revenue') return Number(value).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2});
  if (typeof value === 'object') return JSON.stringify(value);
  return String(value);
}
export function DataTable({rows,columns}:{rows:Row[];columns:string[]}) {
  if (!rows.length) return <p className="empty">No records available. Run a pipeline to populate this view.</p>;
  return <div className="table-scroll"><table><caption className="sr-only">Data platform records</caption><thead><tr>{columns.map(key => <th scope="col" key={key}>{key.replaceAll('_',' ')}</th>)}</tr></thead><tbody>{rows.map((row,index) => <tr key={String(row.id ?? row.name ?? index)}>{columns.map(key => <td key={key}>{display(row[key],key)}</td>)}</tr>)}</tbody></table></div>;
}
