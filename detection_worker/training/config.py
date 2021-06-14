import os
import sys
import json
import datetime
import numpy as np
import skimage.draw

from mrcnn.config import Config
from mrcnn import model as modellib, utils

############################################################
#  Configurations
############################################################


class ObjectConfig(Config):
    """Configuration for training on the object  dataset.
    Derives from the base Config class and overrides some values.
    """
    # Give the configuration a recognizable name
    NAME = "Config_1"

    # We use a GPU with 12GB memory, which can fit two images.
    # Adjust down if you use a smaller GPU.
    IMAGES_PER_GPU = 1
    
    GPU_COUNT = 1
    
    # Number of classes (including background)
    NUM_CLASSES = 1 + 1  # Background + ts

    # Number of training steps per epoch
    STEPS_PER_EPOCH = 100

    # Skip detections with < 90% confidence
    DETECTION_MIN_CONFIDENCE = 0.9

    IMAGE_MIN_DIM = 832
    
    IMAGE_MAX_DIM = 832
    
    LEARNING_RATE = 0.003

############################################################
#  Dataset
############################################################

class ObjectDataset(utils.Dataset):

    def load_object(self, dataset_dir, subset):
        """Load a subset of the object dataset.
        dataset_dir: Root directory of the dataset.
        subset: Subset to load: train or val
        """
        # Add classes. We have only one class to add.
        self.add_class("ts", 1, "ts")

        # Train or validation dataset?
        assert subset in ["train", "val"]
        dataset_dir = os.path.join(dataset_dir, subset)

        # Add images
        
        for a in os.listdir(dataset_dir):
            if a.endswith('.json'):
                with open(dataset_dir + '/' + a, 'r') as f:
                    labels = json.load(f)
                    polygons=[]
                    for label in labels['Label']['traffic-sign']:
                        polygon = {}
                        polygon['all_points_y'] = label['all_y']
                        polygon['all_points_x'] = label['all_x']
                        polygon['name'] = 'polygon'
                        polygon['class'] = 'traffic sign'
                        polygons.append(polygon)
                    # load_mask() needs the image size to convert polygons to masks.
                    image_path = os.path.join(dataset_dir, labels['image_name'])
                    image = skimage.io.imread(image_path)
                    height, width = image.shape[:2]
                    self.add_image(
                        "ts",
                        image_id=labels['image_name'],
                        path=image_path,
                        width=width, height=height,
                        polygons=polygons)

    def load_mask(self, image_id):
        """Generate instance masks for an image.
       Returns:
        masks: A bool array of shape [height, width, instance count] with
            one mask per instance.
        class_ids: a 1D array of class IDs of the instance masks.
        """
        # If not a balloon dataset image, delegate to parent class.
        background = ['',' ', None, 'BG']
        image_info = self.image_info[image_id]
        #print('image_info: ')
        #print(image_info)
        if image_info["source"] != "ts":
            return super(self.__class__, self).load_mask(image_id)

        # Convert polygons to a bitmap mask of shape
        # [height, width, instance_count]
        info = self.image_info[image_id]
        #print('info: ')
        #print(info)
        mask = np.zeros([info["height"], info["width"], len(info["polygons"])],
                        dtype=np.uint8)
        classes = [a['class'] if a not in background else 'background' for a in info['polygons']]
        for index, class_name  in enumerate(classes):
            if class_name == 'traffic sign':
                classes[index] = 1
            elif class_name == 'background':
                 classes[index] = 0
                
        
        classes = np.array(classes, dtype = np.int32)
        if 0 in classes:
            print(classes)
        #print(info["polygons"])
        count_masks = 0
        for i, p in enumerate(info["polygons"]):
            count_masks += 1
            # Get indexes of pixels inside the polygon and set them to 1
            rr, cc = skimage.draw.polygon(p['all_points_y'], p['all_points_x'])
            mask[rr, cc, i] = 1
        print('masks:' + str(count_masks))

        # Return mask, and array of class IDs of each instance.
        return mask.astype(np.bool), classes

    def image_reference(self, image_id):
        """Return the path of the image."""
        info = self.image_info[image_id]
        if info["source"] == "ts":
            return info["path"]
        else:
            super(self.__class__, self).image_reference(image_id)



