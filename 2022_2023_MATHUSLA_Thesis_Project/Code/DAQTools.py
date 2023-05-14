# ----------------------------------------------------------------------------- #
# Import statements 

import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import scipy.optimize as opt

# ----------------------------------------------------------------------------- #

# Fitting a Gaussian curve to the signals of interest
def gauss(p,x):
    A = p[0]
    mu = p[1]
    sigma = p[2]

    return A*np.exp(-0.5*(x-mu)**2/sigma**2)

# ----------------------------------------------------------------------------- #

def getCoarseFineColumns(df,channels):
    """
    Get the column names for the specified channels. Channel names should be given as CH_X_X
    Column names in entries go in the order: Coarse, Fine, Hit 
    """
    entries = {}
    coarse_basename = 'COARSE_{}'
    fine_basename = 'FINE_{}'
    hit_basename = 'HIT_{}'

    channel_names = []
    for ch in channels:
        if ch not in entries:
            ch_num = ch[3:]
            entries[ch] = [coarse_basename.format(ch_num),fine_basename.format(ch_num),hit_basename.format(ch_num)]
            channel_names.append(ch)

    return entries, channel_names

# ----------------------------------------------------------------------------- #

# def getEntries(df, noise_reject_rate=0.01):

#     entries = {}
#     coarse0_basename = 'COARSE_0_{}'
#     fine0_basename = 'FINE_0_{}'
#     hit0_basename = 'HIT_0_{}'
#     coarse1_basename = 'COARSE_1_{}'
#     fine1_basename = 'FINE_1_{}'
#     hit1_basename = 'HIT_1_{}'
#     key0_name = 'CH_0_{}'
#     key1_name = 'CH_1_{}'

#     channel_names = []
    
#     for i in range(32):
#         ch_hits = df[hit0_basename.format(i)].fillna(0).to_numpy().sum()
#         if ch_hits > noise_reject_rate*len(df):
#             entries[key0_name.format(i)] = [coarse0_basename.format(i),fine0_basename.format(i),hit0_basename.format(i)]
#             channel_names.append(key0_name.format(i))

#         ch_hits = df[hit1_basename.format(i)].fillna(0).to_numpy().sum()
#         if ch_hits > noise_reject_rate*len(df):
#             entries[key1_name.format(i)] = [coarse1_basename.format(i),fine1_basename.format(i),hit1_basename.format(i)]
#             channel_names.append(key1_name.format(i))

#     return entries, channel_names

def getEntries(df, noise_reject_rate=0.01):
    """
    Get the channels that were triggered on real interaction events
    Column names in entries go in the order: Coarse, Fine, Hit 
    """
    entries = {}
    coarse_basename = 'COARSE_{}'
    fine_basename = 'FINE_{}'
    hit_basename = 'HIT_{}'
    key_name = 'CH_{}'

    channel_names = []

    all_channels = []
    for col in df.columns:
        if 'HIT' in col:
            all_channels.append(col)
    
    for i in range(len(all_channels)):
        if df[all_channels[i]].isnull().sum() > 0:
            continue
        ch_hits = df[all_channels[i]].fillna(0).to_numpy().sum()
        if ch_hits > noise_reject_rate*df.shape[0]:
            ch_num = all_channels[i][4:]
            entries[key_name.format(ch_num)] = [coarse_basename.format(ch_num),fine_basename.format(ch_num),
                                                hit_basename.format(ch_num)]
            channel_names.append(key_name.format(ch_num))

    return entries, channel_names

# ----------------------------------------------------------------------------- #

def Sturge(N):
    return 1+3.322*np.log(N)

# ----------------------------------------------------------------------------- #

