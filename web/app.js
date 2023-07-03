// Setup audio context and constraints
let audioContext;
let mediaRecorder;
let currentChord = null;
let recordingTimeout = null;
let recordingInterval = null;
let isRecording = false;
let recordedChunks = [];
let correctChord = false;


let numChords;
let currentChordIndex = 0;
let correctChords = 0;
let totalChords = 0;
let currentChordIndexForRecording = 0;

let playMode;

audioContext = new (window.AudioContext || window.webkitAudioContext)();
let audioBuffers = {};

let numFiles = ['c', 'cs', 'd', 'ds', 'e', 'f', 'fs', 'g', 'gs', 'a', 'as', 'b'].length * 6;  // 6 octaves
let numLoaded = 0;

// Disable buttons
document.getElementById("generate-button").disabled = true;
document.getElementById("record-button").disabled = true;

// Load audio files at start of the program
let loadPromises = [];
['c', 'cs', 'd', 'ds', 'e', 'f', 'fs', 'g', 'gs', 'a', 'as', 'b'].forEach(note => {
    for(let octave = 2; octave <= 7; octave++){
        let loadPromise = fetch(`./sounds/${note}${octave}.wav`)
            .then(response => response.arrayBuffer())
            .then(arrayBuffer => audioContext.decodeAudioData(arrayBuffer))
            .then(audioBuffer => {
                audioBuffers[`${note}${octave}`] = audioBuffer;
                numLoaded++;
                document.getElementById("progress-bar").style.width = `${(numLoaded/numFiles) * 100}%`;
            });
        loadPromises.push(loadPromise);
    }
});

let beatBuffer;
let loadBeatPromise = fetch(`./sounds/beat.wav`)
    .then(response => response.arrayBuffer())
    .then(arrayBuffer => audioContext.decodeAudioData(arrayBuffer))
    .then(audioBuffer => {
        beatBuffer = audioBuffer;
        numLoaded++;
        document.getElementById("progress-bar").style.width = `${(numLoaded/(numFiles + 1)) * 100}%`;  // Remember to add 1 to numFiles to account for the beat sound
    });

loadPromises.push(loadBeatPromise);

// Enable buttons when all files are loaded
Promise.all(loadPromises).then(() => {
    document.getElementById("generate-button").disabled = false;
    document.getElementById("record-button").disabled = false;
    document.getElementById("progress-bar").style.display = 'none';  // Hide progress bar
});

function generateChords() {
    if(audioContext.state === 'suspended') {
        audioContext.resume();
    }
    if (!audioContext) {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
    }

    if(window.location.href.endsWith("chords.html")) {
        playMode = "chords";
    } else if(window.location.href.endsWith("notes.html")) {
        playMode = "notes";
    }

    let fetchUrl = playMode === "chords" ? '/generate-chord' : '/generate-notes';


    let chordTypes = [];
    let checkboxes = document.querySelectorAll("input[name='chords']:checked");
    for (let checkbox of checkboxes) {
        chordTypes.push(checkbox.value);
    }
    
    fetchUrl = chordTypes.length > 0 ? `${fetchUrl}?chord_types=${chordTypes.join(',')}` : fetchUrl;

    numChords = document.getElementById("chordNum").value; // Get the number of chords from the slider
    currentChordIndex = 0;
    chords = [];
    let bpm = document.getElementById("bpmSlider").value;
    let beatDuration = 60/bpm * 1000; // Duration of each beat in milliseconds

    for(let i=0; i<numChords; i++) {
        fetch(fetchUrl)
        .then(response => response.json())
        .then(data => {

            if(playMode === "notes"){
                data.notes = [data.notes];
            }
            chords.push(data);

            if(i === 0) {
                document.getElementById("bpmSlider").disabled = true;

                playChord();
            }
        });
    }
}

function playChord() {
    if(currentChordIndex < numChords) {
        let chord = chords[currentChordIndex];
        currentChordIndex += 1;
        document.getElementById('chordName').innerHTML = 'Chord Name: ' + chord.chord_type;
        //document.getElementById('chordNotes').innerHTML = 'Chord Notes: ' + chord.notes.join(', ');

        let bpm = document.getElementById('bpmSlider').value;
        let duration = 60000 / bpm; // Duration in ms for one chord

        let audioSources = chord.notes.map(note => {
            let source = audioContext.createBufferSource();
            source.buffer = audioBuffers[note];
            source.connect(audioContext.destination);
            return source;
        });

        // Create a source for the beat sound
        let beatSource = audioContext.createBufferSource();
        beatSource.buffer = beatBuffer;
        beatSource.connect(audioContext.destination);

        audioSources.forEach(source => source.start());
        
        // Start the beat sound at the same time
        beatSource.start();

        // Set timeout for the next chord
        setTimeout(playChord, duration);
    } 
}


