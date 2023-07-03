from flask import Flask, request, jsonify, send_from_directory
from flask_cors import cross_origin
import numpy as np
import soundfile as sf
import random
from audio_processing import (get_all_notes_freq, divide_buffer_into_non_overlapping_chunks, getFFT,
    remove_dc_offset, PitchSpectralHps, find_nearest_note)
from piano_classes import PianoChord, PianoNote
from werkzeug.exceptions import HTTPException
import traceback
from pydub import AudioSegment
import logging
import subprocess
import os

app = Flask(__name__, static_url_path='', static_folder='web')
app.logger.setLevel(logging.DEBUG)

app.logger.info('This is info analyze')

AudioSegment.converter = "C:\\Users\\pault\\anaconda3\\Scripts\\ffmpeg.exe"


# Define the chord types and their respective intervals
chord_lists = {
    "Major": [0, 4, 7],
    "Minor": [0, 3, 7],
    "Diminished": [0, 3, 6],
    "Augmented": [0, 4, 8],
    "Suspended 2nd": [0, 2, 7],
    "Suspended 4th": [0, 5, 7],
    "Major 7th": [0, 4, 7, 11],
    "Minor 7th": [0, 3, 7, 10],
    "Dominant 7th": [0, 4, 7, 10],
    "Diminished 7th": [0, 3, 6, 9],
    "Half-Diminished 7th": [0, 3, 6, 10],
    "Minor Major 7th": [0, 3, 7, 11],
    "Augmented Major 7th": [0, 4, 8, 11],
    "Augmented 7th": [0, 4, 8, 10]
}
# Select a random chord type 
random_chord_type = random.choice(list(chord_lists.keys()))
random_chord_intervals = chord_lists[random_chord_type]

# Create a random PianoChord instance
start_index = PianoNote.NOTE_NAMES.index("e2")
end_index = PianoNote.NOTE_NAMES.index("e4")
random_chord_root_note = random.choice(PianoNote.NOTE_NAMES[start_index:end_index + 1])
random_chord = PianoChord(random_chord_root_note, random_chord_intervals)




@app.errorhandler(Exception)
def handle_exception(e):
    # If the error is an HTTPException (flask error), use its error code
    # Otherwise use a 500 error code (server error)
    code = 500
    if isinstance(e, HTTPException):
        code = e.code
    return jsonify(error=str(e), traceback=traceback.format_exc()), code


@app.route('/')
def index():
    return send_from_directory(app.static_folder, 'home.html')

@app.route('/generate-chord', methods=['GET'])
@cross_origin()
def generate_chord():
    app.logger.info('This is info generate')

    chord_types = request.args.get('chord_types', None)
    app.logger.info(chord_types)
    if chord_types is not None:
        chord_types = chord_types.split(',')
        random_chord_type = random.choice(chord_types)
    else:
        random_chord_type = random.choice(list(chord_lists.keys()))

    random_chord_intervals = chord_lists[random_chord_type]
    start_index = PianoNote.NOTE_NAMES.index("e2")
    end_index = PianoNote.NOTE_NAMES.index("e4")
    random_chord_root_note = random.choice(PianoNote.NOTE_NAMES[start_index:end_index + 1])
    random_chord = PianoChord(random_chord_root_note, random_chord_intervals)
    return jsonify({'chord_type': random_chord_type, 'notes': random_chord.notes})

@app.route('/generate-notes', methods=['GET'])
@cross_origin()
def generate_notes():
    app.logger.info('This is info generate')

    start_index = PianoNote.NOTE_NAMES.index("e2")
    end_index = PianoNote.NOTE_NAMES.index("e4")
    random_note = random.choice(PianoNote.NOTE_NAMES[start_index:end_index + 1])
    app.logger.info(f"note: {random_note}")
    return jsonify({'chord_type': "Single note",'notes': random_note})


@app.route('/analyze', methods=['POST'])
@cross_origin()
def analyze_audio_file():
    app.logger.info('Analyze route hit')  # logs the initial hit to the route

    if 'file' not in request.files:
        app.logger.error('No file part in the request')  # logs if there's no file in the request
        return jsonify({'error': 'No file part in the request'}), 400

    file = request.files['file']

    if file.filename == '':
        app.logger.error('No file selected for uploading')  # logs if there's no selected file
        return jsonify({'error': 'No file selected for uploading'}), 400

    try:
        # Save the incoming file
        file.save('input.webm')
        
        # Log the file size
        app.logger.info(f'Input file size: {os.path.getsize("input.webm")} bytes')

        # Delete the output file if it already exists
        if os.path.exists('output.wav'):
            os.remove('output.wav')


        # Use ffmpeg to convert the file to wav
        try:
            app.logger.info('Converting file to wav')
            result = subprocess.run(['ffmpeg', '-i', 'input.webm', 'output.wav'], capture_output=True, text=True, check=True)
            app.logger.info(result.stdout)
            app.logger.error(result.stderr)  # Log this as error so we can see it even if the overall log level is set to higher than INFO
        except Exception as e:
            app.logger.error(f'ffmpeg conversion failed: {e}')
            return jsonify({'error': 'ffmpeg conversion failed'}), 500

        # Then, analyze the WAV file...
        app.logger.info('Reading wav file')
        data, sample_rate = sf.read("output.wav")
        app.logger.info(f'Data {data.shape}')

        # Log the rest of the process
        app.logger.info('Beginning note analysis')
        chunk_size = sample_rate // 2
        ordered_note_freq = get_all_notes_freq()
        buffer_chunks = divide_buffer_into_non_overlapping_chunks(data, chunk_size)
        recognized_notes = []
        for chunk in buffer_chunks:
            app.logger.info('Analyzing chunk')
            fft_freq, fft_res, fft_res_len = getFFT(chunk, len(chunk))
            fft_res = remove_dc_offset(fft_res)
            buffer_rms = np.sqrt(np.mean(chunk ** 2))
            all_freqs = PitchSpectralHps(fft_res, fft_freq, sample_rate, buffer_rms)
            strongest_notes = []
            for freq in all_freqs:
                note_name = find_nearest_note(ordered_note_freq, freq[0])
                strongest_notes.append((freq[0], freq[1], note_name))
            strongest_notes.sort(key=lambda x: x[1], reverse=True)
            unique_notes = set()
            for note in strongest_notes:
                if note[2] not in unique_notes:
                    recognized_notes.append(note[2])
                    unique_notes.add(note[2])
                if len(unique_notes) >= 6:
                    break

        app.logger.info('Finished note analysis')
        app.logger.info(f'Recognized notes: {recognized_notes}')
        return jsonify({'recognized_notes': recognized_notes})

    except Exception as e:
        app.logger.error(f"Error: {e}")
        app.logger.error(traceback.format_exc())  # This will log the stack trace

        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run()