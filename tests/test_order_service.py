import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['SMTP_USER'] = ''
os.environ['SMTP_PASSWORD'] = ''

import pytest
import boto3
from moto import mock_aws
import json
from order_service import lambda_handler, convert_decimal


def create_order_event(path, method, body=None, user_id='user1', user_email='user@example.com'):
    """Helper to create order event with proper JWT claims."""
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

        self.orders_table = dynamodb.create_table(
            TableName='orders_table_guru',
            KeySchema=[{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[
                {'AttributeName': 'order_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[{
                'IndexName': 'user_id-index',
                'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                'Projection': {'ProjectionType': 'ALL'}
            }],
            BillingMode='PAY_PER_REQUEST'
        )
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
        self.returns_table = dynamodb.create_table(
            TableName='returns_table_guru',
            KeySchema=[{'AttributeName': 'return_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'return_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        self.product_table.put_item(Item={
            'id': '1', 'name': 'Test Product',
            'price': 100, 'category': 'Test', 'stock_quantity': 10
        })
        self.cart_table.put_item(Item={
            'user_id': 'user1',
            'cart': [{'id': '1', 'name': 'Test Product', 'price': 100, 'quantity': 1}]
        })

    def test_get_all_orders_empty(self):
        response = lambda_handler(create_order_event('/order', 'GET'), {})
        assert response['statusCode'] == 200
        assert isinstance(json.loads(response['body'])['data'], list)

    def test_create_order_success(self):
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['status'] == 'success'
        assert 'order_id' in data['data']
        assert data['data']['status'] == 'created'
        assert 'grand_total' in data['data']
        assert data['data']['address']['city'] == 'Mumbai'

    def test_create_order_missing_address(self):
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}]
        }), {})
        assert response['statusCode'] == 400
        msg = json.loads(response['body'])['message']
        assert 'Validation error' in msg or 'address' in msg

    def test_create_order_invalid_phone(self):
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': {**VALID_ADDRESS, 'phone': '12345'}
        }), {})
        assert response['statusCode'] == 400
        msg = json.loads(response['body'])['message']
        assert 'phone' in msg.lower()

    def test_create_order_invalid_pincode(self):
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': {**VALID_ADDRESS, 'pincode': '123'}
        }), {})
        assert response['statusCode'] == 400
        msg = json.loads(response['body'])['message']
        assert 'pincode' in msg.lower()

    def test_create_order_empty_cart(self):
        self.cart_table.put_item(Item={'user_id': 'user1', 'cart': []})
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        assert response['statusCode'] == 400
        assert 'Cart is empty' in json.loads(response['body'])['message']

    def test_create_order_invalid_product(self):
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '999'}], 'address': VALID_ADDRESS
        }), {})
        assert response['statusCode'] == 400
        assert 'not in cart' in json.loads(response['body'])['message']

    def test_get_order_by_id(self):
        create_resp = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        order_id = json.loads(create_resp['body'])['data']['order_id']

        response = lambda_handler(create_order_event(f'/order/{order_id}', 'GET'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data']['order_id'] == order_id

    def test_update_order_status(self):
        """Customer can cancel their own order via PUT (created → cancelled)."""
        create_resp = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        order_id = json.loads(create_resp['body'])['data']['order_id']

        response = lambda_handler(create_order_event(f'/order/{order_id}', 'PUT', body={'status': 'cancelled'}), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data']['status'] == 'cancelled'

    def test_update_order_status_invalid_transition(self):
        """Customer cannot transition created → shipped (admin-only)."""
        create_resp = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        order_id = json.loads(create_resp['body'])['data']['order_id']

        response = lambda_handler(create_order_event(f'/order/{order_id}', 'PUT', body={'status': 'shipped'}), {})
        assert response['statusCode'] == 400
        assert 'Cannot transition' in json.loads(response['body'])['message']

    def test_update_order_status_not_owner(self):
        """A different user cannot update someone else's order."""
        create_resp = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        order_id = json.loads(create_resp['body'])['data']['order_id']

        response = lambda_handler(create_order_event(f'/order/{order_id}', 'PUT', body={'status': 'cancelled'}, user_id='other-user'), {})
        assert response['statusCode'] == 403

    def test_cancel_order_success(self):
        create_resp = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        order_id = json.loads(create_resp['body'])['data']['order_id']

        response = lambda_handler(create_order_event(f'/order/{order_id}', 'DELETE'), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data']['status'] == 'cancelled'

    def test_cancel_order_already_paid(self):
        self.orders_table.put_item(Item={
            'order_id': 'paid-order-123', 'user_id': 'user1',
            'items': [{'id': '1', 'name': 'Test', 'price': 100, 'quantity': 1}],
            'status': 'paid'
        })
        response = lambda_handler(create_order_event('/order/paid-order-123', 'DELETE'), {})
        assert response['statusCode'] == 400
        assert 'Cannot cancel' in json.loads(response['body'])['message']

    def test_cancel_order_not_found(self):
        response = lambda_handler(create_order_event('/order/nonexistent-id', 'DELETE'), {})
        assert response['statusCode'] == 404

    def test_create_order_with_variants(self):
        self.product_table.put_item(Item={
            'id': '2', 'name': 'T-Shirt', 'price': 1500,
            'stock_quantity': 10,
            'variants': [{'variant_id': 'v1', 'size': 'M', 'price': 1500, 'stock': 10}]
        })
        self.cart_table.put_item(Item={
            'user_id': 'user1',
            'cart': [{'id': '2', 'name': 'T-Shirt', 'price': 1500, 'quantity': 1, 'variant_id': 'v1'}]
        })
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '2', 'variant_id': 'v1'}], 'address': VALID_ADDRESS
        }), {})
        assert response['statusCode'] == 200
        assert json.loads(response['body'])['data']['items'][0]['variant_id'] == 'v1'

    def test_create_order_quantity_aggregation(self):
        self.cart_table.put_item(Item={
            'user_id': 'user1',
            'cart': [{'id': '1', 'name': 'Test Product', 'price': 100, 'quantity': 2}]
        })
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}, {'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        assert response['statusCode'] == 200
        items = json.loads(response['body'])['data']['items']
        assert len(items) == 1
        assert items[0]['quantity'] == 2

    def test_create_order_exceeds_cart_quantity(self):
        self.cart_table.put_item(Item={
            'user_id': 'user1',
            'cart': [{'id': '1', 'name': 'Test Product', 'price': 100, 'quantity': 1}]
        })
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}, {'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        assert response['statusCode'] == 400
        assert 'exceeds cart' in json.loads(response['body'])['message']

    def test_create_order_insufficient_stock(self):
        self.product_table.update_item(
            Key={'id': '1'},
            UpdateExpression='SET stock_quantity = :qty',
            ExpressionAttributeValues={':qty': 0}
        )
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        assert response['statusCode'] == 400
        assert 'Insufficient stock' in json.loads(response['body'])['message']

    def test_create_order_inventory_reserved(self):
        initial_stock = self.product_table.get_item(Key={'id': '1'})['Item']['stock_quantity']
        lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        updated_stock = self.product_table.get_item(Key={'id': '1'})['Item']['stock_quantity']
        assert updated_stock == initial_stock - 1

    def test_cancel_order_restores_inventory(self):
        initial_stock = self.product_table.get_item(Key={'id': '1'})['Item']['stock_quantity']

        create_resp = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        order_id = json.loads(create_resp['body'])['data']['order_id']

        lambda_handler(create_order_event(f'/order/{order_id}', 'DELETE'), {})

        final_stock = self.product_table.get_item(Key={'id': '1'})['Item']['stock_quantity']
        assert final_stock == initial_stock

    def test_create_order_pricing_breakdown(self):
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        data = json.loads(response['body'])['data']
        assert data['subtotal'] == 100
        assert data['delivery_charge'] == 49
        assert data['gst'] == 18
        assert data['grand_total'] == 167

    def test_create_order_free_delivery(self):
        self.product_table.put_item(Item={
            'id': '2', 'name': 'Expensive Product', 'price': 600, 'stock_quantity': 10
        })
        self.cart_table.put_item(Item={
            'user_id': 'user1',
            'cart': [{'id': '2', 'name': 'Expensive Product', 'price': 600, 'quantity': 1}]
        })
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '2'}], 'address': VALID_ADDRESS
        }), {})
        assert json.loads(response['body'])['data']['delivery_charge'] == 0

    def test_invalid_route(self):
        response = lambda_handler(create_order_event('/invalid', 'GET'), {})
        assert response['statusCode'] == 404
        assert 'Route not found' in json.loads(response['body'])['message']

    def test_create_order_unverified_email_still_succeeds(self):
        """Order creation should succeed even with unverified email."""
        event = {
            'rawPath': '/order',
            'requestContext': {
                'http': {'method': 'POST'},
                'authorizer': {'jwt': {'claims': {
                    'sub': 'user1',
                    'email': 'user@example.com',
                    'https://mystore.com/email_verified': 'false'
                }}}
            },
            'body': json.dumps({'items': [{'id': '1'}], 'address': VALID_ADDRESS})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['status'] == 'success'
        # email_verified flag stored on the order
        assert data['data']['email_verified'] is False

    def test_create_order_verified_email_stored(self):
        """email_verified=True should be stored on the order."""
        event = {
            'rawPath': '/order',
            'requestContext': {
                'http': {'method': 'POST'},
                'authorizer': {'jwt': {'claims': {
                    'sub': 'user1',
                    'email': 'user@example.com',
                    'https://mystore.com/email_verified': 'true'
                }}}
            },
            'body': json.dumps({'items': [{'id': '1'}], 'address': VALID_ADDRESS})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['email_verified'] is True

    def test_create_order_missing_verified_claim_defaults_true(self):
        """Missing email_verified claim should default to True (fail open)."""
        response = lambda_handler(create_order_event('/order', 'POST', body={
            'items': [{'id': '1'}], 'address': VALID_ADDRESS
        }), {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['email_verified'] is True
