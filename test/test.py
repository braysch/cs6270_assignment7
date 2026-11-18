import json
from unittest.mock import patch
import pytest

from consumer.widget_storage import _build_s3_key, _build_dynamodb_item, store_widget, update_widget, delete_widget
from consumer.request_source import fetch_request_sqs, delete_request_sqs, get_queue_url


#s3

def test_build_s3_key():
    data = {"owner": "John Schmidt", "widgetId": "abc-123"}
    assert _build_s3_key(data) == "widgets/john-schmidt/abc-123"

def test_build_s3_key_no_spaces():
    data = {"owner": "John", "widgetId": "abc-123"}
    assert _build_s3_key(data) == "widgets/john/abc-123"

def test_build_s3_key_multiple_spaces():
    data = {"owner": "John Jacob Jingle-Heimer Schmidt", "widgetId": "abc-123"}
    assert _build_s3_key(data) == "widgets/john-jacob-jingle-heimer-schmidt/abc-123"

def test_build_s3_key_empty_widget_id():
    data = {"owner": "John Schmidt", "widgetId": ""}
    assert _build_s3_key(data) == "widgets/john-schmidt/"

def test_build_s3_key_missing_widget_id():
    data = {"owner": "John Schmidt"}
    with pytest.raises(KeyError): _build_s3_key(data)

def test_build_s3_key_no_data():
    data = {}
    with pytest.raises(KeyError): _build_s3_key(data)

# dynamodb

def test_build_dynamodb_item():
    data = {
        "type": "WidgetCreateRequest",
        "requestId": "req-001",
        "widgetId": "widget-abc-123",
        "owner": "John Schmidt",
        "label": "Blue Widget",
        "description": "A standard blue widget",
        "otherAttributes": [
            {"name": "color", "value": "blue"},
            {"name": "size", "value": "large"},
            {"name": "weight", "value": "10kg"}
        ]
    }
    item = _build_dynamodb_item(data)
    assert item["id"] == "widget-abc-123"
    assert item["owner"] == "John Schmidt"
    assert item["label"] == "Blue Widget"
    assert item["description"] == "A standard blue widget"
    assert item["color"] == "blue"
    assert item["size"] == "large"
    assert item["weight"] == "10kg"

def test_build_dynamodb_item_no_other_attributes():
    data = {
        "type": "WidgetCreateRequest",
        "requestId": "req-001",
        "widgetId": "widget-abc-123",
        "owner": "John Schmidt",
        "label": "Blue Widget",
        "description": "A standard blue widget",
    }
    item = _build_dynamodb_item(data)
    assert item["id"] == "widget-abc-123"
    assert item["owner"] == "John Schmidt"
    assert item["label"] == "Blue Widget"
    assert item["description"] == "A standard blue widget"
    assert "color" not in item
    assert "size" not in item
    assert "weight" not in item

def test_build_dynamodb_item_other_attributes_empty():
    data = {
        "type": "WidgetCreateRequest",
        "requestId": "req-001",
        "widgetId": "widget-abc-123",
        "owner": "John Schmidt",
        "label": "Blue Widget",
        "description": "A standard blue widget",
        "otherAttributes": []
    }
    item = _build_dynamodb_item(data)
    assert item["id"] == "widget-abc-123"
    assert item["owner"] == "John Schmidt"
    assert item["label"] == "Blue Widget"
    assert item["description"] == "A standard blue widget"
    assert "color" not in item
    assert "size" not in item
    assert "weight" not in item

def test_build_dynamodb_missing_optional_items():
    data = {
        "type": "WidgetCreateRequest",
        "requestId": "req-001",
        "widgetId": "widget-abc-123",
        "owner": "John Schmidt"
    }
    item = _build_dynamodb_item(data)
    assert item["id"] == "widget-abc-123"
    assert item["owner"] == "John Schmidt"
    assert "label" not in item
    assert "description" not in item
    assert "color" not in item
    assert "size" not in item
    assert "weight" not in item

# requests

def test_parse_valid_request():
    request = '{"type": "create", "widgetId": "abc-123", "owner": "John Schmidt"}'
    data = json.loads(request)
    assert data["type"] == "create"
    assert data["widgetId"] == "abc-123"

def test_unknown_request_type():
    request = '{"type": "la;ijdfnoiaevj", "widgetId": "abc-123", "owner": "John Schmidt"}'
    json.loads(request)

# storage

@patch("consumer.widget_storage._store_widget_s3")
def test_store_widget_routes_to_s3(mock_s3):
    data = {"widgetId": "abc-123", "owner": "Alice"}
    store_widget("s3", data, "my-bucket")
    mock_s3.assert_called_once_with(data, "my-bucket")

