

from pydub import AudioSegment
from pydub.playback import play
import random

class PianoNote:
    """
    Represents a single piano note.

    Attributes:
        note_name (str): The name of the note.
        file_path (str): The file path of the audio file for the note.
    """
    NOTE_NAMES = ["a0", "as0", "b0", "c1", "cs1", "d1", "ds1", "e1", "f1", "fs1", "g1", "gs1",
                  "a1", "as1", "b1", "c2", "cs2", "d2", "ds2", "e2", "f2", "fs2", "g2", "gs2",
                  "a2", "as2", "b2", "c3", "cs3", "d3", "ds3", "e3", "f3", "fs3", "g3", "gs3",
                  "a3", "as3", "b3", "c4", "cs4", "d4", "ds4", "e4", "f4", "fs4", "g4", "gs4",
                  "a4", "as4", "b4", "c5", "cs5", "d5", "ds5", "e5", "f5", "fs5", "g5", "gs5",
                  "a5", "as5", "b5", "c6", "cs6", "d6", "ds6", "e6", "f6", "fs6", "g6", "gs6",
                  "a6", "as6", "b6", "c7", "cs7", "d7", "ds7", "e7", "f7", "fs7", "g7", "gs7",
                  "a7", "as7", "b7", "c8"]

    def __init__(self, note_name, file_path):
        self.note_name = note_name
        self.file_path = file_path
        
        
       
class PianoChord:
    """
    Represents a piano chord. 

    Attributes:
        root_note (str): The root note of the chord.
        intervals (list): The intervals of the chord from the root note.
        notes (list): The notes that form the chord.
    """
    def __init__(self, root_note, intervals):
        self.root_note = root_note
        self.intervals = intervals
        self.notes = self.build_notes()

    def build_notes(self):
        """
        Calculate the notes based on the intervals from the root note.

        Returns:
            list: The list of notes that form the chord.
        """
        # Calculate the notes based on the intervals from the root note
        notes = []

        current_note = self.root_note
        for interval in self.intervals:

            note_index = (PianoNote.NOTE_NAMES.index(current_note) + interval) % len(PianoNote.NOTE_NAMES)
            next_note = PianoNote.NOTE_NAMES[note_index]
            
            notes.append(next_note)
        
        return notes



    def play(self):
        """
        Plays the chord by playing together the audio files of all the notes.
        """        
        file_path = f"sounds/{self.notes[0]}.wav"

        note_audio = AudioSegment.from_file(file_path)
        
        chord_audio=note_audio
        
        for note_name in self.notes[1:]:

            file_path = f"sounds/{note_name}.wav"            
            note_audio = AudioSegment.from_file(file_path)
            chord_audio = chord_audio.overlay(note_audio) 
        
        play(chord_audio)
        