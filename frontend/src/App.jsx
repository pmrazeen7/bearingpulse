import React, { lazy, Suspense } from "react";
import { BrowserRouter, Navigate, Route, Routes, useLocation } from "react-router-dom";

import { ToastProvider } from "./components/Toast";
import AppLayout, { PageFallback } from "./layouts/AppLayout";
import { AuthProvider, useAuth } from "./lib/auth";
import { JobsProvider } from "./lib/jobs";
import { useTheme } from "./lib/theme";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import NotFound from "./pages/NotFound";

// App pages are split into their own chunks; the landing page stays light.
const Overview = lazy(() => import("./pages/Overview"));
const Products = lazy(() => import("./pages/Products"));
const ProductDetail = lazy(() => import("./pages/ProductDetail"));
const Sellers = lazy(() => import("./pages/Sellers"));
const SellerDetail = lazy(() => import("./pages/SellerDetail"));
const Alerts = lazy(() => import("./pages/Alerts"));
const Analytics = lazy(() => import("./pages/Analytics"));
const SettingsPage = lazy(() => import("./pages/Settings"));

function RequireAuth({ children }) {
  const { isAuthenticated } = useAuth();
  const location = useLocation();
  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location.pathname + location.search }} />;
  }
  return children;
}

function ThemeRoot({ children }) {
  useTheme();
  return children;
}

export default function App() {
  return (
    <BrowserRouter>
      <ThemeRoot>
        <ToastProvider>
          <AuthProvider>
            <JobsProvider>
            <Routes>
              <Route path="/" element={<Landing />} />
              <Route path="/login" element={<Login />} />
              <Route
                path="/app"
                element={
                  <RequireAuth>
                    <AppLayout />
                  </RequireAuth>
                }
              >
                <Route index element={<Overview />} />
                <Route path="products" element={<Products />} />
                <Route path="products/:asin" element={<ProductDetail />} />
                <Route path="sellers" element={<Sellers />} />
                <Route path="sellers/:sellerId" element={<SellerDetail />} />
                <Route path="alerts" element={<Alerts />} />
                <Route path="analytics" element={<Analytics />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="*" element={<NotFound inApp />} />
              </Route>
              <Route
                path="*"
                element={
                  <Suspense fallback={<PageFallback />}>
                    <NotFound />
                  </Suspense>
                }
              />
            </Routes>
            </JobsProvider>
          </AuthProvider>
        </ToastProvider>
      </ThemeRoot>
    </BrowserRouter>
  );
}
