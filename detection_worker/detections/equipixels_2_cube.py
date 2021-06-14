import numpy as np 

def normalized_image_coordinates(pixel_coords, width, height):
    size = max(width, height)
    p = np.empty((len(pixel_coords), 2))
    p[:, 0] = (pixel_coords[:, 0] + 0.5 - width / 2.0) / size
    p[:, 1] = (pixel_coords[:, 1] + 0.5 - height / 2.0) / size
    return p

def pixel_bearing_many(pixels, width, height):
    pixels = normalized_image_coordinates(pixels, width, height)
    """Unit vector pointing to the pixel viewing directions."""
    lon = pixels[:, 0] * 2 * np.pi
    lat = -pixels[:, 1] * 2 * np.pi
    z = -np.cos(lat) * np.sin(lon)
    y = np.sin(lat)
    x = -np.cos(lat) * np.cos(lon)
    return np.column_stack([x, y, z]).astype(float)

def equipixels_2_cube(x, y, h_equirectangular=2880, w_equirectangular=5760):
    pixels = np.hstack([x.reshape((-1, 1)), y.reshape((-1, 1))])
    bearings = pixel_bearing_many(pixels, w_equirectangular, h_equirectangular)
    max_val = np.max(np.abs(bearings))
    bearings /= float(max_val)
    return bearings