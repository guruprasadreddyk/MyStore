import os
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

import pytest
import boto3
from moto import mock_aws
import json
from services.product_service import lambda_handler

@mock_aws
class TestProductService:
    def setup_method(self, method):
        # Set AWS region for moto
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        
        # Create mock DynamoDB table
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

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

    def test_health_check(self):
        event = {
            'rawPath': '/health',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert 'healthy' in data['message']

    def test_get_all_products(self):
        event = {
            'rawPath': '/products',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert isinstance(data['data'], list)
        # Should have the default products seeded

    def test_get_product_by_id(self):
        # First seed the products by calling get_all_products
        seed_event = {
            'rawPath': '/products',
            'requestContext': {'http': {'method': 'GET'}}
        }
        lambda_handler(seed_event, {})

        event = {
            'rawPath': '/products/1',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['id'] == '1'
        assert 'name' in data['data']

    def test_get_product_not_found(self):
        event = {
            'rawPath': '/products/999',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        data = json.loads(response['body'])
        assert 'not found' in data['message']

    def test_invalid_route(self):
        event = {
            'rawPath': '/invalid',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        data = json.loads(response['body'])
        assert 'Route not found' in data['message']