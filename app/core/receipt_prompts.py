import jsonschema
import json
from typing import Dict, Any, List

# JSON schema for LLM receipt parsing output
RECEIPT_SCHEMA = {
    "type": "object",
    "properties": {
        "store_name": {"type": "string"},
        "date": {"type": "string", "format": "date"},
        "total_amount": {"type": "number"},
        "line_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "category": {"type": "string"},
                    "amount": {"type": "number"}
                },
                "required": ["name", "category", "amount"]
            }
        }
    },
    "required": ["store_name", "date", "total_amount", "line_items"]
}

# Prompt templates with few-shot examples
PROMPT_TEMPLATES = {
    "default": {
        "version": "v1",
        "prompt": """
You are an expert at parsing receipts. Extract the following fields from the receipt text:
- Store name
- Date (YYYY-MM-DD)
- Total amount
- Line items (name, category, amount)

Return the result as a JSON object matching this schema:
{schema}

Example:
Receipt:
Walmart Supercenter
2025-07-01
Milk $3.50 (Dairy)
Bread $2.00 (Bakery)
Total: $5.50

JSON:
{{
  "store_name": "Walmart Supercenter",
  "date": "2025-07-01",
  "total_amount": 5.50,
  "line_items": [
    {{"name": "Milk", "category": "Dairy", "amount": 3.50}},
    {{"name": "Bread", "category": "Bakery", "amount": 2.00}}
  ]
}}
"""
    },
    "grocery": {
        "version": "v1",
        "prompt": """
Extract grocery receipt details as JSON. Fields: store_name, date, total_amount, line_items (name, category, amount).
Example:
Receipt:
Trader Joe's
2025-07-02
Eggs $4.00 (Dairy)
Apples $3.00 (Produce)
Total: $7.00

JSON:
{{
  "store_name": "Trader Joe's",
  "date": "2025-07-02",
  "total_amount": 7.00,
  "line_items": [
    {{"name": "Eggs", "category": "Dairy", "amount": 4.00}},
    {{"name": "Apples", "category": "Produce", "amount": 3.00}}
  ]
}}
"""
    }
}


def validate_llm_receipt_output(data: Dict[str, Any]) -> bool:
    """Validate LLM output against the receipt schema."""
    try:
        jsonschema.validate(instance=data, schema=RECEIPT_SCHEMA)
        return True
    except jsonschema.ValidationError:
        return False


def get_prompt(receipt_type: str = "default", version: str = "v1") -> str:
    """Get prompt template for a given receipt type and version."""
    template = PROMPT_TEMPLATES.get(receipt_type, PROMPT_TEMPLATES["default"])
    if template["version"] == version:
        return template["prompt"].replace("{schema}", json.dumps(RECEIPT_SCHEMA, indent=2))
    return PROMPT_TEMPLATES["default"]["prompt"].replace("{schema}", json.dumps(RECEIPT_SCHEMA, indent=2))


def ab_test_prompt(receipt_text: str, types: List[str]) -> Dict[str, str]:
    """Return prompts for A/B testing across different types."""
    return {t: get_prompt(t) + f"\nReceipt:\n{receipt_text}" for t in types}
