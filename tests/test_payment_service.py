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

        # Seed test order
        self.test_order_id = 'test-order-123'
        self.orders_table.put_item(Item={
            'order_id': self.test_order_id,
            'items': [
                {'id': '1', 'name': 'Test Product', 'price': 100, 'quantity': 2}
            ],
            'status': 'created'
        })

    def test_payment_success(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'order_id': self.test_order_id,
                'amount': 200  # 2 items * 100 each
            })
        }

        # Mock random to always return success
        import services.payment_service as payment_service
        original_random = payment_service.random.choice
        payment_service.random.choice = lambda x: True

        try:
            response = lambda_handler(event, {})
            assert response['statusCode'] == 200
            data = json.loads(response['body'])
            assert data['status'] == 'success'
            assert data['data']['status'] == 'success'
            assert 'payment_id' in data['data']
        finally:
            payment_service.random.choice = original_random

    def test_payment_failure(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'order_id': self.test_order_id,
                'amount': 200
            })
        }

        # Mock random to always return failure
        import services.payment_service as payment_service
        original_random = payment_service.random.choice
        payment_service.random.choice = lambda x: False

        try:
            response = lambda_handler(event, {})
            assert response['statusCode'] == 400
            data = json.loads(response['body'])
            assert data['status'] == 'error'
            assert data['data']['status'] == 'failed'
        finally:
            payment_service.random.choice = original_random

    def test_payment_invalid_order(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'order_id': 'invalid-order',
                'amount': 200
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Invalid order' in data['message']

    def test_payment_amount_mismatch(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'order_id': self.test_order_id,
                'amount': 300  # Wrong amount
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Amount mismatch' in data['message']

    def test_payment_missing_order_id(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'amount': 200
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'order_id is required' in data['message']

    def test_payment_invalid_amount(self):
        event = {
            'rawPath': '/payment',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({
                'order_id': self.test_order_id,
                'amount': 0
            })
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Valid amount is required' in data['message']

    def test_invalid_route(self):
        event = {
            'rawPath': '/invalid',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        data = json.loads(response['body'])
        assert 'Route not found' in data['message']