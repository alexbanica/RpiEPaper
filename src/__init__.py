#!/usr/bin/python
# -*- coding:utf-8 -*-

import logging
from logging.handlers import TimedRotatingFileHandler
from ServerStatusContext import ServerStatusContext
from ServerStatus import ServerStatus
from ePaperRenderer import cleanup_epaper


def setup_logging():
    file_handler = TimedRotatingFileHandler(
        '/var/log/server_status.log',
        when='midnight',
        interval=1,
        backupCount=5
    )
    console_handler = logging.StreamHandler()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] [%(threadName)s]: %(message)s",
        handlers=[file_handler, console_handler]
    )

if __name__ == "__main__":
    setup_logging()
    ServerStatusContext.parse_arguments()
    try:
        ServerStatus().start()
    except Exception as e:
        logging.error(f"Error starting server status: {e}")
        cleanup_epaper()