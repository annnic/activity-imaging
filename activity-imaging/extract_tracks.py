"""
Use threshold and masking to extract mean of red and green channels
"""

import numpy as np
from skimage.measure import label, regionprops_table, regionprops
from skimage import io
import matplotlib.pyplot as plt
import cv2
import napari
import tifffile
import xml.etree.ElementTree as ET

from read_temp import read_temp_csv


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
file_path = '/Users/annikanichols/Desktop/AN20241111a_83-31_FLP-RG_head_play.ome.tiff'
temp_readout_path ='/Users/annikanichols/Desktop/2024-11-11_17-32-27_temperature_data_AN20241111a_83-31_FLP-RG_head_play.csv'
# file_path = '/Users/annikanichols/Desktop/AN20241111a_83-31_FLP-RG_head.ome.tiff'

temp_data = read_temp_csv(temp_readout_path)

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

fig, axes = plt.subplots(4, 1)
axes[0].plot(green_mean, label="GCaMP")
axes[1].plot(red_mean, label="RFP", color="r")
axes[2].plot(gr_ratio, label="Ratio", color="k")
axes[3].plot(temp_data.Time, temp_data.Temp, label="Temp", color="k")




viewer = napari.view_image(red_stack)
viewer.add_image(masks)


# Load OME-TIFF file
with tifffile.TiffFile(file_path) as tif:
    # Extract OME-XML metadata
    ome_metadata = tif.ome_metadata

    # Parse XML to find timestamps
    root = ET.fromstring(ome_metadata)
    # OME-Namespace (needed for proper XML parsing)
    namespace = {'ome': 'http://www.openmicroscopy.org/Schemas/OME/2016-06'}


    Dt = []
    # Extract timestamps from each frame (if available)
    for t in root.findall(".//ome:Plane", namespace):
        if 'DeltaT' in t.attrib:  # Check if timestamp exists
            Dt.append(float(t.attrib['DeltaT']))  # Time in seconds


    acquisition_date = root.find(".//ome:Image/ome:AcquisitionDate", namespace)
    if acquisition_date is not None:
        acquisition_time = acquisition_date.text  # Format: 'YYYY-MM-DDTHH:MM:SS'
        print(f"Acquisition Date: {acquisition_time}")
    else:
        print("Acquisition Date not found")

    # # Extract absolute timestamps for each frame
    # timestamps = []
    # for plane in root.findall(".//ome:Plane", namespace):
    #     if 'Timestamp' in plane.attrib:  # Absolute time per frame
    #         timestamps.append(float(plane.attrib['Timestamp']))  # Might be in UNIX format

