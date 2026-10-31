import React, { useMemo, useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Crown, Trash2 } from "lucide-react";

import { BarList, LineChart, SERIES_COLORS } from "../components/Charts";
import { Modal } from "../components/Modal";
import { PageHeader, StatCard } from "../components/StatCard";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, EmptyState, ErrorState, Segmented, SkeletonRows } from "../components/ui";
import { api } from "../lib/api";
import { STOCK, formatCurrency, formatDate, formatDateTime, formatPercent, formatRelative, parseDate } from "../lib/format";
import { invalidate, useApi } from "../lib/useApi";

const RANGES = [{ value: 7, label: "7d" }, { value: 30, label: "30d" }, { value: 90, label: "90d" }];

export default function ProductDetail() {
  const { asin } = useParams();
  const code = asin.toUpperCase();
  const navigate = useNavigate();
  const toast = useToast();
  const [days, setDays] = useState(7);
  const [confirming, setConfirming] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const detail = useApi(`/asins/${code}`);
  const prices = useApi(`/asins/${code}/prices`, { days });
  const sellers = useApi(`/asins/${code}/sellers`);
  const buybox = useApi(`/asins/${code}/buybox-history`);

  const series = useMemo(() => {
    const groups = new Map();
    (prices.data || []).forEach((row) => {
      const date = parseDate(row.scraped_at);
      if (!date) return;
      if (!groups.has(row.seller_name)) groups.set(row.seller_name, []);
      groups.get(row.seller_name).push({ x: date, y: row.price, meta: { highlight: row.is_buy_box_winner } });
    });
    return [...groups.entries()].map(([name, points], index) => ({ key: name, label: name, points, color: SERIES_COLORS[index % SERIES_COLORS.length] }));
  }, [prices.data]);

  const holders = useMemo(() => {
    const counts = new Map();
    (buybox.data || []).forEach((row) => counts.set(row.seller_name, (counts.get(row.seller_name) || 0) + 1));
    return [...counts.entries()].sort((a, b) => b[1] - a[1]).map(([label, value]) => ({ label, value }));
  }, [buybox.data]);

  const remove = async () => {
    setDeleting(true);
    try {
      await api.delete(`/asins/${code}`);
      invalidate();
      toast.success("Product removed", `${code} and its history were deleted.`);
      navigate("/app/products", { replace: true });
    } catch (err) {
      toast.error("Could not remove product", err.message);
      setDeleting(false);
    }
  };

  if (detail.error?.status === 404) {
    return <div className="page"><EmptyState mood="search" title="Product not found" actions={<Link className="btn" to="/app/products">Back to products</Link>}>{code} isn't being tracked.</EmptyState></div>;
  }
  if (detail.error && !detail.data) return <div className="page"><ErrorState error={detail.error} onRetry={detail.reload} /></div>;

  const d = detail.data;
  const change = d?.buy_box_change_pct;
  return (
    <div className="page">
      <Link to="/app/products" className="back-link"><ArrowLeft size={14} /> Products</Link>
      <PageHeader
        eyebrow={<span className="asin-chip">{code}</span>}
        title={d?.title || (detail.loading ? "Loading…" : "Untitled listing")}
        subtitle={d && <>First seen {formatDate(d.first_seen || d.created_at)} · {d.snapshot_count} snapshots from {d.seller_count} seller(s){d.search_query ? ` · "${d.search_query}"` : ""}</>}
        actions={<><a className="btn" href={`https://www.amazon.in/dp/${code}`} target="_blank" rel="noreferrer">View on Amazon</a><Button variant="danger" icon={Trash2} onClick={() => setConfirming(true)}>Stop tracking</Button></>}
      />

      <div className="grid-stats stagger">
        <StatCard label="Latest price" value={d ? formatCurrency(d.latest_price) : null} loading={!d} foot={d && (d.latest_mrp ? `MRP ${formatCurrency(d.latest_mrp)}` : "No MRP recorded")} />
        <StatCard label="Buy Box holder" tone="info" value={d ? d.buy_box_seller || "—" : null} loading={!d}
          foot={d && (change !== null && change !== undefined ? <span className={change < 0 ? "delta-down" : "delta-up"}>{formatPercent(change, { signed: true })} since previous</span> : "No comparison yet")} />
        <StatCard label="Lowest seen" tone="success" value={d ? formatCurrency(d.min_price) : null} loading={!d} foot={d && `Highest ${formatCurrency(d.max_price)}`} />
        <StatCard label="Average price" tone="warning" value={d ? formatCurrency(d.avg_price) : null} loading={!d} foot={d && `${d.alert_count} alert(s) raised`} />
      </div>

      <Card title="Price history" subtitle="Each seller's observed price. Filled markers indicate the Buy Box winner."
        actions={<Segmented label="Date range" options={RANGES} value={days} onChange={setDays} />}>
        {prices.initialLoading ? <SkeletonRows rows={4} columns={1} /> : series.length ? (
          <LineChart series={series} height={300} ariaLabel={`Price history for ${code}`} yFormat={(v) => formatCurrency(v, { compact: true })}
            xFormat={(date) => formatDate(date)} tooltipTitle={(date) => formatDateTime(date)} />
        ) : <EmptyState compact mood="sleepy" title={`No snapshots in the last ${days} days`}>Run a product refresh from the Run menu, or widen the date range.</EmptyState>}
      </Card>

      <div className="grid-2">
        <Card title="Seller offers" subtitle="Latest price from each seller, cheapest first" flush>
          {sellers.initialLoading ? <SkeletonRows rows={4} columns={4} /> : sellers.data?.length ? (
            <div className="table-wrap"><table className="table">
              <thead><tr><th>Seller</th><th className="align-right">Price</th><th className="align-right">vs. cheapest</th><th>Stock</th><th>Seen</th></tr></thead>
              <tbody>{sellers.data.map((row) => {
                const stock = STOCK[row.stock_status];
                const gap = row.current_price - sellers.data[0].current_price;
                return (
                  <tr key={row.seller_id}>
                    <td><Link to={`/app/sellers/${row.seller_id}`} className="table-title">{row.is_buy_box_winner && <Crown size={13} className="crown" aria-label="Buy Box winner" />} {row.seller_name}</Link>
                      <div className="table-sub">{row.is_fba && <Badge tone="info">FBA</Badge>} {row.simulated_pincode && <span>PIN {row.simulated_pincode}</span>}</div></td>
                    <td className="align-right num"><strong>{formatCurrency(row.current_price)}</strong></td>
                    <td className="align-right num muted">{gap === 0 ? "—" : `+${formatCurrency(gap)}`}</td>
                    <td>{stock ? <Badge tone={stock.tone} dot>{stock.label}</Badge> : "—"}</td>
                    <td className="muted">{formatRelative(row.scraped_at)}</td>
                  </tr>
                );
              })}</tbody>
            </table></div>
          ) : <EmptyState compact title="No seller data yet" />}
        </Card>
        <Card title="Buy Box share" subtitle="Observations won per seller">
          {holders.length ? <BarList rows={holders} /> : <EmptyState compact title="No Buy Box history" />}
        </Card>
      </div>

      <Modal open={confirming} onClose={() => setConfirming(false)} title="Stop tracking this product?"
        description={`This permanently deletes ${code}, its ${d?.snapshot_count ?? 0} snapshots, alerts and any threshold override.`}
        footer={<><Button variant="ghost" onClick={() => setConfirming(false)}>Cancel</Button><Button variant="danger" loading={deleting} onClick={remove}>Delete product</Button></>}>
        <p className="muted">This can't be undone. The product will be re-added if a discovery crawl finds it again.</p>
      </Modal>
    </div>
  );
}
