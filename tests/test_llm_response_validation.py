import pytest
from app.core.llm_response_validation import LLMReceiptValidator

valid_output = {
    "store_name": "Walmart Supercenter",
    "date": "2025-07-01",
    "total_amount": 5.50,
    "line_items": [
        {"name": "Milk", "category": "Dairy", "amount": 3.50},
        {"name": "Bread", "category": "Bakery", "amount": 2.00}
    ]
}

invalid_output = {
    "store_name": "Walmart Supercenter",
    "date": "2025-07-01",
    "total_amount": 5.50
}

invalid_date_output = {
    "store_name": "Walmart Supercenter",
    "date": "07-01-2025",
    "total_amount": 5.50,
    "line_items": [
        {"name": "Milk", "category": "Dairy", "amount": 3.50},
        {"name": "Bread", "category": "Bakery", "amount": 2.00}
    ]
}

def test_validate_success():
    validator = LLMReceiptValidator()
    valid, errors = validator.validate(valid_output)
    assert valid
    assert errors == []

def test_validate_schema_failure():
    validator = LLMReceiptValidator()
    valid, errors = validator.validate(invalid_output)
    assert not valid
    assert "Schema validation failed." in errors

def test_validate_date_failure():
    validator = LLMReceiptValidator()
    valid, errors = validator.validate(invalid_date_output)
    assert not valid
    assert any("Invalid date format" in e for e in errors)

def test_validate_total_mismatch():
    bad_total = valid_output.copy()
    bad_total["total_amount"] = 10.00
    validator = LLMReceiptValidator()
    valid, errors = validator.validate(bad_total)
    assert not valid
    assert any("does not match receipt total" in e for e in errors)

def test_confidence_score():
    validator = LLMReceiptValidator()
    assert validator.confidence_score(valid_output) == 1.0
    assert validator.confidence_score(invalid_output) < 1.0
    assert validator.confidence_score(invalid_date_output) < 1.0

def test_map_to_internal():
    validator = LLMReceiptValidator()
    mapped = validator.map_to_internal(valid_output)
    assert mapped["store_name"] == "Walmart Supercenter"
    assert mapped["receipt_date"] == "2025-07-01"
    assert mapped["total_amount"] == 5.50
    assert len(mapped["line_items"]) == 2

def test_fallback_parse():
    validator = LLMReceiptValidator()
    raw_text = "Walmart Supercenter\n2025-07-01\nMilk $3.50 (Dairy)\nBread $2.00 (Bakery)\nTotal: $5.50"
    parsed = validator.fallback_parse(raw_text)
    assert parsed["store_name"] == "Walmart Supercenter"
    assert parsed["date"] == "2025-07-01"
    assert parsed["total_amount"] == 5.50
    assert len(parsed["line_items"]) == 2
