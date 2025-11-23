// Screen Management
function showScreen(screenId) {
    document.querySelectorAll('.screen').forEach(screen => {
        screen.classList.remove('active');
    });
    const targetScreen = document.getElementById(screenId);
    if (targetScreen) {
        targetScreen.classList.add('active');
        targetScreen.classList.add('slide-in');
        
        // Initialize screen-specific functionality
        if (screenId === 'recording-screen') {
            resetRecording();
        } else if (screenId === 'processing-screen') {
            startProcessing();
        } else if (screenId === 'results-screen') {
            displayResults();
        }
    }
}

// Recording Logic
let isRecording = false;
let recordingTimer = null;
let recordingSeconds = 0;
let mediaRecorder = null;
let audioChunks = [];
let currentAudioBlob = null;
let currentPredictionResult = null;
let audioContext = null;
let analyser = null;
let dataArray = null;
let animationFrameId = null;
let audioStream = null;

function toggleRecording() {
    if (!isRecording) {
        startRecording();
    } else {
        stopRecording();
    }
}

async function startRecording() {
    try {
        audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(audioStream);
        audioChunks = [];

        // Set up Web Audio API for visualization
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 256; // Higher value = more bars, but more processing
        const source = audioContext.createMediaStreamSource(audioStream);
        source.connect(analyser);
        
        const bufferLength = analyser.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);

        mediaRecorder.ondataavailable = (event) => {
            audioChunks.push(event.data);
        };

        mediaRecorder.onstop = () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            currentAudioBlob = audioBlob;
            console.log('Audio recorded:', audioBlob);
            // Processing will be triggered after the processing screen is shown
        };

        mediaRecorder.start();
        isRecording = true;
        document.getElementById('record-btn').classList.add('recording');
        document.getElementById('record-icon').textContent = '⏹';
        
        // Start waveform visualization
        visualizeWaveform();
        
        recordingSeconds = 0;
        recordingTimer = setInterval(() => {
            recordingSeconds++;
            updateTimer();
            updateDurationHint();
        }, 1000);
    } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('Microphone access denied. Please allow microphone access and try again.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
        // Validate recording duration before stopping
        if (recordingSeconds < 10) {
            alert(`Recording is too short. Please record for at least 10 seconds.\n\nCurrent duration: ${recordingSeconds} seconds`);
            return;
        }
        
        mediaRecorder.stop();
        
        // Stop audio visualization
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
            animationFrameId = null;
        }
        
        // Stop audio stream and clean up audio context
        if (audioStream) {
            audioStream.getTracks().forEach(track => track.stop());
            audioStream = null;
        }
        
        if (audioContext && audioContext.state !== 'closed') {
            audioContext.close();
            audioContext = null;
        }
        
        analyser = null;
        dataArray = null;
        
        // Reset waveform bars to default state
        resetWaveform();
        
        isRecording = false;
        document.getElementById('record-btn').classList.remove('recording');
        document.getElementById('record-icon').textContent = '🎤';
        
        if (recordingTimer) {
            clearInterval(recordingTimer);
        }
        
        // Show processing screen, then validate and process audio after a brief delay
        setTimeout(() => {
            showScreen('processing-screen');
            // Wait a bit for the screen transition to be visible, then validate and process
            setTimeout(async () => {
                if (currentAudioBlob) {
                    try {
                        // Validate audio volume before processing
                        await checkAudioVolume(currentAudioBlob);
                        await processAudio(currentAudioBlob);
                    } catch (error) {
                        console.error('Audio validation error:', error);
                        alert(`Audio validation failed: ${error.message}\n\nPlease try recording again with a working microphone and ensure you're speaking clearly.`);
                        showScreen('recording-screen');
                    }
                }
            }, 300);
        }, 500);
    }
}

