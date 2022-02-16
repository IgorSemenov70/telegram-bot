dict_config = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'base': {
            'format': '%(levelname)s | %(name)s | %(funcName)s | %(asctime)s | %(lineno)d | %(message)s',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'DEBUG',
            'formatter': 'base',
        },
    },
    'loggers': {
        'main': {
            'level': 'DEBUG',
            'handlers': ['console'],
        },
    },
    'root': {
        'level': 'DEBUG',
        'handlers': [],
    }
}
