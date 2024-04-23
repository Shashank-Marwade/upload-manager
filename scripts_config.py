import os


class ScriptConfig:

    UPLOAD_DIR = "/data/out"
    print(f"ENV_UPLOAD_DIR: {UPLOAD_DIR}")

    OUT_TEXT_DIR = "/data/out/texts"
    print(f"ENV_UPLOAD_TEXT_DIR: {OUT_TEXT_DIR}")

    OUT_IMAGE_DIR = "/data/out/images"
    print(f"ENV_UPLOAD_IMAGE_DIR: {OUT_IMAGE_DIR}")

    OUT_VIDEO_DIR = "/data/out/videos"
    print(f"ENV_UPLOAD_VIDEO_DIR: {OUT_VIDEO_DIR}")

    ARCHIVE_DIR = "/data/out/archive"
    print(f"ENV_ARCHIVE_DIR: {ARCHIVE_DIR}")

    DAIS_IMAGE_DIR = "/data/dais/alerts/images"
    print(f"DAIS_IMAGE_DIR: {DAIS_IMAGE_DIR}")

    DAIS_VIDEO_DIR = "/data/dais/alerts/videos"
    print(f"DAIS_VIDEO_DIR: {DAIS_VIDEO_DIR}")

    DAIS_ARCHIVES_DIR = "/data/dais/archives"
    print(f"DAIS_ARCHIVES_DIR: {DAIS_ARCHIVES_DIR}")

    DAIS_WHATSAPP_IMG_DIR = "/data/dais/whatsapp_images"
    print(f"DAIS_WHATSAPP_IMG_DIR: {DAIS_WHATSAPP_IMG_DIR}")

    UPLOAD_ACTIVITY_LOGS = "/data/logs"
    print(f"UPLOAD_ACTIVITY_LOGS: {UPLOAD_ACTIVITY_LOGS}")

    SHADOW_FILE = "/data/config.json"
    print(f"ENV_SHADOW_FILE: {SHADOW_FILE}")

    UPLOADER_TMP_DIR = "/tmp"
    print(f"UPLOADER_TMP_DIR: {UPLOADER_TMP_DIR}")

    BUCKET_NAME = os.environ.get("BUCKET_NAME", "my-upload-mgr-bucket")
    print(f"BUCKET_NAME: {BUCKET_NAME}")

    MIN_PROCESS_INTERVAL = int(os.environ.get("MIN_PROCESS_INTERVAL", 60))  # Seconds ~1 Min
    print(f"MIN_PROCESS_INTERVAL: {MIN_PROCESS_INTERVAL}")

    MEMORY_CHECK_INTERVAL = int(os.environ.get("MEMORY_CHECK_INTERVAL", 300))  # Seconds ~5 Min
    print(f"MEMORY_CHECK_INTERVAL: {MEMORY_CHECK_INTERVAL}")

    PURGE_THRESHOLD_PERCENTAGE = float(os.environ.get("PURGE_THRESHOLD_PERCENTAGE", 90))  # Percentage
    print(f"PURGE_THRESHOLD_PERCENTAGE: {PURGE_THRESHOLD_PERCENTAGE}")

    PURGE_INTERVAL = int(os.environ.get("PURGE_INTERVAL", 300))  # Seconds ~5 Min
    print(f"PURGE_INTERVAL: {PURGE_INTERVAL}")

    PURGE_RESUME_PERCENTAGE = float(os.environ.get("PURGE_RESUME_PERCENTAGE", 85))  # Percentage
    print(f"PURGE_RESUME_PERCENTAGE: {PURGE_RESUME_PERCENTAGE}")

    PURGE_CHECK_INTERVAL = 3  # Seconds
    print(f"PURGE_CHECK_INTERVAL: {PURGE_CHECK_INTERVAL}")

    ARCHIVE_PURGE_INTERVAL = int(os.environ.get("ARCHIVE_EXPIRE_DAYS", 30))  # in days
    print(f"ARCHIVE_PURGE_INTERVAL: {ARCHIVE_PURGE_INTERVAL}")
