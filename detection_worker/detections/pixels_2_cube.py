from scipy.spatial.transform import Rotation
import numpy as np

IMAGE_SIZE = 1440   


face_coords= dict(
    F=np.array([(-1,1,1), (-1,1,-1), (-1,-1,-1), (-1,-1,1)]),
    R=np.array([(1,1,-1), (-1,1,-1), (-1,-1,-1), (1,-1,-1)]),
    B=np.array([(1,1,1), (1,1,-1), (1,-1,-1), (1,-1,1)]),
    L=np.array([(-1,1,1), (1,1,1), (1,-1,1), (-1,-1,1)]),
    U=np.array([(-1,1,1), (-1,1,-1), (1,1,-1), (1,1,1)]),
    D=np.array([(-1,-1,1), (-1,-1,-1), (1,-1,-1), (1,-1,1)]),
)

face_normals = dict()
for name, coords in face_coords.items():
    face_normals[name] = np.mean(coords, axis=0)


rotations = dict(
    F=Rotation.from_euler('y', 0, degrees=True).as_matrix(),
    B=Rotation.from_euler('y', 180, degrees=True).as_matrix(),
    L=Rotation.from_euler('y', -90, degrees=True).as_matrix(),
    R=Rotation.from_euler('y', 90, degrees=True).as_matrix(),
    U=Rotation.from_euler('z', 90, degrees=True).as_matrix(),
    D=Rotation.from_euler('z', -90, degrees=True).as_matrix(),
)


def pixels_2_cube(faces, x, y):
        
    coords = np.empty((len(x), 3))
    
    coords[:, 2] = x
    coords[:, 1] = y
    
    coords[:, 1:] -= IMAGE_SIZE /2
    coords[:, 1:] /= -IMAGE_SIZE /2
    
    coords[:, 0] = -1
        
    
    for idx, face in enumerate(faces):
        face_normal = face_normals[face]

        R = rotations[face]

        coords[idx] = R.T.dot(coords[idx])
    
    return coords