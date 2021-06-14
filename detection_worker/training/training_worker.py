import os 
import logging 
import time 
import threading
import traceback
import tempfile
import shutil

from training.trainer import Trainer
from cloud import bq_utils
from cloud.shell import ShellCmd

IN_COCO_PATH = '/tmp/coco_weights'
IN_DATA_PATH = '/tmp/data'
IN_MODEL_PATH = '/tmp/model_logs'

def create_folders(folder_list):
    for folder in folder_list:
        if not os.path.exists(folder):
            os.makedirs(folder)
        else:
            shutil.rmtree(folder)
            os.makedirs(folder)

def download_coco_weights(folder):
    p_trip = ShellCmd(
                    cmd=[
                        "gsutil", "-m", "-q", "cp", "-r",
                        "gs://gecko-models/mask_rcnn_coco.h5",
                        folder
                    ],
                    name='gsutil frames video',
                )

    p_trip.wait()

def download_dataset(dataset,folder):
    p_trip = ShellCmd(
                    cmd=[
                        "gsutil", "-m", "-q", "cp", "-r",
                        os.path.join("gs://gecko-datasets/",dataset + '/*'),
                        folder
                    ],
                    name='gsutil frames video',
                )

    p_trip.wait()

def upload_model_weights(folder):
    p_trip = ShellCmd(
                    cmd=[
                        "gsutil", "-m", "-q", "cp", "-r",
                        folder,
                        "gs://gecko-frames/upload_test"
                    ],
                    name='gsutil frames video',
                )

    p_trip.wait()


class TrainingWorker(object):
    def __init__(self, data, logger):
        self.data = data
        self.logger = logger

    def log(self, level, message, location, **kwargs):
        dct = dict(
            message=message, location=location
        )

        for key,val in kwargs.items():
            dct[key] = val

        self.logger.log(level, dct)

    def process(self):
        try:
            self.log(logging.INFO, message='processing data', location='trainer')
            create_folders([IN_COCO_PATH,IN_DATA_PATH,IN_MODEL_PATH])
            download_coco_weights(IN_COCO_PATH)
            download_dataset(self.data['dataset_path'],IN_DATA_PATH)
            trainer = Trainer(self.data,IN_COCO_PATH,IN_DATA_PATH,IN_MODEL_PATH)
            upload_model_weights(IN_MODEL_PATH)

        except:
            self.log(logging.ERROR, message=traceback.format_exc(), location='handle_message')
