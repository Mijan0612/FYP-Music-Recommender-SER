import librosa
from librosa import display
from matplotlib import pyplot as plt

path = "FYP(Music Recommender SER)/Ravdess/Audio_Song_Actors_01-24/03-02-01-01-01-01-04.wav"
data, sampling_rate = librosa.load(path)


import os
import pandas as pd
import glob

plt.figure(figsize=(12, 4))
librosa.display.waveplot(data, sr=sampling_rate)