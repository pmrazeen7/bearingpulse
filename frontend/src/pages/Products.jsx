import React, { useEffect, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Plus } from "lucide-react";

import { Modal } from "../components/Modal";
import { PageHeader } from "../components/StatCard";
import { useToast } from "../components/Toast";
import { Badge, Button, Card, EmptyState, ErrorState, Field, Pagination, SearchInput, SkeletonRows, RowLink, RangeBar } from "../components/ui";
import { api } from "../lib/api";
import { ASIN_PATTERN, STOCK, discountPct, formatCurrency, formatPercent, formatRelative } from "../lib/format";
import { invalidate, useApi, useDebounced } from "../lib/useApi";

const PAGE_SIZE = 20;

function AddProductModal({ open, onClose, onCreated }) {
  const toast = useToast();
  const [asin, setAsin] = useState("");
  const [title, setTitle] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => { if (open) { setAsin(""); setTitle(""); setError(""); } }, [open]);

  const submit = async (event) => {
    event.preventDefault();
    const code = asin.trim().toUpperCase();
    if (!ASIN_PATTERN.test(code)) { setError("An ASIN is exactly 10 letters or digits, e.g. B07XYZ1234."); return; }
    setBusy(true);
    try {
      await api.post("/asins", { asin: code, title: title.trim() || null });
      invalidate();
      toast.success("Product added", `${code} is now tracked.`);
      onCreated(code);
    } catch (err) {
      setError(err.message);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Modal open={open} onClose={onClose} title="Track a product" description="Add an Amazon India ASIN. Price history starts with the next crawl."
      footer={<><Button variant="ghost" onClick={onClose}>Cancel</Button><Button variant="primary" type="submit" form="add-asin" loading={busy}>Add product</Button></>}>
      <form id="add-asin" onSubmit={submit} noValidate className="stack">
        <Field label="ASIN" htmlFor="asin" error={error} hint="Found in the product URL after /dp/">
          <input id="asin" data-autofocus className="input mono" maxLength={10} placeholder="B07XYZ1234" value={asin} aria-invalid={Boolean(error)} onChange={(e) => { setAsin(e.target.value.toUpperCase()); setError(""); }} />
        </Field>
        <Field label="Title (optional)" htmlFor="title">
          <input id="title" className="input" maxLength={500} placeholder="SKF 6205-2Z deep groove ball bearing" value={title} onChange={(e) => setTitle(e.target.value)} />
        </Field>
      </form>
    </Modal>
  );
}

export default function Products() {
  const [params, setParams] = useSearchParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState(params.get("q") || "");
  const [page, setPage] = useState(0);
  const [adding, setAdding] = useState(false);
  const debounced = useDebounced(query);

  useEffect(() => { setQuery(params.get("q") || ""); }, [params]);
  useEffect(() => {
    setPage(0);
    setParams(debounced ? { q: debounced } : {}, { replace: true });
  }, [debounced]); // eslint-disable-line react-hooks/exhaustive-deps

  const { data, total, error, initialLoading, loading, reload } = useApi("/asins", { q: debounced, limit: PAGE_SIZE, offset: page * PAGE_SIZE });

  return (
    <div className="page">
      <PageHeader title="Products" subtitle="Every ASIN being monitored, with its most recent Buy Box price."
        actions={<Button variant="primary" icon={Plus} onClick={() => setAdding(true)}>Track product</Button>} />
      <Card flush>
        <div className="toolbar">
          <SearchInput value={query} onChange={setQuery} placeholder="Search ASIN, title or query" />
          <span className="toolbar-spacer" />
          {loading && !initialLoading && <span className="spinner subtle" aria-label="Refreshing" />}
        </div>
        {error && !data ? <ErrorState error={error} onRetry={reload} /> : initialLoading ? <SkeletonRows rows={8} columns={5} /> : data?.length ? (
          <>
            <div className="table-wrap">
              <table className="table">
                <thead><tr><th>Product</th><th className="align-right">Price</th><th className="align-right hide-sm">Range</th><th className="hide-sm">Buy Box</th><th>Stock</th><th className="hide-sm">Updated</th></tr></thead>
                <tbody>
                  {data.map((row) => {
                    const stock = STOCK[row.latest_stock_status];
                    const off = discountPct(row.latest_price, row.latest_mrp);
                    return (
                      <tr key={row.asin} className="is-clickable" onClick={() => navigate(`/app/products/${row.asin}`)}>
                        <td><RowLink to={`/app/products/${row.asin}`} className="table-title" title={row.title || undefined}>{row.title || "Untitled listing"}</RowLink><div className="table-sub"><span className="asin-chip">{row.asin}</span> {row.search_query && <span>· {row.search_query}</span>}</div></td>
                        <td className="align-right"><div className="num"><strong>{formatCurrency(row.latest_price)}</strong></div>{off && <div className="table-sub"><Badge tone="success">{formatPercent(off, { digits: 0 })} off</Badge></div>}</td>
                        <td className="align-right hide-sm"><RangeBar value={row.latest_price} min={row.min_price} max={row.max_price} format={(v) => formatCurrency(v, { compact: true })} /></td>
                        <td className="hide-sm">{row.latest_seller || <span className="subtle">—</span>}</td>
                        <td>{stock ? <Badge tone={stock.tone} dot>{stock.label}</Badge> : <span className="subtle">—</span>}</td>
                        <td className="muted nowrap hide-sm">{formatRelative(row.latest_scraped_at)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
            <Pagination page={page} pageSize={PAGE_SIZE} total={total} onPage={setPage} />
          </>
        ) : (
          <EmptyState mood={debounced ? "search" : "sleepy"} title={debounced ? "No matching products" : "No products tracked yet"}
            actions={debounced ? <Button onClick={() => setQuery("")}>Clear search</Button> : <Button variant="primary" icon={Plus} onClick={() => setAdding(true)}>Track your first product</Button>}>
            {debounced ? `Nothing matches "${debounced}".` : "Add an ASIN, or run a discovery crawl from the Run menu."}
          </EmptyState>
        )}
      </Card>
      <AddProductModal open={adding} onClose={() => setAdding(false)} onCreated={(code) => { setAdding(false); navigate(`/app/products/${code}`); }} />
    </div>
  );
}
