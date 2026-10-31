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


# Shape of a current amazon.in product page (trimmed from a real response): the live price lives
# in .priceToPay, the MRP is a struck-through .a-text-price, and both repeat their text visibly
# and for screen readers, so a naive float() on the text crashes.
REAL_SHAPE_HTML = """
<span id="productTitle"> SKF 6205-2RS Deep Groove Ball Bearing </span>
<div id="corePrice_feature_div">
  <span class="a-price aok-align-center reinventPricePriceToPayMargin priceToPay">
    <span class="a-offscreen">₹839.00</span>
    <span aria-hidden="true"><span class="a-price-symbol">₹</span><span class="a-price-whole">839</span></span>
  </span>
</div>
<div id="corePriceDisplay_desktop_feature_div">
  M.R.P.:
  <span class="a-price a-text-price" data-a-strike="true">
    <span class="a-offscreen">₹1,999.00</span>
    <span aria-hidden="true">₹1,999</span>
  </span>
</div>
<a id="sellerProfileTriggerId">Clicktech Retail Private Ltd</a>
<div id="availability"><span> In stock </span></div>
"""


def test_parse_product_page_reads_current_amazon_markup():
    product = parse_product_page(REAL_SHAPE_HTML)
    assert product["title"] == "SKF 6205-2RS Deep Groove Ball Bearing"
    assert product["current_price"] == 839.0
    assert product["mrp"] == 1999.0
    assert product["buy_box_seller_name"] == "Clicktech Retail Private Ltd"
    assert product["stock_status"] == StockStatus.IN_STOCK.value
    assert product["is_js_heavy"] is False


def test_normalize_price_handles_real_world_text():
    from data_pipeline.normalizer import normalize_price

    assert normalize_price("₹1,999.00") == 1999.0
    assert normalize_price("₹ 839") == 839.0
    assert normalize_price("₹1,999 ₹1,999") == 1999.0  # the text that used to crash the spider
    assert normalize_price("Currently unavailable") is None
    assert normalize_price("") is None
    assert normalize_price(None) is None
    assert normalize_price(12) == 12.0


def test_empty_or_bot_check_page_yields_no_price_instead_of_raising():
    product = parse_product_page("<html><title>Sorry</title><p>Enter the characters you see</p></html>")
    assert product["current_price"] is None
    assert product["is_js_heavy"] is True


# Trimmed from a real amazon.in search page: result cards carry nested data-asin nodes, and one
# layout keeps only the brand in the first h2 span with the product name in `a > h2`.
REAL_SEARCH_HTML = """
<div data-asin="B01N9I07UE" data-component-type="s-search-result">
  <div data-asin="B01N9I07UE"><h2 class="brand"><span>SKF</span></h2></div>
  <a href="/dp/B01N9I07UE"><h2><span>6205-2Z/C3 Same Day Shipping - Factory New!</span></h2></a>
  <span class="a-price"><span class="a-offscreen">₹4,132</span></span>
</div>
<div data-asin="B0HLPVNKRQ" data-component-type="s-search-result">
  <h2 aria-label="6205 2RS Ball Bearings, Pack of 2"><span>6205 2RS Ball Bearings, Pack of 2</span></h2>
  <span class="a-price"><span class="a-offscreen">₹350</span></span>
</div>
<div data-asin="" data-component-type="s-search-result"><h2><span>Ad slot</span></h2></div>
"""


def test_parse_search_results_reads_current_markup_without_duplicates():
    results = parse_search_results(REAL_SEARCH_HTML)
    assert [item["asin"] for item in results] == ["B01N9I07UE", "B0HLPVNKRQ"]
    assert results[0]["title"] == "6205-2Z/C3 Same Day Shipping - Factory New!"  # not just the brand "SKF"
    assert results[0]["price"] == 4132.0
    assert results[1]["title"] == "6205 2RS Ball Bearings, Pack of 2"
    assert results[1]["price"] == 350.0
