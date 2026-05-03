import os
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

import pytest
import boto3
from moto import mock_aws
import json
from decimal import Decimal
from services.catalog_service import lambda_handler

@mock_aws
class TestSearchService:
    def setup_method(self, method):
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

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

        # Seed test products
        self.product_table.put_item(Item={
            'id': '1',
            'name': 'Wireless Bluetooth Headphones',
            'price': 15000,
            'category': 'Electronics',
            'stock_quantity': 25,
            'description': 'Premium noise-cancelling wireless headphones with 30-hour battery life.',
            'rating': Decimal('4.6')
        })

        self.product_table.put_item(Item={
            'id': '2',
            'name': 'Smart Fitness Watch',
            'price': 25000,
            'category': 'Electronics',
            'stock_quantity': 10,
            'description': 'Advanced fitness tracker with heart rate monitoring and GPS.',
            'rating': Decimal('4.4')
        })

        self.product_table.put_item(Item={
            'id': '3',
            'name': 'Organic Cotton T-Shirt',
            'price': 2500,
            'category': 'Clothing',
            'stock_quantity': 50,
            'description': 'Comfortable, eco-friendly t-shirt made from 100% organic cotton.',
            'rating': Decimal('4.0')
        })

    def test_search_by_name(self):
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'headphones'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['status'] == 'success'
        assert len(data['data']['items']) == 1
        assert 'Wireless Bluetooth Headphones' in data['data']['items'][0]['name']

    def test_search_by_description(self):
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'fitness'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert len(data['data']['items']) == 1
        assert 'Smart Fitness Watch' in data['data']['items'][0]['name']

    def test_search_case_insensitive(self):
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'HEADPHONES'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert len(data['data']['items']) == 1

    def test_search_multiple_results(self):
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'wireless'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert len(data['data']['items']) == 1  # Only headphones have "wireless"

    def test_search_no_results(self):
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'nonexistent'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert len(data['data']['items']) == 0
        assert data['data']['total'] == 0

    def test_search_with_price_filter(self):
        """Server-side price filter: only products within range returned."""
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'watch', 'minPrice': '20000', 'maxPrice': '30000'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        items = data['data']['items']
        assert len(items) == 1
        assert items[0]['name'] == 'Smart Fitness Watch'

    def test_search_with_category_filter(self):
        """Server-side category filter: only Clothing items returned."""
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'cotton', 'category': 'Clothing'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        items = data['data']['items']
        assert len(items) == 1
        assert items[0]['category'] == 'Clothing'

    def test_search_response_has_pagination_fields(self):
        """Response should always include pagination metadata."""
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'headphones'}
        }
        response = lambda_handler(event, {})
        data = json.loads(response['body'])
        assert 'items' in data['data']
        assert 'lastEvaluatedKey' in data['data']
        assert 'total' in data['data']

    def test_search_empty_query(self):
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': ''}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Query parameter' in data['message']

    def test_search_no_query_param(self):
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Query parameter' in data['message']

    def test_invalid_route(self):
        event = {
            'rawPath': '/invalid',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        data = json.loads(response['body'])
        assert 'Route not found' in data['message']
