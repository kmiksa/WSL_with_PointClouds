import traceback 

from tracking.OpticalFlow import trackFeatures

def areFeaturesInBox(frames_list, original_bbox, compared_bbox, frames_path, view):
    (xmin,ymin,xmax,ymax) = compared_bbox
    count=0 # number of features in the box
    
    try:
        features = trackFeatures(frames_list, original_bbox, frames_path, view)
    except:
        print('exception in taking features from OpticalFLow')
        traceback.print_exc()
        return False 

    if not len(features) > 0:
        return False

    for feature in features:
        if xmin < feature[0] < xmax and ymin < feature[1] < ymax:
            count+=1 # feature is in the box 
    min_threshold = 0.9 # percent features in the box
    if count/len(features) > min_threshold:
        print('features in the box')
        return True 
    else:
        return False