function resetRecording() {
    isRecording = false;
    recordingSeconds = 0;
    updateTimer();
    updateDurationHint();
    document.getElementById('record-btn').classList.remove('recording');
    document.getElementById('record-icon').textContent = '🎤';
    if (recordingTimer) {
        clearInterval(recordingTimer);
    }
    
    // Stop any ongoing visualization
    if (animationFrameId) {
        cancelAnimationFrame(animationFrameId);
        animationFrameId = null;
    }
    
    // Clean up audio context if it exists
    if (audioContext && audioContext.state !== 'closed') {
        audioContext.close();
        audioContext = null;
    }
    
    if (audioStream) {
        audioStream.getTracks().forEach(track => track.stop());
        audioStream = null;
    }
    
    analyser = null;
    dataArray = null;
    resetWaveform();
}

// Waveform Visualization
function visualizeWaveform() {
    if (!analyser || !dataArray) return;
    
    analyser.getByteFrequencyData(dataArray);
    
    const waveformBars = document.querySelectorAll('.waveform-bar');
    const barCount = waveformBars.length;
    
    // Map frequency data to bars
    // We'll use different frequency ranges for each bar to create a more interesting visualization
    const step = Math.floor(dataArray.length / barCount);
    
    waveformBars.forEach((bar, index) => {
        // Get average amplitude for this bar's frequency range
        let sum = 0;
        const start = index * step;
        const end = Math.min(start + step, dataArray.length);
        
        for (let i = start; i < end; i++) {
            sum += dataArray[i];
        }
        
        const average = sum / (end - start);
        // Normalize to 0-100% (dataArray values are 0-255)
        const normalized = (average / 255) * 100;
        
        // Set minimum height and add some smoothing
        const minHeight = 20;
        const maxHeight = 200;
        const height = Math.max(minHeight, minHeight + (normalized / 100) * (maxHeight - minHeight));
        
        bar.style.height = `${height}px`;
        bar.style.opacity = Math.max(0.5, normalized / 100);
    });
    
    if (isRecording) {
        animationFrameId = requestAnimationFrame(visualizeWaveform);
    }
}

function resetWaveform() {
    const waveformBars = document.querySelectorAll('.waveform-bar');
    waveformBars.forEach(bar => {
        bar.style.height = '20px';
        bar.style.opacity = '0.5';
    });
}

function updateTimer() {
    const minutes = Math.floor(recordingSeconds / 60);
    const seconds = recordingSeconds % 60;
    document.getElementById('timer').textContent = 
        `${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
}

function updateDurationHint() {
    const hintEl = document.getElementById('duration-hint');
    if (!hintEl) return;
    
    if (recordingSeconds < 10) {
        const remaining = 10 - recordingSeconds;
        hintEl.textContent = `Minimum 10 seconds required (${remaining} more needed)`;
        hintEl.style.color = 'var(--warning)';
    } else {
        hintEl.textContent = '✓ Minimum duration met';
        hintEl.style.color = 'var(--success)';
    }
}

// Helper function to get audio duration
function getAudioDuration(audioFile) {
    return new Promise((resolve, reject) => {
        const audio = new Audio();
        const url = URL.createObjectURL(audioFile);
        
        audio.addEventListener('loadedmetadata', () => {
            URL.revokeObjectURL(url);
            resolve(audio.duration);
        });
        
        audio.addEventListener('error', (e) => {
            URL.revokeObjectURL(url);
            reject(new Error('Failed to load audio file'));
        });
        
        audio.src = url;
    });
}

// Helper function to check audio volume/amplitude
async function checkAudioVolume(audioFile) {
    return new Promise((resolve, reject) => {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const fileReader = new FileReader();
        
        fileReader.onload = async (e) => {
            try {
                const audioData = e.target.result;
                const audioBuffer = await audioContext.decodeAudioData(audioData);
                
                // Get the audio channel data (use first channel)
                const channelData = audioBuffer.getChannelData(0);
                
                // Calculate RMS (Root Mean Square) amplitude
                let sumSquares = 0;
                for (let i = 0; i < channelData.length; i++) {
                    sumSquares += channelData[i] * channelData[i];
                }
                const rms = Math.sqrt(sumSquares / channelData.length);
                
                // Also check peak amplitude
                let peak = 0;
                for (let i = 0; i < channelData.length; i++) {
                    const abs = Math.abs(channelData[i]);
                    if (abs > peak) {
                        peak = abs;
                    }
                }
                
                // Close audio context
                audioContext.close();
                
                // Threshold: RMS should be at least 0.01 (1% of max amplitude)
                // and peak should be at least 0.02 (2% of max amplitude)
                const minRMS = 0.01;
                const minPeak = 0.02;
                
                if (rms < minRMS || peak < minPeak) {
                    reject(new Error(`Audio volume is too low. Please ensure your microphone is working and you're speaking clearly.`));
                } else {
                    resolve({ rms, peak });
                }
            } catch (error) {
                audioContext.close();
                reject(new Error('Failed to analyze audio volume: ' + error.message));
            }
        };
        
        fileReader.onerror = () => {
            audioContext.close();
            reject(new Error('Failed to read audio file'));
        };
        
        fileReader.readAsArrayBuffer(audioFile);
    });
}

