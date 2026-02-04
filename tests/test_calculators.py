from app.main import MouldingQuoteInput, ToolingQuoteInput
from app.main import calculate_moulding_quote, calculate_tooling_quote


def test_tooling_quote_calculator():
    payload = ToolingQuoteInput(
        engineering_hours=10,
        machining_hours=20,
        labor_rate_per_hour=50,
        material_cost=1000,
        component_cost=500,
        overhead_rate=0.1,
        margin_rate=0.2,
    )
    result = calculate_tooling_quote(payload)

    assert result.labor_subtotal == 1500
    assert result.overhead == 150
    assert result.total == 3780


def test_moulding_quote_calculator():
    payload = MouldingQuoteInput(
        part_weight_kg=0.1,
        material_cost_per_kg=3,
        cycle_time_seconds=30,
        machine_rate_per_hour=60,
        scrap_rate=0.05,
        packaging_cost_per_unit=0.1,
        margin_rate=0.2,
    )
    result = calculate_moulding_quote(payload)

    assert round(result.shots_per_hour, 2) == 120.0
    assert round(result.unit_cost, 4) == 0.935
    assert round(result.quoted_unit_price, 4) == 1.122
