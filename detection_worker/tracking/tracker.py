import json 
import pandas as pd
import time
import math 
import threading
from pympler import asizeof

import logging
import traceback
import base64

from tracking.Sort import sort_tracker
from tracking.areFeaturesInBox import areFeaturesInBox

from google.cloud import bigquery
from google.cloud import pubsub

publisher = pubsub.PublisherClient()
PROJECT = 'continual-grin-207218'
error_topic = 'projects/{}/topics/{}'.format(PROJECT, 'errors')


def convert_size(size_bytes):
   if size_bytes == 0:
       return "0B"
   size_name = ("B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB")
   i = int(math.floor(math.log(size_bytes, 1024)))
   p = math.pow(1024, i)
   s = round(size_bytes / p, 2)
   return "%s %s" % (s, size_name[i])

def generate_row(table, item):
    row = []
    for field in table.schema:
        row.append(item.get(field.name))
    return row

class Tracker(object):

    def __init__ (self, dets, sort_threshold=0, do_opticalFlow=False, panoramic=False):
        '''
            Merges tracks from Sort algorithm. 
            Argument:
                dets - detections list.
                frames_path - path to frames with name of project, trip and video. 
                sort_threshold - minimum number of objects in track. 
            Returns: 
                tracks_df_sort - pandas df with sort tracked objects. 
                tracks_df - pandas df with sort tracks connected with optical flow. 
        '''
    
        self.dets = dets
        self.sort_threshold = sort_threshold
        self.do_opticalFlow = do_opticalFlow
        self.panoramic = panoramic
        self._pubsub_wait = None 
        self._pubsub_ack = None

    def track_sort(self):
        tracks_df_sort = sort_tracker(self.dets, self.sort_threshold, self.panoramic)

        for index, row in tracks_df_sort.iterrows():
            tracks_df_sort['names'][index] = json.dumps(tracks_df_sort['names'][index])

        tracks_df_sort['object_id'] = 0
        for ind ,(frame, group) in enumerate(tracks_df_sort.groupby('frame')):
            count=0
            for index, row in group.iterrows():
                tracks_df_sort['object_id'][index] = count
                count+=1
        print(tracks_df_sort)
        return tracks_df_sort

    
    def track_opticalFlow(self):

        #TODO self.frames_path,dete dict is now df. 
        tracks_df = tracks_df_sort.copy() # doing it to return both sort and sort+optical flow and save them in bigquerry. 

        track_ids = sorted(tracks_df.track_id.unique())
        view = self.dets[0]['view']
        # function loops through the objects_df grouped by track_id, 
        # takes last frame from track1(t1) and compares it with the first frame from track2(t2)
        # if tracks t1 and t2 can be merged it changes track_id value from objects_df from t2 to t1
        print(track_ids)
        for original_idx, original_trackid in enumerate(track_ids):
            original_track = tracks_df[tracks_df.track_id == original_trackid]
            original_frame = original_track.iloc[-1].frame
            #take compared track - t2
            for compared_trackid in track_ids[original_idx:]:
                compared_track = tracks_df[tracks_df.track_id == compared_trackid]
                compared_frame = compared_track.iloc[0].frame
                # compares first frame from t1 with last frame from t2 and checks if t2 started 
                # after t1 end.
                print('opticalflow frames compared: ',original_frame, compared_frame)
                if compared_frame < original_frame: 
                    continue                
                if compared_frame - original_frame > 30:
                    print('breaked cause the distance is too big')
                    break
                # takes bounding boxes to be used for Optical Flow 
                original_bbox = original_track[original_track.frame == original_frame].loc[:, ['x1', 'y1', 'x2', 'y2']].values[0]
                compared_bbox = compared_track[compared_track.frame == compared_frame].loc[:, ['x1', 'y1', 'x2', 'y2']].values[0]
                #So some frames are not in the database, therefore:
                frames_list = tracks_df['frame'][tracks_df['frame'] <= compared_frame].unique()
                frames_list = frames_list[frames_list >=  original_frame]
                #check if features from t1 object are tracked to t2 bbox with optical flow.
                if areFeaturesInBox(frames_list,original_bbox,compared_bbox,self.frames_path,view) == True:
                    # changes t2.track_id to t1.track_id
                    tracks_df.track_id = tracks_df.track_id.replace(compared_trackid, original_trackid)
                    # deletes t2 value from track_ids
                    track_ids.remove(compared_trackid)
                    print(track_ids)
                    # t1 last frame value is updated to be t2 last frame 
                    original_track = tracks_df[tracks_df.track_id == original_trackid]
                    original_frame = original_track.iloc[-1].frame

