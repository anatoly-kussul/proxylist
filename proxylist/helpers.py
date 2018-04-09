import asyncio
import logging.config
from functools import wraps

import time


def setup_logging(verbose=False):
    logging.config.dictConfig({
        'version': 1,
        'formatters': {
            'colored': {
                '()': 'colorlog.ColoredFormatter',
                'format': '%(log_color)s%(asctime)s - %(levelname)s - %(filename)s:%(lineno)s - %(message)s',
            },
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'formatter': 'colored',
                'stream': 'ext://sys.stdout',
            },
        },
        'loggers': {
            '': {
                'level': 'DEBUG' if verbose else 'INFO',
                'propagate': True,
                'handlers': ['console'],
            },
            'aiohttp': {
                'level': 'WARNING',
            },
        },
    })


def run_coro_in_background(coro, name=None, loop=None):
    """
    Run coroutine in background while still handling all exceptions
    :param coro: coroutine object
    :param name: task name used in start/stop logging
    :param loop
    """
    def done_callback(fut):
        if not fut.cancelled():
            e = fut.exception()
            if e:
                logging.critical('Uncaught exception {!r} in \'{}\' coroutine'.format(e, name), exc_info=e)

    if not name:
        name = coro.__name__
    if loop is None:
        logging.warning('Loop for {!r} not specified.'.format(name))
    future = asyncio.ensure_future(coro, loop=loop)
    future.add_done_callback(done_callback)
    return future


def periodic(period=0):
    def wrapper(func):
        @wraps(func)
        async def wrapped(*args, **kwargs):
            while True:
                time_start = time.time()
                await func(*args, **kwargs)
                duration = time.time() - time_start
                time_to_sleep = max(period - duration, 0)
                if period and not time_to_sleep:
                    logging.warning(
                        f'Coro \'{func.__name__}\' can`t keep up with given period.'
                        f' (Period: {period}, Duration: {duration})'
                    )
                await asyncio.sleep(time_to_sleep)
        return wrapped
    return wrapper
