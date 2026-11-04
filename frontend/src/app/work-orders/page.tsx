"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge, PageHeading, formatDate } from "@/components/app-shell";
import { listOrders, type WorkOrderList } from "@/lib/api";

const statuses = ["", "draft", "approved", "in_progress", "completed", "cancelled"];
const pageSize = 10;
export default function WorkOrdersPage() {
  const [status, setStatus] = useState(""); const [page, setPage] = useState(0);
  const [data, setData] = useState<WorkOrderList | null>(null); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  useEffect(() => { const c = new AbortController(); listOrders(status, pageSize, page * pageSize, c.signal).then(setData).catch(e => { if (!c.signal.aborted) setError(e.message); }).finally(() => { if (!c.signal.aborted) setLoading(false); }); return () => c.abort(); }, [status, page]);
  return <><PageHeading eyebrow="WORKSPACE / WORK ORDERS" title="Work orders" description="Browse the intake queue and open any order for evidence, review and audit history." action={<Link href="/intake" className="button primary">+ New intake</Link>} />
    <div className="filter-bar"><label htmlFor="status-filter">Status</label><select id="status-filter" value={status} onChange={e => { setLoading(true); setError(""); setStatus(e.target.value); setPage(0); }} className="input select"><option value="">All statuses</option>{statuses.slice(1).map(s => <option key={s} value={s}>{s.replaceAll("_", " ")}</option>)}</select><span className="filter-count">{data ? `${data.total} matching` : ""}</span></div>
    <section className="panel table-panel">{loading ? <p className="state-message">Loading work orders…</p> : error ? <p role="alert" className="error-box">{error}</p> : data?.items.length ? <><div className="table-scroll"><table className="orders-table"><thead><tr><th>WORK ORDER</th><th>LOCATION</th><th>PRIORITY</th><th>STATUS</th><th>CREATED</th><th aria-label="Open" /></tr></thead><tbody>{data.items.map(order => <tr key={order.id}><td><Link href={`/work-orders/${order.id}`} className="table-title">{order.title}</Link><span className="table-subtitle">{order.equipment_type || "Equipment unspecified"}</span></td><td>{order.location || "—"}</td><td><Badge value={order.suggested_priority} kind="priority" /></td><td><Badge value={order.status} /></td><td>{formatDate(order.created_at)}</td><td><Link href={`/work-orders/${order.id}`} className="row-arrow" aria-label={`Open ${order.title}`}>→</Link></td></tr>)}</tbody></table></div><div className="pagination"><span>Showing {page * pageSize + 1}–{Math.min((page + 1) * pageSize, data.total)} of {data.total}</span><div><button type="button" className="button secondary" disabled={page === 0} onClick={() => { setLoading(true); setError(""); setPage(p => p - 1); }}>Previous</button><button type="button" className="button secondary" disabled={(page + 1) * pageSize >= data.total} onClick={() => { setLoading(true); setError(""); setPage(p => p + 1); }}>Next</button></div></div></> : <div className="empty-state"><span className="empty-symbol">▤</span><h3>No matching work orders</h3><p>{status ? "Try a different status filter." : "Create your first intake to begin the queue."}</p><Link href="/intake" className="button primary">New intake</Link></div>}</section>
  </>;
}
