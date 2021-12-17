#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug  6 17:24:42 2021

@author: Lea
"""

from Preprocessing import Preprocessor
import numpy as np
import os
import mne 
import numpy as np 
import pickle
import pyxdf


# path = "/mnt/data/analysis_INTENSE/data_dicts"
# subjects =  ["AmWo", "AuWi", "BuUl", "EiHe", "FuMa", "GeKl", "GrMa", "GuWi", "HeIn", "KaBe", "MaPe", "MaSy", "MeRu", "PlKa", "PoHe", "SaCe", "SoFa", "WiLu", "ZaRo"]
# path_list = []
# files_list = []
# for subject in subjects:
#     subject_path = os.path.join(path, subject)
#     for file in os.listdir(subject_path):
#         if file.endswith(".pickle"):
#             file_path = os.path.join(subject_path, file)
#             path_list.append(file_path)
#             files_list.append(file)
            
            
# #for i in range(17, len(path_list)):
    
# index = 8 # run again for 0 and 3
# # cut epo2s
# print(index)
# p = Preprocessor()
# print("Loading the data...")
# data = p.load_data_dict(path_list[index])
# data["time_series"] = p.filter_data(data["time_series"], data["fs"])
# print("Cutting the epochs...")
# epochs = p.cut_epochs(data)
# print("Epochs have shape: " + str(epochs.shape))
# epochs = epochs.reshape(epochs.shape[0], epochs.shape[2], epochs.shape[1])
# epochs_stacked = epochs.reshape(epochs.shape[1], epochs.shape[0]*epochs.shape[2])
  
# #create MNE object
# n_channels = 64
# sampling_freq = data["fs"]  
# channel_names = list(data["channel_info"][0,:])
# info = mne.create_info(channel_names, sfreq=sampling_freq)
# raw_data = data["time_series"].T
# raw = mne.io.RawArray(raw_data, info)
# #mne.viz.plot_raw(raw)
# #epochs_data = mne.Epoc
# #hsArray(raw_data, info)
# #epochs_data.plot(picks ="all", n_epochs = 1, n_channels =5)


# timepoints = np.array(Preprocessor.timepoints, dtype ="int")
# events = np.zeros((timepoints.shape[0], 3), dtype = "int")
# events[:,0] = timepoints
# epochs_mne = mne.Epochs(raw, events, 0, tmax = 0, tmin = -3.006, baseline = None, detrend = 0)
# epochs_mne.plot(picks ="all", n_epochs = 2, n_channels =n_channels, block = True)

# # #save mne object
# print("saving the cleaned data...")
# path = "/mnt/data/analysis_INTENSE/data_cleaned/" + ((path_list[index].split("/")[-1]).replace(".pickle", "_epo.fif"))
# epochs_mne.save(path)

#%% For Johanna's Data
path = "/mnt/server/data08/RawData/2019_ST_IN-TENS"
subjects =  ["AmWo", "AuWi", "BuUl", "EiHe", "FuMa", "GeKl", "GrMa", "GuWi", "HeIn", "KaBe", "MaPe", "MaSy", "MeRu", "PlKa", "PoHe", "SaCe", "SoFa", "WiLu", "ZaRo"]
path_list = []
session_path = []
files_list = []
for subject in subjects:
    subject_path = os.path.join(path, subject)
    for folder in os.listdir(subject_path):
        if folder.startswith("pre") or folder.startswith("post"):
            session_path = os.path.join(subject_path, folder)
            for file in os.listdir(session_path):
                if file.endswith(".xdf") and file.startswith("mapping"):
                    file_path = os.path.join(session_path, file)
                    path_list.append(file_path)
                    files_list.append(file)
                    
index = 4                
streams, header = pyxdf.load_xdf(path_list[index])
print("Reading the data...")
data = np.array(streams[3]["time_series"]).T[:64,:]  # EEG time series

# sampling frequency:
fs = 1000

# channel names:
try:
    ch_names = []
    for i in range(64):
        ch_names.append(streams[3]["info"]["desc"][0]["channels"][0]["channel"][i]["label"][0])
except:
    ch_names = ['Fp1','Fp2','F3','F4','C3','C4','P3','P4','O1','O2','F7','F8','T7','T8','P7','P8','Fz','Cz','Pz',\
     'Iz','FC1','FC2','CP1','CP2','FC5','FC6','CP5','CP6','FT9','FT10', 'TP9','TP10','F1',\
    'F2','C1','C2','P1','P2','AF3','AF4','FC3','FC4','CP3','CP4','PO3','PO4','F5','F6','C5',\
     'C6','P5','P6','AF7','AF8','FT7','FT8','TP7','TP8','PO7', 'PO8','Fpz', 'CPz','POz','Oz']

info = mne.create_info(ch_names = ch_names, sfreq=fs, ch_types='eeg')

print("Creating a plot...")
raw = mne.io.RawArray(data, info)

raw = mne.io.Raw.filter(raw, l_freq=0.5, h_freq=40, picks ='all')

mne.viz.plot_raw(raw)

# Generate events and plot epochs

# ! be aware! sometimes loacalite markers sit in stream[0] (eg. BuUl) stream[1] (eg. AmWo)
try:
    localitemarkers =  streams[1]['time_series'] # Information about localite markers
except: 
    localitemarkers =  streams[0]['time_series']
TMStimes_all =  streams[1]['time_stamps']  

# get length of all loaclite markers 
markers =  len(TMStimes_all)
# define array for TMS pulses and other markers
TMS_events = np.zeros(markers)


# find the marker type which corresponds to TMS pulse
idxPulse = []
for idx, event in enumerate(localitemarkers):
    if "coil_0_didt" in event[0]: # "coil_0_didt" is wanted markertype
        idxPulse.append(idx)

event_array = []
for i in range(len(idxPulse)):
    event_array.append(streams[1]["time_stamps"][i])
    
event_array = np.unique(np.array(event_array, dtype = "int"))
events = np.zeros((event_array.shape[0], 3), dtype = "int")
events[:,0] = event_array



epoched = mne.Epochs(raw, events, 0, tmax = 0, tmin = -3.006, baseline = None, detrend = 0)


#plots all channels, 4 epochs at a time, with sliding bar over time series
epoched.plot(picks ="all", n_epochs = 2, n_channels = 64, block = True)





