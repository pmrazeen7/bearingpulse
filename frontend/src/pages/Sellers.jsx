import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { PageHeader } from "../components/StatCard";
import { Badge, Button, Card, EmptyState, ErrorState, Pagination, SearchInput, SkeletonRows, RowLink } from "../components/ui";
import { formatCurrency, formatRelative } from "../lib/format";
import { useApi, useDebounced } from "../lib/useApi";

const PAGE_SIZE = 20;

export default function Sellers() {
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [page, setPage] = useState(0);
  const debounced = useDebounced(query);
  useEffect(() => setPage(0), [debounced]);
  const { data, total, error, initialLoading, reload } = useApi("/sellers", { q: debounced, limit: PAGE_SIZE, offset: page * PAGE_SIZE });

  return (
    <div className="page">
      <PageHeader title="Sellers" subtitle="Sellers seen on your tracked listings." />
      <Card flush>
        <div className="toolbar"><SearchInput value={query} onChange={setQuery} placeholder="Search seller name or ID" /></div>
        {error && !data ? <ErrorState error={error} onRetry={reload} /> : initialLoading ? <SkeletonRows rows={8} columns={5} /> : data?.length ? (
          <>
            <div className="table-wrap"><table className="table">
              <thead><tr><th>Seller</th><th className="hide-sm">Fulfilment</th><th className="align-right hide-sm">Products</th><th className="align-right">Buy Box wins</th><th className="align-right">Best price</th><th className="hide-sm">Last seen</th></tr></thead>
              <tbody>{data.map((row) => (
                <tr key={row.seller_id} className="is-clickable" onClick={() => navigate(`/app/sellers/${row.seller_id}`)}>
                  <td><RowLink to={`/app/sellers/${row.seller_id}`} className="table-title" title={row.seller_name}>{row.seller_name}</RowLink><div className="table-sub">{row.location_state || "Location unknown"}</div></td>
                  <td className="hide-sm">{row.is_fba ? <Badge tone="info">FBA</Badge> : <Badge>Merchant</Badge>}</td>
                  <td className="align-right num hide-sm">{row.asin_count}</td>
                  <td className="align-right num">{row.buy_box_wins}</td>
                  <td className="align-right num">{formatCurrency(row.best_price)}</td>
                  <td className="muted hide-sm">{formatRelative(row.last_seen)}</td>
                </tr>))}</tbody>
            </table></div>
            <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPage={setPage} />
          </>
        ) : (
          <EmptyState mood={debounced ? "search" : "sleepy"} title={debounced ? "No matching sellers" : "No sellers yet"}
            actions={debounced && <Button onClick={() => setQuery("")}>Clear search</Button>}>
            {debounced ? `Nothing matches "${debounced}".` : "Sellers appear after the first product refresh."}
          </EmptyState>
        )}
      </Card>
    </div>
  );
}
