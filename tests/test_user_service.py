import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

import pytest
import boto3
from moto import mock_aws
import json
from user_service import lambda_handler, convert_decimal


def create_user_event(path, method, body=None, user_id='user1', user_email='user@example.com'):
    """Helper to create user event with proper JWT claims."""
    event = {
        'rawPath': path,
        'requestContext': {
            'http': {'method': method},
            'authorizer': {
                'jwt': {
                    'claims': {
                        'sub': user_id,
                        'email': user_email
                    }
                }
            }
        }
    }
    if body:
        event['body'] = json.dumps(body)
    return event


@mock_aws
class TestUserService:
    def setup_method(self, method):
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        self.cart_table = dynamodb.create_table(
            TableName='cart_table_guru',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        self.product_table = dynamodb.create_table(
            TableName='products_table_guru',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        self.user_data_table = dynamodb.create_table(
            TableName='user_data_table_guru',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        self.wishlist_table = dynamodb.create_table(
            TableName='wishlist_table_guru',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        self.product_table.put_item(Item={
            'id': '1', 'name': 'Test Product',
            'price': 100, 'category': 'Test', 'stock_quantity': 10
        })

    # ── Cart ──────────────────────────────────────────────────────────────────

    def test_get_cart_empty(self):
        response = lambda_handler(create_user_event('/cart', 'GET'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data'] == []

    def test_add_item_to_cart(self):
        response = lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])['data']
        assert len(data) == 1
        assert data[0]['id'] == '1'
        assert data[0]['quantity'] == 1

    def test_add_item_invalid_product(self):
        response = lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '999'}), {})
        assert response['statusCode'] == 400
        assert 'Invalid product' in json.loads(response['body'])['message']

    def test_add_item_out_of_stock(self):
        self.product_table.put_item(Item={
            'id': '1', 'name': 'Test Product', 'price': 100,
            'category': 'Test', 'stock_quantity': 0
        })
        response = lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        assert response['statusCode'] == 400
        assert 'out of stock' in json.loads(response['body'])['message']

    def test_remove_item_from_cart(self):
        lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        response = lambda_handler(create_user_event('/cart/remove/1', 'DELETE'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data'] == []

    def test_clear_cart(self):
        lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        response = lambda_handler(create_user_event('/cart', 'DELETE'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['message'] == 'Cart cleared'

    def test_add_to_cart_increments_quantity(self):
        lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        response = lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])['data']
        assert len(data) == 1
        assert data[0]['quantity'] == 2

    def test_remove_from_cart_decrements_quantity(self):
        lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        response = lambda_handler(create_user_event('/cart/remove/1', 'DELETE'), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])['data']
        assert len(data) == 1
        assert data[0]['quantity'] == 1

    def test_remove_from_cart_not_found(self):
        response = lambda_handler(create_user_event('/cart/remove/999', 'DELETE'), {})
        assert response['statusCode'] == 404

    def test_add_to_cart_exceeds_stock(self):
        for _ in range(10):
            lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        response = lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '1'}), {})
        assert response['statusCode'] == 400
        assert 'available in stock' in json.loads(response['body'])['message']

    def test_add_to_cart_unexpected_fields(self):
        response = lambda_handler(
            create_user_event('/cart/add', 'POST', body={'id': '1', 'price': 999, 'malicious': 'data'}), {}
        )
        assert response['statusCode'] == 400
        assert 'Unexpected fields' in json.loads(response['body'])['message']

    def test_add_to_cart_with_variant(self):
        self.product_table.put_item(Item={
            'id': '2', 'name': 'T-Shirt', 'price': 1500,
            'variants': [{'variant_id': 'v1', 'size': 'M', 'price': 1500, 'stock': 10}]
        })
        response = lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '2', 'variant_id': 'v1'}), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data'][0]['variant_id'] == 'v1'

    def test_add_to_cart_invalid_variant(self):
        self.product_table.put_item(Item={
            'id': '2', 'name': 'T-Shirt', 'price': 1500,
            'variants': [{'variant_id': 'v1', 'size': 'M', 'price': 1500, 'stock': 10}]
        })
        response = lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '2', 'variant_id': 'invalid'}), {})
        assert response['statusCode'] == 400
        assert 'Invalid variant' in json.loads(response['body'])['message']

    def test_add_to_cart_variant_out_of_stock(self):
        self.product_table.put_item(Item={
            'id': '2', 'name': 'T-Shirt', 'price': 1500,
            'variants': [{'variant_id': 'v1', 'size': 'M', 'price': 1500, 'stock': 0}]
        })
        response = lambda_handler(create_user_event('/cart/add', 'POST', body={'id': '2', 'variant_id': 'v1'}), {})
        assert response['statusCode'] == 400
        assert 'out of stock' in json.loads(response['body'])['message']

    # ── Addresses ─────────────────────────────────────────────────────────────

    def test_get_addresses_empty(self):
        response = lambda_handler(create_user_event('/addresses', 'GET'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data'] == []

    def test_add_address_success(self):
        response = lambda_handler(create_user_event('/addresses', 'POST', body={
            'full_name': 'Test User', 'phone': '9876543210',
            'address_line1': '123 Test St', 'city': 'Mumbai',
            'state': 'Maharashtra', 'pincode': '400001'
        }), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])['data']
        assert len(data) == 1
        assert data[0]['full_name'] == 'Test User'
        assert data[0]['is_default'] is True

    def test_add_address_invalid_phone(self):
        response = lambda_handler(create_user_event('/addresses', 'POST', body={
            'full_name': 'Test User', 'phone': '12345',
            'address_line1': '123 Test St', 'city': 'Mumbai',
            'state': 'Maharashtra', 'pincode': '400001'
        }), {})
        assert response['statusCode'] == 400
        msg = json.loads(response['body'])['message']
        assert 'Validation error' in msg or 'phone' in msg.lower()

    def test_add_address_invalid_pincode(self):
        response = lambda_handler(create_user_event('/addresses', 'POST', body={
            'full_name': 'Test User', 'phone': '9876543210',
            'address_line1': '123 Test St', 'city': 'Mumbai',
            'state': 'Maharashtra', 'pincode': '123'
        }), {})
        assert response['statusCode'] == 400
        msg = json.loads(response['body'])['message']
        assert 'Validation error' in msg or 'pincode' in msg.lower()

    def test_set_default_address(self):
        for name, phone in [('User A', '9876543210'), ('User B', '9123456780')]:
            lambda_handler(create_user_event('/addresses', 'POST', body={
                'full_name': name, 'phone': phone,
                'address_line1': '123 St', 'city': 'Mumbai',
                'state': 'Maharashtra', 'pincode': '400001'
            }), {})

        addresses = json.loads(
            lambda_handler(create_user_event('/addresses', 'GET'), {})['body']
        )['data']
        second_id = addresses[1]['address_id']

        response = lambda_handler(create_user_event(f'/addresses/{second_id}', 'PUT'), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])['data']
        defaults = [a for a in data if a['is_default']]
        assert len(defaults) == 1
        assert defaults[0]['address_id'] == second_id

    def test_delete_address(self):
        lambda_handler(create_user_event('/addresses', 'POST', body={
            'full_name': 'Test User', 'phone': '9876543210',
            'address_line1': '123 St', 'city': 'Mumbai',
            'state': 'Maharashtra', 'pincode': '400001'
        }), {})

        addr_id = json.loads(
            lambda_handler(create_user_event('/addresses', 'GET'), {})['body']
        )['data'][0]['address_id']

        response = lambda_handler(create_user_event(f'/addresses/{addr_id}', 'DELETE'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data'] == []

    def test_delete_address_not_found(self):
        response = lambda_handler(create_user_event('/addresses/nonexistent-id', 'DELETE'), {})
        assert response['statusCode'] == 404

    # ── Profile ───────────────────────────────────────────────────────────────

    def test_get_profile_empty(self):
        response = lambda_handler(create_user_event('/profile/me', 'GET'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data'] == {}

    def test_update_profile_success(self):
        response = lambda_handler(create_user_event('/profile/me', 'PUT', body={
            'display_name': 'Guru', 'phone': '9876543210', 'bio': 'Developer'
        }), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])['data']
        assert data['display_name'] == 'Guru'
        assert data['phone'] == '9876543210'
        assert data['bio'] == 'Developer'

    def test_update_profile_invalid_phone(self):
        response = lambda_handler(create_user_event('/profile/me', 'PUT', body={'phone': '123'}), {})
        assert response['statusCode'] == 400
        msg = json.loads(response['body'])['message']
        assert 'Validation error' in msg or 'phone' in msg.lower()

    def test_update_profile_ignores_unknown_fields(self):
        response = lambda_handler(create_user_event('/profile/me', 'PUT', body={
            'display_name': 'Guru', 'email': 'hack@evil.com', 'role': 'admin'
        }), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])['data']
        assert 'email' not in data
        assert 'role' not in data
        assert data['display_name'] == 'Guru'

    def test_profile_persists_after_update(self):
        lambda_handler(create_user_event('/profile/me', 'PUT', body={
            'display_name': 'Guru', 'bio': 'Dev'
        }), {})
        response = lambda_handler(create_user_event('/profile/me', 'GET'), {})
        data = json.loads(response['body'])['data']
        assert data['display_name'] == 'Guru'
        assert data['bio'] == 'Dev'

    # ── Wishlist ──────────────────────────────────────────────────────────────

    def test_get_wishlist_empty(self):
        response = lambda_handler(create_user_event('/wishlist', 'GET'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data'] == []

    def test_add_to_wishlist_success(self):
        response = lambda_handler(create_user_event('/wishlist/add', 'POST', body={'id': '1'}), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])['data']
        assert len(data) == 1
        assert data[0]['id'] == '1'

    def test_add_to_wishlist_invalid_product(self):
        response = lambda_handler(create_user_event('/wishlist/add', 'POST', body={'id': '999'}), {})
        assert response['statusCode'] == 400
        assert 'Invalid product' in json.loads(response['body'])['message']

    def test_add_to_wishlist_duplicate(self):
        lambda_handler(create_user_event('/wishlist/add', 'POST', body={'id': '1'}), {})
        response = lambda_handler(create_user_event('/wishlist/add', 'POST', body={'id': '1'}), {})
        assert response['statusCode'] == 400
        assert 'already in wishlist' in json.loads(response['body'])['message']

    def test_remove_from_wishlist_success(self):
        lambda_handler(create_user_event('/wishlist/add', 'POST', body={'id': '1'}), {})
        response = lambda_handler(create_user_event('/wishlist/remove/1', 'DELETE'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data'] == []

    def test_remove_from_wishlist_not_found(self):
        response = lambda_handler(create_user_event('/wishlist/remove/999', 'DELETE'), {})
        assert response['statusCode'] == 404

    # ── Misc ──────────────────────────────────────────────────────────────────

    def test_invalid_route(self):
        response = lambda_handler(create_user_event('/invalid', 'GET'), {})
        assert response['statusCode'] == 404
        assert 'Route not found' in json.loads(response['body'])['message']

    def test_convert_decimal(self):
        from decimal import Decimal
        result = convert_decimal({'price': Decimal('100.5'), 'items': [1, Decimal('2.5'), {'nested': Decimal('3.7')}]})
        assert result['price'] == 100.5
        assert result['items'] == [1, 2.5, {'nested': 3.7}]
