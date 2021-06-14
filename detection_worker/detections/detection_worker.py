import logging 
import time 
import threading
import traceback

from detections.images import PerspectiveImage, PanoramicImage, LeftRightPanoramicImage
from detections.detector import Detector
from cloud import bq_utils

class DetectionWorker(object):
    def __init__(self, data, logger,bq_client,detections_table):
        self.data = data
        self.logger = logger
        self.bq_client = bq_client
        self.detections_table = detections_table
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
                self.log(logging.INFO, message='moving pubsub ack...', location='video_worker')
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
            self.log(logging.INFO, message='processing image', location='detector')
            image = PerspectiveImage(
                    bucket=self.data['bucket'],
                    project=self.data['project'],
                    trip=self.data['trip'],
                    image = self.data['image'],
                    download_all=False)
            detector = Detector(
                    image = image,
                    run=self.data['run'],
                    class_names=self.data['class_names'],
                    version=self.data['version'],
                    logger=self.logger,
                    panoramic=False)
            rows_to_insert = detector.process_frame(simple_polygons=False)
            bq_utils.push_to_bigquery(rows_to_insert, self.bq_client, self.detections_table)
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