import os
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

import pytest
import boto3
from moto import mock_aws
import json
from services.payment_service import lambda_handler

@mock_aws
class TestPaymentService:
    def setup_method(self, method):
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Orders table
        self.orders_table = dynamodb.create_table(
            TableName='orders_table_guru',
            KeySchema=[
                {'AttributeName': 'order_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'order_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Standard order: 2 items * 100 = 200 subtotal
        # GST 18% = 36, delivery free (>= 500? no, 200 < 500 so +49), grand_total = 200+49+36 = 285
        self.test_order_id = 'test-order-123'
        self.orders_table.put_item(Item={
            'order_id': self.test_order_id,
            'items': [
                {'id': '1', 'name': 'Test Product', 'price': 100, 'quantity': 2}
            ],
            'subtotal': 200,
            'delivery_charge': 49,
            'gst': 36,
            'grand_total': 285,
            'status': 'created'
        })

        # High-value order: triggers INSUFFICIENT_FUNDS rule (amount > 500,000)
        self.high_value_order_id = 'test-order-highvalue'
        self.orders_table.put_item(Item={
            'order_id': self.high_value_order_id,
            'items': [
                {'id': '2', 'name': 'Expensive Item', 'price': 600000, 'quantity': 1}
            ],
            'status': 'created'
        })

        # Large cart order: triggers CARD_VELOCITY_EXCEEDED rule (> 10 items)
        self.large_cart_order_id = 'test-order-largecart'
        self.orders_table.put_item(Item={
            'order_id': self.large_cart_order_id,
            'items': [{'id': str(i), 'name': f'Item {i}', 'price': 10, 'quantity': 1} for i in range(11)],
            'grand_total': 110,  # 11 * 10, no delivery (>= 500? no, but keeping simple for test)
            'status': 'created'
        })

    def test_payment_success(self):
        """Standard order within all limits should succeed."""
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'order_id': self.test_order_id,
                'amount': 285  # grand_total: 200 subtotal + 49 delivery + 36 GST
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['status'] == 'success'
        assert data['data']['status'] == 'success'
        assert 'payment_id' in data['data']
        assert data['data']['decline_code'] is None

    def test_payment_already_paid(self):
        """Paying an already-paid order should be rejected."""
        self.orders_table.put_item(Item={
            'order_id': 'paid-order',
            'items': [{'id': '1', 'name': 'Item', 'price': 100, 'quantity': 1}],
            'status': 'paid'
        })
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'order_id': 'paid-order', 'amount': 100})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'already been paid' in data['message']

    def test_payment_declined_insufficient_funds(self):
        """High-value order should be declined with INSUFFICIENT_FUNDS code."""
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'order_id': self.high_value_order_id,
                'amount': 600000
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert data['data']['decline_code'] == 'INSUFFICIENT_FUNDS'
        assert data['data']['status'] == 'declined'

    def test_payment_declined_velocity(self):
        """Order with > 10 items should be declined with CARD_VELOCITY_EXCEEDED."""
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'order_id': self.large_cart_order_id,
                'amount': 110  # matches grand_total
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert data['data']['decline_code'] == 'CARD_VELOCITY_EXCEEDED'

    def test_payment_invalid_order(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'order_id': 'invalid-order', 'amount': 200})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Invalid order' in data['message']

    def test_payment_amount_mismatch(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'order_id': self.test_order_id, 'amount': 999})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Amount mismatch' in data['message']

    def test_payment_missing_order_id(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'amount': 200})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'order_id is required' in data['message']

    def test_payment_invalid_amount(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'order_id': self.test_order_id, 'amount': 0})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'greater than zero' in data['message']

    def test_invalid_route(self):
        event = {
            'rawPath': '/invalid',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        data = json.loads(response['body'])
        assert 'Route not found' in data['message']
