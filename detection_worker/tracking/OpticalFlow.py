import cv2
import numpy as np
import time
import os 


# Parameters for Shi-Tomasi corner detection
feature_params = dict(maxCorners = 300, qualityLevel = 0.2, minDistance = 2, blockSize = 7)
# Parameters for Lucas-Kanade optical flow
lk_params = dict(winSize = (15,15), maxLevel = 2, criteria = (cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
# Variable for color to draw optical flow track
color = (0, 255, 0)


def trackFeatures(frames_list, original_bbox, frames_path, view, play_realtime=False):
    # initilize

    original_image = cv2.imread(frames_path + "{}_{}.jpg".format(frames_list[0],view))
    # Converts frame to grayscale because we only need the luminance channel for detecting edges - less computationally expensive
    prev_gray = cv2.cvtColor(original_image, cv2.COLOR_BGR2GRAY)

    # Sets the start of the Optical Flow trackign to the original bbox
    #n_object = 1
    #bboxs = np.empty((n_object,),dtype=np.ndarray)
    (xmin, ymin, xmax, ymax) = original_bbox 
    boxw = xmax-xmin
    boxh = ymax-ymin
    #bboxs[0] = np.array((xmin,ymin,boxw,boxh))
    mask = np.zeros_like(prev_gray)

    #for i in range(len(bboxs)):
    mask[int(ymin):int(ymin)+int(boxh), int(xmin):int(xmin)+int(boxw)] = 255

    # Finds the strongest corners in the first frame by Shi-Tomasi method - I will track the optical flow for these corners
    # https://docs.opencv.org/3.0-beta/modules/imgproc/doc/feature_detection.html#goodfeaturestotrack
    prev = cv2.goodFeaturesToTrack(prev_gray, mask = mask, **feature_params)

    # Creates an image filled with zero intensities with the same dimensions as the frame - for later drawing purposes
    mask = np.zeros_like(original_image)

    for frame_index in frames_list[1:]:
        frame_path = frames_path + "{}_{}.jpg".format(frame_index,view)
        frame = cv2.imread(frame_path)
        print('Processing optical flow frame: ',frame_index)
        try:
            print(frame.shape)
        except:
            print('*'*80)
            print('NONE shape', frame_index)
        # Converts each frame to grayscale - previously only converted the first frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        # Calculates sparse optical flow by Lucas-Kanade method
        # https://docs.opencv.org/3.0-beta/modules/video/doc/motion_analysis_and_object_tracking.html#calcopticalflowpyrlk
        next, status, error = cv2.calcOpticalFlowPyrLK(prev_gray, gray, np.float32(prev), None, **lk_params)
        # Selects good feature points for previous position
        good_old = prev[status == 1]
        # Selects good feature points for next position
        good_new = next[status == 1]
        # Updates previous frame
        prev_gray = gray.copy()
        # Updates previous good feature points
        prev = good_new.reshape(-1, 1, 2)
        # imshow if to play the result in real time

    return good_new
    
if __name__ == "__main__":
    print('in main')
    cap = cv2.VideoCapture("garbage2.mp4")
    objectTracking(cap,draw_bb=True,play_realtime=True,save_to_file=True)
    print('releasing')
    cap.release()
