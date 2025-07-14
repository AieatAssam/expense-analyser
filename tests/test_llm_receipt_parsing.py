import pytest
from app.core.receipt_prompts import validate_llm_receipt_output, get_prompt, ab_test_prompt, RECEIPT_SCHEMA
import jsonschema

# Example valid output
valid_output = {
    "store_name": "Walmart Supercenter",
    "date": "2025-07-01",
    "total_amount": 5.50,
    "line_items": [
        {"name": "Milk", "category": "Dairy", "amount": 3.50},
        {"name": "Bread", "category": "Bakery", "amount": 2.00}
    ]
}

# Example invalid output (missing line_items)
invalid_output = {
    "store_name": "Walmart Supercenter",
    "date": "2025-07-01",
    "total_amount": 5.50
}

@pytest.mark.parametrize("output,expected", [
    (valid_output, True),
    (invalid_output, False)
])
def test_validate_llm_receipt_output(output, expected):
    assert validate_llm_receipt_output(output) == expected


def test_jsonschema_direct():
    # Should not raise
    jsonschema.validate(instance=valid_output, schema=RECEIPT_SCHEMA)
    # Should raise
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=invalid_output, schema=RECEIPT_SCHEMA)


def test_get_prompt_includes_schema():
    prompt = get_prompt()
    assert "store_name" in prompt
    assert "line_items" in prompt
    assert "amount" in prompt


def test_ab_test_prompt_variations():
    receipt_text = "Walmart Supercenter\n2025-07-01\nMilk $3.50 (Dairy)\nBread $2.00 (Bakery)\nTotal: $5.50"
    prompts = ab_test_prompt(receipt_text, ["default", "grocery"])
    assert "Walmart Supercenter" in prompts["default"]
    assert "Trader Joe's" in prompts["grocery"]
    assert receipt_text in prompts["default"]
    assert receipt_text in prompts["grocery"]

# Example for A/B testing statistical validation (mocked)
def test_ab_testing_statistical_analysis():
    # Simulate two prompt versions and mock LLM outputs
    outputs = [
        {"store_name": "Walmart", "date": "2025-07-01", "total_amount": 5.50, "line_items": [{"name": "Milk", "category": "Dairy", "amount": 3.50}]},
        {"store_name": "Walmart", "date": "2025-07-01", "total_amount": 5.50, "line_items": [{"name": "Milk", "category": "Dairy", "amount": 3.50}]}
    ]
    # All outputs valid
    valid_count = sum(validate_llm_receipt_output(o) for o in outputs)
    assert valid_count == len(outputs)
