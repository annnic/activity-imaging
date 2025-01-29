"""
Use threshold and masking to extract mean of red and green channels
"""

import numpy as np
from skimage.measure import label, regionprops_table, regionprops
from skimage import io
import matplotlib.pyplot as plt
import cv2

import napari


def thresh_mask(idx):
    # threshold image
    _, binary_image = cv2.threshold(red_stack[idx], 3000, 65536, cv2.THRESH_BINARY)

    # Label connected components
    labeled_image = label(binary_image)

    # Get properties of all objects
    regions = regionprops(labeled_image)

    # Find the largest object
    largest_region = max(regions, key=lambda r: r.area)

    # Create an empty mask for the largest region
    largest_region_mask = np.zeros_like(labeled_image)

    # Assign the label of the largest region to the new mask
    largest_region_mask[labeled_image == largest_region.label] = 1

    # # Get bounding box coordinates (min_row, min_col, max_row, max_col)
    # bbox = largest_region.bbox
    return largest_region_mask

# load the image and segment it
# file_path = '/Users/annikanichols/Desktop/AN20241111a_83-31_FLP-RG_head_play.ome.tiff'
file_path = '/Users/annikanichols/Desktop/AN20241111a_83-31_FLP-RG_head.ome.tiff'

stack = io.imread(file_path)
red_stack = stack[0, ...]
green_stack = stack[1, ...]
NUM_IMAGES = red_stack.shape[0]

masks = np.stack([thresh_mask(idx) for idx in range(NUM_IMAGES)])

red_mean = np.zeros(NUM_IMAGES)
green_mean = np.zeros(NUM_IMAGES)

for i in np.arange(0, NUM_IMAGES):
    red_mean[i] = np.mean(red_stack[i, ]*masks[i])
    green_mean[i] = np.mean(green_stack[i, ]*masks[i])

gr_ratio = green_mean/red_mean

plt.plot(green_mean, c='g')
plt.plot(red_mean, c='r')
plt.plot(gr_ratio, c='k')
plt.show()

viewer = napari.view_image(red_stack)
viewer.add_image(masks)
