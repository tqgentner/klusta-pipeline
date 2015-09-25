
# Merge stimuli information from spike2 mat file into Kwik file

import h5py as h5
import tables
import os
import numpy as np
import argparse
import glob

try: import simplejson as json
except ImportError: import json

from klusta_pipeline.dataio import load_digmark, load_stim_info

def get_args():

    parser = argparse.ArgumentParser(description='Compile Spike2 epoch .mat files into KlustaKwik KWD file.')
    parser.add_argument('path', default = './', nargs='?',
                       help='directory containing all of the mat files to compile')
    parser.add_argument('dest', default = './', nargs='?',
                       help='destination directory for kwd and other files')
    return parser.parse_args()

def get_rec_samples(kwd_file,index):
    with h5.File(kwd_file, 'r') as kwd:
        return kwd['/recordings/{}/data'.format(index)].shape[0]

def main():
    args = get_args()

    spike2mat_folder = os.path.abspath(args.path)
    kwik_folder = os.path.abspath(args.dest)

    info_json = glob.glob(os.path.join(kwik_folder,'*_info.json'))[0]
    with open(info_json, 'r') as f:
        info = json.load(f)

    kwik_data_file = os.path.join(kwik_folder,info['name']+'.kwik')
    kwd_raw_file = os.path.join(kwik_folder,info['name']+'.raw.kwd')

    with tables.open_file(kwik_data_file,'r+') as kkfile:

        digmark_timesamples = []
        digmark_recording = []
        digmark_codes = []
        stimulus_timesamples = []
        stimulus_recording = []
        stimulus_codes = []
        stimulus_names = []

        for rr, rec in enumerate(info['recordings']):
            t0 = rec['start_time']
            fs = rec['fs']
            n_samps = get_rec_samples(kwd_raw_file,rr)
            dur = float(n_samps) / fs

            s2mat = os.path.split(rec['file_origin'])[-1]
            s2mat = os.path.join(spike2mat_folder,s2mat)

            codes, times = load_digmark(s2mat)
            rec_mask = (times >= t0) * (times < (t0+dur))

            codes = codes[rec_mask]
            times = times[rec_mask] - t0
            time_samples = (times * fs).round().astype(np.uint64)
            recording = rr * np.ones(codes.shape,np.uint16)

            digmark_timesamples.append(time_samples)
            digmark_recording.append(recording)
            digmark_codes.append(codes)

            codes, times, names = load_stim_info(s2mat)
            rec_mask = (times >= t0) * (times < (t0+dur))

            codes = codes[rec_mask]
            names = names[rec_mask]
            times = times[rec_mask] - t0
            time_samples = (times * fs).round().astype(np.uint64)
            recording = rr * np.ones(codes.shape,np.uint16)

            stimulus_timesamples.append(time_samples)
            stimulus_recording.append(recording)
            stimulus_codes.append(codes)
            stimulus_names.append(names)

        digmark_timesamples = np.concatenate(digmark_timesamples)
        digmark_recording = np.concatenate(digmark_recording)
        digmark_codes = np.concatenate(digmark_codes)
        stimulus_timesamples = np.concatenate(stimulus_timesamples)
        stimulus_recording = np.concatenate(stimulus_recording)
        stimulus_codes = np.concatenate(stimulus_codes)
        stimulus_names = np.concatenate(stimulus_names)

        print digmark_timesamples.dtype
        print digmark_recording.dtype
        print digmark_codes.dtype
        print stimulus_timesamples.dtype
        print stimulus_recording.dtype
        print stimulus_codes.dtype
        print stimulus_names.dtype

        kkfile.create_group("/", "event_types", "event_types")

        kkfile.create_group("/event_types", "DigMark")
        kkfile.create_earray("/event_types/DigMark", 'time_samples', obj=digmark_timesamples)
        kkfile.create_earray("/event_types/DigMark", 'recording', obj=digmark_recording)
        kkfile.create_earray("/event_types/DigMark", 'codes', obj=digmark_codes)


        kkfile.create_group("/event_types", "Stimulus")
        kkfile.create_earray("/event_types/Stimulus", 'time_samples', obj=stimulus_timesamples)
        kkfile.create_earray("/event_types/Stimulus", 'recording', obj=stimulus_recording)
        kkfile.create_earray("/event_types/Stimulus", 'codes', obj=stimulus_codes)
        kkfile.create_earray("/event_types/Stimulus", 'text', obj=stimulus_names)