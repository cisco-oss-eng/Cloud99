import logging

# TODO this should be configurable with oslo conf
LOGGER_NAME = "cloud99"
LOG_FILE_NAME = "/tmp/cloud99.log"
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'
FORMAT_STRING = ('%(asctime)s - %(filename)s:%(lineno)d - %(levelname)s - '
                 '%(message)s')

LOGGER = logging.getLogger(LOGGER_NAME)
LOGGER.setLevel(logging.ERROR)
FORMATTER = logging.Formatter(FORMAT_STRING)

if not LOGGER.handlers:
    LOG_FILE_HANDLER = logging.FileHandler(LOG_FILE_NAME)
    LOG_FILE_HANDLER.setFormatter(FORMATTER)

    STREAM_HANDLER = logging.StreamHandler()
    STREAM_HANDLER.setFormatter(FORMATTER)

    LOGGER.addHandler(STREAM_HANDLER)
    LOGGER.addHandler(LOG_FILE_HANDLER)

logging.basicConfig(format=FORMAT_STRING, datefmt=DATE_FORMAT)
