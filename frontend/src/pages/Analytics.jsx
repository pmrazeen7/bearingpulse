import React, { useState } from "react";
import { Link } from "react-router-dom";

import { BarList } from "../components/Charts";
import { PageHeader } from "../components/StatCard";
import { Badge, Card, EmptyState, ErrorState, Segmented, SkeletonRows } from "../components/ui";
import { formatCurrency, formatDateTime } from "../lib/format";
import { useApi } from "../lib/useApi";

const WINDOWS = [{ value: 7, label: "7d" }, { value: 30, label: "30d" }, { value: 90, label: "90d" }, { value: 0, label: "All" }];

export default function Analytics() {
  const [days, setDays] = useState(30);
  const window = days || undefined;
  const leaders = useApi("/analytics/price-leaders", { days: window });
  const undercuts = useApi("/analytics/undercut-events", { days: window, limit: 50 });
  const products = useApi("/asins", { limit: 500 });

  const titles = Object.fromEntries((products.data || []).map((p) => [p.asin, p.title]));
  const seller = new Map();
  (leaders.data || []).forEach((row) => seller.set(row.seller_name, (seller.get(row.seller_name) || 0) + 1));
  const byLeader = [...seller.entries()].sort((a, b) => b[1] - a[1]).slice(0, 8).map(([label, value]) => ({ label, value, sub: "products led" }));

  if (leaders.error && !leaders.data) return <div className="page"><ErrorState error={leaders.error} onRetry={leaders.reload} /></div>;

  return (
    <div className="page">
      <PageHeader title="Analytics" subtitle="Who is winning on price, and when the market's lowest price moved."
        actions={<Segmented label="Window" options={WINDOWS} value={days} onChange={setDays} />} />
      <div className="grid-2-even">
        <Card title="Price leadership" subtitle="Sellers most often offering the lowest price">
          {leaders.initialLoading ? <SkeletonRows rows={4} columns={1} /> : byLeader.length ? <BarList rows={byLeader} /> : <EmptyState compact mood="sleepy" title="Not enough data">Leaders appear once products have price snapshots in this window.</EmptyState>}
        </Card>
        <Card title="Lead streaks by product" subtitle="Top seller per ASIN and observations led" flush>
          {leaders.initialLoading ? <SkeletonRows rows={4} columns={3} /> : leaders.data?.length ? (
            <ul className="feed">{leaders.data.slice().sort((a, b) => b.lead_count - a.lead_count).slice(0, 8).map((row) => (
              <li key={row.asin}><Link to={`/app/products/${row.asin}`} className="feed-main"><span className="asin-chip">{row.asin}</span><span className="table-title">{titles[row.asin] || row.seller_name}</span></Link><span className="muted">{row.seller_name}</span><Badge tone="accent">{row.lead_count}×</Badge></li>
            ))}</ul>
          ) : <EmptyState compact title="No data" />}
        </Card>
      </div>
      <Card title="Undercut events" subtitle="Moments when the lowest market price dropped" flush>
        {undercuts.initialLoading ? <SkeletonRows rows={6} columns={5} /> : undercuts.data?.length ? (
          <div className="table-wrap"><table className="table">
            <thead><tr><th>When</th><th>Product</th><th>Seller</th><th className="align-right">Previous low</th><th className="align-right">New low</th><th className="align-right">Drop</th></tr></thead>
            <tbody>{undercuts.data.map((event, index) => (
              <tr key={`${event.asin}-${event.scraped_at}-${index}`}>
                <td className="muted nowrap">{formatDateTime(event.scraped_at)}</td>
                <td><Link to={`/app/products/${event.asin}`} className="table-title">{titles[event.asin] || event.asin}</Link><div className="table-sub"><span className="asin-chip">{event.asin}</span></div></td>
                <td className="nowrap">{event.seller_name}</td>
                <td className="align-right num muted">{formatCurrency(event.buy_box_price)}</td>
                <td className="align-right num"><strong>{formatCurrency(event.price)}</strong></td>
                <td className="align-right num delta-down">−{(((event.buy_box_price - event.price) / event.buy_box_price) * 100).toFixed(1)}%</td>
              </tr>))}</tbody>
          </table></div>
        ) : <EmptyState compact mood="happy" title="No undercuts in this window">The lowest price hasn't dropped between observations.</EmptyState>}
      </Card>
    </div>
  );
}
