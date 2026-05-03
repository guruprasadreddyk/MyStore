import os
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

import pytest
import boto3
from moto import mock_aws
import json
from services.user_service import lambda_handler, convert_decimal

@mock_aws
class TestCartService:
    def setup_method(self, method):
        # Set AWS region for moto
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        
        # Create mock DynamoDB tables
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Cart table
        self.cart_table = dynamodb.create_table(
            TableName='cart_table_guru',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Products table
        self.product_table = dynamodb.create_table(
            TableName='products_table_guru',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # user_data_table (addresses + profile)
        self.user_data_table = dynamodb.create_table(
            TableName='user_data_table_guru',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # wishlist table
        self.wishlist_table = dynamodb.create_table(
            TableName='wishlist_table_guru',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Seed product data
        self.product_table.put_item(Item={
            'id': '1',
            'name': 'Test Product',
            'price': 100,
            'category': 'Test',
            'stock_quantity': 10
        })

    def test_get_cart_empty(self):
        event = {
            'rawPath': '/cart',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data'] == []

    def test_add_item_to_cart(self):
        event = {
            'rawPath': '/cart/add',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'id': '1'})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert len(data['data']) == 1
        assert data['data'][0]['id'] == '1'
        assert data['data'][0]['quantity'] == 1

    def test_add_item_invalid_product(self):
        event = {
            'rawPath': '/cart/add',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'id': '999'})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Invalid product' in data['message']

    def test_add_item_out_of_stock(self):
        # Update product stock to 0
        self.product_table.put_item(Item={
            'id': '1',
            'name': 'Test Product',
            'price': 100,
            'category': 'Test',
            'stock_quantity': 0
        })

        event = {
            'rawPath': '/cart/add',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'id': '1'})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'out of stock' in data['message']

    def test_remove_item_from_cart(self):
        # First add an item
        add_event = {
            'rawPath': '/cart/add',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'id': '1'})
        }
        lambda_handler(add_event, {})

        # Now remove it
        remove_event = {
            'rawPath': '/cart/remove/1',
            'requestContext': {'http': {'method': 'DELETE'}}
        }
        response = lambda_handler(remove_event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data'] == []

    def test_clear_cart(self):
        # Add an item first
        add_event = {
            'rawPath': '/cart/add',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'id': '1'})
        }
        lambda_handler(add_event, {})

        # Clear cart
        clear_event = {
            'rawPath': '/cart',
            'requestContext': {'http': {'method': 'DELETE'}}
        }
        response = lambda_handler(clear_event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['message'] == 'Cart cleared'

    def test_invalid_route(self):
        event = {
            'rawPath': '/invalid',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        data = json.loads(response['body'])
        assert 'Route not found' in data['message']

    def test_convert_decimal(self):
        # Test convert_decimal function
        from decimal import Decimal
        test_data = {
            'price': Decimal('100.5'),
            'items': [1, Decimal('2.5'), {'nested': Decimal('3.7')}]
        }
        result = convert_decimal(test_data)
        assert result['price'] == 100.5
        assert result['items'] == [1, 2.5, {'nested': 3.7}]


# ── Address tests ─────────────────────────────────────────────────────────────

    def test_get_addresses_empty(self):
        event = {'rawPath': '/addresses', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data'] == []

    def test_add_address_success(self):
        event = {
            'rawPath': '/addresses',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'full_name': 'Test User', 'phone': '9876543210',
                'address_line1': '123 Test St', 'city': 'Mumbai',
                'state': 'Maharashtra', 'pincode': '400001'
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert len(data['data']) == 1
        assert data['data'][0]['full_name'] == 'Test User'
        assert data['data'][0]['is_default'] is True  # first address is default

    def test_add_address_invalid_phone(self):
        event = {
            'rawPath': '/addresses',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'full_name': 'Test User', 'phone': '12345',
                'address_line1': '123 Test St', 'city': 'Mumbai',
                'state': 'Maharashtra', 'pincode': '400001'
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Phone' in data['message']

    def test_add_address_invalid_pincode(self):
        event = {
            'rawPath': '/addresses',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'full_name': 'Test User', 'phone': '9876543210',
                'address_line1': '123 Test St', 'city': 'Mumbai',
                'state': 'Maharashtra', 'pincode': '123'
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'PIN' in data['message']

    def test_set_default_address(self):
        # Add two addresses
        for name, phone in [('User A', '9876543210'), ('User B', '9123456780')]:
            lambda_handler({
                'rawPath': '/addresses',
                'requestContext': {'http': {'method': 'POST'}},
                'body': json.dumps({
                    'full_name': name, 'phone': phone,
                    'address_line1': '123 St', 'city': 'Mumbai',
                    'state': 'Maharashtra', 'pincode': '400001'
                })
            }, {})

        # Get addresses to find second one's ID
        get_resp = lambda_handler({'rawPath': '/addresses', 'requestContext': {'http': {'method': 'GET'}}}, {})
        addresses = json.loads(get_resp['body'])['data']
        second_id = addresses[1]['address_id']

        # Set second as default
        event = {
            'rawPath': f'/addresses/{second_id}',
            'requestContext': {'http': {'method': 'PUT'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        defaults = [a for a in data['data'] if a['is_default']]
        assert len(defaults) == 1
        assert defaults[0]['address_id'] == second_id

    def test_delete_address(self):
        # Add an address
        lambda_handler({
            'rawPath': '/addresses',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'full_name': 'Test User', 'phone': '9876543210',
                'address_line1': '123 St', 'city': 'Mumbai',
                'state': 'Maharashtra', 'pincode': '400001'
            })
        }, {})

        # Get its ID
        get_resp = lambda_handler({'rawPath': '/addresses', 'requestContext': {'http': {'method': 'GET'}}}, {})
        addr_id = json.loads(get_resp['body'])['data'][0]['address_id']

        # Delete it
        event = {
            'rawPath': f'/addresses/{addr_id}',
            'requestContext': {'http': {'method': 'DELETE'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data'] == []

    def test_delete_address_not_found(self):
        event = {
            'rawPath': '/addresses/nonexistent-id',
            'requestContext': {'http': {'method': 'DELETE'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404

# ── Profile tests ─────────────────────────────────────────────────────────────

    def test_get_profile_empty(self):
        event = {'rawPath': '/profile/me', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data'] == {}

    def test_update_profile_success(self):
        event = {
            'rawPath': '/profile/me',
            'requestContext': {'http': {'method': 'PUT'}},
            'body': json.dumps({'display_name': 'Guru', 'phone': '9876543210', 'bio': 'Developer'})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['display_name'] == 'Guru'
        assert data['data']['phone'] == '9876543210'
        assert data['data']['bio'] == 'Developer'

    def test_update_profile_invalid_phone(self):
        event = {
            'rawPath': '/profile/me',
            'requestContext': {'http': {'method': 'PUT'}},
            'body': json.dumps({'phone': '123'})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Phone' in data['message']

    def test_update_profile_ignores_unknown_fields(self):
        """Only display_name, phone, bio are allowed — unknown fields silently ignored."""
        event = {
            'rawPath': '/profile/me',
            'requestContext': {'http': {'method': 'PUT'}},
            'body': json.dumps({'display_name': 'Guru', 'email': 'hack@evil.com', 'role': 'admin'})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert 'email' not in data['data']
        assert 'role' not in data['data']
        assert data['data']['display_name'] == 'Guru'

    def test_profile_persists_after_update(self):
        """Profile saved to DynamoDB should be readable back."""
        lambda_handler({
            'rawPath': '/profile/me',
            'requestContext': {'http': {'method': 'PUT'}},
            'body': json.dumps({'display_name': 'Guru', 'bio': 'Dev'})
        }, {})

        get_event = {'rawPath': '/profile/me', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(get_event, {})
        data = json.loads(response['body'])
        assert data['data']['display_name'] == 'Guru'
        assert data['data']['bio'] == 'Dev'
