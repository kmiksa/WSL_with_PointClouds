import logging 
import time 
import threading
import traceback

from tracking.tracker import Tracker
from cloud import bq_utils

class TrackingnWorker(object):
    def __init__(self, data, logger,bq_client,sort_table, opticalFlow_table=None):
        self.data = data
        self.logger = logger
        self.bq_client = bq_client
        self.sort_table = sort_table
        self.opticalFlow_table = opticalFlow_table
        self._pubsub_wait = None 
        self._pubsub_ack = None

    def configure_pubsub(self, pubsub_wait, pubsub_ack):
        self._pubsub_wait = pubsub_wait
        self._pubsub_ack = pubsub_ack

    def log(self, level, message, location, **kwargs):
        dct = dict(
            message=message, location=location
        )

        for key,val in kwargs.items():
            dct[key] = val

        self.logger.log(level, dct)

    def wait(self):
       while self.running:
            if self._pubsub_wait is not None:
                self.log(logging.INFO, message='moving pubsub ack...', location='tracking_worker')
                self._pubsub_wait()
            time.sleep(30)

    def start(self):
        self.running = True
        threading.Thread(target=self.wait, args=()).start()

    def stop(self):
        self.running = False

    def process(self):
        try:
            self.start()
            self.log(logging.INFO, message='processing track', location='tracker')
            if self.data['data_format'] == 'image_list':
                detections = bq_utils.querry_frames(self.data, self.bq_client)
            if self.data['data_format'] == 'video':
                detections = bq_utils.querry_video(self.data, self.bq_client)
            tracker = Tracker(detections)
            tracks = tracker.track_sort().to_dict('records')
            bq_utils.push_to_bigquery(tracks, self.bq_client, self.sort_table)
            self.stop()
            if self._pubsub_ack is not None:
                self.log(logging.INFO, message="pubsub ack", location='detections')
                self._pubsub_ack()
            else:
                print('*'*80)
                print('pubsub ack is None!!!')
        except:
            self.stop()
            self.log(logging.ERROR, message=traceback.format_exc(), location='handle_message')
            if self._pubsub_ack is not None:
                self.log(logging.INFO, message="pubsub ack", location='detections')
                self._pubsub_ack()
            else:
                print('*'*80)
                print('pubsub ack is NONE!!!')