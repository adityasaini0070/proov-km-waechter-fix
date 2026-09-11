# test_km_wachter.py
from km_wachter import needs_service, wear_percent, SERVICE_INTERVAL_KM


def test_almost_due_car_is_flagged():
    # A car at 14,900 of its 15,000 km window is about 99% worn and MUST be flagged.
    assert needs_service({"id": "VOS-4471", "odometer": 14900, "last_service_km": 0}) is True


def test_missing_reading_is_not_treated_as_zero():
    # A car with NO last-service reading must not be treated as fully worn.
    assert needs_service({"id": "VOS-7788", "odometer": 92000}) is False


# --- wear_percent correctness ---

def test_wear_percent_zero():
    # 0 km driven → 0% wear
    assert wear_percent(0, SERVICE_INTERVAL_KM) == 0.0


def test_wear_percent_half_interval():
    # 7,500 km out of 15,000 → exactly 50%
    assert wear_percent(7500, SERVICE_INTERVAL_KM) == 50.0


def test_wear_percent_full_interval():
    # 15,000 km out of 15,000 → exactly 100%
    assert wear_percent(15000, SERVICE_INTERVAL_KM) == 100.0


def test_wear_percent_fractional():
    # 14,900 km out of 15,000 → 99.333…%; must NOT be rounded down to 0 (was the bug)
    result = wear_percent(14900, SERVICE_INTERVAL_KM)
    assert 99.0 < result < 100.0


def test_wear_percent_over_interval():
    # 30,000 km (two full intervals) → 200%
    assert wear_percent(30000, SERVICE_INTERVAL_KM) == 200.0


def test_wear_threshold_at_exactly_80_percent():
    # 12,000 km is exactly 80% of 15,000 → must be flagged (>= threshold)
    assert needs_service({"id": "VOS-TEST", "odometer": 12000, "last_service_km": 0}) is True


def test_wear_threshold_just_below_80_percent():
    # 11,999 km is just under 80% → must NOT be flagged
    assert needs_service({"id": "VOS-TEST", "odometer": 11999, "last_service_km": 0}) is False
