"""
Tests for validation.py
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

from validation import validate


def test_validate_create_order_success():
    validate({
        'items': [{'id': '1'}, {'id': '2', 'variant_id': 'var_1'}],
        'address': {
            'full_name': 'John Doe', 'phone': '9876543210',
            'address_line1': '123 Main St', 'city': 'Mumbai',
            'state': 'Maharashtra', 'pincode': '400001'
        }
    }, 'create_order')


def test_validate_create_order_missing_items():
    with pytest.raises(ValueError, match="'items' is required"):
        validate({'address': {'full_name': 'John', 'phone': '9876543210',
                              'address_line1': '123 St', 'city': 'Mumbai',
                              'state': 'MH', 'pincode': '400001'}}, 'create_order')


def test_validate_create_order_missing_address():
    with pytest.raises(ValueError, match="'address' is required"):
        validate({'items': [{'id': '1'}]}, 'create_order')


def test_validate_create_order_empty_items():
    with pytest.raises(ValueError, match="items must not be empty"):
        validate({'items': [], 'address': {'full_name': 'John', 'phone': '9876543210',
                                           'address_line1': '123 St', 'city': 'Mumbai',
                                           'state': 'MH', 'pincode': '400001'}}, 'create_order')


def test_validate_create_payment_success():
    validate({'order_id': 'order_123', 'amount': 1000}, 'create_payment')


def test_validate_create_payment_missing_order_id():
    with pytest.raises(ValueError, match="'order_id' is required"):
        validate({'amount': 1000}, 'create_payment')


def test_validate_create_payment_missing_amount():
    with pytest.raises(ValueError, match="'amount' is required"):
        validate({'order_id': 'order_123'}, 'create_payment')


def test_validate_create_payment_invalid_amount():
    with pytest.raises(ValueError, match="amount must be of type"):
        validate({'order_id': 'order_123', 'amount': 'invalid'}, 'create_payment')


def test_validate_create_payment_negative_amount():
    with pytest.raises(ValueError, match="amount must be positive"):
        validate({'order_id': 'order_123', 'amount': -100}, 'create_payment')


def test_validate_create_review_success():
    validate({'rating': 5, 'title': 'Great!', 'comment': 'Excellent product.'}, 'create_review')


def test_validate_create_review_missing_rating():
    with pytest.raises(ValueError, match="'rating' is required"):
        validate({'comment': 'Great product!'}, 'create_review')


def test_validate_create_review_missing_comment():
    with pytest.raises(ValueError, match="'comment' is required"):
        validate({'rating': 5}, 'create_review')


def test_validate_create_review_invalid_rating_low():
    with pytest.raises(ValueError, match="rating must be between 1 and 5"):
        validate({'rating': 0, 'comment': 'Bad'}, 'create_review')


def test_validate_create_review_invalid_rating_high():
    with pytest.raises(ValueError, match="rating must be between 1 and 5"):
        validate({'rating': 6, 'comment': 'Great'}, 'create_review')


def test_validate_create_review_empty_comment():
    with pytest.raises(ValueError, match="comment must not be empty"):
        validate({'rating': 5, 'comment': ''}, 'create_review')


def test_validate_create_return_success():
    validate({'order_id': 'order_123', 'reason': 'Product damaged'}, 'create_return')


def test_validate_create_return_missing_order_id():
    with pytest.raises(ValueError, match="'order_id' is required"):
        validate({'reason': 'Product damaged'}, 'create_return')


def test_validate_create_return_missing_reason():
    with pytest.raises(ValueError, match="'reason' is required"):
        validate({'order_id': 'order_123'}, 'create_return')


def test_validate_create_return_empty_reason():
    with pytest.raises(ValueError, match="reason must not be empty"):
        validate({'order_id': 'order_123', 'reason': ''}, 'create_return')


def test_validate_unknown_schema():
    with pytest.raises(ValueError, match="Unknown validation schema"):
        validate({'test': 'data'}, 'unknown_schema')


def test_validate_none_data():
    with pytest.raises(ValueError, match="Data cannot be None"):
        validate(None, 'create_order')


def test_validate_wrong_type_string():
    with pytest.raises(ValueError, match="Data must be a dictionary"):
        validate('string', 'create_order')


def test_validate_wrong_type_list():
    with pytest.raises(ValueError, match="Data must be a dictionary"):
        validate(['list'], 'create_order')


def test_validate_extra_fields_allowed():
    # Extra fields should not raise
    validate({'order_id': 'order_123', 'amount': 1000, 'extra_field': 'ignored'}, 'create_payment')


def test_validate_nested_validation():
    validate({
        'items': [{'id': '1'}, {'id': '2'}],
        'address': {
            'full_name': 'John Doe', 'phone': '9876543210',
            'address_line1': '123 Main St', 'city': 'Mumbai',
            'state': 'Maharashtra', 'pincode': '400001',
            'extra_field': 'allowed'
        }
    }, 'create_order')


def test_validate_type_coercion_strict():
    # String amount should raise (strict validation)
    with pytest.raises(ValueError):
        validate({'order_id': 'order_123', 'amount': '1000'}, 'create_payment')


def test_validate_rating_boundary_values():
    validate({'rating': 1, 'comment': 'Poor product'}, 'create_review')
    validate({'rating': 5, 'comment': 'Excellent product'}, 'create_review')


def test_validate_long_strings():
    # No max length on comment — should pass
    validate({'rating': 5, 'comment': 'A' * 10000}, 'create_review')


def test_validate_special_characters():
    validate({'rating': 5, 'comment': 'Great! <script>alert("xss")</script>'}, 'create_review')


def test_validate_unicode_characters():
    validate({'rating': 5, 'comment': 'बहुत अच्छा उत्पाद! 很好的产品！'}, 'create_review')


def test_validate_whitespace_only_comment():
    # Whitespace-only comment should fail (min_length check strips)
    with pytest.raises(ValueError, match="comment must not be empty"):
        validate({'rating': 5, 'comment': '   '}, 'create_review')
