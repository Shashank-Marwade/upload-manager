import logging
import os
from flask import Flask, request, jsonify
import pyinotify
import threading
import signal

from data_purge_manager import DataPurger
from scripts_config import ScriptConfig as Config
from uploader import EventHandler, graceful_shutdown, watch_folder_in_thread

app = Flask(__name__)
watch_manager = pyinotify.WatchManager()
notifier = None

def start_monitoring(paths):
    global notifier
    if notifier is not None:
        notifier.stop()
    
    for path in paths:
        watch_manager.add_watch(path, pyinotify.IN_CREATE | pyinotify.IN_MODIFY)

    notifier = pyinotify.ThreadedNotifier(watch_manager, EventHandler())
    notifier.start()

@app.route('/update', methods=['POST'])
def update_paths():
    data = request.get_json()
    paths = data.get('paths')
    if not paths:
        return jsonify({'error': 'No paths provided'}), 400

    start_monitoring(paths)
    return jsonify({'message': f'Monitoring updated to paths: {paths}'}), 200

@app.route('/stop', methods=['POST'])
def stop_monitoring():
    if notifier is not None:
        notifier.stop()
    return jsonify({'message': 'Monitoring stopped'}), 200

if __name__ == "__main__":
    folders_to_watch_for_upload = [
        Config.OUT_TEXT_DIR,
        Config.OUT_IMAGE_DIR,
        Config.OUT_VIDEO_DIR,
    ]

    folders_to_watch_for_purge = [
        Config.OUT_TEXT_DIR,
        Config.OUT_IMAGE_DIR,
        Config.OUT_VIDEO_DIR,
        Config.DAIS_IMAGE_DIR,
        Config.DAIS_VIDEO_DIR,
        Config.DAIS_ARCHIVES_DIR,
        Config.DAIS_WHATSAPP_IMG_DIR,
    ]

    # Create an instance of DataPurger (outside the if block)
    data_purger = DataPurger(folders_to_watch_for_purge)

    # Create memory_thread and purge_thread outside the if block
    memory_thread = threading.Thread(target=data_purger.monitor_memory_usage, daemon=True)
    purge_thread = threading.Thread(target=data_purger.handle_data_purge, daemon=True)

    # Start memory_thread and purge_thread regardless of is_enabled
    memory_thread.start()
    purge_thread.start()

    shutdown_event = threading.Event()  # Event to signal shutdown
    threads = []

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, graceful_shutdown)

    is_enabled = bool(os.environ.get("UPLOAD_ENABLED", False))
    logging.info(f"UPLOAD_ENABLED: {is_enabled}")

    if is_enabled:
        logging.info("Starting uploader service...")

        # Watch folders in separate threads (within the if block)
        for folder in folders_to_watch_for_upload:
            thread = threading.Thread(target=watch_folder_in_thread, args=(folder, shutdown_event))
            thread.start()
            threads.append(thread)

    try:
        # Wait for uploader threads (if enabled) to complete (unchanged)
        if is_enabled:
            for thread in threads:
                thread.join()
        memory_thread.join()
        purge_thread.join()
    except KeyboardInterrupt:
        logging.info("Main thread stopped by user.")
    finally:
        logging.info("All uploader threads (if enabled) have completed. Exiting.")

    app.run(debug=True, port=5000)


