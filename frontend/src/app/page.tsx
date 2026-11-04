"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { Badge, PageHeading, formatDate } from "@/components/app-shell";
import { listOrders, type WorkOrder } from "@/lib/api";

export default function Home() {
  const [orders, setOrders] = useState<WorkOrder[]>([]);
  const [total, setTotal] = useState(0);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  useEffect(() => { const c = new AbortController(); listOrders("", 5, 0, c.signal).then(data => { setOrders(data.items); setTotal(data.total); }).catch(e => { if (!c.signal.aborted) setError(e.message); }).finally(() => { if (!c.signal.aborted) setLoading(false); }); return () => c.abort(); }, []);
  return <><PageHeading eyebrow="OPERATIONS OVERVIEW" title="A clearer path from report to review." description="Turn field observations into structured work orders, with every decision visible to a human reviewer." action={<Link className="button primary" href="/intake">+ New intake</Link>} />
    <section className="hero-panel"><div><span className="hero-kicker">YOUR WORKSPACE</span><h2>Make the first report count.</h2><p>Add a description, photo, or voice note. FieldOps AI organizes the evidence into a draft you can inspect and approve.</p><Link href="/intake" className="button light">Start an intake <span aria-hidden="true">↗</span></Link></div><div className="hero-art" aria-hidden="true"><span className="art-line one" /><span className="art-line two" /><span className="art-card"><i>01</i><b>Evidence</b><small>Captured at source</small></span><span className="art-card second"><i>02</i><b>Review</b><small>Human decision</small></span></div></section>
    <div className="section-heading"><div><p className="eyebrow">RECENT ACTIVITY</p><h2>Latest work orders</h2></div><Link href="/work-orders" className="text-link">View all work orders →</Link></div>
    <section className="panel">{loading ? <p className="state-message">Loading work orders…</p> : error ? <p role="alert" className="error-box">{error}</p> : orders.length ? <><div className="list-meta">{total} total work {total === 1 ? "order" : "orders"}</div><div className="order-list">{orders.map(order => <Link className="order-row" key={order.id} href={`/work-orders/${order.id}`}><span className="order-icon">▤</span><span className="order-main"><strong>{order.title}</strong><small>{order.equipment_type || "Equipment unspecified"} · {order.location || "Location unspecified"}</small></span><Badge value={order.suggested_priority} kind="priority" /><Badge value={order.status} /><time>{formatDate(order.created_at)}</time><span className="row-arrow">→</span></Link>)}</div></> : <div className="empty-state"><span className="empty-symbol">✦</span><h3>No work orders yet</h3><p>Your first intake will appear here as a draft ready for review.</p><Link href="/intake" className="button primary">Create first intake</Link></div>}</section>
  </>;
}
