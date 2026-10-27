"""
Builders that reproduce India Post's anti-scraping obfuscation for tests.

The live site renders every real value onto a <canvas> (pixels, not text) and keeps
the true string only in the aria-label of the wrapping role="img" span. Alongside each
real value it injects hidden <span data-fake>XX..YY</span> decoys to poison naive
text scraping. These builders recreate that structure with SYNTHETIC data so the
adapter's de-obfuscation can be tested without hitting the network or storing anyone's
real parcel data.
"""
from typing import List, Optional, Sequence, Tuple

# (status, date, time, office, remarks)
Event = Tuple[str, str, str, str, Optional[str]]


def _decoy(seed: str) -> str:
    # A junk token shaped like the real site's decoys: XX<junk>YY
    return f'<span aria-hidden="true" style="position:absolute;left:-9999px;visibility:hidden">' \
           f'<span data-fake="{seed}">XX{seed}junk8x7YY</span></span>'


def cell(value: str, seed: str = "d") -> str:
    """One obfuscated value: real text in aria-label on a canvas span, plus a hidden decoy."""
    return (
        f'<span role="img" aria-label="{value}">'
        f'<canvas aria-hidden="true" width="120" height="30"></canvas></span>'
        f'{_decoy(seed)}'
    )


def _summary_row(label: str, value: str, seed: str) -> str:
    return f'<div class="summary-row"><span class="lbl">{label}</span>{cell(value, seed)}</div>'


def build_india_post_page(
    *,
    article_number: str = "EY672780687IN",
    article_type: str = "SP_INLAND_DOC",
    booked_at: str = "Goregaon RS SO",
    destination: str = "Tivim S.O",
    origin_pincode: str = "400104",
    destination_pincode: str = "403502",
    events: Sequence[Event],
    column_order: str = "event_first",
    include_summary_divs: bool = True,
    include_summary_table: bool = False,
) -> str:
    """Render a full obfuscated India Post result page for tests.

    column_order:
      - "event_first": Event | Date | Time | Office | Remarks (the real current layout)
      - "date_first":  Date | Time | Office | Event           (an older layout)
    """
    if column_order == "event_first":
        header = ["Event", "Date", "Time", "Office", "Remarks"]
        def row(ev: Event) -> List[str]:
            s, d, t, o, r = ev
            return [s, d, t, o, r if r is not None else "-"]
    elif column_order == "date_first":
        header = ["Date", "Time", "Office", "Event"]
        def row(ev: Event) -> List[str]:
            s, d, t, o, _ = ev
            return [d, t, o, s]
    else:
        raise ValueError(f"unknown column_order {column_order!r}")

    head_html = "".join(f"<th>{h}</th>" for h in header)
    rows_html = ""
    for i, ev in enumerate(events):
        tds = "".join(f"<td>{cell(v, f'r{i}c{j}')}</td>" for j, v in enumerate(row(ev)))
        rows_html += f"<tr>{tds}</tr>"
    table_html = f"<table><tr>{head_html}</tr>{rows_html}</table>"

    summary_divs = ""
    if include_summary_divs:
        summary_divs = (
            _summary_row("Article Number:", article_number, "an")
            + _summary_row("Article Type:", article_type, "at")
            + _summary_row("Booked At:", booked_at, "ba")
            + _summary_row("Destination:", destination, "de")
            + _summary_row("Origin Pincode:", origin_pincode, "op")
            + _summary_row("Destination Pincode:", destination_pincode, "dp")
        )

    summary_table = ""
    if include_summary_table:
        # Older layout: summary carried in a table (Booked At | Booked On | Destination Pincode | Article Type)
        summary_table = (
            "<table><tr><th>Booked At</th><th>Booked On</th>"
            "<th>Destination Pincode</th><th>Article Type</th></tr>"
            f"<tr><td>{cell(booked_at,'sba')}</td><td>{cell('22/10/2026','sbo')}</td>"
            f"<td>{cell(destination_pincode,'sdp')}</td><td>{cell(article_type,'sat')}</td></tr></table>"
        )

    return f"""<!doctype html><html><body>
      <div id="result">{summary_divs}{summary_table}{table_html}</div>
    </body></html>"""


# A convenient default event list: a parcel that ends on hold (EXCEPTION).
ON_HOLD_EVENTS: List[Event] = [
    ("Item Booked", "22/10/2026", "17:35:49", "Goregaon RS SO", None),
    ("Item bagged", "22/10/2026", "18:09:46", "Goregaon RS SO", None),
    ("Item Dispatched", "22/10/2026", "18:18:01", "Goregaon RS SO", None),
    ("Bag Received", "22/10/2026", "22:27:40", "Mumbai NSH", None),
    ("Item received at Destination", "26/10/2026", "09:32:02", "Tivim S.O", None),
    ("Taken out for delivery", "26/10/2026", "10:56:27", "Tivim S.O", None),
    ("Item Kept on Hold", "26/10/2026", "19:26:43", "Tivim S.O", "Addressee Absent[For enquiry]"),
]

# A parcel that ends delivered.
DELIVERED_EVENTS: List[Event] = [
    ("Item Booked", "05/08/2026", "12:15:00", "Panaji NSH", None),
    ("Bag Received", "06/08/2026", "08:30:00", "Bicholim S.O", None),
    ("Taken out for delivery", "07/08/2026", "10:00:00", "Bambavada S.O", None),
    ("Item Delivered", "07/08/2026", "14:30:00", "Bambavada S.O", "Delivered to addressee"),
]
