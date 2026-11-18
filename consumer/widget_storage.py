import json
import boto3

def store_widget(storage_target, data, widget_destination):
    success = False
    if storage_target == "s3":
        success = _store_widget_s3(data, widget_destination)
    else:
        success = _store_widget_dynamodb(data, widget_destination)
    return success

def _store_widget_s3(data, widget_destination):
    key = _build_s3_key(data)
    s3 = boto3.client("s3")
    body = json.dumps(data)
    response = s3.put_object(Bucket=widget_destination, Key=key, Body=body)
    status = response["ResponseMetadata"]["HTTPStatusCode"]
    return status == 200

def _store_widget_dynamodb(data, widget_destination):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(widget_destination)
    item = _build_dynamodb_item(data)
    response = table.put_item(Item=item)
    status = response["ResponseMetadata"]["HTTPStatusCode"]
    return status == 200

def _build_s3_key(data):
    owner = data["owner"]
    if owner == "" or owner is None:
        owner = "Unknown Owner"
    owner_string = owner.lower().replace(" ", "-")
    widget_id = data["widgetId"]
    key = "widgets/"+owner_string+"/"+widget_id
    return key

def _build_dynamodb_item(data):
    item = {
        "id": data["widgetId"],
        "owner": data["owner"]
    }
    if "label" in data:
        item["label"] = data["label"]
    if "description" in data:
        item["description"] = data["description"]
    if "otherAttributes" in data:
        for attributes in data["otherAttributes"]:
            item[attributes["name"]] = attributes["value"]
        #print(item)
    return item

def update_widget(storage_target, data, widget_destination):
    success = False
    if storage_target == "s3":
        success = _update_widget_s3(data, widget_destination)
    else:
        success = _update_widget_dynamodb(data, widget_destination)
    return success

def _update_widget_s3(data, widget_destination):
    key = _build_s3_key(data)
    s3 = boto3.client("s3")
    response = s3.get_object(Bucket=widget_destination, Key=key)
    existing = json.loads(response["Body"].read().decode("utf-8"))
    for field in ["owner", "label", "description"]:
        if field in data:
            existing[field] = data[field]
    if "otherAttributes" in data:
        for attr in data["otherAttributes"]:
            existing[attr["name"]] = attr["value"]
    response = s3.put_object(Bucket=widget_destination, Key=key, Body=json.dumps(existing))
    status = response["ResponseMetadata"]["HTTPStatusCode"]
    return status == 200

def _update_widget_dynamodb(data, widget_destination):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(widget_destination)
    response = table.get_item(Key={"id": data["widgetId"]})
    existing = response["Item"]
    for field in ["owner", "label", "description"]:
        if field in data:
            existing[field] = data[field]
    if "otherAttributes" in data:
        for attr in data["otherAttributes"]:
            existing[attr["name"]] = attr["value"]
    response = table.put_item(Item=existing)
    status = response["ResponseMetadata"]["HTTPStatusCode"]
    return status == 200

def delete_widget(storage_target, data, widget_destination):
    success = False
    if storage_target == "s3":
        success = _delete_widget_s3(data, widget_destination)
    else:
        success = _delete_widget_dynamodb(data, widget_destination)
    return success

def _delete_widget_s3(data, widget_destination):
    key = _build_s3_key(data)
    s3 = boto3.client("s3")
    response = s3.delete_object(Bucket=widget_destination, Key=key)
    status = response["ResponseMetadata"]["HTTPStatusCode"]
    return status == 200

def _delete_widget_dynamodb(data, widget_destination):
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(widget_destination)
    response = table.delete_item(Key={"id": data["widgetId"]})
    status = response["ResponseMetadata"]["HTTPStatusCode"]
    return status == 200
