import { fireEvent, render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it, vi } from "vitest";

import { RangeBar, RowLink } from "./ui";

const money = (v) => `₹${v}`;

describe("RangeBar", () => {
  it("places the marker by where the price sits between lowest and highest", () => {
    const { container } = render(<RangeBar value={150} min={100} max={200} format={money} />);
    expect(container.querySelector(".range-bar span").style.left).toBe("50%");
    expect(screen.getByRole("img")).toHaveAccessibleName(/mid-range/);
  });

  it("describes a price near an extreme in words, not just by position", () => {
    render(<RangeBar value={105} min={100} max={200} format={money} />);
    expect(screen.getByRole("img")).toHaveAccessibleName(/near its lowest: ₹105 between ₹100 and ₹200/);
  });

  it("handles a flat range and missing data without breaking", () => {
    const flat = render(<RangeBar value={100} min={100} max={100} format={money} />);
    expect(flat.container.querySelector(".range-bar span").style.left).toBe("50%");
    flat.unmount();
    render(<RangeBar value={null} min={1} max={2} format={money} />);
    expect(screen.getByText("—")).toBeInTheDocument();
  });
});

describe("RowLink", () => {
  it("is a real, focusable link and keeps the row's click handler from firing twice", () => {
    const rowClick = vi.fn();
    render(
      <MemoryRouter>
        <table>
          <tbody>
            <tr onClick={rowClick}>
              <td>
                <RowLink to="/app/products/B012345678">SKF 6205</RowLink>
              </td>
            </tr>
          </tbody>
        </table>
      </MemoryRouter>,
    );
    const link = screen.getByRole("link", { name: "SKF 6205" });
    expect(link).toHaveAttribute("href", "/app/products/B012345678");
    fireEvent.click(link);
    expect(rowClick).not.toHaveBeenCalled();
  });
});
