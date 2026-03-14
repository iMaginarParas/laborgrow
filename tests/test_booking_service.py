"""
Unit tests for BookingService.calculate_pricing.

Run with:
    python -m pytest tests/ -v
"""
import pytest
from services.booking_service import BookingService


class TestCalculatePricing:
    """Suite for the core pricing formula used in every booking."""

    def test_standard_pricing(self):
        result = BookingService.calculate_pricing(hourly_rate=500.0, hours=2)
        assert result["base_amount"]     == 1000.0,  "base should be rate * hours"
        assert result["platform_fee"]    == 50.0,    "platform fee is always ₹50"
        assert result["discount_amount"] == 0.0,     "no discount for repeat customers"
        assert result["total_amount"]    == 1050.0,  "total = base + fee"

    def test_first_booking_discount(self):
        result = BookingService.calculate_pricing(
            hourly_rate=500.0, hours=2, is_first_booking=True
        )
        expected_discount = 1000.0 * 0.20   # 20% of base
        assert result["discount_amount"] == expected_discount
        assert result["total_amount"]    == 1000.0 + 50.0 - expected_discount

    def test_minimum_one_hour(self):
        result = BookingService.calculate_pricing(hourly_rate=300.0, hours=1)
        assert result["base_amount"] == 300.0
        assert result["total_amount"] == 350.0

    def test_zero_hourly_rate_no_crash(self):
        result = BookingService.calculate_pricing(hourly_rate=0.0, hours=5)
        assert result["base_amount"]  == 0.0
        assert result["total_amount"] == 50.0   # only platform fee


class TestGenerateBookingRef:
    """Ref format: LBG-<year>-<4digit random>"""

    def test_format(self):
        ref = BookingService.generate_booking_ref()
        parts = ref.split("-")
        assert len(parts) == 3,              "format must be LBG-YYYY-NNNN"
        assert parts[0] == "LBG"
        assert len(parts[1]) == 4,           "year must be 4 digits"
        assert len(parts[2]) == 4,           "random suffix must be 4 digits"
        assert parts[2].isdigit()

    def test_uniqueness(self):
        refs = {BookingService.generate_booking_ref() for _ in range(100)}
        # At least some randomness — not all identical
        assert len(refs) > 1
