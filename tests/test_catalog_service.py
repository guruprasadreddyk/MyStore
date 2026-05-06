import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

import pytest
import boto3
from moto import mock_aws
import json
from decimal import Decimal
from catalog_service import lambda_handler

@mock_aws
class TestCatalogService:
    def setup_method(self, method):
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
        
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

        # Products table
        self.product_table = dynamodb.create_table(
            TableName='products_table_guru',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )

        # Reviews table
        self.reviews_table = dynamodb.create_table(
            TableName='reviews_table_guru',
            KeySchema=[{'AttributeName': 'review_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[
                {'AttributeName': 'review_id', 'AttributeType': 'S'},
                {'AttributeName': 'product_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'product_id-index',
                    'KeySchema': [{'AttributeName': 'product_id', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'}
                },
                {
                    'IndexName': 'user_id-index',
                    'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ],
            BillingMode='PAY_PER_REQUEST'
        )

        # Orders table (needed for verified purchase checks)
        self.orders_table = dynamodb.create_table(
            TableName='orders_table_guru',
            KeySchema=[{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[
                {'AttributeName': 'order_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user_id-index',
                    'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}],
                    'Projection': {'ProjectionType': 'ALL'}
                }
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
            'rating': Decimal('4.6'),
            'review_count': 0
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

    def _create_auth_event(self, path, method, body=None, user_id='test-user-123', user_email='test@example.com'):
        """Helper to create authenticated event."""
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

    # ── Product Tests ─────────────────────────────────────────────────────────

    def test_health_check(self):
        event = {'rawPath': '/health', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert 'healthy' in data['message']

    def test_get_all_products(self):
        event = {'rawPath': '/products', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert isinstance(data['data']['items'], list)
        assert len(data['data']['items']) >= 3

    def test_get_product_by_id(self):
        event = {'rawPath': '/products/1', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['id'] == '1'
        assert data['data']['name'] == 'Wireless Bluetooth Headphones'

    def test_get_product_not_found(self):
        event = {'rawPath': '/products/999', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        data = json.loads(response['body'])
        assert 'not found' in data['message']

    # ── Search Tests ──────────────────────────────────────────────────────────

    def test_search_by_name(self):
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'headphones'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
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

    def test_search_with_rating_filter(self):
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'watch', 'minRating': '4.5'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        items = data['data']['items']
        # Smart Fitness Watch has 4.4 rating, should be filtered out
        assert len(items) == 0

    def test_search_with_stock_filter(self):
        # Add out-of-stock product
        self.product_table.put_item(Item={
            'id': '4',
            'name': 'Out of Stock Watch',
            'price': 20000,
            'category': 'Electronics',
            'stock_quantity': 0,
            'description': 'This watch is out of stock.',
            'rating': Decimal('4.5')
        })
        
        event = {
            'rawPath': '/search',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'q': 'watch', 'inStockOnly': 'true'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        items = data['data']['items']
        # Should only return Smart Fitness Watch (stock_quantity=10)
        assert len(items) == 1
        assert items[0]['stock_quantity'] > 0

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

    # ── Reviews Tests ─────────────────────────────────────────────────────────

    def test_get_reviews_empty(self):
        event = {'rawPath': '/products/1/reviews', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['reviews'] == []

    def test_create_review_success(self):
        # Add a delivered order for the user
        self.orders_table.put_item(Item={
            'order_id': 'order_123',
            'user_id': 'test-user-123',
            'status': 'delivered',
            'items': [{'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}]
        })
        
        event = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 5, 'title': 'Great product!', 'comment': 'Really love this product.'}
        )
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['rating'] == 5
        assert data['data']['title'] == 'Great product!'
        assert 'review_id' in data['data']

    def test_create_review_unauthenticated(self):
        event = {
            'rawPath': '/products/1/reviews',
            'requestContext': {'http': {'method': 'POST'}},
            'body': json.dumps({'rating': 5, 'comment': 'Test'})
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 401
        data = json.loads(response['body'])
        assert 'Authentication required' in data['message']

    def test_create_review_missing_rating(self):
        event = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'comment': 'Test comment'}
        )
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Rating is required' in data['message']

    def test_create_review_invalid_rating(self):
        # Add a delivered order for the user
        self.orders_table.put_item(Item={
            'order_id': 'order_123',
            'user_id': 'test-user-123',
            'status': 'delivered',
            'items': [{'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}]
        })
        
        event = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 6, 'comment': 'Test'}
        )
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'between 1 and 5' in data['message']

    def test_create_review_duplicate(self):
        # Add a delivered order for the user
        self.orders_table.put_item(Item={
            'order_id': 'order_123',
            'user_id': 'test-user-123',
            'status': 'delivered',
            'items': [{'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}]
        })
        
        # Create first review
        event1 = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 5, 'comment': 'First review'}
        )
        lambda_handler(event1, {})

        # Try to create second review
        event2 = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 4, 'comment': 'Second review'}
        )
        response = lambda_handler(event2, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'already reviewed' in data['message']

    def test_product_rating_updated_after_review(self):
        # Add delivered orders for two users
        self.orders_table.put_item(Item={
            'order_id': 'order_1',
            'user_id': 'user1',
            'status': 'delivered',
            'items': [{'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}]
        })
        self.orders_table.put_item(Item={
            'order_id': 'order_2',
            'user_id': 'user2',
            'status': 'delivered',
            'items': [{'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}]
        })
        
        # Create first review (5 stars)
        event1 = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 5, 'comment': 'Excellent!'},
            user_id='user1'
        )
        lambda_handler(event1, {})

        # Create second review (3 stars)
        event2 = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 3, 'comment': 'Okay'},
            user_id='user2'
        )
        lambda_handler(event2, {})

        # Check product rating (should be 4.0 = (5+3)/2)
        product = self.product_table.get_item(Key={'id': '1'})['Item']
        assert float(product['rating']) == 4.0
        assert product['review_count'] == 2

    def test_mark_review_helpful(self):
        # Add a delivered order for the user
        self.orders_table.put_item(Item={
            'order_id': 'order_123',
            'user_id': 'test-user-123',
            'status': 'delivered',
            'items': [{'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}]
        })
        
        # Create review first
        create_event = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 5, 'comment': 'Great!'}
        )
        create_response = lambda_handler(create_event, {})
        review_id = json.loads(create_response['body'])['data']['review_id']

        # Mark as helpful
        helpful_event = {
            'rawPath': f'/reviews/{review_id}/helpful',
            'requestContext': {'http': {'method': 'PUT'}}
        }
        response = lambda_handler(helpful_event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert 'helpful' in data['message']

    def test_delete_review_success(self):
        # Add a delivered order for the user
        self.orders_table.put_item(Item={
            'order_id': 'order_123',
            'user_id': 'user1',
            'status': 'delivered',
            'items': [{'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}]
        })
        
        # Create review
        create_event = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 5, 'comment': 'Test'},
            user_id='user1'
        )
        create_response = lambda_handler(create_event, {})
        review_id = json.loads(create_response['body'])['data']['review_id']

        # Delete review
        delete_event = self._create_auth_event(
            f'/reviews/{review_id}',
            'DELETE',
            user_id='user1'
        )
        response = lambda_handler(delete_event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert 'deleted' in data['message']

    def test_delete_review_unauthorized(self):
        # Add delivered orders for two users
        self.orders_table.put_item(Item={
            'order_id': 'order_1',
            'user_id': 'user1',
            'status': 'delivered',
            'items': [{'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}]
        })
        
        # Create review as user1
        create_event = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 5, 'comment': 'Test'},
            user_id='user1'
        )
        create_response = lambda_handler(create_event, {})
        review_id = json.loads(create_response['body'])['data']['review_id']

        # Try to delete as user2
        delete_event = self._create_auth_event(
            f'/reviews/{review_id}',
            'DELETE',
            user_id='user2'
        )
        response = lambda_handler(delete_event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Not authorized' in data['message']

    # ── Recommendations Tests ─────────────────────────────────────────────────

    def test_get_recommendations_success(self):
        """Recommendations should return similar products based on category and price."""
        event = {
            'rawPath': '/recommendations',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'productIds': '1,2', 'limit': '5'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert isinstance(data['data'], list)
        # Should recommend products from same category (Electronics)
        for rec in data['data']:
            assert rec['id'] not in ['1', '2']  # Should not recommend input products

    def test_get_recommendations_missing_product_ids(self):
        event = {
            'rawPath': '/recommendations',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'Product IDs are required' in data['message']

    def test_get_recommendations_invalid_product_ids(self):
        event = {
            'rawPath': '/recommendations',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'productIds': '999,888'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        # Should return empty list for non-existent products
        assert data['data'] == []

    # ── Product Variants Tests ────────────────────────────────────────────────

    def test_get_product_variants(self):
        """Test getting all variants for a product."""
        # Add product with variants
        self.product_table.put_item(Item={
            'id': '10',
            'name': 'T-Shirt',
            'price': 1500,
            'category': 'Clothing',
            'stock_quantity': 100,
            'variants': [
                {'variant_id': 'v1', 'size': 'S', 'color': 'Red', 'price': 1500, 'stock': 20},
                {'variant_id': 'v2', 'size': 'M', 'color': 'Blue', 'price': 1500, 'stock': 30}
            ]
        })

        event = {
            'rawPath': '/products/10/variants',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert len(data['data']) == 2
        assert data['data'][0]['variant_id'] == 'v1'

    def test_get_specific_variant(self):
        """Test getting a specific variant by variant_id."""
        self.product_table.put_item(Item={
            'id': '10',
            'name': 'T-Shirt',
            'price': 1500,
            'variants': [
                {'variant_id': 'v1', 'size': 'S', 'color': 'Red', 'price': 1500, 'stock': 20}
            ]
        })

        event = {
            'rawPath': '/products/10/variants/v1',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['variant_id'] == 'v1'
        assert data['data']['size'] == 'S'

    def test_get_variant_not_found(self):
        event = {
            'rawPath': '/products/10/variants/nonexistent',
            'requestContext': {'http': {'method': 'GET'}}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404

    # ── Filtering and Sorting Tests ───────────────────────────────────────────

    def test_filter_by_category(self):
        event = {
            'rawPath': '/products',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'category': 'Electronics'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        items = data['data']['items']
        assert all(item['category'] == 'Electronics' for item in items)

    def test_filter_by_price_range(self):
        event = {
            'rawPath': '/products',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'minPrice': '10000', 'maxPrice': '20000'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        items = data['data']['items']
        for item in items:
            assert 10000 <= item['price'] <= 20000

    def test_sort_by_price_low_to_high(self):
        event = {
            'rawPath': '/products',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'sortBy': 'price_low_high'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        items = data['data']['items']
        prices = [item['price'] for item in items]
        assert prices == sorted(prices)

    def test_sort_by_price_high_to_low(self):
        event = {
            'rawPath': '/products',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'sortBy': 'price_high_low'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        items = data['data']['items']
        prices = [item['price'] for item in items]
        assert prices == sorted(prices, reverse=True)

    # ── Pagination Tests ──────────────────────────────────────────────────────

    def test_pagination_with_limit(self):
        event = {
            'rawPath': '/products',
            'requestContext': {'http': {'method': 'GET'}},
            'queryStringParameters': {'limit': '2'}
        }
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert len(data['data']['items']) <= 2

    # ── Invalid Route ─────────────────────────────────────────────────────────

    def test_invalid_route(self):
        event = {'rawPath': '/invalid', 'requestContext': {'http': {'method': 'GET'}}}
        response = lambda_handler(event, {})
        assert response['statusCode'] == 404
        data = json.loads(response['body'])
        assert 'Route not found' in data['message']

    # ── Verified Purchase Tests ───────────────────────────────────────────────

    def test_create_review_without_purchase(self):
        """Test that users can't review products they haven't ordered."""
        event = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 5, 'comment': 'Great product!'},
            user_id='user_no_orders'
        )
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'can only review products you have ordered' in data['message']

    def test_create_review_with_verified_purchase(self):
        """Test that users can review products they've ordered and received."""
        # Add delivered order with product (orders table already exists from setup)
        self.orders_table.put_item(Item={
            'order_id': 'order_123',
            'user_id': 'verified_user',
            'status': 'delivered',
            'items': [
                {'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}
            ]
        })

        # Create review
        event = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 5, 'comment': 'Excellent product!'},
            user_id='verified_user'
        )
        response = lambda_handler(event, {})
        assert response['statusCode'] == 200
        data = json.loads(response['body'])
        assert data['data']['rating'] == 5

    def test_create_review_order_not_delivered(self):
        """Test that users can't review if order not delivered/shipped."""
        # Add order with "processing" status (not delivered)
        self.orders_table.put_item(Item={
            'order_id': 'order_456',
            'user_id': 'pending_user',
            'status': 'processing',
            'items': [
                {'id': '1', 'name': 'Wireless Bluetooth Headphones', 'price': 15000, 'quantity': 1}
            ]
        })

        # Try to create review
        event = self._create_auth_event(
            '/products/1/reviews',
            'POST',
            body={'rating': 5, 'comment': 'Great!'},
            user_id='pending_user'
        )
        response = lambda_handler(event, {})
        assert response['statusCode'] == 400
        data = json.loads(response['body'])
        assert 'can only review products you have ordered' in data['message']
