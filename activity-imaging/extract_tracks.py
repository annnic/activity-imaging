"""
Use threshold and masking to extract mean of red and green channels
"""
import os

import napari
import pandas as pd
import numpy as np
from skimage.measure import label, regionprops_table, regionprops
from skimage import io
from skimage import data
import matplotlib.pyplot as plt
import cv2
import tifffile
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta

from read_temp import read_temp_csv


def thresh_mask(idx, red_stack, threshold=2500):
    # threshold image
    _, binary_image = cv2.threshold(red_stack[idx], threshold, 65536, cv2.THRESH_BINARY)

    # Label connected components
    labeled_image = label(binary_image)

    # Get properties of all objects
    regions = regionprops(labeled_image)

    if regions: #### NEED TO FIX!!!!
        # Find the largest object
        largest_region = max(regions, key=lambda r: r.area)

        # Create an empty mask for the largest region
        largest_region_mask = np.zeros_like(labeled_image)

        # Assign the label of the largest region to the new mask
        largest_region_mask[labeled_image == largest_region.label] = 1

    else:
        largest_region_mask = labeled_image

    return largest_region_mask


# load the image and segment it
file_path = '/Users/annikanichols/Desktop/AN20241111a_83-31_FLP-RG_head_play.ome.tiff'
temp_readout_path ='/Users/annikanichols/Desktop/2024-11-11_17-32-27_temperature_data_AN20241111a_83-31_FLP-RG_head_play.csv'
# file_path = '/Users/annikanichols/Desktop/AN20241111a_83-31_FLP-RG_head.ome.tiff'

file_path = '/Users/annikanichols/Desktop/AN20250213/AN20250213a_83-31_1DOA_protocol6.ome.tiff'
temp_readout_path ='/Users/annikanichols/Desktop/AN20250213/2025-02-13_17-29-29_temperature_data.csv'

temp_data, temp_data_bin = read_temp_csv(temp_readout_path)

stack = io.imread(file_path)
red_stack = stack[0, ...]
green_stack = stack[1, ...]
NUM_IMAGES = red_stack.shape[0]

masks = []
for idx in range(NUM_IMAGES):
    masks.append(thresh_mask(idx, red_stack, 2500))
masks = np.stack(masks)

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

subsplot_n = 3
fig, axes = plt.subplots(subsplot_n, 1)
axes[0].plot(green_mean, color="g", label="GCaMP")
axes[1].plot(red_mean, label="RFP", color="r")
axes[2].plot(gr_ratio, label="Ratio", color="k")
for axis in np.arange(subsplot_n):
    axes[axis].legend()
    axes[axis].set_xlim([0, 190])
# axes[3].plot(temp_data.Time, temp_data.Temp, label="Temp", color="k")
plt.savefig(os.path.join(os.path.split(file_path)[0], "{}_G_R_ratio.png".format(os.path.split(file_path)[1])))

plt.plot(temp_data_bin.Temp, c='k')
plt.show()




viewer = napari.view_image(red_stack)
viewer.add_image(green_stack)
viewer.add_image(masks)

# viewer, image_layer = napari.imshow(data.astronaut(), rgb=True)

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

# Truncate to microseconds (6 decimal places) and remove 'Z'
acq_time_fixed = acquisition_time[:-2]  # Remove last '9Z'
# if '.' in acq_time_fixed:
#     acq_time_fixed = acq_time_fixed[:acq_time_fixed.index('.') + 7]  # Keep only first 6 digits after '.'

start_time = datetime.strptime(acq_time_fixed, "%Y-%m-%dT%H:%M:%S.%f")

# Create datetime array by adding timedelta(seconds=Dt[i]) to start_time
datetime_array = np.array([start_time + timedelta(seconds=dt) for dt in Dt])
ts_array = datetime_array[::2]  # Take every second element
ts = pd.to_datetime(ts_array)
first_date = ts[0].date()


# Replace the date in temp_data_bin.Time with first_date
temp_data_bin["ts"] = temp_data_bin["Time"].apply(lambda t: pd.Timestamp.combine(first_date, t.time()))