// File Upload
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        console.log('File selected:', file);
        
        // Validate file duration
        try {
            const duration = await getAudioDuration(file);
            if (duration < 10) {
                alert(`Audio file is too short. Please upload a file that is at least 10 seconds long.\n\nCurrent duration: ${duration.toFixed(1)} seconds`);
                // Reset file input
                event.target.value = '';
                return;
            }
        } catch (error) {
            console.error('Error checking audio duration:', error);
            alert('Unable to verify audio file duration. Please ensure the file is a valid audio file.');
            event.target.value = '';
            return;
        }
        
        currentAudioBlob = file;
        showScreen('processing-screen');
        // Wait a bit for the screen transition to be visible, then validate and process
        setTimeout(async () => {
            try {
                // Validate audio volume before processing
                await checkAudioVolume(file);
                await processAudio(file);
            } catch (error) {
                console.error('Audio validation error:', error);
                alert(`Audio validation failed: ${error.message}\n\nPlease upload an audio file with clear audio content.`);
                // Reset file input and go back to recording screen
                event.target.value = '';
                showScreen('recording-screen');
            }
        }, 300);
    }
}

// Processing
async function processAudio(audioFile) {
    try {
        const result = await predictAudioFile(audioFile);
        currentPredictionResult = result;
        showScreen('results-screen');
    } catch (error) {
        console.error('Error processing audio:', error);
        alert(`Error processing audio: ${error.message}\n\nPlease make sure the backend is running at http://localhost:8000`);
        // Go back to recording screen on error
        showScreen('recording-screen');
    }
}

function startProcessing() {
    // This function is called when processing screen is shown
    // The actual processing happens in processAudio()
}

// Results Display
function displayResults() {
    if (!currentPredictionResult) {
        console.warn('No prediction result available');
        return;
    }
    
    const result = currentPredictionResult;
    const probability = result.percentage || result.probability * 100 || 0;
    
    // Update gauge
    const circumference = 2 * Math.PI * 100; // radius = 100
    const offset = circumference - (probability / 100) * circumference;
    document.getElementById('gauge-circle').style.setProperty('--gauge-offset', offset);
    document.getElementById('gauge-circle').style.strokeDashoffset = offset;
    
    // Update percentage
    document.getElementById('probability-percentage').textContent = `${probability.toFixed(1)}%`;
    
    // Update disclaimer if provided by API
    if (result.disclaimer) {
        const disclaimerEl = document.getElementById('disclaimer-text');
        if (disclaimerEl) {
            disclaimerEl.innerHTML = `<strong>⚠️ Important:</strong> ${result.disclaimer}`;
        }
    }
    
    // Update explanation text with classification if available
    if (result.classification) {
        const explanationEl = document.getElementById('explanation-text');
        if (explanationEl) {
            const classificationText = result.classification === 'parkinsons_likely' 
                ? 'The analysis suggests possible Parkinson\'s-related voice characteristics.'
                : 'The analysis suggests minimal Parkinson\'s-related voice characteristics.';
            explanationEl.innerHTML = `<strong>What this means:</strong><br>${classificationText} This percentage represents the likelihood based on your voice sample. This is not a medical diagnosis. Please consult a healthcare professional for any health concerns.`;
        }
    }
}

// Save Result
function saveResult() {
    // Here you would save the result to your backend
    console.log('Saving result...');
    alert('Result saved! (This is a placeholder - implement backend integration)');
}

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // Any initialization code
});

