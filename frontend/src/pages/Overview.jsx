import React from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Bell, Package, Play, Store, Zap } from "lucide-react";

import { BarChart, Donut } from "../components/Charts";
import { PageHeader, StatCard } from "../components/StatCard";
import { Badge, Button, Card, EmptyState, ErrorState, SkeletonRows } from "../components/ui";
import { useCrawl } from "../layouts/AppLayout";
import { ALERT_TYPES, formatCurrency, formatDate, formatNumber, formatRelative } from "../lib/format";
import { useApi } from "../lib/useApi";

const STOCK_COLORS = { in_stock: "var(--success)", low_stock: "var(--warning)", out_of_stock: "var(--danger)", unknown: "var(--chart-6)" };
const STOCK_LABELS = { in_stock: "In stock", low_stock: "Low stock", out_of_stock: "Out of stock", unknown: "Unknown" };

export default function Overview() {
  const overview = useApi("/analytics/overview");
  const alerts = useApi("/alerts", { limit: 6, acknowledged: false });
  const products = useApi("/asins", { limit: 6 });
  const crawl = useCrawl();
  const data = overview.data;

  if (overview.error && !data) return <div className="page"><ErrorState error={overview.error} onRetry={overview.reload} /></div>;

  const empty = data && data.asin_count === 0;
  const stock = data ? Object.entries(data.stock_breakdown).map(([key, value]) => ({ label: STOCK_LABELS[key] || key, value, color: STOCK_COLORS[key] || STOCK_COLORS.unknown })) : [];
  const stockTotal = stock.reduce((sum, item) => sum + item.value, 0);

  return (
    <div className="page">
      <PageHeader
        title="Overview"
        subtitle="Live view of your tracked bearing catalogue on Amazon India."
        actions={<Button variant="primary" icon={Play} onClick={() => crawl("search")}>Discover products</Button>}
      />

      <div className="grid-stats stagger">
        <StatCard label="Tracked products" icon={Package} tone="accent" value={data?.asin_count} loading={!data} foot={data && `${formatNumber(data.snapshot_count)} price snapshots`} />
        <StatCard label="Sellers" icon={Store} tone="info" value={data?.seller_count} loading={!data} foot={data && `${data.fba_seller_count} fulfilled by Amazon`} />
        <StatCard label="Open alerts" icon={Bell} tone={data?.open_alert_count ? "danger" : "success"} value={data?.open_alert_count} loading={!data} foot={data && `${data.alerts_24h} in the last 24h`} />
        <StatCard label="Snapshots · 24h" icon={Zap} tone="success" value={data?.snapshots_24h} loading={!data} foot={data && `Last crawl ${formatRelative(data.last_scraped_at)}`} />
      </div>

      {empty ? (
        <Card>
          <EmptyState mood="sleepy" title="Nothing tracked yet" actions={<>
            <Button variant="primary" icon={Play} onClick={() => crawl("search")}>Run a discovery crawl</Button>
            <Link className="btn" to="/app/products">Add a product by ASIN</Link>
          </>}>
            Add an ASIN manually or run the search crawl to start building price history. Crawls need Redis and a Celery worker running.
          </EmptyState>
        </Card>
      ) : (
        <>
          <div className="grid-2">
            <Card title="Collection activity" subtitle="Price snapshots collected per day">
              {data ? (
                <BarChart
                  height={200}
                  ariaLabel="Snapshots per day"
                  labelEvery={Math.ceil(data.activity.length / 7)}
                  format={formatNumber}
                  data={data.activity.map((day) => ({ label: formatDate(day.date), value: day.snapshots, title: formatDate(day.date) }))}
                />
              ) : <SkeletonRows rows={3} columns={1} />}
            </Card>
            <Card title="Stock health" subtitle="Last 14 days of observations">
              {data && (
                <div className="row" style={{ gap: 24, flexWrap: "wrap", justifyContent: "center" }}>
                  <Donut segments={stock} center={<><strong className="num" style={{ fontSize: 22 }}>{formatNumber(stockTotal)}</strong><span className="subtle" style={{ fontSize: 11 }}>observations</span></>} />
                  <ul className="legend" style={{ flexDirection: "column", listStyle: "none", margin: 0, padding: 0 }}>
                    {stock.map((item) => <li key={item.label} className="legend-item"><span className="swatch" style={{ background: item.color }} />{item.label} <span className="num subtle">{item.value}</span></li>)}
                    {!stock.length && <li className="subtle">No observations yet</li>}
                  </ul>
                </div>
              )}
            </Card>
          </div>

          <div className="grid-2-even">
            <Card title="Latest alerts" subtitle="Unacknowledged signals" flush actions={<Link className="link" to="/app/alerts">View all <ArrowRight size={13} style={{ display: "inline" }} /></Link>}>
              {alerts.initialLoading ? <SkeletonRows rows={4} columns={3} /> : alerts.data?.length ? (
                <ul className="feed">
                  {alerts.data.map((alert) => {
                    const meta = ALERT_TYPES[alert.alert_type] || { label: alert.alert_type, tone: "" };
                    return (
                      <li key={alert.id}>
                        <Badge tone={meta.tone} dot>{meta.label}</Badge>
                        <Link to={`/app/products/${alert.asin}`} className="feed-main">
                          <span className="asin-chip">{alert.asin}</span>
                          <span className="muted">{alert.alert_type === "price_drop" ? `${formatCurrency(alert.old_value)} → ${formatCurrency(alert.new_value)}` : alert.title || ""}</span>
                        </Link>
                        <span className="subtle">{formatRelative(alert.triggered_at)}</span>
                      </li>
                    );
                  })}
                </ul>
              ) : <EmptyState compact mood="happy" title="All clear">No open alerts right now.</EmptyState>}
            </Card>

            <Card title="Recently tracked" subtitle="Newest products and their latest price" flush actions={<Link className="link" to="/app/products">View all <ArrowRight size={13} style={{ display: "inline" }} /></Link>}>
              {products.initialLoading ? <SkeletonRows rows={4} columns={3} /> : products.data?.length ? (
                <ul className="feed">
                  {products.data.map((item) => (
                    <li key={item.asin}>
                      <span className="asin-chip">{item.asin}</span>
                      <Link to={`/app/products/${item.asin}`} className="feed-main"><span className="table-title">{item.title || "Untitled listing"}</span></Link>
                      <strong className="num">{formatCurrency(item.latest_price)}</strong>
                    </li>
                  ))}
                </ul>
              ) : <EmptyState compact title="No products yet" />}
            </Card>
          </div>
        </>
      )}
    </div>
  );
}
