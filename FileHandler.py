#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Aug 27 08:43:52 2021

@author: Lea
"""
import libeep
import numpy as np
import os
import pickle
import pyxdf



class FileHandler():
    
    def __init__(self, fname):
        self.fname = fname
        self.cnt = libeep.cnt_file(fname)

    
    
    def load_data(self):
        """
        Loads a cnt file and puts it into a numpy array with timepoint x channels
        """        
        print("Loading the data")
        data = np.array(self.cnt.get_samples(0, self.cnt.get_sample_count()))
        
        return data
    
    
    def acquire_channel_info(self):
        """
        acquires the channel info from the cnt file and puts it into a numpy array
        """
        channels = []
        references = []
        for chan in range(self.cnt.get_channel_count()):
            channels.append(self.cnt.get_channel_info(chan)[0])
            references.append(self.cnt.get_channel_info(chan)[1])
        channels = np.array(channels)
        references = np.array(references)
        return np.stack((channels, references))
    
    
    
    def save_data(self, data, path, label):
        """
        saves the data as a dictionary, so everything can be openened in Spyder
        """
        
        print("Creating and saving the data dictionary")
        trigger_tstamp = np.zeros(self.cnt.get_trigger_count())
        trigger_tmarker = np.zeros(self.cnt.get_trigger_count())
        for trig in range(len(trigger_tstamp)):
            tmarker, tstamp, *info  = self.cnt.get_trigger(trig)
            trigger_tstamp[trig] = tstamp
            trigger_tmarker[trig] = tmarker
         
        data_dict = {}
        data_dict["fs"] = self.cnt.get_sample_frequency()
        data_dict["time_series"] = data
        data_dict["trigger_time_stamp"] = trigger_tstamp
        data_dict["trigger_marker"] = trigger_tmarker
        data_dict["channel_info"] = self.acquire_channel_info()


          # make patient folder if it doesn't exist
        if os.path.exists(path) == False:
            os.makedirs(path)
        
        # check for trial file of the same name, if it's there then don't overwrite it
        save_path = os.path.join(path, label)
        if os.path.exists(save_path + '.pickle') == True:
            pass
#            label = label + '_2'
#            with open(save_path+ '.pickle', 'wb') as handle:
#                pickle.dump(data_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
        else:
            with open(save_path + '.pickle', 'wb') as handle:
                pickle.dump(data_dict, handle, protocol=pickle.HIGHEST_PROTOCOL)
                
                
#%% for Johanna's Data:
    
data = pyxdf.load_xdf("/mnt/server/data08/RawData/2019_ST_IN-TENS/AmWo/post6/TMS_NMES_AmWo_post6.xdf")
    
                
#%% function execution
# if you want to run the FileHandler for the cnt files, you have to use the command line
# for this open the terminal, use cd to go to the directory FileHandler.py is in and the type the command:
# python3 FileHandler.py 
#....then just wait
              
if __name__ == "__main__":
    
    server_path = "/mnt/server/data02/RawData/2019_ST_RoboTMS_EEG"

    subjects = ["PlKa", "SaCe"]

    path_list = []
    for subject in subjects:
        subject_path = os.path.join(server_path, subject)
        for file in os.listdir(subject_path):
            subj_date_path = os.path.join(subject_path, file)
            for file in os.listdir(subj_date_path):
                if file.endswith(".cnt"):
                    
                    fname = os.path.join(subj_date_path, file)
                    
                    label = file.replace(".cnt", "")
                    
                    save_path = os.path.join("/mnt/data/analysis_INTENSE/data_dicts", subject)
                    
                    f = FileHandler(fname)
                    data = f.load_data()
                    f.save_data(data, save_path, label)
    