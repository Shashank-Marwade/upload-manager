import json
import subprocess
import sys
import boto3
import os
import logging
import time
import threading
import hashlib

from scripts_config import ScriptConfig as Config
from datetime import datetime, date

# Define a lock for synchronization
credentials_lock = threading.Lock()

class S3UploadMaxRetryReached(Exception):
    def __init__(self, message):
        self.message = message
        super().__init__(self.message)


class MoveFile:
    def __init__(self):
        self.access_key = None
        self.secret_key = None
        self.session_token = None
        self.prefix = None
        self.retry_count = 0
        self.config_file_path = Config.AWSIOT_SHADOW_FILE
        self.load_aws_credentials()
        self.s3 = boto3.client(
            "s3",
            aws_access_key_id=self.access_key,
            aws_secret_access_key=self.secret_key,
            aws_session_token=self.session_token,
        )

    def load_aws_credentials(self):
        with open(self.config_file_path, "r") as config_file:
            logging.info("Loading AWS credentials...")
            config_data = json.load(config_file)
            self.access_key = config_data["state"]["desired"]["S3"]["AccessKey"]
            self.secret_key = config_data["state"]["desired"]["S3"]["SecretKey"]
            self.session_token = config_data["state"]["desired"]["S3"]["SessionToken"]
            self.prefix = f'{config_data["state"]["delta"]["S3"]["Prefix"]}'

    def update_aws_credentials(self, access_key, secret_key, session_token):
        logging.info("Updating AWS credentials...")
        self.access_key = access_key
        self.secret_key = secret_key
        self.session_token = session_token

    def upload_file(self, src, dst):
        try:
            dst = f"{self.prefix}/{dst}"
            if "/texts/" in src or "/priority.texts/" in src:
                bucket = Config.TXT_BUCKET_NAME
            elif "/images/" in src or "/priority.images/" in src:
                bucket = Config.IMG_BUCKET_NAME
            elif "/videos/" in src:
                bucket = Config.VIDEO_BUCKET_NAME
            logging.info(f"Uploading started for {src} to {dst}")
            self.s3.upload_file(src, bucket, dst)
            upload_date_time = datetime.now().isoformat()
            file_date_time = date.today().isoformat()
            logging.info(f"Uploaded file {src} to S3 object {dst}")
            object_name = os.path.basename(src)
            mime_type = subprocess.getoutput(f"file --brief --mime-type {src}")

            bucket_type = self.get_bucket_type(src)
            activity_log(object_name, bucket_type, mime_type, file_date_time, upload_date_time)
            logging.info(f"Log file updated")

        except boto3.exceptions.S3UploadFailedError as error:
            if "InvalidToken" or "ExpiredToken" in str(error):
                access_key_request_log(datetime.now().isoformat())
                if self.retry_count <= 3:
                    self.retry_count += 1
                    self.handle_exception(src, dst)
                else:
                    logging.exception(f"Max retry count reached for {src} to {dst}. Skipping for now")
                    raise S3UploadMaxRetryReached("Maximum retry limit reached for S3 upload operation.")
            else:
                logging.exception(f"Error uploading file {src} to S3: {error}")

        except Exception as error:
            logging.exception(f"Error uploading file {src} to S3: {error}")

    def get_bucket_type(self, src):
        if "/texts/" in src or "/priority.texts/" in src:
            return "texts"
        elif "/images/" in src or "/priority.images/" in src:
            return "images"
        elif "/videos/" in src:
            return "videos"
        else:
            return "unknown"

    def handle_exception(self, src, dst):
        expired_key_cache_file = "expired_key_cache.json"
        with open(expired_key_cache_file, "w") as cache_file:
            json.dump(
                {
                    "access_key": self.access_key,
                    "secret_key": self.secret_key,
                    "session_token": self.session_token,
                },
                cache_file,
            )

        new_access_key, new_secret_key, new_session_token = get_credentials()
        self.update_aws_credentials(new_access_key, new_secret_key, new_session_token)

        # Retry the file upload using the updated AWS credentials
        self.upload_file(src, dst)


def move_json(json_obj):
    json_str = json.dumps(json_obj)  # Convert dictionary to JSON-formatted string
    md5_hash = hashlib.md5(json_str.encode()).hexdigest()

    if not md5_hash:
        logging.error(f"Failed to generate the content hash: {json_obj}", file=sys.stderr)
        return

    log_file_tmp = os.path.join(Config.UPLOAD_MQTT_DIR, f"transferring.activity-{os.getpid()}")
    with open(log_file_tmp, "w") as tmp_file:
        json_obj["ContentHash"] = md5_hash
        json.dump(json_obj, tmp_file)

    if os.path.getsize(log_file_tmp) == 0:
        logging.error(f"Failed to generate the JSON log: {json_obj}", file=sys.stderr)
        return

    log_file = os.path.join(Config.UPLOAD_MQTT_DIR,f"activity_{datetime.now().isoformat().replace(' ', '_')}_{md5_hash}.json",)
    try:
        os.rename(log_file_tmp, log_file)
        logging.info(f"Activity log committed, to {log_file}")
    except OSError as error:
        os.remove(log_file_tmp)
        logging.error(f"Error occurred: {error}, Failed to commit {log_file}")
        return


def activity_log(object, bucket_type, mime_type, date_time, upload_date_time):
    json_obj = {
        "Kind": "Upload",
        "Object": object,
        "BucketType": bucket_type,
        "MIME": mime_type,
        "DateTime": date_time,
        "UploadDateTime": upload_date_time
    }
    move_json(json_obj)


def access_key_request_log(date_time):
    json_obj = {
        "Kind": "Request",
        "Task": "S3AccessKeyUpdate",
        "Detail": "none",
        "DateTime": date_time
    }
    move_json(json_obj)


def get_credentials():
    # Acquire the lock to ensure exclusive access to the credentials
    credentials_lock.acquire()
    logging.info(f"Acquired the lock for the credentials")

    try:
        """Simulate waiting for 5 seconds to fetch updated credentials because shadow file update on every 5 seconds so
        credentials will be updated after every 5 seconds and this is temporary solution to fetch updated credentials
        till device registration module not completed"""
        time.sleep(10)

        # Read the updated AWS configuration file
        with open(Config.AWSIOT_SHADOW_FILE, "r") as config_file:
            config_data = json.load(config_file)
            new_access_key = config_data["state"]["desired"]["S3"]["AccessKey"]
            new_secret_key = config_data["state"]["desired"]["S3"]["SecretKey"]
            new_session_token = config_data["state"]["desired"]["S3"]["SessionToken"]

        return new_access_key, new_secret_key, new_session_token
    finally:
        # Release the lock to allow other threads to access the credentials
        credentials_lock.release()
        logging.info(f"Released the lock for the credentials")
