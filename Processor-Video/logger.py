# logger.py
import datetime


def log(message):
    """
    Log a message with a timestamp.
    :param message:
    :return:
    """
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')
    print(f'{timestamp} {message}')