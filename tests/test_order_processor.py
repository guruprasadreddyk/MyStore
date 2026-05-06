"""
Tests for order_processor.py (SQS order fulfillment worker)
"""
import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'services'))

os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['RESEND_API_KEY'] = 'test-key'
os.environ['RESEND_FROM'] = 'test@example.com'

import pytest
import json
import boto3
from moto import mock_aws
from unittest.mock import patch


@mock_aws
class TestOrderProcessor:
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

        self.orders_table.put_item(Item={
            'order_id': 'order_123',
            'user_id': 'user_123',
            'user_email': 'test@example.com',
            'items': [{'id': '1', 'name': 'Test Product', 'price': 999, 'quantity': 1}],
            'address': {
                'full_name': 'John Doe',
                'phone': '9876543210',
                'address_line1': '123 Test St',
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'pincode': '400001'
            },
            'status': 'paid',
            'grand_total': 1179,
            'created_at': '2026-05-05T10:00:00Z'
        })

    def test_process_order_success(self):
        """Test successful order processing."""
        from order_processor import lambda_handler

        event = {'Records': [{'body': json.dumps({'order_id': 'order_123'})}]}

        with patch('order_processor.send_email_via_resend'), \
             patch('order_processor.publish_sns_notification'):
            response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        order = self.orders_table.get_item(Key={'order_id': 'order_123'})['Item']
        assert order['status'] == 'shipped'

    def test_process_multiple_orders(self):
        """Test processing multiple orders in batch."""
        self.orders_table.put_item(Item={
            'order_id': 'order_456',
            'user_id': 'user_456',
            'user_email': 'test2@example.com',
            'items': [{'id': '2', 'name': 'Product 2', 'price': 1999, 'quantity': 1}],
            'address': {'full_name': 'Jane Doe', 'phone': '9876543211',
                        'address_line1': '456 Test Ave', 'city': 'Delhi',
                        'state': 'Delhi', 'pincode': '110001'},
            'status': 'paid',
            'grand_total': 2359,
            'created_at': '2026-05-05T11:00:00Z'
        })

        event = {
            'Records': [
                {'body': json.dumps({'order_id': 'order_123'})},
                {'body': json.dumps({'order_id': 'order_456'})}
            ]
        }

        with patch('order_processor.send_email_via_resend'), \
             patch('order_processor.publish_sns_notification'):
            response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        assert self.orders_table.get_item(Key={'order_id': 'order_123'})['Item']['status'] == 'shipped'
        assert self.orders_table.get_item(Key={'order_id': 'order_456'})['Item']['status'] == 'shipped'

    def test_process_order_not_found(self):
        """Test processing order that doesn't exist."""
        from order_processor import lambda_handler

        event = {'Records': [{'body': json.dumps({'order_id': 'nonexistent_order'})}]}

        with patch('order_processor.send_email_via_resend'), \
             patch('order_processor.publish_sns_notification'):
            response = lambda_handler(event, None)

        assert response['statusCode'] == 200

    def test_process_order_email_failure(self):
        """Test order processing continues even if email fails."""
        from order_processor import lambda_handler

        event = {'Records': [{'body': json.dumps({'order_id': 'order_123'})}]}

        with patch('order_processor.send_email_via_resend', side_effect=Exception('Email failed')), \
             patch('order_processor.publish_sns_notification'):
            response = lambda_handler(event, None)

        assert response['statusCode'] == 200
        order = self.orders_table.get_item(Key={'order_id': 'order_123'})['Item']
        assert order['status'] == 'shipped'

    def test_process_order_invalid_json(self):
        """Test processing message with invalid JSON."""
        from order_processor import lambda_handler

        event = {'Records': [{'body': 'invalid json'}]}

        response = lambda_handler(event, None)
        assert response['statusCode'] == 200

    def test_process_order_missing_order_id(self):
        """Test processing message without order_id."""
        from order_processor import lambda_handler

        event = {'Records': [{'body': json.dumps({'some_other_field': 'value'})}]}

        response = lambda_handler(event, None)
        assert response['statusCode'] == 200

    def test_empty_sqs_batch(self):
        """Test processing empty SQS batch."""
        from order_processor import lambda_handler

        event = {'Records': []}
        response = lambda_handler(event, None)
        assert response['statusCode'] == 200

    def test_process_order_updates_status(self):
        """Test that order status is updated to shipped."""
        from order_processor import lambda_handler

        event = {'Records': [{'body': json.dumps({'order_id': 'order_123'})}]}

        with patch('order_processor.send_email_via_resend'), \
             patch('order_processor.publish_sns_notification'):
            lambda_handler(event, None)

        order = self.orders_table.get_item(Key={'order_id': 'order_123'})['Item']
        assert order['status'] == 'shipped'

    def test_process_order_concurrent_update(self):
        """Test handling order already shipped (idempotent)."""
        from order_processor import lambda_handler

        self.orders_table.update_item(
            Key={'order_id': 'order_123'},
            UpdateExpression='SET #s = :status',
            ExpressionAttributeNames={'#s': 'status'},
            ExpressionAttributeValues={':status': 'shipped'}
        )

        event = {'Records': [{'body': json.dumps({'order_id': 'order_123'})}]}

        with patch('order_processor.send_email_via_resend'), \
             patch('order_processor.publish_sns_notification'):
            response = lambda_handler(event, None)

        assert response['statusCode'] == 200


# Need to import at module level for the class methods that don't re-import
from order_processor import lambda_handler
