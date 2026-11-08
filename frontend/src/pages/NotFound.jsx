import React from "react";
import { Link } from "react-router-dom";

import { EmptyState } from "../components/ui";

export default function NotFound({ inApp = false }) {
  const body = (
    <EmptyState
      mood="search"
      title="Page not found"
      actions={
        <Link className="btn btn-primary" to={inApp ? "/app" : "/"}>
          {inApp ? "Back to overview" : "Back to home"}
        </Link>
      }
    >
      This address doesn't match any page.
    </EmptyState>
  );
  return inApp ? <div className="page">{body}</div> : <div className="auth">{body}</div>;
}
