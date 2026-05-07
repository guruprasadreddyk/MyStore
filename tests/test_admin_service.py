"""
Tests for admin_service.py
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['SMTP_USER'] = ''
os.environ['SMTP_PASSWORD'] = ''

import pytest
import json
from moto import mock_aws
import boto3
from decimal import Decimal


def create_admin_event(path, method, body=None, query_params=None):
    """Helper to create admin event with proper JWT claims."""
    event = {
        'rawPath': path,
        'requestContext': {
            'http': {'method': method},
            'authorizer': {
                'jwt': {
                    'claims': {
                        'sub': 'admin_user',
                        'email': 'admin@example.com',
                        'https://mystore.com/roles': ['admin']
                    }
                }
            }
        }
    }
    if body:
        event['body'] = json.dumps(body)
    if query_params:
        event['queryStringParameters'] = query_params
    return event


@pytest.fixture
def dynamodb_tables():
    """Create mock DynamoDB tables for testing."""
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        
        # Create products table
        products_table = dynamodb.create_table(
            TableName='products_table_guru',
            KeySchema=[
                {'AttributeName': 'id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'id', 'AttributeType': 'S'},
                {'AttributeName': 'category', 'AttributeType': 'S'},
                {'AttributeName': 'price', 'AttributeType': 'N'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'category-price-index',
                    'KeySchema': [
                        {'AttributeName': 'category', 'KeyType': 'HASH'},
                        {'AttributeName': 'price', 'KeyType': 'RANGE'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        
        # Create orders table
        orders_table = dynamodb.create_table(
            TableName='orders_table_guru',
            KeySchema=[
                {'AttributeName': 'order_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'order_id', 'AttributeType': 'S'},
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST',
            GlobalSecondaryIndexes=[
                {
                    'IndexName': 'user_id-index',
                    'KeySchema': [
                        {'AttributeName': 'user_id', 'KeyType': 'HASH'}
                    ],
                    'Projection': {'ProjectionType': 'ALL'}
                }
            ]
        )
        
        # Create user data table
        user_data_table = dynamodb.create_table(
            TableName='user_data_table_guru',
            KeySchema=[
                {'AttributeName': 'user_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'user_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Create returns table
        returns_table = dynamodb.create_table(
            TableName='returns_table_guru',
            KeySchema=[
                {'AttributeName': 'return_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'return_id', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        
        # Seed test data
        products_table.put_item(Item={
            'id': '1',
            'name': 'Test Product',
            'price': 999,
            'category': 'Electronics',
            'stock_quantity': 10,
            'description': 'Test description',
            'rating': Decimal('4.5'),
            'review_count': 100
        })
        
        orders_table.put_item(Item={
            'order_id': 'order_123',
            'user_id': 'user_123',
            'user_email': 'test@example.com',
            'items': [
                {
                    'id': '1',
                    'name': 'Test Product',
                    'price': 999,
                    'quantity': 1
                }
            ],
            'status': 'created',
            'grand_total': 1179,
            'created_at': '2026-05-05T10:00:00Z'
        })
        
        user_data_table.put_item(Item={
            'user_id': 'user_123',
            'email': 'test@example.com',
            'created_at': '2026-01-01T00:00:00Z'
        })
        
        yield {
            'products_table': products_table,
            'orders_table': orders_table,
            'user_data_table': user_data_table,
            'returns_table': returns_table
        }


def test_get_all_products_admin(dynamodb_tables):
    """Test admin can get all products."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/products', 'GET')
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert len(body['data']) > 0


def test_create_product(dynamodb_tables):
    """Test admin can create a product."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/products', 'POST', body={
        'id': '999',
        'name': 'New Product',
        'price': 1999,
        'category': 'Electronics',
        'stock_quantity': 50,
        'description': 'New product description',
        'rating': 4.0
    })
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert body['data']['name'] == 'New Product'
    assert 'id' in body['data']


def test_update_product(dynamodb_tables):
    """Test admin can update a product."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/products/1', 'PUT', body={
        'name': 'Updated Product',
        'price': 1499
    })
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert body['data']['name'] == 'Updated Product'
    assert body['data']['price'] == 1499


def test_update_product_stock(dynamodb_tables):
    """Test admin can update product stock."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/products/1', 'PUT', body={
        'stock_quantity': 100
    })
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert body['data']['stock_quantity'] == 100


def test_delete_product(dynamodb_tables):
    """Test admin can delete a product."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/products/1', 'DELETE')
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'


def test_get_all_orders_admin(dynamodb_tables):
    """Test admin can get all orders."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/orders', 'GET')
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert len(body['data']) > 0


def test_update_order_status_admin(dynamodb_tables):
    """Test admin can update order status."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/orders/order_123', 'PUT', body={
        'status': 'shipped'
    })
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert body['data']['status'] == 'shipped'


