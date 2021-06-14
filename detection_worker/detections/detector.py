import numpy as np 
import json
from imantics import Polygons, Mask
from shapely.geometry import Polygon
import logging

from cloud.shell import ShellCmd
from cloud.pubsub_logging import init_logger
from google.cloud import pubsub

from detections.model import Model
from detections.pixels_2_cube import pixels_2_cube
from detections.equipixels_2_cube import equipixels_2_cube

publisher = pubsub.PublisherClient()
PROJECT = 'continual-grin-207218'
error_topic = 'projects/{}/topics/{}'.format(PROJECT, 'errors')

init_logger()
log = logging.getLogger()

WEIGHTS = 'mask_rcnn_hasselt_ts_1_0185'

def poly_area(x,y):
    return 0.5*np.abs(np.dot(x,np.roll(y,1))-np.dot(y,np.roll(x,1)))

def simplify_polygons(self, x_points, y_points):
    polygon = Polygon(zip(x_points,y_points)).simplify(10)
    new_points = polygon.exterior.coords
    x_points_new = []
    y_points_new = []
    for point in new_points:
        x_points_new.append(point[0])
        y_points_new.append(point[1])

    return x_points_new, y_points_new

model = Model(WEIGHTS).model

class Detector(object):

    def __init__(self, image, run, version, class_names, logger, panoramic=False):
        self.image = image
        self.run = run
        self.version = version
        self.class_names = class_names
        self.logger = logger
        self.panoramic = panoramic

    def read_detection(self,results,k,panoramic=False):
        x1,x2,y1,y2 = results['rois'][k]
        x1,x2,y1,y2 = (int(x1), int(x2), int(y1), int(y2))                     
        class_id = results['class_ids'][k]
        score = results['scores'][k]
        mask =  results['masks'][:, :, k] 
        polygons = Mask(mask).polygons().points[0]
        x_points = polygons[:, 0].tolist()
        y_points = polygons[:, 1].tolist()
        return dict(
            name = self.class_names[class_id],
            object_id = k,
            x1 = x1, x2 = x2, y1 = y1, y2 = y2, 
            x_points_2d_original = json.dumps(x_points), 
            y_points_2d_original = json.dumps(y_points),  
            score=float(results['scores'][k]),
            weights=WEIGHTS,
            version=self.version,
            run=self.run
            )
    
    def xyz_points(self,x_points,y_points,panoramic,face):
        if panoramic:
            cube_coords = equipixels_2_cube(np.array(x_points),np.array(y_points))
        else:
            cube_coords = pixels_2_cube([face]*len(x_points),x_points,y_points)
        return dict(
            x_points = json.dumps(cube_coords[:, 0].tolist()),
            y_points = json.dumps(cube_coords[:, 1].tolist()),
            z_points = json.dumps(cube_coords[:, 2].tolist()),
        )

    def process_frame(self, panoramic=False, simple_polygons=False):
        rows_to_insert = []
        for face, frame in self.image.frames.items():
            if panoramic == True:
                frame, add_x, add_y = frame.cropped_frame, frame.add_x, frame.add_y
            results = model.detect([frame], verbose=0)[0]
            print('Predicted frame:')
            for k in range(len(results['scores'])):
                detection_dict = self.read_detection(results,k)
                x_points, y_points = eval(detection_dict['x_points_2d_original']), eval(detection_dict['y_points_2d_original'])
                if simple_polygons:
                    x_points_new, y_points_new = simplify_polygons(x_points, y_points) 
                    rows_to_insert.append({**self.xyz_points(x_points_new,y_points_new,panoramic,face), **detection_dict, 
                                            **self.image.image_dict, **dict(
                                                                            x_points_2d_simplified = json.dumps(x_points_new),
                                                                            y_points_2d_simplified = json.dumps(y_points_new),
                                                                            view = face)})
                else:
                    rows_to_insert.append({**self.xyz_points(x_points,y_points,panoramic,face), 
                                            **detection_dict, **self.image.image_dict, **dict(view = face)})                    
        return rows_to_insert


