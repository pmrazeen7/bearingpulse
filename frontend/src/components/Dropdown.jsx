import React, { useEffect, useRef, useState } from "react";

export function Dropdown({ trigger, children, label }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    const onDown = (event) => {
      if (!rootRef.current?.contains(event.target)) setOpen(false);
    };
    const onKey = (event) => event.key === "Escape" && setOpen(false);
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div className="dropdown" ref={rootRef}>
      {trigger({ open, toggle: () => setOpen((value) => !value), "aria-expanded": open, "aria-haspopup": "menu" })}
      {open && (
        <div className="dropdown-menu" role="menu" aria-label={label}>
          {typeof children === "function" ? children({ close: () => setOpen(false) }) : children}
        </div>
      )}
    </div>
  );
}

export function DropdownItem({ icon: Icon, children, hint, onSelect, close }) {
  return (
    <button
      type="button"
      role="menuitem"
      className="dropdown-item"
      onClick={() => {
        close?.();
        onSelect?.();
      }}
    >
      {Icon && <Icon aria-hidden="true" />}
      <span>
        {children}
        {hint && <small>{hint}</small>}
      </span>
    </button>
  );
}
