import numpy as np
import pandas as pd


def convert_to_datetime(df):
    df['Time'] = pd.to_datetime(df['Time'], format='%H:%M:%S.%f')
    custom_datetime = np.datetime64('1900-01-01T00:00:00.000000')
    time_dif = df['Time'][0] - custom_datetime
    df['Time'] = df['Time'] - time_dif
    return df


def read_temp_csv(temp_readout_path):
    # colnames = ['Date', 'Time', 'Sensor', 'Temp']
    # temp_data = pd.read_csv(temp_readout_path, names=colnames, header=None, skipinitialspace=True, encoding='ISO-8859-1')

    ### workaround for bad format
    colnames = ['Date', 'Time', 'Temp']
    temp_data = pd.read_csv(temp_readout_path, names=colnames, header=None, skipinitialspace=True,
                            encoding='ISO-8859-1')
    ##### work around for weird data with test and C
    # Use regex to extract temperatures
    temp_data['Temp'] = temp_data['Temp'].str.extract(r"th_temp = ([\d.]+)")[0]

    # convert to datetime
    temp_data = convert_to_datetime(temp_data)

    # protocol_5['Time'] = pd.to_datetime(protocol_5['Time'], format='%H:%M:%S.%f')
    # protocol_5 = convert_time(protocol_5)

    # # Define min and max values for scaling
    # min_scale = 15
    # max_scale = 45
    #
    # # Apply scaling formula to the column
    # protocol_5['FractionB_scaled'] = (protocol_5['FractionB'] - protocol_5['FractionB'].min()) / (
    #             protocol_5['FractionB'].max() - protocol_5['FractionB'].min()) * (max_scale - min_scale) + min_scale



    # Drop rows without temperatures if needed
    temp_data = temp_data.dropna(subset=['Temp']).reset_index(drop=True)

    temp_data['Temp'] = pd.to_numeric(temp_data['Temp'], errors='coerce')

    # as using four sensors take rolling mean of four !!!!!!!!!!!!!!
    # !!!!!!!!!!!!!!! IDEALLY TAKE THE TEMPS FROM THE SAME TIMEPOINT, AT THE MOMENT IT JUST TAKES THE
    # FIRST SET OF 4 ONWARDS
    temp_data = temp_data.drop(columns=['Date'])
    temp_data.Temp = temp_data.rolling(window=4).mean()

    # temp_data.set_index('timestamp').resample('4T').mean()  # Bins every 4 minutes

    # Bin every 4 rows
    temp_data_bin = temp_data.groupby(np.arange(len(temp_data)) // 4).mean()  # Replace 'mean()' with any aggregation

    return temp_data_bin
