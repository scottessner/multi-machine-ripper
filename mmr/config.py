# Configuration dictionary
import logging

Config = {
    'ROOT_PATH': '/app',
    'PORT_NUMBER': 1900,
    'CONVENTION_LEADER': '192.168.40.10',
    'WATCH_FOLDERS': ['/data/incoming'],
}

class actorLogFilter(logging.Filter):
    def filter(self, logrecord):
        return 'actorAddress' in logrecord.__dict__


class coordinatorLogFilter(logging.Filter):
    def filter(self, logrecord):
        module = logrecord.__dict__.get('module', None)
        return module == 'coordinator'


class notActorLogFilter(logging.Filter):
    def filter(self, logrecord):
        return 'actorAddress' not in logrecord.__dict__

LogConfig = {'version': 1,
             'formatters': {'normal': {'format': '%(asctime)s %(levelname)-8s %(message)s',
                                       'datefmt': '%m/%d/%Y %I:%M:%S %p'},
                            'actor': {'format': '%(asctime)s %(levelname)-8s %(actorAddress)s => %(message)s',
                                      'datefmt': '%m/%d/%Y %I:%M:%S %p'}
                            },
             'filters': {'isActorLog': {'()': actorLogFilter},
                         'notActorLog': {'()': notActorLogFilter},
                         'coordinatorLog': {'()': coordinatorLogFilter}
                         },
             'handlers': {'h1': {'class': 'logging.FileHandler',
                                 'filename': '/log/mmr.log',
                                 'formatter': 'normal',
                                 'filters': ['notActorLog'],
                                 'level': logging.INFO},
                          'h2': {'class': 'logging.FileHandler',
                                 'filename': '/log/mmr.log',
                                 'formatter': 'actor',
                                 'filters': ['isActorLog'],
                                 'level': logging.DEBUG},
                          'h3': {'class': 'logging.FileHandler',
                                 'filename': '/log/coordinator.log',
                                 'formatter': 'actor',
                                 'filters': ['coordinatorLog'],
                                 'level': logging.DEBUG},
                          },
             'loggers': {'': {'handlers': ['h1', 'h2', 'h3'], 'level': logging.DEBUG}}
             }