def getTOF(channels, df, noise_reject_rate=0.01):

    """
    Get time of flight between two channels. This means that channels should be an input with two array elements.
    Implicitly, assume that the faster channel is first in the array and the slower channel is second in the array.
    """
    if channels == []:
        entries, channel_names = getEntries(df, noise_reject_rate)
        print(channel_names)
    else:
        entries, channel_names = getCoarseFineColumns(channels)
        print(channel_names)

    # From triggered channels, remove rows that have hit equal to 0
    for ch in channel_names:
        df[entries[ch][2]].fillna(0,inplace=True)
        df = df.drop(df[df[entries[ch][2]] == 0].index)

    # Find the channel that triggers first
    min_sum = np.inf
    trigger_ch = None

    for ch in channel_names:
        if df[entries[ch][0]].sum() + df[entries[ch][1]].sum() < min_sum:
            min_sum = df[entries[ch][0]].sum() + df[entries[ch][1]].sum()
            trigger_ch = ch
    
    if trigger_ch == None:
        print('No trigger channel detected. Using the first of the hit channels')
        trigger_ch = channel_names[0]

    print(trigger_ch)
    # Get ToF of all other channels relative to the trigger channel
    tof_dict = {}
    for n in range(len(channel_names)):
        if channel_names[n] == trigger_ch:
            continue

        # Columns are: HIT_CH1, HIT_CH2, COARSE_CH1, FINE_CH1, COARSE_CH2, FINE_CH2
        df_filter = df[[entries[trigger_ch][2],entries[channel_names[n]][2],
                        entries[trigger_ch][0],entries[trigger_ch][1],
                        entries[channel_names[n]][0],entries[channel_names[n]][1]]]

        np_filter = df_filter.to_numpy()
        # print(np_filter)
        np_filter = np.delete(np_filter,np.where(np_filter[:,0]==0),axis=0)
        np_filter = np.delete(np_filter,np.where(np_filter[:,0]==np.nan),axis=0)
        np_filter = np.delete(np_filter,np.where(np_filter[:,1]==0),axis=0)
        np_filter = np.delete(np_filter,np.where(np_filter[:,1]==np.nan),axis=0)
        
        # print(np_filter)
        min_fine_0 = np_filter[:,3].min()
        max_fine_0 = np_filter[:,3].max()
        min_fine_1 = np_filter[:,5].min()
        max_fine_1 = np_filter[:,5].max()

        # fine_CH = df[[entries[channels[0]][2],entries[channels[0]][1]]].to_numpy()
        # fine_CH = np.delete(fine_CH,np.where(fine_CH[:,0]==0),axis=0)
        # min_fine_0 = np.min(fine_CH[:,1])

        # fine_CH = df[[entries[channels[1]][2],entries[channels[1]][1]]].to_numpy()
        # fine_CH = np.delete(fine_CH,np.where(fine_CH[:,0]==0),axis=0)
        # min_fine_1 = np.min(fine_CH[:,1])

        # max_fine_0 = np.max(df[entries[channels[0]][1]])
        # max_fine_1 = np.max(df[entries[channels[1]][1]])

        alfa_0 = 25/(max_fine_0-min_fine_0)           # In ns per step
        alfa_1 = 25/(max_fine_1-min_fine_1)           # In ns per step

        # print(alfa_0,alfa_1)

        # fine_0 = df[entries[channels[0]][1]].to_numpy()

        fine_0 = np_filter[:,3]
        fine_0 = (fine_0-min_fine_0)*alfa_0

        # fine_1 = df[entries[channels[1]][1]].to_numpy()

        fine_1 = np_filter[:,5]
        fine_1 = (fine_1-min_fine_1)*alfa_1 

        # coarse_0 = df[entries[channels[0]][0]].to_numpy()
        # coarse_1 = df[entries[channels[1]][0]].to_numpy()

        coarse_0 = np_filter[:,2]
        coarse_1 = np_filter[:,4]

        tof = ((coarse_1)*25-fine_1) - ((coarse_0)*25-fine_0)

        tof_dict['{} - {}'.format(channel_names[n],trigger_ch)] = tof
    
    return tof_dict