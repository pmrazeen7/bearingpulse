from __future__ import annotations

from typing import List

from bs4 import BeautifulSoup

from data_pipeline.normalizer import detect_fba, map_stock_status, normalize_price


def _text(element) -> str:
    return element.get_text(" ", strip=True) if element else ""


SEARCH_PRICE_SELECTORS = (
    "span.a-price:not(.a-text-price) .a-offscreen",
    "[data-cy='price-recipe']",
)


def _search_title(card) -> str:
    """Product name from a search card.

    Current markup keeps the brand in one <h2> span and the name in ``a > h2``; some cards put the
    full name in the h2's aria-label. Take the first non-empty of those, then fall back to older
    markup and finally the product image's alt text.
    """
    for heading in card.select("h2"):
        label = (heading.get("aria-label") or "").strip()
        if label:
            return label
    for selector in ("a h2 span", "h2 a span", "h2 span"):
        text = _text(card.select_one(selector))
        if text:
            return text
    image = card.select_one("img.s-image")
    return (image.get("alt") or "").strip() if image else ""


def parse_search_results(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    # One element per result. Nested nodes also carry data-asin, so fall back to the broad
    # selector only when the page has no result cards at all (older/test markup).
    cards = soup.select("div[data-component-type='s-search-result']") or soup.select("[data-asin]")
    items: List[dict] = []
    seen: set[str] = set()
    for card in cards:
        asin = (card.get("data-asin") or "").strip().upper()
        if len(asin) != 10 or asin in seen:
            continue
        seen.add(asin)
        price_el = None
        for selector in SEARCH_PRICE_SELECTORS:
            price_el = card.select_one(selector)
            if price_el:
                break
        combined_price = ""
        if price_el:
            combined_price = _text(price_el) or price_el.get("aria-label", "")
        if not combined_price:  # older markup: price in an aria-label
            labelled = card.find(attrs={"aria-label": lambda value: isinstance(value, str) and "₹" in value})
            combined_price = (labelled.get("aria-label", "") or _text(labelled)) if labelled else ""
        seller_hint = _text(card.find(attrs={"data-csa-c-delivery-price": True}))
        items.append(
            {
                "asin": asin,
                "title": _search_title(card),
                "price": normalize_price(combined_price),
                "seller_hint": seller_hint,
            }
        )
    return items


PRICE_SELECTORS = (
    "#corePrice_feature_div .priceToPay .a-offscreen",
    "#corePrice_feature_div span.a-price:not(.a-text-price) .a-offscreen",
    ".priceToPay .a-offscreen",
    "span.a-price:not(.a-text-price) .a-offscreen",
)
MRP_SELECTORS = (
    "span.a-text-price .a-offscreen",
    "[data-a-strike='true'] .a-offscreen",
    "[data-a-strike='true']",
)
SELLER_SELECTORS = (
    "#sellerProfileTriggerId",
    "#merchant-info a",
    "[data-feature-name='desktop_merchant_info']",
)
STOCK_SELECTORS = ("#availability span", "[data-feature-name='availability']")


def _first_text(soup, selectors) -> str:
    for selector in selectors:
        text = _text(soup.select_one(selector))
        if text:
            return text
    return ""


def parse_product_page(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title = _text(soup.select_one("#productTitle"))
    mrp_text = _first_text(soup, MRP_SELECTORS)
    price_text = _first_text(soup, PRICE_SELECTORS)
    if not price_text:  # older layouts
        container = (
            soup.find(id="corePrice_feature_div")
            or soup.find(id="corePrice_desktop")
            or soup.find(id="corePriceDisplay_desktop_feature_div")
        )
        price_text = _text(container.find(attrs={"aria-hidden": "true"}) if container else None) or _text(
            soup.find(attrs={"data-a-color": "price"})
        )
    buy_box_seller = _first_text(soup, SELLER_SELECTORS)
    stock_status = _first_text(soup, STOCK_SELECTORS)
    return {
        "title": title,
        "mrp": normalize_price(mrp_text),
        "current_price": normalize_price(price_text),
        "buy_box_seller_name": buy_box_seller,
        "stock_status": map_stock_status(stock_status).value,
        "is_js_heavy": not bool(price_text and buy_box_seller),
    }


def parse_offer_listing(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    offers: List[dict] = []
    offer_nodes = soup.select("[data-csa-c-offer-id]") or soup.select("[data-seller-id]")
    for index, offer in enumerate(offer_nodes):
        seller_node = offer.select_one("[data-seller-id]") or offer
        seller_id = seller_node.get("data-seller-id") or offer.get("data-seller-id")
        seller_name = _text(
            offer.select_one("h3")
            or offer.select_one("a[role='link']")
            or offer.find(attrs={"aria-label": True})
        )
        price_node = offer.find(attrs={"data-cy": "price-recipe"}) or offer.find(
            attrs={"aria-label": lambda value: isinstance(value, str) and "₹" in value}
        )
        price_text = _text(price_node) or (price_node.get("aria-label", "") if price_node else "")
        shipping_text = _text(
            offer.find(string=lambda value: isinstance(value, str) and "delivery" in value.lower())
        )
        badge_text = _text(
            offer.find(
                string=lambda value: isinstance(value, str)
                and ("fulfilled by amazon" in value.lower() or "amazon fulfilled" in value.lower())
            )
        )
        condition = _text(
            offer.find(
                string=lambda value: isinstance(value, str)
                and value.strip().lower() in {"new", "used", "renewed"}
            )
        )
        offers.append(
            {
                "seller_name": seller_name,
                "seller_id_amazon": seller_id,
                "price": normalize_price(price_text),
                "shipping_cost": normalize_price(shipping_text),
                "is_fba": detect_fba(badge_text),
                "condition": condition or "new",
                "is_buy_box_winner": index == 0,
            }
        )
    return offers
