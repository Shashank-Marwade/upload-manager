import logging
import os
import threading
import time
import zipfile
import pyinotify

from scripts_config import ScriptConfig as Config
from mv_file import MoveFile

mv_service = MoveFile()
shutdown_event = threading.Event()


class EventHandler(pyinotify.ProcessEvent):
    def __init__(self, folder_path):
        super().__init__()
        self.processed_files = set()
        self.folder_path = folder_path
        self.processing_files = set()

    def get_missed_files(self):
        # Check if there is any missed files
        logging.info("Checking for missed files...")
        missed_files = []
        current_time = time.time()

        for filename in os.listdir(self.folder_path):
            file_path = os.path.join(self.folder_path, filename)
            file_creation_time = os.path.getctime(file_path)
            if current_time - file_creation_time >= Config.MIN_PROCESS_INTERVAL:
                missed_files.append(file_path)

        return missed_files

    def process_missed_files(self):
        # Upload all missed file if not then return normally
        logging.info("Processing missed files...")
        missed_files = self.get_missed_files()

        if len(missed_files) == 0:
            return

        for file_path in missed_files:
            filename = file_path.split("/")[-1].split(".")[0]
            dst = os.path.basename(file_path)
            _, file_extension = os.path.splitext(file_path)
            file_extension = file_extension.lower()
            if any(file_extension.endswith(ext) for ext in (".log", ".json")):
                zipped_file_path = self.zip_file(file_path, filename)
                self.retry_upload_and_cleanup(zipped_file_path, dst)
                os.remove(file_path)
                logging.info(f"Original log file removed: {file_path}")
            else:
                self.retry_upload_and_cleanup(file_path, dst)
                logging.info(f"Original file removed {file_path}")
                self.processed_files.add(file_path)
                logging.info("Missed files processed successfully")

    def wait_for_completion(self):
        # Wait for ongoing file uploads to complete before returning
        while self.processing_files:
            time.sleep(1)

    def retry_upload_and_cleanup(self, file_path, dst):
        max_retries = 3
        retry_delay = 1
        for _ in range(max_retries):
            try:
                mv_service.upload_file(file_path, dst)
                if os.path.exists(file_path):
                    os.remove(file_path)
                logging.info(f"File removed: {file_path}")
                break  # Break out of the retry loop on success
            except Exception as e:
                logging.warning(f"Upload failed: {e}. Retrying after {retry_delay} seconds.")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff

    def zip_file(self, file_path, filename):
        zip_file_path = file_path.split(".")[0] + ".tgz"
        with zipfile.ZipFile(zip_file_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
            zip_file.write(file_path, os.path.join("pack", os.path.basename(file_path)))
        return zip_file_path

    def process_default(self, event):
        # Process all events for files that are not in the processed_files set.
        # These events are handled by process_moved_to and process_created respectively.
        try:
            if event.mask & pyinotify.IN_MOVED_TO or event.mask & pyinotify.IN_CREATE:
                self.process_missed_files()
                src = event.pathname
                if src in self.processed_files or src in self.processing_files:
                    return

                self.processing_files.add(src)  # Add current file to processing list
                if os.path.exists(src) and os.path.isfile(src):
                    logging.info(f"Event received for file: {src}")
                    filename = src.split("/")[-1].split(".")[0]
                    _, file_extension = os.path.splitext(src)
                    file_extension = file_extension.lower()

                    is_log_file = any(file_extension.endswith(ext) for ext in (".log", ".json"))
                    dst = os.path.basename(src)

                    try:
                        if is_log_file:
                            zipped_file_path = self.zip_file(src, filename)
                            self.retry_upload_and_cleanup(zipped_file_path, dst)
                        else:
                            self.retry_upload_and_cleanup(src, dst)
                        if os.path.exists(src):
                            os.remove(src)

                    finally:
                        self.processing_files.remove(src)  # Remove current processed file from processing list
                        logging.info("Event processed successfully")

        except Exception as e:
            logging.exception(f"Failed to process event: {e}")


def watch_folder_in_thread(folder_path, shutdown_event):
    wm = pyinotify.WatchManager()
    mask = pyinotify.IN_MOVED_TO | pyinotify.IN_CREATE
    handler = EventHandler(folder_path)
    notifier = pyinotify.Notifier(wm, handler)
    wm.add_watch(folder_path, mask, rec=True)
    logging.info(f"Monitoring started for folder: {folder_path}")

    try:
        while not shutdown_event.is_set():
            notifier.process_events()
            if notifier.check_events(timeout=1):
                notifier.read_events()

        # Wait for ongoing file uploads to complete before exiting
        handler.wait_for_completion()

    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user.")
    finally:
        notifier.stop()
        logging.info(f"Monitoring stopped for folder: {folder_path}")

def graceful_shutdown(_, __):
    logging.info("Received termination signal. Initiating graceful shutdown.")
    shutdown_event.set()
