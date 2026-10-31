import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { Modal } from "./Modal";
import { Pagination } from "./ui";

describe("Pagination", () => {
  it("shows the range and disables the first/last controls", () => {
    const onPage = vi.fn();
    render(<Pagination page={0} pageSize={20} total={45} onPage={onPage} />);
    expect(screen.getByLabelText("Previous page")).toBeDisabled();
    fireEvent.click(screen.getByLabelText("Next page"));
    expect(onPage).toHaveBeenCalledWith(1);
  });
});

describe("Modal", () => {
  it("closes on Escape and renders an accessible dialog", () => {
    const onClose = vi.fn();
    render(<Modal open onClose={onClose} title="Hello">body</Modal>);
    expect(screen.getByRole("dialog", { name: "Hello" })).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(onClose).toHaveBeenCalled();
  });
});
