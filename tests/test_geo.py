from datetime import date

from app.geo import circle_polygon, restriction_display_status


def test_restriction_display_status_active_moratorium():
    assert (
        restriction_display_status(
            lifecycle_status="active",
            start_date=date(2026, 1, 1),
            end_date=date(2027, 1, 1),
            on_date=date(2026, 6, 1),
        )
        == "active"
    )


def test_restriction_display_status_proposed():
    assert (
        restriction_display_status(
            lifecycle_status="proposed",
            start_date=None,
            end_date=None,
        )
        == "proposed"
    )


def test_restriction_display_status_expired():
    assert (
        restriction_display_status(
            lifecycle_status="active",
            start_date=date(2024, 1, 1),
            end_date=date(2025, 1, 1),
            on_date=date(2026, 1, 1),
        )
        == "expired"
    )


def test_circle_polygon_closes_ring():
    geometry = circle_polygon(44.0, -93.0, 2.0, points=8)
    ring = geometry["coordinates"][0]
    assert ring[0] == ring[-1]
    assert geometry["type"] == "Polygon"