@patch("consumer.widget_storage._store_widget_dynamodb")
def test_store_widget_routes_to_dynamodb(mock_dynamo):
    data = {"widgetId": "abc-123", "owner": "Alice"}
    store_widget("dynamodb", data, "my-table")
    mock_dynamo.assert_called_once_with(data, "my-table")

# update routing

@patch("consumer.widget_storage._update_widget_s3")
def test_update_widget_routes_to_s3(mock_s3):
    data = {"widgetId": "abc-123", "owner": "Alice"}
    update_widget("s3", data, "my-bucket")
    mock_s3.assert_called_once_with(data, "my-bucket")

@patch("consumer.widget_storage._update_widget_dynamodb")
def test_update_widget_routes_to_dynamodb(mock_dynamo):
    data = {"widgetId": "abc-123", "owner": "Alice"}
    update_widget("dynamodb", data, "my-table")
    mock_dynamo.assert_called_once_with(data, "my-table")

# delete routing

@patch("consumer.widget_storage._delete_widget_s3")
def test_delete_widget_routes_to_s3(mock_s3):
    data = {"widgetId": "abc-123", "owner": "Alice"}
    delete_widget("s3", data, "my-bucket")
    mock_s3.assert_called_once_with(data, "my-bucket")

@patch("consumer.widget_storage._delete_widget_dynamodb")
def test_delete_widget_routes_to_dynamodb(mock_dynamo):
    data = {"widgetId": "abc-123", "owner": "Alice"}
    delete_widget("dynamodb", data, "my-table")
    mock_dynamo.assert_called_once_with(data, "my-table")

# SQS fetch

@patch("consumer.request_source.sqs_client")
def test_fetch_request_sqs_returns_message(mock_sqs):
    import consumer.request_source as rs
    rs.message_cache = []
    rs.queue_url_cache = "https://sqs.us-east-1.amazonaws.com/123/cs5270-requests"
    mock_sqs.receive_message.return_value = {
        "Messages": [
            {"Body": '{"type": "create"}', "ReceiptHandle": "handle-1"}
        ]
    }
    receipt_handle, body = fetch_request_sqs("cs5270-requests")
    assert body == '{"type": "create"}'
    assert receipt_handle == "handle-1"

@patch("consumer.request_source.sqs_client")
def test_fetch_request_sqs_no_messages(mock_sqs):
    import consumer.request_source as rs
    rs.message_cache = []
    rs.queue_url_cache = "https://sqs.us-east-1.amazonaws.com/123/cs5270-requests"
    mock_sqs.receive_message.return_value = {}
    receipt_handle, body = fetch_request_sqs("cs5270-requests")
    assert body is None
    assert receipt_handle is None

@patch("consumer.request_source.sqs_client")
def test_fetch_request_sqs_uses_cache(mock_sqs):
    import consumer.request_source as rs
    rs.message_cache = [
        {"Body": '{"type": "delete"}', "ReceiptHandle": "handle-cached"}
    ]
    receipt_handle, body = fetch_request_sqs("cs5270-requests")
    assert body == '{"type": "delete"}'
    assert receipt_handle == "handle-cached"
    mock_sqs.receive_message.assert_not_called()

# SQS delete

@patch("consumer.request_source.sqs_client")
def test_delete_request_sqs(mock_sqs):
    import consumer.request_source as rs
    rs.queue_url_cache = "https://sqs.us-east-1.amazonaws.com/123/cs5270-requests"
    delete_request_sqs("cs5270-requests", "handle-1")
    mock_sqs.delete_message.assert_called_once_with(
        QueueUrl="https://sqs.us-east-1.amazonaws.com/123/cs5270-requests",
        ReceiptHandle="handle-1"
    )

# get_queue_url

@patch("consumer.request_source.sqs_client")
def test_get_queue_url_calls_api(mock_sqs):
    import consumer.request_source as rs
    rs.queue_url_cache = None
    mock_sqs.get_queue_url.return_value = {"QueueUrl": "https://sqs.us-east-1.amazonaws.com/123/my-queue"}
    url = get_queue_url("my-queue")
    assert url == "https://sqs.us-east-1.amazonaws.com/123/my-queue"
    mock_sqs.get_queue_url.assert_called_once_with(QueueName="my-queue")

@patch("consumer.request_source.sqs_client")
def test_get_queue_url_uses_cache(mock_sqs):
    import consumer.request_source as rs
    rs.queue_url_cache = "https://sqs.us-east-1.amazonaws.com/123/cached-queue"
    url = get_queue_url("cached-queue")
    assert url == "https://sqs.us-east-1.amazonaws.com/123/cached-queue"
    mock_sqs.get_queue_url.assert_not_called()