# -*- coding: utf-8 -*-
"""
Created on Thu Jul 15 10:00:37 2021

@author: Lea
"""

"""
Class for EEG preprocessing
"""

import numpy as np
from scipy.signal import filtfilt, butter
import matplotlib.pyplot as plt
import os
import pickle
from multichannel_tools.visual_inspection import visual_inspection

import numpy as np
from scipy.signal import filtfilt, butter
import pickle
import pandas as pd
import mne

class Preprocessor():
    
    timepoints = []


                
    def load_data_dict(self, path):
        """
        loads the data dictionary which is saved by the FileHandler
        """
        with open(path, 'rb') as handle:
            data_dict = pickle.load(handle)
            
        return data_dict
        
    
    def cut_epochs(self, data_dict, before_pulse = 0.006, epoch_length = 3):
        """
        make epochs of the length 3 seconds and cut 2 ms before the pulse
        """
        
        # define important variables to cut the epochs
        self.fs = data_dict["fs"]
        self.channel_info = data_dict["channel_info"]
        self.trigger_count = (len(data_dict["trigger_time_stamp"]))
        self.raw_data = data_dict["time_series"]
        
        # converts value in seconds into a sample number
        before_pulse_samples = int(self.fs * before_pulse)
        epoch_length_samples = int(self.fs * epoch_length)
        
        # initializes an array with the number of TMS pulses, so one epoch per pulse
        self.epochs = []
        # creates an index for C3 from channel info to use with the data
        cz_idx = np.where(self.channel_info[0] == "Cz")[0]
        
        for trig in range(self.trigger_count):
            # FIRST all the correct timepoint for the TMS pulse needs to be found
            tstamp = data_dict["trigger_time_stamp"][trig]  # get timestamp for trigger
            if tstamp != 0:

                cz_data = self.raw_data[:,cz_idx]  # get only the data for c3 because TMS can be detected best here
                time_window = cz_data[int(tstamp) - self.fs: int(tstamp) + self.fs, :]  # create time window with the trigger
                TMS_time = np.argmax(np.absolute(time_window))  # get the time point of the TMS pulse within the time window
                TMS_peak_value = float(time_window[TMS_time])# get the value of the TMS
                potential_TMS_peak = np.where(cz_data == TMS_peak_value)[0]  # gets all the timepoints in the whole time_window, where TMS_peak_value is reached
                TMS_peak = potential_TMS_peak[np.argmin(np.abs(potential_TMS_peak - tstamp))]  # gets only the one closest to the timestamp for the case of several of the same values
               
                if TMS_peak not in self.timepoints:
                    self.timepoints.append(TMS_peak)
                    # THEN the epochs are formed accordingly
                    
                    epoch = self.raw_data[TMS_peak - (epoch_length_samples + before_pulse_samples): TMS_peak - before_pulse_samples, :]
                    for x in epoch:
                        x -= epoch.mean()
                    self.epochs.append(epoch)
         

                c3_data = self.raw_data[:,cz_idx]  # get only the data for c3 because TMS can be detected best here
                time_window = c3_data[int(tstamp) - self.fs: int(tstamp) + self.fs, :]  # create time window with the trigger
                TMS_time = np.argmax(np.absolute(time_window))  # get the time point of the TMS pulse within the time window
                TMS_peak_value = float(time_window[TMS_time])# get the value of the TMS
                potential_TMS_peak = np.where(c3_data == TMS_peak_value)[0]  # gets all the timepoints in the whole time_window, where TMS_peak_value is reached
                TMS_peak = potential_TMS_peak[np.argmin(np.abs(potential_TMS_peak - tstamp))]  # gets only the one closest to the timestamp for the case of several of the same values
                # THEN the epochs are formed accordingly
                epoch = self.raw_data[TMS_peak - (epoch_length_samples + before_pulse_samples): TMS_peak - before_pulse_samples, :]
                self.epochs.append(epoch)
