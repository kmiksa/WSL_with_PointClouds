import logging
import sys
import json

class StackdriverFormatter(logging.Formatter):

    def __init__(self, *args, **kwargs):
        super(StackdriverFormatter, self).__init__(*args, **kwargs)

    def format(self, record):
        msg = {
            'severity': record.levelname,
            'message': record.msg,
            'name': record.name
        }
        if isinstance(msg['message'], dict):
            dct = msg['message']
            del msg['message']
            msg = dict(**msg, **dct)
        return json.dumps(msg)


def init_logger():
    log = logging.getLogger()
    sh = logging.StreamHandler(sys.stdout)
    sf = StackdriverFormatter()
    sh.setFormatter(sf)
    log.addHandler(sh)
    log.setLevel(logging.INFO)
