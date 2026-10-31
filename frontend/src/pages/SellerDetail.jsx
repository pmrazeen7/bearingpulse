import React from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { ArrowLeft, Crown, Package, Tag } from "lucide-react";

import { PageHeader, StatCard } from "../components/StatCard";
import { Badge, Card, EmptyState, ErrorState, SkeletonRows } from "../components/ui";
import { formatCurrency, formatRelative } from "../lib/format";
import { useApi } from "../lib/useApi";

export default function SellerDetail() {
  const { sellerId } = useParams();
  const navigate = useNavigate();
  const seller = useApi(`/sellers/${sellerId}`);
  const asins = useApi(`/sellers/${sellerId}/asins`);

  if (seller.error?.status === 404) {
    return <div className="page"><EmptyState mood="search" title="Seller not found" actions={<Link className="btn" to="/app/sellers">Back to sellers</Link>} /></div>;
  }
  if (seller.error && !seller.data) return <div className="page"><ErrorState error={seller.error} onRetry={seller.reload} /></div>;
  const s = seller.data;

  return (
    <div className="page">
      <Link to="/app/sellers" className="back-link"><ArrowLeft size={14} /> Sellers</Link>
      <PageHeader title={s?.seller_name || "Loading…"}
        subtitle={s && <>{s.location_state || "Location unknown"}{s.seller_id_amazon ? ` · Amazon ID ${s.seller_id_amazon}` : ""} · last seen {formatRelative(s.last_seen)}</>}
        actions={s && (s.is_fba ? <Badge tone="info">Fulfilled by Amazon</Badge> : <Badge>Merchant fulfilled</Badge>)} />
      <div className="grid-stats stagger">
        <StatCard label="Products listed" icon={Package} value={s?.asin_count} loading={!s} foot="Distinct ASINs" />
        <StatCard label="Buy Box wins" icon={Crown} tone="warning" value={s?.buy_box_wins} loading={!s} foot="Observed snapshots" />
        <StatCard label="Snapshots" icon={Tag} tone="info" value={s?.snapshot_count} loading={!s} foot="Price observations" />
        <StatCard label="Best price" tone="success" value={s ? formatCurrency(s.best_price) : null} loading={!s} foot="Lowest ever seen" />
      </div>
      <Card title="Products this seller competes on" flush>
        {asins.initialLoading ? <SkeletonRows rows={5} columns={4} /> : asins.data?.length ? (
          <div className="table-wrap"><table className="table">
            <thead><tr><th>Product</th><th className="align-right">Best price</th><th className="align-right">Snapshots</th><th>Last seen</th></tr></thead>
            <tbody>{asins.data.map((row) => (
              <tr key={row.asin} className="is-clickable" onClick={() => navigate(`/app/products/${row.asin}`)}>
                <td><div className="table-title">{row.title || "Untitled listing"}</div><div className="table-sub"><span className="asin-chip">{row.asin}</span></div></td>
                <td className="align-right num">{formatCurrency(row.best_price)}</td>
                <td className="align-right num">{row.snapshot_count}</td>
                <td className="muted">{formatRelative(row.last_seen)}</td>
              </tr>))}</tbody>
          </table></div>
        ) : <EmptyState compact title="No listings recorded" />}
      </Card>
    </div>
  );
}
