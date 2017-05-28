#! /usr/bin/env python
# -*- coding: utf-8 -*

import numpy as np
import scipy.io.wavfile
from python_speech_features import mfcc, fbank, logfbank, hz2mel


def read_wav(wav_path, feature_type='logmelfbank'):
    """Read wav file & convert to MFCC or log mel filterbank features.
    Args:
        wav_path: path to a wav file
        feature: logmelfbank or mfcc
    Returns:
        inputs:
        seq_len:
    """
    # load wav file
    fs, audio = scipy.io.wavfile.read(wav_path)

    if feature_type == 'mfcc':
        features = mfcc(audio, samplerate=fs)  # (291, 13)
    elif feature_type == 'logmelfbank':
        fbank_features, energy = fbank(audio, nfilt=40)
        logfbank = np.log(fbank_features)
        logenergy = np.log(energy)
        logmelfbank = hz2mel(logfbank)
        features = np.c_[logmelfbank, logenergy]  # (291, 41)

    delta1 = delta(features, N=2)
    delta2 = delta(delta1, N=2)
    inputs = np.c_[features, delta1, delta2]

    # transform to 3D array
    inputs = np.asarray(inputs[np.newaxis, :])  # (1, 291, 39) or (1, 291, 123)
    seq_len = [inputs.shape[1]]  # [291]

    # normalization
    inputs = (inputs - np.mean(inputs)) / np.std(inputs)

    return inputs, seq_len


def delta(feat, N):
    """Compute delta features from a feature vector sequence.
    Args:
        feat: A numpy array of size (NUMFRAMES by number of features) containing features.
              Each row holds 1 feature vector.
        N: For each frame, calculate delta features based on preceding and following N frames.
    Rreturns:
        dfeat: A numpy array of size (NUMFRAMES by number of features) containing delta features.
               Each row holds 1 delta feature vector.
    """
    NUMFRAMES = len(feat)
    feat = np.concatenate(([feat[0] for i in range(N)],
                           feat, [feat[-1] for i in range(N)]))
    denom = sum([2 * i * i for i in range(1, N + 1)])
    dfeat = []
    for j in range(NUMFRAMES):
        dfeat.append(np.sum([n * feat[N + j + n]
                             for n in range(-1 * N, N + 1)], axis=0) / denom)
    return dfeat


def read_text(text_path):
    """Read char-level transcripts.
    Args:
        text_path: path to a transcript text file
    Returns:
        transcript: a text of transcript
    """
    # read ground truth labels
    with open(text_path, 'r') as f:
        line = f.readlines()[-1]
        transcript = ' '.join(line.strip().lower().split(' ')[2:])
    return transcript


def read_phone(text_path):
    """Read phone-level transcripts.
    Args:
        text_path: path to a transcript text file
    Returns:
        transcript: a text of transcript
    """
    # read ground truth labels
    phone_list = []
    with open(text_path, 'r') as f:
        for line in f:
            line = line.strip().split(' ')
            phone_list.append(line[-1])
    transcript = ' '.join(phone_list)
    return transcript


def generate_data(label_type, model):
    """
    Args:
        label_type: character or phone
        model: ctc or attention
    """
    # make input data
    inputs, seq_len = read_wav('./sample/LDC93S1.wav',
                               feature_type='logmelfbank')
    # inputs, seq_len = read_wav('../sample/LDC93S1.wav',
    #                            feature_type='mfcc')

    if label_type == 'character':
        transcript = read_text('./sample/LDC93S1.txt')
        if model == 'ctc':
            transcript = ' ' + transcript.replace('.', '') + ' '
            labels = [alpha2num(transcript)]
        elif model == 'attention':
            pass
    elif label_type == 'phone':
        if model == 'ctc':
            transcript = read_phone('./sample/LDC93S1.phn')
            labels = [phone2num(transcript)]
        elif model == 'attention':
            pass

    return inputs, labels, seq_len


def phone2num(transcript):
    """Convert from phone to number.
    Args:
        transcript: sequence of phones (string)
    Returns:
        index_list: list of indices of phone (int)
    """
    phone_list = list(transcript)

    # read mapping file from phone to number
    phone_dict = {}
    with open('../../experiments/timit/evaluation/mapping_files/ctc/phone2num_39.txt') as f:
        for line in f:
            line = line.strip().split()
            phone_dict[line[0]] = int(line[1])

    # convert from phone to the corresponding number
    index_list = []
    for i in range(len(phone_list)):
        if phone_list[i] in phone_dict.keys():
            index_list.append(phone_dict[phone_list[i]])
    return index_list


def num2phone(index_list):
    """Convert from number to phone.
    Args:
        index_list: list of indices of phone (int)
    Returns:
        transcript: sequence of phones (string)
    """
    # read a phone mapping file
    phone_dict = {}
    with open('../../experiments/timit/evaluation/mapping_files/ctc/phone2num_39.txt') as f:
        for line in f:
            line = line.strip().split()
            phone_dict[int(line[1])] = line[0]

    # convert from num to the corresponding phone
    phone_list = []
    for i in range(len(index_list)):
        phone_list.append(phone_dict[index_list[i]])
    transcript = ' '.join(phone_list)
    return transcript


def alpha2num(transcript):
    """Convert from alphabet to number.
    Args:
        transcript: sequence of characters (string)
    Returns:
        index_list: list of indices of alphabet (int)
    """
    char_list = list(transcript)

    # 0 is reserved for space
    space_index = 0
    first_index = ord('a') - 1
    index_list = [space_index if char == ' ' else ord(
        char) - first_index for char in char_list]
    return index_list


def num2alpha(index_list):
    """Convert from number to alphabet.
    Args:
        index_list: list of indices of alphabet (int)
    Returns:
        transcript: sequence of character (string)
    """
    # 0 is reserved to space
    first_index = ord('a') - 1
    char_list = [' ' if num == 0 else chr(
        num + first_index) for num in index_list]
    transcript = ''.join(char_list)
    return transcript
