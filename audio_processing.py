import numpy as np
import wave
import math

note_threshold = 8_000.0

# Parameters
sample_rate  = 44100                     # Sampling Frequency
fft_len      = 22050   # 2048                      # Length of the FFT window
overlap      = 0.5                       # Hop overlap percentage between windows
hop_length   = int(fft_len*(1-overlap))  # Number of samples between successive frames

TWELVE_ROOT_OF_2 = math.pow(2, 1.0 / 12)


def divide_buffer_into_non_overlapping_chunks(buffer, max_len):
    buffer_len = len(buffer)
    chunks = int(buffer_len / max_len)
    division_pts_list = []
    for i in range(1, chunks):
        division_pts_list.append(i * max_len)
    splitted_array_view = np.split(buffer, division_pts_list, axis=0)
    return splitted_array_view

def getFFT(data, rate):
    len_data = len(data)
    data = data * np.hamming(len_data)
    fft = np.fft.rfft(data)
    fft = np.abs(fft)
    ret_len_FFT = len(fft)
    freq = np.fft.rfftfreq(len_data, 1.0 / sample_rate)
    return freq, fft, ret_len_FFT

def remove_dc_offset(fft_res):
    fft_res[0] = 0.0
    fft_res[1] = 0.0
    fft_res[2] = 0.0
    return fft_res

def find_nearest_note(ordered_note_freq, freq):
    final_note_name = 'note_not_found'
    last_dist = 1_000_000.0
    for note_name, note_freq in ordered_note_freq:
        curr_dist = abs(note_freq - freq)
        if curr_dist < last_dist:
            last_dist = curr_dist
            final_note_name = note_name
        elif curr_dist > last_dist:
            break
    return final_note_name

def freq_for_note(base_note, note_index):

    
    A4 = 440.0
    base_notes_freq = {"A2": A4 / 4, "A3": A4 / 2, "A4": A4, "A5": A4 * 2, "A6": A4 * 4}
    scale_notes = {"C": -9.0, "C#": -8.0, "D": -7.0, "D#": -6.0, "E": -5.0, "F": -4.0, "F#": -3.0,
                   "G": -2.0, "G#": -1.0, "A": 1.0, "A#": 2.0, "B": 3.0, "Cn": 4.0}
    scale_notes_index = list(range(-9, 5))
    note_index_value = scale_notes_index[note_index]
    freq_0 = base_notes_freq[base_note]
    freq = freq_0 * math.pow(TWELVE_ROOT_OF_2, note_index_value)
    return freq

def get_all_notes_freq():
    ordered_note_freq = []
    ordered_notes = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    for octave_index in range(2, 7):
        base_note = "A" + str(octave_index)
        for note_index in range(0, 12):
            note_freq = freq_for_note(base_note, note_index)
            note_name = ordered_notes[note_index] + "_" + str(octave_index)
            ordered_note_freq.append((note_name, note_freq))
    return ordered_note_freq

def read_wav_file(path, filename):
    wav_handler = wave.open(path + filename, 'rb')  # Read only.
    num_frames = wav_handler.getnframes()
    sample_rate = wav_handler.getframerate()
    wav_frames = wav_handler.readframes(num_frames)

    signal_temp = np.frombuffer(wav_frames, np.int16)
    signal_array = np.zeros(len(signal_temp), float)

    for i in range(0, len(signal_temp)):
        signal_array[i] = signal_temp[i] / (2.0 ** 15)

    return sample_rate, signal_array

def to_str_f(value):
    return "{0:.0f}".format(value)

def to_str_f4(value):
    return "{0:.4f}".format(value)

def note_threshold_scaled_by_RMS(buffer_rms):
    note_threshold = 1000.0 * (4 / 0.090) * buffer_rms
    return note_threshold

def PitchSpectralHps(X, freq_buckets, f_s, buffer_rms):

    iOrder = 4
    f_min = 65.41

    f = np.zeros(len(X))

    iLen = int((X.shape[0] - 1) / iOrder)
    afHps = X[np.arange(0, iLen)]
    k_min = int(round(f_min / f_s * 2 * (X.shape[0] - 1)))


    for j in range(1, iOrder):
        X_d = X[::(j + 1)]
        afHps *= X_d[np.arange(0, iLen)]


    note_threshold = note_threshold_scaled_by_RMS(buffer_rms)

    all_freq = np.argwhere(afHps[np.arange(k_min, afHps.shape[0])] > note_threshold)

    freqs_out = (all_freq + k_min) / (X.shape[0] - 1) * f_s / 2

    
    x = afHps[np.arange(k_min, afHps.shape[0])]
    freq_indexes_out = np.where( x > note_threshold)
    freq_values_out = x[freq_indexes_out]

    max_value = np.max(afHps[np.arange(k_min, afHps.shape[0])])
    max_index = np.argmax(afHps[np.arange(k_min, afHps.shape[0])])
    
    freqs_out_tmp = []
    for freq, value  in zip(freqs_out, freq_values_out):
        freqs_out_tmp.append((freq[0], value))
    
    return freqs_out_tmp


def analyze_audio_file(file_path):
    note_threshold = 8_000.0  # Adjust the note threshold value as needed

    # Parameters
    sample_rate = 44100  # Sampling Frequency
    chunk_size=sample_rate//2
    fft_len = 22050  # Length of the FFT window
    overlap = 0.5  # Hop overlap percentage between windows
    hop_length = int(fft_len * (1 - overlap))  # Number of samples between successive frames


    ordered_note_freq = get_all_notes_freq()

    sample_rate_file, input_buffer = read_wav_file("",file_path)

    buffer_chunks = divide_buffer_into_non_overlapping_chunks(input_buffer, chunk_size)

    count = 0

    for chunk in buffer_chunks:
        print("\n...Chunk: ", str(count))

        fft_freq, fft_res, fft_res_len = getFFT(chunk, len(chunk))
        fft_res = remove_dc_offset(fft_res)

        buffer_rms = np.sqrt(np.mean(chunk ** 2))

        all_freqs = PitchSpectralHps(fft_res, fft_freq, sample_rate_file, buffer_rms)

        for freq in all_freqs:
            note_name = find_nearest_note(ordered_note_freq, freq[0])
            print("=> freq: " + to_str_f(freq[0]) + " Hz  value: " + to_str_f(freq[1]) + " note_name: " + note_name)

        count += 1
        