# test_fleet_report.py
from fleet_report import fleet_summary

SAMPLE = [
    {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
    {"id": "VOS-2210", "odometer": 48400, "last_service_km": 45000},
]


def test_summary_counts_due_cars():
    # Only VOS-4471 is nearly worn, so exactly one car is due.
    assert fleet_summary(SAMPLE)["due"] == 1


def test_summary_no_crash_when_last_service_km_missing():
    # A car with no "last_service_km" key must not cause fleet_summary to crash.
    # VOS-7788 has no service reading; it should count as 0% worn (just serviced).
    fleet = [
        {"id": "VOS-7788", "odometer": 92000},
        {"id": "VOS-4471", "odometer": 14900, "last_service_km": 0},
    ]
    result = fleet_summary(fleet)
    assert result["count"] == 2
    # VOS-7788 is treated as freshly serviced → 0% wear, not due
    # VOS-4471 is at 99% → due
    assert result["due"] == 1
