import re

# Validation rules
VALIDATION_RULES = {
    "create_order": {
        "required": ["items", "address"],
        "items": {
            "type": list,
            "min_length": 1,
            "item_schema": {
                "required": ["id"],
                "id": {"type": str, "min_length": 1}
            }
        },
        "address": {
            "type": dict,
            "required": ["full_name", "phone", "address_line1", "city", "state", "pincode"],
            "full_name": {"type": str, "min_length": 1, "max_length": 100},
            "phone": {"type": str, "pattern": r"^[0-9]{10}$"},
            "address_line1": {"type": str, "min_length": 1},
            "city": {"type": str, "min_length": 1},
            "state": {"type": str, "min_length": 1},
            "pincode": {"type": str, "pattern": r"^[0-9]{6}$"}
        }
    },
    "add_to_cart": {
        "required": ["id"],
        "id": {"type": str, "min_length": 1}
    },
    "add_address": {
        "required": ["full_name", "phone", "address_line1", "city", "state", "pincode"],
        "full_name": {"type": str, "min_length": 1, "max_length": 100},
        "phone": {"type": str, "pattern": r"^[0-9]{10}$"},
        "address_line1": {"type": str, "min_length": 1},
        "city": {"type": str, "min_length": 1},
        "state": {"type": str, "min_length": 1},
        "pincode": {"type": str, "pattern": r"^[0-9]{6}$"}
    },
    "update_profile": {
        "display_name": {"type": str, "min_length": 1, "max_length": 100},
        "phone": {"type": str, "pattern": r"^[0-9]{10}$"},
        "bio": {"type": str, "max_length": 500}
    },
    "create_payment": {
        "required": ["order_id", "amount"],
        "order_id": {"type": str, "min_length": 1},
        "amount": {"type": (int, float), "minimum": 1}
    },
    "create_return": {
        "required": ["order_id", "reason"],
        "order_id": {"type": str, "min_length": 1},
        "reason": {"type": str, "min_length": 1}
    },
    "create_review": {
        "required": ["rating", "comment"],
        "rating": {"type": int, "minimum": 1, "maximum": 5},
        "title": {"type": str, "max_length": 200},
        "comment": {"type": str, "min_length": 1}
    },
    "add_product": {
        "required": ["id", "name", "price", "category", "stock_quantity", "description", "rating"],
        "id": {"type": str, "min_length": 1},
        "name": {"type": str, "min_length": 1, "max_length": 200},
        "price": {"type": (int, float), "minimum": 0},
        "category": {"type": str, "min_length": 1},
        "stock_quantity": {"type": int, "minimum": 0},
        "description": {"type": str, "min_length": 1},
        "rating": {"type": (int, float), "minimum": 0, "maximum": 5}
    }
}


def validate_field(value, rules, field_name):
    """Validate a single field against its rules."""
    # Type check
    expected_type = rules.get("type")
    if expected_type:
        # bool is a subclass of int — reject booleans when int/float is expected
        if isinstance(value, bool) and expected_type in ((int, float), int, float):
            raise ValueError(f"{field_name} must be a number, not a boolean")
        if not isinstance(value, expected_type):
            type_name = expected_type.__name__ if hasattr(expected_type, '__name__') else str(expected_type)
            raise ValueError(f"{field_name} must be of type {type_name}")

    # String validations
    if isinstance(value, str):
        if "min_length" in rules and len(value.strip()) < rules["min_length"]:
            raise ValueError(f"{field_name} must not be empty")
        if "max_length" in rules and len(value) > rules["max_length"]:
            raise ValueError(f"{field_name} must be at most {rules['max_length']} characters")
        if "pattern" in rules and not re.match(rules["pattern"], value):
            raise ValueError(f"{field_name} format is invalid")

    # Number validations
    if isinstance(value, (int, float)):
        if "minimum" in rules and value < rules["minimum"]:
            if field_name == "amount":
                raise ValueError(f"{field_name} must be positive")
            elif field_name == "rating":
                raise ValueError(f"{field_name} must be between 1 and 5")
            else:
                raise ValueError(f"{field_name} must be at least {rules['minimum']}")
        if "maximum" in rules and value > rules["maximum"]:
            if field_name == "rating":
                raise ValueError(f"{field_name} must be between 1 and 5")
            else:
                raise ValueError(f"{field_name} must be at most {rules['maximum']}")

    # Enum validation
    if "enum" in rules and value not in rules["enum"]:
        raise ValueError(f"{field_name} must be one of: {', '.join(rules['enum'])}")

    # Dict validation — recurse into sub-fields
    if isinstance(value, dict) and "required" in rules:
        for req_field in rules["required"]:
            if req_field not in value:
                raise ValueError(f"{field_name}.{req_field} is required")
        for sub_field, sub_value in value.items():
            if sub_field in rules and sub_field != "required":
                validate_field(sub_value, rules[sub_field], f"{field_name}.{sub_field}")

    # List validation
    if isinstance(value, list):
        if "min_length" in rules and len(value) < rules["min_length"]:
            raise ValueError(f"{field_name} must not be empty")
        if "item_schema" in rules:
            for i, item in enumerate(value):
                if not isinstance(item, dict):
                    raise ValueError(f"{field_name}[{i}] must be an object")
                item_rules = rules["item_schema"]
                # Check required fields in list items
                if "required" in item_rules:
                    for req_field in item_rules["required"]:
                        if req_field not in item:
                            raise ValueError(f"{field_name}[{i}].{req_field} is required")
                        if req_field in item_rules:
                            validate_field(item[req_field], item_rules[req_field], f"{field_name}[{i}].{req_field}")


def validate(data, schema_name):
    """Validate data against schema using simple Python validation."""
    if data is None:
        raise ValueError("Data cannot be None")
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")
    if schema_name not in VALIDATION_RULES:
        raise ValueError(f"Unknown validation schema: {schema_name}")

    rules = VALIDATION_RULES[schema_name]

    # Check required fields
    if "required" in rules:
        for field in rules["required"]:
            if field not in data:
                raise ValueError(f"Field '{field}' is required")

    # Validate each field present in data
    for field, value in data.items():
        if field == "required":
            continue
        if field in rules:
            field_rules = rules[field]
            validate_field(value, field_rules, field)

    return True
