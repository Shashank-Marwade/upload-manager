import os
import psutil
import threading
import logging
from datetime import datetime, timedelta
from queue import Queue
from scripts_config import ScriptConfig as Config
import time

class DataPurger:
    def __init__(self, src_dirs):
        self.src_dirs = src_dirs
        self.memory_queue = Queue()
        self.last_check_time = datetime.now()

    def purge_old_archived_files(self, directory, days=Config.ARCHIVE_PURGE_INTERVAL):
        current_time = time.time()  # Get current time in seconds

        # Calculate the threshold time (30 days ago)
        threshold_time = current_time - (days * 24 * 60 * 60)

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_mtime = os.path.getmtime(file_path)

                if file_mtime < threshold_time:
                    logging.info(f"Purging old archived file: {file_path}")
                    os.remove(file_path)

    def purge_data(self, dir_path):
        try:
            logging.info(f"Purging data in {dir_path}")
            current_time = datetime.now()
            files = os.listdir(dir_path)
            files.sort(key=lambda x: os.path.getmtime(os.path.join(dir_path, x)))
            logging.info(f"Files to delete: {files}")

            for file_name in files:
                file_path = os.path.join(dir_path, file_name)
                file_modified_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if current_time - file_modified_time > timedelta(days=Config.PURGE_INTERVAL):
                    os.remove(file_path)
                    logging.info(f"Deleted file: {file_path}")

                    # Check memory usage after deleting each file
                    memory_percent = psutil.virtual_memory().percent
                    if memory_percent < Config.PURGE_RESUME_PERCENTAGE:
                        logging.info("Memory usage below threshold. Resuming monitoring.")
                        return
        except Exception as e:
            logging.error(f"Error purging data in {dir_path}: {e}")

    def purge_all_folders(self):
        try:
            threads = []
            for dir in self.src_dirs:
                logging.info("Creating the purge threads for each folder")
                thread = threading.Thread(target=self.purge_data, args=(dir,))
                threads.append(thread)
                thread.start()
            for thread in threads:
                thread.join()
        except Exception as e:
            logging.error(f"Error purging data in all folders: {e}")

    def monitor_memory_usage(self):
        try:
            while True:
                memory_percent = psutil.virtual_memory().percent
                if memory_percent > Config.PURGE_THRESHOLD_PERCENTAGE:
                    self.memory_queue.put(True)
                    logging.info("Memory threshold exceeded. Triggering data purge.")
                else:
                    self.memory_queue.put(False)
                time.sleep(Config.MEMORY_CHECK_INTERVAL)
        except Exception as e:
            logging.error(f"Error monitoring memory: {e}")

    def handle_data_purge(self):
        try:
            while True:
                if self.memory_queue.get():
                    """purges data from data/out/video data/out/image data/out/text"""
                    logging.info("Triggering data purge.")
                    self.purge_all_folders()
        except Exception as e:
            logging.error(f"Error handling data purge: {e}")
