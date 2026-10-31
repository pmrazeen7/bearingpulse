from data_pipeline.normalizer import StockStatus
from data_pipeline.parser import parse_offer_listing, parse_product_page, parse_search_results


SEARCH_HTML = """
<div data-asin="B012345678">
  <h2><a><span>SKF 6205 Bearing</span></a></h2>
  <div data-cy="price-recipe" aria-label="₹1,234.00"></div>
  <span data-csa-c-delivery-price="1">Seller hint</span>
</div>
<div data-asin="">
  <h2><span>Ignored</span></h2>
</div>
"""

PRODUCT_HTML = """
<span id="productTitle">SKF 6205 Deep Groove Ball Bearing</span>
<span data-a-strike="true">₹1,500.00</span>
<div id="corePrice_feature_div"><span aria-hidden="true">₹1,234.00</span></div>
<a id="sellerProfileTriggerId">Bearing Hub</a>
<div id="availability"><span>Only 3 left in stock.</span></div>
"""

OFFER_HTML = """
<div data-csa-c-offer-id="1" data-seller-id="SELLER1">
  <h3>Seller One</h3>
  <div data-cy="price-recipe" aria-label="₹1,200.00"></div>
  <span>Fulfilled by Amazon</span>
  <span>New</span>
</div>
<div data-csa-c-offer-id="2" data-seller-id="SELLER2">
  <h3>Seller Two</h3>
  <div data-cy="price-recipe" aria-label="₹1,250.00"></div>
  <span>Used</span>
</div>
"""


def test_parse_search_results_extracts_valid_asins():
    results = parse_search_results(SEARCH_HTML)
    assert len(results) == 1
    assert results[0]["asin"] == "B012345678"
    assert results[0]["price"] == 1234.0


def test_parse_product_page_extracts_core_fields():
    product = parse_product_page(PRODUCT_HTML)
    assert product["title"] == "SKF 6205 Deep Groove Ball Bearing"
    assert product["mrp"] == 1500.0
    assert product["current_price"] == 1234.0
    assert product["buy_box_seller_name"] == "Bearing Hub"


def test_parse_product_page_maps_low_stock():
    product = parse_product_page(PRODUCT_HTML)
    assert product["stock_status"] == StockStatus.LOW_STOCK.value


def test_parse_offer_listing_extracts_all_sellers():
    offers = parse_offer_listing(OFFER_HTML)
    assert len(offers) == 2
    assert offers[0]["seller_id_amazon"] == "SELLER1"
    assert offers[1]["seller_name"] == "Seller Two"


def test_parse_offer_listing_marks_first_offer_as_buybox():
    offers = parse_offer_listing(OFFER_HTML)
    assert offers[0]["is_buy_box_winner"] is True
    assert offers[1]["is_buy_box_winner"] is False
