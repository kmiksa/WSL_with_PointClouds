import os 
import shutil
import tempfile
import json
import cv2
from cv2 import VideoWriter, VideoWriter_fourcc, imread, resize

from cloud.shell import ShellCmd


def download_frame(bucket,project,trip,image,folder):
    p_trip = ShellCmd(
                    cmd=[
                        "gsutil", "-m", "-q", "cp", "-r",
                        os.path.join("gs://", bucket, project, trip, 
                                            image +  '.jpg'),
                        folder
                    ],
                    name='gsutil frames video',
                )

    p_trip.wait()


class Crop(object):
    """
    A class used to represent an Cropped Frame

    ...

    Attributes
    ----------
    start : int
         a degree at which to start cropping the image 
    stop : int
        a degree at which to stop cropping the image 
    frame : np array
        cv2 image object
    top : int 
        how much of the top to crop
    bottom : int 
        how much from the top to leave
    
    bottom is by default set to none as it is calculated based on 
    height in crop() method()

    Methods
    -------
    crop()
        Returns cropped frame 
    """

    def __init__(self,start,stop,frame,top=400,bottom=None):
        self.start = start
        self.stop = stop
        self.frame = frame
        self.top = top
        self.bottom = bottom

        self.crop()

    def crop(self):
        """Return cropped frame.

        Returns:
        ----------
        cropped_frame
        add_x, add_y values to add to get the object cords on full image. 
        """

        height, width = self.frame.shape[0], self.frame.shape[1]
        left = int(width/360 * self.start)
        right = int(width/360 * self.stop)
        if self.bottom is None:
            bottom = int(2 * height/3)
        top = self.top
        self.add_x = left
        self.add_y = right
        self.cropped_frame = self.frame[top:bottom, left:right]


class Frame:
    """General Image Class"""
    def __init__(self,bucket, project, trip, image):
        self.bucket = bucket
        self.project = project
        self.trip = trip
        self.image = image
        self.frame_number = int(self.image.split('-')[5].split('_')[0])
        self.frames = {}

    def create_image_dict(self):
        self.image_dict = dict(
            project=self.project,
            trip = self.trip,
            image = self.image,
            frame = self.frame_number)


class PerspectiveImage(Frame):   
    def __init__(self,bucket,project,trip,image,download_all=False):
        self.download_all = download_all
        super().__init__(bucket,project,trip,image)

        if self.download_all == True:
            self.load_frames() 
        else:
            self.load_frame()
        self.create_image_dict()

    def load_frames(self):
        for face in ['_F','_L','_R','_B']:
            with tempfile.TemporaryDirectory() as temp:
                download_frame(self.bucket,self.project,self.trip,self.image+face, temp)
                frame = cv2.imread(os.path.join(temp,self.image+face+'.jpg'))
                frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
                self.frames[face] = frame

    def load_frame(self):
         with tempfile.TemporaryDirectory() as temp:
            download_frame(self.bucket,self.project,self.trip,self.image, temp)
            frame = cv2.imread(os.path.join(temp,self.image + '.jpg'))
            self.frame = cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)
            face = self.image[-1]
            self.frames[face] = frame

class PanoramicImage(Frame):
    def __init__(self,bucket,project,trip,image):
        super().__init__(bucket,project,trip,image)

        self.load_frame()
        self.create_image_dict()      

    def load_frame(self):
        with tempfile.TemporaryDirectory() as temp:
            download_frame(self.bucket,self.project,self.trip,self.image, temp)
            self.frame = cv2.imread(os.path.join(temp,self.image+'.jpg'))
            self.frame = cv2.cvtColor(self.frame,cv2.COLOR_BGR2RGB)

    def generate_crops(self,view):
        count = 0
        for crop in self.crops:
            cropped_frame = Crop(crop[0],crop[1],self.frame)
            view = view + str(count)
            self.frames[view] = cropped_frame


class LeftRightPanoramicImage(PanoramicImage):
    def __init__(self,bucket,project,trip,image,crops=[[0,180],[180,360]]):
        self.crops = crops 
        super().__init__(bucket,project,trip,image)

        self.generate_crops(view='LRP-')

class LeftRightDiagonalPanoramicImage(PanoramicImage):
    def __init__(self,bucket,project,trip,image,crops=[[90,180],[180,270]]):
        self.crops = crops 
        super().__init__(bucket,project,trip,image)

        self.generate_crops(view='LRDP-')
    

if __name__ == "__main__":
    print('main')
    bucket = 'gecko-frames'
    project = 'hasselt'
    trip = 'Trip-gopro2-2020-06-07-09-33-28'
    image = 'Trip-11-45-06-8800-697_F'
    '''
    Crops = LeftRightDiagonalPanoramicImage(bucket,project,trip,image)
    for face, frame in Crops.frames.items():
        print(frame.cropped_frame)
        cv2.imshow('frame',frame.cropped_frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    '''
    Perspective = PerspectiveImage(bucket,project,trip,image,download_all=False)
    for face, frame in Perspective.frames.items():
        cv2.imshow('frame',frame)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
    #for key,value in Perspective.frames.items():
    #    print(key,value)



