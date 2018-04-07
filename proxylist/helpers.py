import logging.config


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
            # 'aiohttp': {
            #     'level': 'WARNING',
            # },
        },
    })
