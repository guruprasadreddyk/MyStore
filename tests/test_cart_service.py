import os
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

import pytest
import boto3
from moto import mock_aws
import json
from services.cart_service import lambda_handler, convert_decimal

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
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'}
            ],
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
        assert result['price'] == 100
        assert result['items'] == [1, 2, {'nested': 3}]