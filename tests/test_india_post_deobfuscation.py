"""
Unit tests for the India Post anti-scraping de-obfuscation.

Contract under test (the reason this adapter exists): India Post hides real values on
<canvas> with the true text in aria-label, and injects hidden [data-fake] XX..YY decoys.
The adapter must return the REAL values and must never leak a decoy.
"""
import re
import pytest
from bs4 import BeautifulSoup

from backend.carriers.india_post_web import IndiaPostWebAdapter
from backend.carriers.base import BaseCarrierAdapter
from tests.india_post_fixtures import (
    build_india_post_page, cell, ON_HOLD_EVENTS, DELIVERED_EVENTS,
)

DECOY = re.compile(r"XX[0-9A-Za-z×]+?YY")


@pytest.fixture
def adapter():
    return IndiaPostWebAdapter(headless=True)


def _frag(html: str):
    return BeautifulSoup(html, "html.parser")


# --- _real_text: the core de-obfuscation primitive ---------------------------------

def test_real_text_reads_aria_label_not_canvas(adapter):
    el = _frag(cell("Tivim S.O")).find("div") or _frag(cell("Tivim S.O"))
    assert adapter._real_text(_frag(cell("Tivim S.O"))) == "Tivim S.O"


def test_real_text_drops_decoy_spans(adapter):
    text = adapter._real_text(_frag(cell("Item Booked", seed="poison")))
    assert text == "Item Booked"
    assert "XX" not in text and "poison" not in text


def test_real_text_joins_multiple_values_in_order(adapter):
    html = f"<div>{cell('Goregaon RS SO')}{cell('(400104)')}</div>"
    assert adapter._real_text(_frag(html).find("div")) == "Goregaon RS SO (400104)"


def test_real_text_falls_back_to_plain_text_and_strips_decoys(adapter):
    # If a value is served as plain text (no canvas), decoys are still stripped.
    html = "<td>Mumbai NSH<span>XXdecoy123YY</span></td>"
    assert adapter._real_text(_frag(html).find("td")) == "Mumbai NSH"


def test_real_text_handles_none(adapter):
    assert adapter._real_text(None) == ""


# --- Full page extraction ----------------------------------------------------------

def test_extract_on_hold_parcel_is_clean_and_exception(adapter):
    html = build_india_post_page(events=ON_HOLD_EVENTS)
    result = adapter.extract_table_data(html, "EY672780687IN")
    events, details = result["events"], result["details"]

    assert len(events) == len(ON_HOLD_EVENTS)
    assert events[0]["status"] == "Item Booked"
    assert events[0]["location"] == "Goregaon RS SO"
    assert events[0]["date"] == "22/10/2026"
    assert events[0]["time"] == "17:35:49"
    # Latest event is "Item Kept on Hold" -> EXCEPTION
    assert details["status"] == BaseCarrierAdapter.STATUS_EXCEPTION
    assert details["origin"] == "Goregaon RS SO"
    assert details["destination"] == "Tivim S.O"
    assert details["article_type"] == "SP_INLAND_DOC"


def test_extract_delivered_parcel(adapter):
    html = build_india_post_page(events=DELIVERED_EVENTS, article_type="Speed Post",
                                 booked_at="Panaji NSH", destination="Bambavada S.O")
    result = adapter.extract_table_data(html, "EM740043207IN")
    assert result["details"]["status"] == BaseCarrierAdapter.STATUS_DELIVERED
    assert len(result["events"]) == 4


def test_no_decoy_ever_leaks_into_any_field(adapter):
    html = build_india_post_page(events=ON_HOLD_EVENTS)
    result = adapter.extract_table_data(html, "EY672780687IN")
    blob = str(result)
    assert not DECOY.search(blob), "a decoy token leaked into the parsed result"
    assert "junk" not in blob.lower()


def test_remarks_dash_is_treated_as_empty(adapter):
    html = build_india_post_page(events=ON_HOLD_EVENTS)
    result = adapter.extract_table_data(html, "EY672780687IN")
    booked = result["events"][0]
    # "Item Booked" had remarks "-"; description should fall back, not be "-"
    assert booked["description"] != "-"


# --- Robustness: column order & summary source -------------------------------------

def test_column_order_independence_event_first_vs_date_first(adapter):
    a = adapter.extract_table_data(build_india_post_page(events=ON_HOLD_EVENTS, column_order="event_first"), "EY672780687IN")
    b = adapter.extract_table_data(build_india_post_page(events=ON_HOLD_EVENTS, column_order="date_first"), "EY672780687IN")
    norm = lambda r: [(e["status"], e["date"], e["location"]) for e in r["events"]]
    assert norm(a) == norm(b)


def test_summary_from_table_fallback_when_no_div_labels(adapter):
    html = build_india_post_page(events=ON_HOLD_EVENTS, include_summary_divs=False, include_summary_table=True)
    result = adapter.extract_table_data(html, "EY672780687IN")
    assert result["details"]["origin"] == "Goregaon RS SO"
    assert result["details"]["article_type"] == "SP_INLAND_DOC"


def test_empty_page_yields_no_events(adapter):
    result = adapter.extract_table_data("<html><body><p>No records found.</p></body></html>", "EM740043207IN")
    assert result["events"] == []
    assert result["details"]["status"] == BaseCarrierAdapter.STATUS_UNKNOWN
