import os
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

import pytest
import boto3
from moto import mock_aws
import json
from services.order_service import lambda_handler, convert_decimal

# Valid address used across all order creation tests
VALID_ADDRESS = {
    'full_name':     'Test User',
    'phone':         '9876543210',
    'address_line1': '123 Test Street',
    'address_line2': '',
    'city':          'Mumbai',
    'state':         'Maharashtra',
    'pincode':       '400001'
}

@mock_aws
class TestOrderService:
    def setup_method(self, method):
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Orders table
        self.orders_table = dynamodb.create_table(
            TableName='orders_table_guru',
            KeySchema=[{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'order_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Cart table
        self.cart_table = dynamodb.create_table(
            TableName='cart_table_guru',
            KeySchema=[{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'user_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Products table
        self.product_table = dynamodb.create_table(
            TableName='products_table_guru',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Seed product and cart
        self.product_table.put_item(Item={
            'id': '1', 'name': 'Test Product',
            'price': 100, 'category': 'Test', 'stock_quantity': 10
        })
        self.cart_table.put_item(Item={
            'user_id': 'user1',
            'cart': [{'id': '1', 'name': 'Test Product', 'price': 100, 'quantity': 1}]
        })

    def test_get_all_orders_empty(self):
        event = {'rawPath': '/order', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert isinstance(data['data'], list)

    def test_create_order_success(self):
        event = {
            'rawPath': '/order',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'items': [{'id': '1'}], 'address': VALID_ADDRESS})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['status'] == 'success'
        assert 'order_id' in data['data']
        assert data['data']['status'] == 'created'
        # Verify pricing breakdown is stored
        assert 'grand_total' in data['data']
        assert 'gst' in data['data']
        assert 'delivery_charge' in data['data']
        # Verify address is stored
        assert data['data']['address']['city'] == 'Mumbai'

    def test_create_order_missing_address(self):
        """Order without address should be rejected."""
        event = {
            'rawPath': '/order',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'items': [{'id': '1'}]})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Missing address fields' in data['message']

    def test_create_order_invalid_phone(self):
        """Invalid phone number should be rejected."""
        bad_address = {**VALID_ADDRESS, 'phone': '12345'}
        event = {
            'rawPath': '/order',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'items': [{'id': '1'}], 'address': bad_address})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Phone' in data['message']

    def test_create_order_invalid_pincode(self):
        """Invalid PIN code should be rejected."""
        bad_address = {**VALID_ADDRESS, 'pincode': '123'}
        event = {
            'rawPath': '/order',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'items': [{'id': '1'}], 'address': bad_address})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'PIN' in data['message']

    def test_create_order_empty_cart(self):
        self.cart_table.put_item(Item={'user_id': 'user1', 'cart': []})
        event = {
            'rawPath': '/order',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'items': [{'id': '1'}], 'address': VALID_ADDRESS})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Cart is empty' in data['message']

    def test_create_order_invalid_product(self):
        event = {
            'rawPath': '/order',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'items': [{'id': '999'}], 'address': VALID_ADDRESS})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'not in cart' in data['message']

    def test_get_order_by_id(self):
        create_event = {
            'rawPath': '/order',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'items': [{'id': '1'}], 'address': VALID_ADDRESS})
        }
        create_response = lambda_handler(create_event, {})
        order_id = json.loads(create_response['body'])['data']['order_id']

        event = {
            'rawPath': f'/order/{order_id}',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['order_id'] == order_id

    def test_update_order_status(self):
        create_event = {
            'rawPath': '/order',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'items': [{'id': '1'}], 'address': VALID_ADDRESS})
        }
        create_response = lambda_handler(create_event, {})
        order_id = json.loads(create_response['body'])['data']['order_id']

        event = {
            'rawPath': f'/order/{order_id}',
            'requestContext': {'http': {'method': 'PUT'}},
            'body': json.dumps({'status': 'shipped'})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['status'] == 'shipped'

    def test_cancel_order_success(self):
        """Order in 'created' state can be cancelled and inventory is restored."""
        create_event = {
            'rawPath': '/order',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'items': [{'id': '1'}], 'address': VALID_ADDRESS})
        }
        create_response = lambda_handler(create_event, {})
        order_id = json.loads(create_response['body'])['data']['order_id']

        cancel_event = {
            'rawPath': f'/order/{order_id}',
            'requestContext': {'http': {'method': 'DELETE'}}
        }
        response = lambda_handler(cancel_event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['status'] == 'cancelled'

    def test_cancel_order_already_paid(self):
        """Paid orders cannot be cancelled."""
        self.orders_table.put_item(Item={
            'order_id': 'paid-order-123',
            'user_id': 'user1',
            'items': [{'id': '1', 'name': 'Test', 'price': 100, 'quantity': 1}],
            'status': 'paid'
        })
        event = {
            'rawPath': '/order/paid-order-123',
            'requestContext': {'http': {'method': 'DELETE'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Cannot cancel' in data['message']

    def test_cancel_order_not_found(self):
        event = {
            'rawPath': '/order/nonexistent-id',
            'requestContext': {'http': {'method': 'DELETE'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404

    def test_invalid_route(self):
        event = {'rawPath': '/invalid', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        data = json.loads(response['body'])
        assert 'Route not found' in data['message']
