import os
import random
import sys
import tensorflow as tf
import numpy as np
import tempfile

from training.config import ObjectConfig, ObjectDataset
from mrcnn import utils
import mrcnn.model as modellib
from mrcnn.model import log

class _InfConfig(ObjectConfig):
    IMAGES_PER_GPU = 1
    GPU_COUNT = 1
    DETECTION_MIN_CONFIDENCE = 0.9

class Trainer():
    def __init__(self,data,coco_path,data_path,model_dir):
        self.data = data
        self.cooc_path = coco_path + '/mask_rcnn_coco.h5'
        self.data_path = data_path
        self.model_dir = model_dir
        self.config = ObjectConfig()

        self.config.display()
        self.train()

    def train(self):
        # Training dataset
        dataset_train = ObjectDataset()
        dataset_train.load_object(self.data_path, "train")
        dataset_train.prepare()

        # Validation dataset
        dataset_val = ObjectDataset()
        dataset_val.load_object(self.data_path, "val")
        dataset_val.prepare()

        ################### Constructing the model #################

        # Create model in training mode
        model_train = modellib.MaskRCNN(mode="training", config=self.config,
                                        model_dir=self.model_dir)


        ################### Preparing mAP Callback #################


        model_inference = modellib.MaskRCNN(mode="inference", config=_InfConfig(), model_dir=self.model_dir)
        mean_average_precision_callback = modellib.MeanAveragePrecisionCallback(model_train, model_inference, dataset_val, 1,
                                                                                verbose=1)

        ################### Training #################

        # Which weights to start with?
        model_train.load_weights(self.cooc_path, by_name=True,
                                exclude=["mrcnn_class_logits", "mrcnn_bbox_fc",
                                        "mrcnn_bbox", "mrcnn_mask"])

        model_train.train(dataset_train, dataset_val,
                        learning_rate=self.config.LEARNING_RATE,
                        epochs=self.data['epochs'],
                        layers=self.data['layers'],
                        custom_callbacks=[mean_average_precision_callback])
