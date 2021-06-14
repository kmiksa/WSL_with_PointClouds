from __future__ import print_function

import numpy as np 
np.set_printoptions(suppress=True)

from numba import jit
import os.path
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from skimage import io
from sklearn.utils.linear_assignment_ import linear_assignment
import glob
import time
import argparse
import pandas as pd
from filterpy.kalman import KalmanFilter

@jit
def iou(bb_test,bb_gt):
  """
  Computes IUO between two bboxes in the form [x1,y1,x2,y2]
  """
  xx1 = np.maximum(bb_test[0], bb_gt[0])
  yy1 = np.maximum(bb_test[1], bb_gt[1])
  xx2 = np.minimum(bb_test[2], bb_gt[2])
  yy2 = np.minimum(bb_test[3], bb_gt[3])
  w = np.maximum(0., xx2 - xx1)
  h = np.maximum(0., yy2 - yy1)
  wh = w * h
  o = wh / ((bb_test[2]-bb_test[0])*(bb_test[3]-bb_test[1])
    + (bb_gt[2]-bb_gt[0])*(bb_gt[3]-bb_gt[1]) - wh)
  return(o)

def convert_bbox_to_z(bbox):
  """
  Takes a bounding box in the form [x1,y1,x2,y2] and returns z in the form
    [x,y,s,r] where x,y is the centre of the box and s is the scale/area and r is
    the aspect ratio
  """
  w = bbox[2]-bbox[0]
  h = bbox[3]-bbox[1]
  x = bbox[0]+w/2.
  y = bbox[1]+h/2.
  s = w*h    #scale is just area
  r = w/float(h)
  return np.array([x,y,s,r]).reshape((4,1))

def convert_x_to_bbox(x,score=None):
  """
  Takes a bounding box in the centre form [x,y,s,r] and returns it in the form
    [x1,y1,x2,y2] where x1,y1 is the top left and x2,y2 is the bottom right
  """
  w = np.sqrt(x[2]*x[3])
  h = x[2]/w
  if(score==None):
    return np.array([x[0]-w/2.,x[1]-h/2.,x[0]+w/2.,x[1]+h/2.]).reshape((1,4))
  else:
    return np.array([x[0]-w/2.,x[1]-h/2.,x[0]+w/2.,x[1]+h/2.,score]).reshape((1,5))


class KalmanBoxTracker(object):
  """
  This class represents the internel state of individual tracked objects observed as bbox.
  """
  count = 0
  def __init__(self,bbox):
    """
    Initialises a tracker using initial bounding box.
    """
    #define constant velocity model
    self.kf = KalmanFilter(dim_x=7, dim_z=4)
    self.kf.F = np.array([[1,0,0,0,1,0,0],[0,1,0,0,0,1,0],[0,0,1,0,0,0,1],[0,0,0,1,0,0,0],  [0,0,0,0,1,0,0],[0,0,0,0,0,1,0],[0,0,0,0,0,0,1]])
    self.kf.H = np.array([[1,0,0,0,0,0,0],[0,1,0,0,0,0,0],[0,0,1,0,0,0,0],[0,0,0,1,0,0,0]])

    self.kf.R[2:,2:] *= 10.
    self.kf.P[4:,4:] *= 1000. #give high uncertainty to the unobservable initial velocities
    self.kf.P *= 10.
    self.kf.Q[-1,-1] *= 0.01
    self.kf.Q[4:,4:] *= 0.01

    self.kf.x[:4] = convert_bbox_to_z(bbox)
    self.time_since_update = 0
    self.id = KalmanBoxTracker.count
    KalmanBoxTracker.count += 1
    self.history = []
    self.hits = 0
    self.hit_streak = 0
    self.age = 0
    self.names = [bbox[-1]]
    self.score = bbox[4]
    self.max_score = bbox[4]

  def update(self,bbox):
    """
    Updates the state vector with observed bbox.
    """
    self.time_since_update = 0
    self.history = []
    self.hits += 1
    self.hit_streak += 1
    self.names.append(bbox[-1])
    self.kf.update(convert_bbox_to_z(bbox))
    self.max_score = max(self.max_score, bbox[4])
    self.score = bbox[4]

  def predict(self):
    """
    Advances the state vector and returns the predicted bounding box estimate.
    """
    if((self.kf.x[6]+self.kf.x[2])<=0):
      self.kf.x[6] *= 0.0
    self.kf.predict()
    self.age += 1
    if(self.time_since_update>0):
      self.hit_streak = 0
    self.time_since_update += 1
    self.history.append(convert_x_to_bbox(self.kf.x))
    return self.history[-1]

  def get_state(self):
    """
    Returns the current bounding box estimate.
    """
    return convert_x_to_bbox(self.kf.x)

def associate_detections_to_trackers(detections,trackers,iou_threshold = 0.3):
  """
  Assigns detections to tracked object (both represented as bounding boxes)
  Returns 3 lists of matches, unmatched_detections and unmatched_trackers
  """
  if(len(trackers)==0):
    return np.empty((0,2),dtype=int), np.arange(len(detections)), np.empty((0,5),dtype=int)
  iou_matrix = np.zeros((len(detections),len(trackers)),dtype=np.float32)

  for d,det in enumerate(detections):
    for t,trk in enumerate(trackers):
      iou_matrix[d,t] = iou(det[:5].astype(np.float64), trk)
  matched_indices = linear_assignment(-iou_matrix)

  unmatched_detections = []
  for d,det in enumerate(detections):
    if(d not in matched_indices[:,0]):
      unmatched_detections.append(d)
  unmatched_trackers = []
  for t,trk in enumerate(trackers):
    if(t not in matched_indices[:,1]):
      unmatched_trackers.append(t)

  #filter out matched with low IOU
  matches = []
  for m in matched_indices:
    if(iou_matrix[m[0],m[1]]<iou_threshold):
      unmatched_detections.append(m[0])
      unmatched_trackers.append(m[1])
    else:
      matches.append(m.reshape(1,2))
  if(len(matches)==0):
    matches = np.empty((0,2),dtype=int)
  else:
    matches = np.concatenate(matches,axis=0)

  return matches, np.array(unmatched_detections), np.array(unmatched_trackers)