function startRecording() {

    if (!isRecording && currentChordIndexForRecording < numChords) {
        totalChords += 1;
        let bpm = document.getElementById('bpmSlider').value;
        let delay = 60000 / bpm;

        navigator.mediaDevices.getUserMedia({ audio: true }).then(function(stream) {
            mediaRecorder = new MediaRecorder(stream);
            mediaRecorder.ondataavailable = (event) => {
                if (event.data.size > 0) {
                    recordedChunks.push(event.data);
                }
            };
            mediaRecorder.onstop = (event) => {
                isRecording = false;
                if(currentChordIndexForRecording < numChords){
                    analyzeRecording();

                }else{
                    document.getElementById("score-display").innerText = `Score: ${correctChords}/${numChords}`;
                    correctChords = 0;
                    totalChords = 0;
                    currentChordIndexForRecording = 0;
                }
            };

            mediaRecorder.start();

            // Create a source for the beat sound
            let beatSource = audioContext.createBufferSource();
            beatSource.buffer = beatBuffer;
            beatSource.connect(audioContext.destination);

            // Start the beat sound at the same time
            beatSource.start();

            document.getElementById('recording-status').innerHTML = 'Recording chord ' + (currentChordIndexForRecording + 1);
            document.getElementById('recording-status').classList.remove('not-recording');
            document.getElementById('recording-status').classList.add('recording');
            isRecording = true;

            setTimeout(function() {
                mediaRecorder.stop();
                document.getElementById('recording-status').innerHTML = 'Not Recording';
                document.getElementById('recording-status').classList.remove('recording');
                document.getElementById('recording-status').classList.add('not-recording');
            }, delay);
        }).catch(function(err) {
            console.error('getUserMedia failed:', err);
        });
    }
}




function stopRecording() {
    clearInterval(recordingTimeout);

}


function analyzeRecording() {
    const recordedBlob = new Blob(recordedChunks, { 'type' : 'audio/webm; codecs=opus' });

    let formData = new FormData();
    formData.append("file", recordedBlob);
    recordedChunks = [];  // Clear the recorded chunks for the next recording

    // Send the recorded audio to the server
    fetch('/analyze', { method: 'POST', body: formData })
        .then(response => response.json())
        .then(data => {
            if ('recognized_notes' in data && Array.isArray(data.recognized_notes)) {
                let recognizedNotes = data.recognized_notes;

                    if(window.location.href.endsWith("chords.html")) {
                        playMode = "chords";
                    } else if(window.location.href.endsWith("notes.html")) {
                        playMode = "notes";
                    }

                if (playMode === "chords") {
                    let correct = false;
                    for (let num_notes = 3; num_notes <= 6; num_notes++) {
                        if (recognizedNotes.length >= num_notes) {
                            if (allNotesInChord(recognizedNotes.slice(0, num_notes), chords[currentChordIndexForRecording].notes)) {
                                correctChords+=1;
                                correct = true;
                                break;
                            }
                        }
                    }

                } else if (playMode === "notes") {
                    // For single notes, just compare the first recognized note to the correct note
                    if (allNotesInChord([recognizedNotes[0]], chords[currentChordIndexForRecording].notes)) {
                        correctChords+=1;
                    }
                }
            } else {
                console.error('Received undefined or non-array for recognized_notes');
            }
            currentChordIndexForRecording += 1;

            // Call `startRecording()` here to ensure it runs after `analyzeRecording`
            if (currentChordIndexForRecording < numChords) {
                startRecording();
            } else {
                document.getElementById("score-display").innerText = `Score: ${correctChords}/${numChords}`;
                correctChords = 0;
                totalChords = 0;
                currentChordIndexForRecording = 0;
            }
        })
        .catch(error => {
            console.error('Error:', error);
        });
}



function allNotesInChord(notes, chord) {
      let noteSet1 = new Set(notes.map(note =>
        note.toLowerCase().replace(/#/g, 's').replace(/_/g, '').slice(0, -1)
      ));
    
      let noteSet2 = new Set(chord.map(note =>
        note.slice(0, -1)
      ));
      console.log(noteSet1)
      console.log(noteSet2)


      // Check if all notes of noteSet1 are present in noteSet2
      for (let note of noteSet1) {
        if (!noteSet2.has(note)) {
          return false;
        }
      }
    
      // Check if all notes of noteSet2 are present in noteSet1
      for (let note of noteSet2) {
        if (!noteSet1.has(note)) {
          return false;
        }
      }
    
      return true;
}