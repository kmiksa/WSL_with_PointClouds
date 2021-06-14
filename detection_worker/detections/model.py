import os

from google.cloud import storage

# Instantiates a client
storage_client = storage.Client()

from mrcnn import model as modellib
from mrcnn.objects_configs import hasselt_ts

PATH_TO_WEIGHTS ='/tmp/weights.h5'
MODELS_BUCKET = storage_client.get_bucket('gecko-models')

class Model(object):

    def __init__(self,weights,gpu=True):
        self.weights = weights
        self.models_bucket = MODELS_BUCKET
        self.gpu = gpu

        self.prepare_model()
        
    def download_model(self):

        if os.path.exists(PATH_TO_WEIGHTS):
            return True

        weights_blob = self.models_bucket.blob(self.weights + '.h5')
        with open(PATH_TO_WEIGHTS, 'wb') as file_obj:
            weights_blob.download_to_file(file_obj)

    def config_model(self):

        batch_size = 1

        self.config = hasselt_ts.TSConfig()

        class InferenceConfig(self.config.__class__):
            # Run detection on one image at a time
            GPU_COUNT = 1
            IMAGES_PER_GPU = 1

        self.config = InferenceConfig()
        self.config.display()

        if self.gpu == True:
            self.model = modellib.MaskRCNN(
                mode='inference', model_dir=PATH_TO_WEIGHTS, config=self.config)

        else:
            DEVICE = "/cpu:0" # default is GPU but for testing purposes on mac i changed to cpu.
            
            with tf.device(DEVICE):
                model = modellib.MaskRCNN(
                    mode='inference', model_dir=PATH_TO_WEIGHTS, config=config)

        print("Loading weights", PATH_TO_WEIGHTS)
        self.model.load_weights(PATH_TO_WEIGHTS, by_name=True)
    
    def prepare_model(self):

        self.download_model()
        self.config_model()