#            except ValueError:
#                self.epochs.append(0)
         
        epochs = np.array(self.epochs)
        return epochs
    
    
    def filter_data(self, data, lowcut = 0.5, highcut = 40):
        """
        band pass filter data from 0.5 to 40 Hz,
        so low frequencies and line noise are filtered out
        """
        nyq = 0.5 * self.fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(1, [low, high], btype='bandpass')
        
        # applies the filter
        filt_data = filtfilt(b, a, data.T).T
        
        return filt_data
    
    
    def eliminate_bad_data(self, data_filt):
        """
        eliminates all the trials (channel in an epoch), not good enough for the analysis

        """
        data_cleaned = np.zeros(data_filt.shape())
        for i in range(len(self.epochs)):
            epoch = self.epochs[i]
            for chan in range(epoch.shape[1]):
                minimum = np.min(data_filt)
                base_line_corrected = data_filt - minimum
                if (np.max(base_line_corrected) <= 2) or (np.max(np.abs(base_line_corrected)) > 50):
                    data_cleaned[:, chan] = 0
                else:
                    data_cleaned[:, chan] = data_filt[:, chan]
            
        


        epochs = np.array(self.epochs)
        return epochs

    def filter_data(self, data, fs, lowcut = 0.5, highcut = 40):
        """
        band pass filter data from 0.5 to 40 Hz,
        so low frequencies and line noise are filtered out
        """
        nyq = 0.5 * fs
        low = lowcut / nyq
        high = highcut / nyq
        b, a = butter(1, [low, high], btype='bandpass')
        
        # applies the filter
        filt_data = filtfilt(b, a, data.T).T
        
        return filt_data
          
    def get_relevant_epochs(self, cleaned):
        """
        returns a list of the epochs not dropped for later compuations with EMG data
        """
        return cleaned.selection

    def make_rereference_common_average(self):
        """ 
        makes the reference the common average
        """
        # acquire the online reference
        reference = self.channel_info[1][0]
        
        # make new column for the online reference, which is 0 before re-referencing
        # and append to data array
        reference_column = np.zeros((self.cnt.get_sample_count(), 1))
        self.data = np.append(self.data, reference_column, axis = 1)
        
        # change the channel_info to also include online reference and to indicate common average as new offline reference
        info_new = np.zeros((2,1))
        self.channel_info = np.append(self.channel_info, info_new, axis = 1)
        self.channel_info[0][-1] = reference
        for references in range(len(self.channel_info)):
            self.channel_info[1][references] = "common average"
            
        # compute average of all timepoints within an epoch and set as new reference by subtracting it from all values
        for epoch in range(len(self.epochs)):
            avg = np.mean(self.epochs[epoch])
            for timepoint in range(len(self.epochs[epoch])):
                for chan in range(self.channel_info.shape[0]):
                    self.epochs[epoch][timepoint][chan] -= avg
        

    
    def apply_surface_laplacian(self, epochs):
        """ 
        computes the current source density aka surface laplacian
        """
        
        # do it epoch wise???
        
        return mne.preprocessing.compute_current_source_density(epochs)
    
    

    def normalize_data(self):
        """
        normalizes the data
        """
        # (observed value - mean)/ standard deviation
        
        pass
    

    def save_preprocessed_data(self, epochs_mne, path_list_index):
        path = "/mnt/data/analysis_INTENSE/data_preprocessed/" + ((path_list_index.split("/")[-1]).replace(".pickle", "_epo.fif"))
        epochs_mne.save(path)


    def save_preprocessed_data(self):
        pass
        
#%% 
#    
#if __name__ == "__main__":
#    
#    server_path = "/mnt/server/data02/RawData/2019_ST_RoboTMS_EEG"
#    subjects = ["AmWo", "AuWi", "BuUl", "EiHe", "FuMa", "GeKl", "GrMa", "GuWi", "HeIn", "KaBe", "MaPe", "MaSy", "MeRu", "PlKa", "PoHe", "SaCe", "SoFa", "WiLu", "ZaRo"]
#    path_list = []
#    files_list = []
#    for subject in subjects:
#        subject_path = os.path.join(server_path, subject)
#        for file in os.listdir(subject_path):
#            subj_date_path = os.path.join(subject_path, file)
#            for file in os.listdir(subj_date_path):
#                if file.endswith(".cnt"):
#                    
#                    fname = os.path.join(subj_date_path, file)
#                    
#                    label = file.replace(".cnt", "")
#                    
#                    save_path = os.path.join("/mnt/data/analysis_INTENSE/data_dicts", subject)
#                    path_to_load = os.path.join(save_path, label) + ".pickle"
#                    path_list.append(path_to_load)
#                    files_list.append(file)
#      



