from __future__ import annotations

from typing import List

from bs4 import BeautifulSoup

from data_pipeline.normalizer import detect_fba, map_stock_status, normalize_price


def _text(element) -> str:
    return element.get_text(" ", strip=True) if element else ""


def parse_search_results(html: str) -> List[dict]:
    soup = BeautifulSoup(html, "lxml")
    items: List[dict] = []
    for card in soup.select("[data-asin]"):
        asin = (card.get("data-asin") or "").strip()
        if len(asin) != 10:
            continue
        title_el = card.select_one("h2 a span") or card.select_one("h2 span")
        price_container = card.select_one("[data-cy='price-recipe']") or card.find(
            attrs={"aria-label": lambda value: isinstance(value, str) and "₹" in value}
        )
        combined_price = ""
        if price_container:
            combined_price = price_container.get("aria-label", "") or _text(price_container)
        seller_hint = _text(card.find(attrs={"data-csa-c-delivery-price": True}))
        items.append(
            {
                "asin": asin.upper(),
                "title": _text(title_el),
                "price": normalize_price(combined_price),
                "seller_hint": seller_hint,
            }
        )
    return items


def parse_product_page(html: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    title = _text(soup.select_one("#productTitle"))
    mrp_text = _text(soup.find(attrs={"data-a-strike": "true"}))
    price_candidate = (
        soup.find(id="corePrice_feature_div")
        or soup.find(id="corePrice_desktop")
        or soup.find(id="corePriceDisplay_desktop_feature_div")
    )
    price_text = _text(
        price_candidate.find(attrs={"aria-hidden": "true"}) if price_candidate else None
    ) or _text(soup.find(attrs={"data-a-color": "price"}))
    buy_box_seller = _text(
        soup.select_one("#sellerProfileTriggerId")
        or soup.find(attrs={"data-feature-name": "desktop_merchant_info"})
    )
    stock_status = _text(
        soup.select_one("#availability span")
        or soup.find(attrs={"data-feature-name": "availability"})
    )
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
