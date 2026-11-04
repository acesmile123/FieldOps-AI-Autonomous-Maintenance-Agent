"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";
import { getHealth, type Health } from "@/lib/api";

const links = [
  { href: "/", label: "Overview", icon: "◫" },
  { href: "/intake", label: "New intake", icon: "+" },
  { href: "/work-orders", label: "Work orders", icon: "▤" },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const [health, setHealth] = useState<Health | null>(null);
  const [error, setError] = useState(false);
  useEffect(() => {
    const controller = new AbortController();
    getHealth(controller.signal).then(value => { setHealth(value); setError(false); }).catch(() => { if (!controller.signal.aborted) { setHealth(null); setError(true); } });
    return () => controller.abort();
  }, [path]);
  return <div className="app-shell">
    <aside className="sidebar">
      <Link href="/" className="brand"><span className="brand-mark">F<span>✦</span></span><span>FieldOps <b>AI</b><small>OPERATIONS DESK</small></span></Link>
      <div className="nav-label">WORKSPACE</div>
      <nav aria-label="Main navigation" className="nav-list">{links.map(link => <Link key={link.href} href={link.href} className={`nav-item ${path === link.href || (link.href === "/work-orders" && path.startsWith("/work-orders/")) ? "active" : ""}`}><span className="nav-icon" aria-hidden="true">{link.icon}</span>{link.label}</Link>)}</nav>
      <div className="sidebar-bottom"><div className="sidebar-note"><span className="note-icon">✦</span><strong>Human review first</strong><p>AI prepares a draft. A person decides what happens next.</p></div><div className="connection"><span className={`status-dot ${error ? "offline" : health ? "online" : "pending"}`} />{error ? "Backend offline" : health ? "Backend connected" : "Connecting…"}</div></div>
    </aside>
    <div className="main-column"><header className="topbar"><div className="topbar-label">FIELD SERVICE / <span>{path === "/" ? "OVERVIEW" : path.startsWith("/intake") ? "NEW INTAKE" : "WORK ORDERS"}</span></div><div className="topbar-right"><span className={`mode-pill ${health?.demo_mock_mode ? "mock" : ""}`}>{error ? "MODE UNKNOWN" : !health ? "CHECKING MODE" : health.demo_mock_mode ? "MOCK DATA" : "LIVE META"}</span><span className="avatar" aria-label="Operations workspace">FO</span></div></header><main className="content">{children}</main></div>
  </div>;
}

export function Badge({ value, kind = "status" }: { value: string; kind?: "status" | "priority" }) { return <span className={`badge ${kind}-${value.toLowerCase()}`}>{value.replaceAll("_", " ")}</span>; }
export function PageHeading({ eyebrow, title, description, action }: { eyebrow: string; title: string; description?: string; action?: React.ReactNode }) { return <div className="page-heading"><div><p className="eyebrow">{eyebrow}</p><h1>{title}</h1>{description && <p className="page-description">{description}</p>}</div>{action && <div className="heading-action">{action}</div>}</div>; }
export const formatDate = (value: string) => new Intl.DateTimeFormat(undefined, { dateStyle: "medium", timeStyle: "short" }).format(new Date(value));