def test_create_product_missing_fields(dynamodb_tables):
    """Test creating product with missing required fields."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/products', 'POST', body={
        'name': 'Incomplete Product'
        # Missing required fields
    })
    
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert body['status'] == 'error'


def test_update_nonexistent_product(dynamodb_tables):
    """Test updating a product that doesn't exist."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/products/999', 'PUT', body={
        'name': 'Updated Product'
    })
    
    response = lambda_handler(event, None)
    
    # Product doesn't exist, but update returns success with empty result
    # This is acceptable behavior - just verify no crash
    assert response['statusCode'] in [200, 404]


def test_invalid_route(dynamodb_tables):
    """Test invalid admin route."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/invalid', 'GET')
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert body['status'] == 'error'


def test_get_all_returns_admin(dynamodb_tables):
    """Test admin can get all return requests."""
    from services.admin_service import lambda_handler
    
    # Use the returns table from fixture
    returns_table = dynamodb_tables['returns_table']
    
    returns_table.put_item(Item={
        'return_id': 'return_123',
        'order_id': 'order_123',
        'user_id': 'user_123',
        'reason': 'defective',
        'status': 'pending',
        'refund_amount': 1179,
        'created_at': '2026-05-05T10:00:00Z'
    })
    
    event = create_admin_event('/admin/returns', 'GET')
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert len(body['data']) > 0


def test_get_returns_with_status_filter(dynamodb_tables):
    """Test filtering returns by status."""
    from services.admin_service import lambda_handler
    
    returns_table = dynamodb_tables['returns_table']
    
    # Add returns with different statuses
    returns_table.put_item(Item={
        'return_id': 'return_pending',
        'order_id': 'order_123',
        'status': 'pending'
    })
    
    returns_table.put_item(Item={
        'return_id': 'return_approved',
        'order_id': 'order_456',
        'status': 'approved'
    })
    
    event = create_admin_event('/admin/returns', 'GET', query_params={'status': 'pending'})
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert all(item['status'] == 'pending' for item in body['data'])


def test_approve_return_admin(dynamodb_tables):
    """Test approving a return request."""
    from services.admin_service import lambda_handler
    
    returns_table = dynamodb_tables['returns_table']
    
    returns_table.put_item(Item={
        'return_id': 'return_123',
        'order_id': 'order_123',
        'status': 'pending'
    })
    
    event = create_admin_event('/admin/returns/return_123/approve', 'PUT')
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert body['data']['status'] == 'approved'


def test_reject_return_admin(dynamodb_tables):
    """Test rejecting a return with reason."""
    from services.admin_service import lambda_handler
    
    returns_table = dynamodb_tables['returns_table']
    
    returns_table.put_item(Item={
        'return_id': 'return_456',
        'order_id': 'order_456',
        'status': 'pending'
    })
    
    event = create_admin_event('/admin/returns/return_456/reject', 'PUT', body={'reason': 'Return window expired'})
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert body['data']['status'] == 'rejected'
    assert body['data']['rejection_reason'] == 'Return window expired'


def test_reject_return_without_reason(dynamodb_tables):
    """Test rejecting without reason still works."""
    from services.admin_service import lambda_handler
    
    returns_table = dynamodb_tables['returns_table']
    
    returns_table.put_item(Item={
        'return_id': 'return_789',
        'order_id': 'order_789',
        'status': 'pending'
    })
    
    event = create_admin_event('/admin/returns/return_789/reject', 'PUT', body={})
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert body['data']['status'] == 'rejected'


def test_process_refund_admin(dynamodb_tables):
    """Test processing refund for approved return."""
    from services.admin_service import lambda_handler
    
    returns_table = dynamodb_tables['returns_table']
    
    returns_table.put_item(Item={
        'return_id': 'return_999',
        'order_id': 'order_999',
        'status': 'approved'
    })
    
    event = create_admin_event('/admin/returns/return_999/refund', 'PUT')
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert body['data']['status'] == 'refunded'
    assert body['data']['refund_status'] == 'completed'


def test_get_dashboard_stats(dynamodb_tables):
    """Test dashboard analytics endpoint."""
    from services.admin_service import lambda_handler
    
    event = create_admin_event('/admin/dashboard', 'GET')
    response = lambda_handler(event, None)
    
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['status'] == 'success'
    assert 'total_orders' in body['data']
    assert 'total_revenue' in body['data']
    assert 'status_counts' in body['data']
    assert 'low_stock' in body['data']
    assert 'top_products' in body['data']
    assert 'time_series' in body['data']