class Sort(object):
  def __init__(self,max_age=1,min_hits=0):
    """
    Sets key parameters for SORT
    """
    self.max_age = max_age
    self.min_hits = min_hits
    self.trackers = []
    self.frame_count = 0

  def update(self,dets):
    """
    Params:
      dets - a numpy array of detections in the format [[x1,y1,x2,y2,score],[x1,y1,x2,y2,score],...]
    Requires: this method must be called once for each frame even with empty detections.
    Returns the a similar array, where the last column is the object ID.
    NOTE: The number of objects returned may differ from the number of detections provided.
    """
    self.frame_count += 1
    #if self.frame_count % 100 == 0:
        #print(self.frame_count)
    #get predicted locations from existing trackers.
    trks = np.zeros((len(self.trackers),5))
    to_del = []
    ret = []
    for t,trk in enumerate(trks):
      pos = self.trackers[t].predict()[0]
      trk[:] = [pos[0], pos[1], pos[2], pos[3], 0]
      if(np.any(np.isnan(pos))):
        to_del.append(t)
    trks = np.ma.compress_rows(np.ma.masked_invalid(trks))
    for t in reversed(to_del):
      self.trackers.pop(t)
    matched, unmatched_dets, unmatched_trks = associate_detections_to_trackers(dets,trks)

    #update matched trackers with assigned detections
    for t,trk in enumerate(self.trackers):
      if(t not in unmatched_trks):
        d = matched[np.where(matched[:,1]==t)[0],0]
        trk.update(dets[d,:][0])

    #create and initialise new trackers for unmatched detections
    for i in unmatched_dets:
        trk = KalmanBoxTracker(dets[i,:]) 
        self.trackers.append(trk)
    i = len(self.trackers)
    for trk in reversed(self.trackers):
        d = trk.get_state()[0]

        if((trk.time_since_update < 1) and (trk.hit_streak >= self.min_hits)):
          ret.append(np.concatenate((d,[trk.id+1, trk.score, trk.names])).reshape(1,-1)) # +1 as MOT benchmark requires positive
        i -= 1
        #remove dead tracklet
        if(trk.time_since_update > self.max_age):
          self.trackers.pop(i)
    if(len(ret)>0):
#       print('ret:',ret)
      return np.concatenate(ret)
    return np.empty((0,5))
    
def sort_tracker(df_detections,threshold=0,panoramic=False,**kwargs):
    #df_detections = pd.DataFrame(data=detections)
    if panoramic:
      left_add_x = kwargs['left_add_x']
      left_add_y = kwargs['left_add_y']
      right_add_x = kwargs['right_add_x']
      right_add_y = kwargs['right_add_y']
      print(df_detections)
      if kwargs['panoramic_face'] == '_L':
        df_detections = df_detections.sub(left_add_x,'x1')
        df_detections = df_detections.sub(left_add_x, 'x2')
        df_detections = df_detections.sub(left_add_y,'y1')
        df_detections = df_detections.sub(left_add_y,'y2')
      else:
        df_detections = df_detections.sub(right_add_x,'x1')
        df_detections = df_detections.sub(right_add_x,'x2')
        df_detections = df_detections.sub(right_add_y,'y1')
        df_detections = df_detections.sub(right_add_y,'y2')

    print('detections data frame: ', df_detections['view'])
    df = df_detections.groupby(['project','trip','video'])
    print(df)
    rows = []
    mot_tracker = Sort() #create instance of the SORT tracker
    for (project, trip, video), group in df:
        max_frame = group.frame.max()
        for frame in range(max_frame + 1):
            dets = group[group.frame == frame].loc[:, ['x1', 'y1', 'x2', 'y2', 'score', 'name']].values            
            trackers = mot_tracker.update(dets)    
            for track in trackers:
                x1, y1, x2, y2, track_id, score, names = track
                #print('names:  ', names)
                row = {'project': project,'trip': trip, 'video': video,'frame': frame,
                    'names': names, 'x1': x1,'y1': y1,'x2': x2,'y2': y2, 'score': score,
                    'track_id': track_id, 'view' : df_detections['view'].iloc[0]}
                rows.append(row)
    obj_df = pd.DataFrame(rows)
    if panoramic:
      if kwargs['panoramic_face'] == '_L':
        df = df.add('x1', left_add_x)
        df = df.add('x2', left_add_x)
        df = df.add('y1', left_add_y)
        df = df.add('y2', left_add_y)
      else:
        df = df.add('x1', right_add_x)
        df = df.add('x2', right_add_x)
        df = df.add('y1', right_add_y)
        df = df.add('y2', right_add_y)

    obj_df['len'] = obj_df['names'].str.len()
    obj_df = obj_df[obj_df['len'] > threshold]
    #print(obj_df)
    return obj_df

if __name__ == '__main__':
  dets = 'something'
  d=sort_tracker(dets)