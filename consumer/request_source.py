import boto3

client = boto3.client("s3")
sqs_client = boto3.client("sqs")
queue_url_cache = None
message_cache = []

def get_queue_url(queue_name):
    global queue_url_cache
    if queue_url_cache is not None:
        return queue_url_cache
    response = sqs_client.get_queue_url(QueueName=queue_name)
    queue_url_cache = response["QueueUrl"]
    return queue_url_cache

def fetch_request_sqs(queue_name):
    if message_cache:
        message = message_cache.pop(0)
        return message["Body"], message["ReceiptHandle"]
    url = get_queue_url(queue_name)
    response = sqs_client.receive_message(
        QueueUrl=url,
        MaxNumberOfMessages=10,
        WaitTimeSeconds=20
    )
    if "Messages" not in response:
        return None, None
    message_cache.extend(response["Messages"])
    message = message_cache.pop(0)
    return message["Body"], message["ReceiptHandle"]


def delete_request_sqs(queue_name, receipt_handle):
    url = get_queue_url(queue_name)
    sqs_client.delete_message(QueueUrl=url, ReceiptHandle=receipt_handle)

def fetch_request(bucket): # fetch the next request
    response = client.list_objects_v2(
        Bucket=bucket,
        MaxKeys = 1
    )
    # print(response)
    if "Contents" not in response:
        return None, None
    key = response["Contents"][0]["Key"]
    obj = client.get_object(Bucket=bucket, Key=key)
    body = obj["Body"].read().decode("utf-8")
    # print("key="+key)
    # print("body="+body)
    return key, body

def delete_request(bucket, key): # delete request after reading
    client.delete_object(Bucket=bucket, Key=key)