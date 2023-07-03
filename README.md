# PlayByEarTrainer
A powerful tool for musicians, offering interactive ear training exercises. Generates chords or single notes for users to play on their instruments and then records &amp; analyzes their responses, providing instant feedback

![image](https://github.com/Ni-co-la-s/PlayByEarTrainer/assets/96898279/61f2d2fb-2753-4869-af1d-a64bfee78722)

## Table of Contents

1. [Features](#features)
2. [Dependencies](#dependencies)
3. [Installation](#installation)
4. [Usage](#usage)
5. [Sources](#sources)


## Features

- Generates random chords or single notes based on user selection.
- Uses Web Audio API to play sounds and record user input.
- Analyzes the recorded audio and gives feedback on accuracy.
- Allows users to adjust the BPM and number of notes/chords.
- Supports major, minor, diminished, augmented, suspended, and various 7th chords.

## Dependencies

- numpy
- matplotlib
- wave
- flask
- flask_cors
- soundfile
- pydub
- werkzeug

## Installation

This project requires Python 3.7 or higher and a modern web browser with JavaScript enabled.

## Usage

After installing the project, you can start the server by running app.py. Once the server is running, open your web browser and navigate to `localhost:5000` to start the exercises.

## Sources

The polyphonic note detection used in this project comes from the code of the following repository:

- [Polyphonic_note_detector_using_Harmonic_Product_Spectrum](https://github.com/joaocarvalhoopen/Polyphonic_note_detector_using_Harmonic_Product_Spectrum/tree/main)
