from flask import Flask, request, jsonify
import threading
import os
import signal
import logging
import boto3
from data_purge_manager import DataPurger
from uploader import watch_folder_in_thread
import configparser

app = Flask(__name__)
upload_folders = []
purge_folders = []

data_purger = None
memory_thread = None
purge_thread = None
upload_threads = []
shutdown_event = threading.Event()

def graceful_shutdown(signum, frame):
    shutdown_event.set()
    app.logger.info("Gracefully shutting down from SIGINT (Ctrl-C)")

@app.route('/list_directories', methods=['GET'])
def list_directories():
    path = request.args.get('path', '/data')
    if not os.path.exists(path):
        return jsonify({"error": "Path does not exist"}), 404

    try:
        directories = [dirs for dirs in os.listdir(path) if os.path.isdir(os.path.join(path, dirs))]
        return jsonify(directories)
    except PermissionError as e:
        return jsonify({"error": f"Permission error: {str(e)}"}), 403
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/update_folders', methods=['POST'])
def update_folders():
    global upload_folders, purge_folders
    data = request.get_json()
    upload_folders = data.get('upload_folders', [])
    purge_folders = data.get('purge_folders', [])

    # Restart all monitoring based on new folders
    restart_monitoring()
    return jsonify({"message": "Folders updated successfully"}), 200


def read_aws_credentials(config_file_path="/root/.aws/credentials"):

    try:
        config = configparser.ConfigParser()
        config.read(config_file_path)

        if config.has_section('default'):
            credentials = {
                'aws_access_key_id': config['default'].get('aws_access_key_id'),
                'aws_secret_access_key': config['default'].get('aws_secret_access_key'),
                'region_name': config['default'].get('region_name'),
            }
            return credentials
        else:
            logging.warning(f"Error: 'default' section not found in {config_file_path}")
            return None

    except (configparser.Error, FileNotFoundError) as e:
        logging.error(f"Error reading credentials from {config_file_path}: {e}")
        return None

@app.route('/list_s3_objects', methods=['GET'])
def list_s3_objects():

    try:
        # List objects using ListObjectsV2 for pagination
        paginator = s3.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=os.environ.get('BUCKET_NAME'))

        # Collect object information from all pages
        all_objects = []
        for page in pages:
            if 'Contents' in page:
                all_objects.extend(page['Contents'])

        # Return list of object details (customize as needed)
        object_data = [{'Key': obj['Key'], 'LastModified': obj['LastModified']} for obj in all_objects]
        return jsonify(object_data)

    except Exception as e:
        # Catch general exceptions
        return jsonify({'error': str(e)}), 500

def restart_monitoring():
    global data_purger, memory_thread, purge_thread, upload_threads, shutdown_event
    shutdown_event.set()  # Signal existing threads to stop

    # Restart purger with new folders
    data_purger = DataPurger(purge_folders)
    memory_thread = threading.Thread(target=data_purger.monitor_memory_usage, daemon=True)
    purge_thread = threading.Thread(target=data_purger.handle_data_purge, daemon=True)
    memory_thread.start()
    purge_thread.start()

    # Restart uploader threads if enabled
    is_enabled = bool(os.environ.get("UPLOAD_ENABLED", False))
    if is_enabled:
        logging.info("Starting uploader service with dynamic folders...")
        for thread in upload_threads:
            if thread.is_alive():
                thread.join()  # Ensure old threads are finished
        upload_threads = [threading.Thread(target=watch_folder_in_thread, args=(folder, shutdown_event)) for folder in upload_folders]
        for thread in upload_threads:
            thread.start()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    signal.signal(signal.SIGINT, graceful_shutdown)
    logging.info(f"UPLOAD_ENABLED: {bool(os.environ.get('UPLOAD_ENABLED', False))}")

    credentials = read_aws_credentials()
    if credentials:
        s3 = boto3.client('s3',
                        aws_access_key_id=credentials['aws_access_key_id'],
                        aws_secret_access_key=credentials['aws_secret_access_key'],
                        region_name=credentials['region_name'])
    else:
        logging.error("Failed to read credentials. Exiting.")

    app.run(debug=True, port=5000)