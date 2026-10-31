import React, { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";

import { CloseButton } from "./ui";

const FOCUSABLE = 'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

export function Modal({ open, onClose, title, description, children, footer, labelledBy = "modal-title" }) {
  const [mounted, setMounted] = useState(open);
  const [closing, setClosing] = useState(false);
  const dialogRef = useRef(null);
  const restoreRef = useRef(null);

  useEffect(() => {
    if (open) {
      restoreRef.current = document.activeElement;
      setMounted(true);
      setClosing(false);
    } else if (mounted) {
      setClosing(true);
      const id = setTimeout(() => {
        setMounted(false);
        restoreRef.current?.focus?.();
      }, 200);
      return () => clearTimeout(id);
    }
    return undefined;
  }, [open, mounted]);

  useEffect(() => {
    if (!mounted || closing) return undefined;
    const node = dialogRef.current;
    const first = node?.querySelector("[data-autofocus]") || node?.querySelector(FOCUSABLE);
    first?.focus();
    const onKey = (event) => {
      if (event.key === "Escape") onClose();
      if (event.key === "Tab" && node) {
        const items = [...node.querySelectorAll(FOCUSABLE)].filter((el) => !el.disabled);
        if (!items.length) return;
        const firstItem = items[0];
        const lastItem = items[items.length - 1];
        if (event.shiftKey && document.activeElement === firstItem) {
          event.preventDefault();
          lastItem.focus();
        } else if (!event.shiftKey && document.activeElement === lastItem) {
          event.preventDefault();
          firstItem.focus();
        }
      }
    };
    document.addEventListener("keydown", onKey);
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = previousOverflow;
    };
  }, [mounted, closing, onClose]);

  if (!mounted) return null;
  return createPortal(
    <div
      className={`modal-backdrop ${closing ? "is-closing" : ""}`}
      onMouseDown={(event) => event.target === event.currentTarget && onClose()}
    >
      <div className="modal" role="dialog" aria-modal="true" aria-labelledby={labelledBy} ref={dialogRef}>
        <div className="modal-header">
          <div>
            <h2 className="modal-title" id={labelledBy}>
              {title}
            </h2>
            {description && <p className="modal-desc">{description}</p>}
          </div>
          <CloseButton onClick={onClose} />
        </div>
        <div className="modal-body">{children}</div>
        {footer && <div className="modal-footer">{footer}</div>}
      </div>
    </div>,
    document.body,
  );
}
