"""
Tests for utils.py
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
import json
import os


def test_convert_decimal():
    from services.utils import convert_decimal

    assert convert_decimal(Decimal('10.5')) == 10.5
    assert isinstance(convert_decimal(Decimal('10.5')), float)

    data = {'price': Decimal('999.99'), 'rating': Decimal('4.5'), 'name': 'Product'}
    result = convert_decimal(data)
    assert result['price'] == 999.99
    assert result['rating'] == 4.5
    assert result['name'] == 'Product'

    data = [{'price': Decimal('100')}, {'price': Decimal('200')}]
    result = convert_decimal(data)
    assert result[0]['price'] == 100
    assert result[1]['price'] == 200

    data = {'items': [{'price': Decimal('50.5')}, {'price': Decimal('75.25')}], 'total': Decimal('125.75')}
    result = convert_decimal(data)
    assert result['items'][0]['price'] == 50.5
    assert result['total'] == 125.75

    assert convert_decimal(None) is None
    assert convert_decimal('string') == 'string'
    assert convert_decimal(123) == 123


def test_convert_decimal_edge_cases():
    from services.utils import convert_decimal

    assert convert_decimal({}) == {}
    assert convert_decimal([]) == []
    assert convert_decimal(True) is True
    assert convert_decimal(Decimal('0')) == 0
    assert convert_decimal(Decimal('-10.5')) == -10.5
    assert convert_decimal(Decimal('999999999.99')) == 999999999.99
    assert convert_decimal(Decimal('0.01')) == 0.01


def test_response():
    from services.utils import response

    result = response(200, data={'id': '1'}, message='Success')
    assert result['statusCode'] == 200
    assert result['headers']['Content-Type'] == 'application/json'
    assert result['headers']['Access-Control-Allow-Origin'] == '*'
    body = json.loads(result['body'])
    assert body['status'] == 'success'
    assert body['data'] == {'id': '1'}
    assert body['message'] == 'Success'

    result = response(400, message='Bad request')
    body = json.loads(result['body'])
    assert body['status'] == 'error'
    assert body['message'] == 'Bad request'
    assert body['data'] is None

    result = response(200, data={'items': []})
    body = json.loads(result['body'])
    assert body['status'] == 'success'
    assert body['data'] == {'items': []}
    assert body['message'] is None


def test_response_with_decimals():
    from services.utils import response

    result = response(200, data={'price': Decimal('999.99'), 'rating': Decimal('4.5')})
    body = json.loads(result['body'])
    assert body['data']['price'] == 999.99
    assert body['data']['rating'] == 4.5


def test_response_cors_headers():
    from services.utils import response

    result = response(200, data={'test': 'data'})
    assert 'Access-Control-Allow-Origin' in result['headers']
    assert 'Access-Control-Allow-Methods' in result['headers']
    assert 'Access-Control-Allow-Headers' in result['headers']


def test_get_user_id():
    from services.utils import get_user_id

    event = {'requestContext': {'authorizer': {'jwt': {'claims': {'sub': 'auth0|123456789'}}}}}
    assert get_user_id(event) == 'auth0|123456789'

    assert get_user_id({'requestContext': {}}) is None


def test_get_email_verified_true():
    from services.utils import get_email_verified

    event = {'requestContext': {'authorizer': {'jwt': {'claims': {
        'https://mystore.com/email_verified': 'true'
    }}}}}
    assert get_email_verified(event) is True


def test_get_email_verified_false():
    from services.utils import get_email_verified

    event = {'requestContext': {'authorizer': {'jwt': {'claims': {
        'https://mystore.com/email_verified': 'false'
    }}}}}
    assert get_email_verified(event) is False


def test_get_email_verified_missing_claim_defaults_true():
    """When claim is absent (Auth0 Action not yet updated), fail open — allow emails."""
    from services.utils import get_email_verified

    event = {'requestContext': {'authorizer': {'jwt': {'claims': {'sub': 'user_123'}}}}}
    assert get_email_verified(event) is True


def test_get_email_verified_missing_context_defaults_true():
    from services.utils import get_email_verified

    assert get_email_verified({'requestContext': {}}) is True


def test_get_email_verified_bool_true():
    """Handle boolean value (not just string)."""
    from services.utils import get_email_verified

    event = {'requestContext': {'authorizer': {'jwt': {'claims': {
        'https://mystore.com/email_verified': True
    }}}}}
    assert get_email_verified(event) is True


def test_get_user_email():
    from services.utils import get_user_email

    event = {'requestContext': {'authorizer': {'jwt': {'claims': {'email': 'test@example.com'}}}}}
    assert get_user_email(event) == 'test@example.com'

    # Namespaced claim takes priority
    event = {'requestContext': {'authorizer': {'jwt': {'claims': {
        'https://mystore.com/email': 'ns@example.com',
        'email': 'plain@example.com'
    }}}}}
    assert get_user_email(event) == 'ns@example.com'

    assert get_user_email({'requestContext': {}}) is None


def test_get_user_email_rejects_non_string():
    """Auth0 Action misconfiguration — boolean True stored as email claim — must return empty string."""
    from services.utils import get_user_email

    # Simulates: api.accessToken.setCustomClaim('https://mystore.com/email', event.user.email_verified)
    event = {'requestContext': {'authorizer': {'jwt': {'claims': {
        'https://mystore.com/email': True,   # boolean, not a string
        'email': None
    }}}}}
    result = get_user_email(event)
    assert result == ''
    assert result is not True


def test_get_user_email_falls_back_when_namespaced_is_boolean():
    """If namespaced claim is boolean but standard email is valid, use standard email."""
    from services.utils import get_user_email

    event = {'requestContext': {'authorizer': {'jwt': {'claims': {
        'https://mystore.com/email': True,
        'email': 'fallback@example.com'
    }}}}}
    assert get_user_email(event) == 'fallback@example.com'


# ── get_table_name ────────────────────────────────────────────────────────────

def test_get_table_name_defaults():
    from services.utils import get_table_name

    assert get_table_name('products')  == 'products_table_guru'
    assert get_table_name('orders')    == 'orders_table_guru'
    assert get_table_name('cart')      == 'cart_table_guru'
    assert get_table_name('wishlist')  == 'wishlist_table_guru'
    assert get_table_name('user_data') == 'user_data_table_guru'
    assert get_table_name('reviews')   == 'reviews_table_guru'
    assert get_table_name('returns')   == 'returns_table_guru'


def test_get_table_name_env_override():
    from services.utils import get_table_name

    with patch.dict(os.environ, {'PRODUCTS_TABLE': 'my_custom_products_table'}):
        assert get_table_name('products') == 'my_custom_products_table'

    # Other tables unaffected
    assert get_table_name('orders') == 'orders_table_guru'


# ── send_email (Gmail SMTP) ───────────────────────────────────────────────────

def test_send_email_no_credentials():
    """No SMTP creds — should log and return without raising."""
    from services.utils import send_email_via_resend

    with patch.dict(os.environ, {'SMTP_USER': '', 'SMTP_PASSWORD': ''}):
        send_email_via_resend('test@example.com', 'Subject', '<p>Body</p>')


def test_send_email_no_recipient():
    """Empty recipient — should skip silently."""
    from services.utils import send_email_via_resend

    with patch.dict(os.environ, {'SMTP_USER': 'sender@gmail.com', 'SMTP_PASSWORD': 'pass'}):
        send_email_via_resend('', 'Subject', '<p>Body</p>')


def test_send_email_success():
    """Successful SMTP send."""
    from services.utils import send_email_via_resend

    with patch.dict(os.environ, {
        'SMTP_USER': 'sender@gmail.com',
        'SMTP_PASSWORD': 'apppassword',
        'SMTP_FROM': 'MyStore <sender@gmail.com>'
    }), patch('smtplib.SMTP_SSL') as mock_ssl:
        mock_server = MagicMock()
        mock_ssl.return_value.__enter__.return_value = mock_server

        send_email_via_resend('customer@example.com', 'Order Confirmed', '<p>Hi</p>', 'Hi')

        mock_server.login.assert_called_once_with('sender@gmail.com', 'apppassword')
        mock_server.sendmail.assert_called_once()


def test_send_email_retry_on_failure():
    """Should retry up to 3 times on SMTP error."""
    from services.utils import send_email_via_resend

    with patch.dict(os.environ, {'SMTP_USER': 'sender@gmail.com', 'SMTP_PASSWORD': 'pass'}), \
         patch('smtplib.SMTP_SSL', side_effect=Exception('Connection refused')), \
         patch('time.sleep'):  # speed up retries
        # Should not raise — just log errors
        send_email_via_resend('customer@example.com', 'Subject', '<p>Body</p>')


def test_send_email_succeeds_on_second_attempt():
    """Should succeed on retry after first failure."""
    from services.utils import send_email_via_resend

    mock_server = MagicMock()
    call_count = {'n': 0}

    def smtp_side_effect(*args, **kwargs):
        call_count['n'] += 1
        if call_count['n'] == 1:
            raise Exception('Temporary failure')
        ctx = MagicMock()
        ctx.__enter__ = MagicMock(return_value=mock_server)
        ctx.__exit__ = MagicMock(return_value=False)
        return ctx

    with patch.dict(os.environ, {'SMTP_USER': 'sender@gmail.com', 'SMTP_PASSWORD': 'pass'}), \
         patch('smtplib.SMTP_SSL', side_effect=smtp_side_effect), \
         patch('time.sleep'):
        send_email_via_resend('customer@example.com', 'Subject', '<p>Body</p>')

    assert mock_server.sendmail.called


# ── update_order_status ───────────────────────────────────────────────────────

def test_update_order_status_success():
    from services.utils import update_order_status
    from moto import mock_aws
    import boto3

    with patch.dict(os.environ, {'AWS_DEFAULT_REGION': 'us-east-1'}), mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='orders_table_guru',
            KeySchema=[{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'order_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.put_item(Item={'order_id': 'order_123', 'status': 'created', 'user_id': 'user_1'})

        result = update_order_status('order_123', 'shipped')
        assert result is True

        item = table.get_item(Key={'order_id': 'order_123'})['Item']
        assert item['status'] == 'shipped'
        # History tracking — new field added by the upgraded function
        assert 'status_history' in item
        assert item['status_history'][0]['status'] == 'shipped'


def test_update_order_status_with_message():
    from services.utils import update_order_status
    from moto import mock_aws
    import boto3

    with patch.dict(os.environ, {'AWS_DEFAULT_REGION': 'us-east-1'}), mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='orders_table_guru',
            KeySchema=[{'AttributeName': 'order_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'order_id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.put_item(Item={'order_id': 'order_123', 'status': 'created'})

        update_order_status('order_123', 'delivered', message='Delivered by courier')

        item = table.get_item(Key={'order_id': 'order_123'})['Item']
        assert item['status_history'][0]['message'] == 'Delivered by courier'


def test_update_order_status_failure():
    from services.utils import update_order_status
    from moto import mock_aws

    with mock_aws():
        # No table created — should handle gracefully
        result = update_order_status('nonexistent_order', 'shipped')
        assert result is False


# ── publish_sns_notification ──────────────────────────────────────────────────

def test_publish_sns_notification_success():
    from services.utils import publish_sns_notification
    from moto import mock_aws
    import boto3

    with patch.dict(os.environ, {'AWS_DEFAULT_REGION': 'us-east-1', 'AWS_REGION_NAME': 'us-east-1', 'SNS_TOPIC_NAME': 'order-notifications-guru'}), \
         mock_aws():
        sns = boto3.client('sns', region_name='us-east-1')
        sns.create_topic(Name='order-notifications-guru')

        result = publish_sns_notification('Test Subject', 'Test message')
        assert result is True


def test_publish_sns_notification_failure():
    from services.utils import publish_sns_notification

    result = publish_sns_notification('Test', 'Message')
    assert result is False


# ── fetch_product ─────────────────────────────────────────────────────────────

def test_fetch_product_not_found():
    from services.utils import fetch_product
    from moto import mock_aws
    import boto3

    with patch.dict(os.environ, {'AWS_DEFAULT_REGION': 'us-east-1'}), mock_aws():
        boto3.resource('dynamodb', region_name='us-east-1').create_table(
            TableName='products_table_guru',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        assert fetch_product('999') is None


def test_fetch_product_found():
    from services.utils import fetch_product
    from moto import mock_aws
    import boto3

    with patch.dict(os.environ, {'AWS_DEFAULT_REGION': 'us-east-1'}), mock_aws():
        table = boto3.resource('dynamodb', region_name='us-east-1').create_table(
            TableName='products_table_guru',
            KeySchema=[{'AttributeName': 'id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'id', 'AttributeType': 'S'}],
            BillingMode='PAY_PER_REQUEST'
        )
        table.put_item(Item={'id': '1', 'name': 'Test Product', 'price': 999})

        product = fetch_product('1')
        assert product is not None
        assert product['name'] == 'Test Product'
