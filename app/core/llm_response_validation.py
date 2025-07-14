import re
from typing import Any, Dict, List, Tuple
from app.core.receipt_prompts import validate_llm_receipt_output, RECEIPT_SCHEMA
from datetime import datetime

class LLMReceiptValidator:
    """
    Validates and maps LLM receipt parsing responses to internal models.
    Implements schema validation, business logic checks, confidence scoring, and fallback parsing.
    """
    def __init__(self, schema=RECEIPT_SCHEMA):
        self.schema = schema

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate LLM output against schema and business rules."""
        errors = []
        # Schema validation
        if not validate_llm_receipt_output(data):
            errors.append("Schema validation failed.")
        # Business logic validation
        if "date" in data:
            if not self._validate_date(data["date"]):
                errors.append(f"Invalid date format: {data['date']}")
        if "total_amount" in data and "line_items" in data:
            total = sum(item.get("amount", 0) for item in data["line_items"])
            if abs(total - data["total_amount"]) > 0.01:
                errors.append(f"Line items total ({total}) does not match receipt total ({data['total_amount']})")
        return (len(errors) == 0, errors)

    def _validate_date(self, date_str: str) -> bool:
        """Check if date is in YYYY-MM-DD format."""
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except Exception:
            return False

    def confidence_score(self, data: Dict[str, Any]) -> float:
        """Simple confidence scoring based on field presence and validation."""
        score = 1.0
        if not validate_llm_receipt_output(data):
            score -= 0.5
        if "date" in data and not self._validate_date(data["date"]):
            score -= 0.2
        if "total_amount" in data and "line_items" in data:
            total = sum(item.get("amount", 0) for item in data["line_items"])
            if abs(total - data["total_amount"]) > 0.01:
                score -= 0.2
        return max(score, 0.0)

    def map_to_internal(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Map LLM output to internal receipt and line item models."""
        receipt = {
            "store_name": data.get("store_name"),
            "receipt_date": data.get("date"),
            "total_amount": data.get("total_amount"),
            "line_items": [
                {
                    "name": item.get("name"),
                    "category": item.get("category"),
                    "amount": item.get("amount"),
                }
                for item in data.get("line_items", [])
            ]
        }
        return receipt

    def fallback_parse(self, raw_text: str) -> Dict[str, Any]:
        """Fallback parsing for malformed LLM responses using regex heuristics."""
        # Very basic fallback: extract store name, date, total, and line items
        lines = raw_text.splitlines()
        store_name = lines[0] if lines else "Unknown"
        date_match = re.search(r"\d{4}-\d{2}-\d{2}", raw_text)
        date = date_match.group(0) if date_match else "1970-01-01"
        total_match = re.search(r"Total[:]?\s*\$?(\d+\.\d{2})", raw_text)
        total = float(total_match.group(1)) if total_match else 0.0
        line_items = []
        for line in lines[1:]:
            m = re.match(r"(.+)\s+\$([\d\.]+)\s*\((.+)\)", line)
            if m:
                line_items.append({
                    "name": m.group(1).strip(),
                    "category": m.group(3).strip(),
                    "amount": float(m.group(2))
                })
        return {
            "store_name": store_name,
            "date": date,
            "total_amount": total,
            "line_items": line_items
        }
