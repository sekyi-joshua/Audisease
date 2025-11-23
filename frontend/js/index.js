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

        mediaRecorder.onstop = async () => {
            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            currentAudioBlob = audioBlob;
            console.log('Audio recorded:', audioBlob);
            
            // Upload and process the recorded audio
            await processAudio(audioBlob);
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
        }, 1000);
    } catch (error) {
        console.error('Error accessing microphone:', error);
        alert('Microphone access denied. Please allow microphone access and try again.');
    }
}

function stopRecording() {
    if (mediaRecorder && isRecording) {
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
        
        // Show processing screen
        setTimeout(() => {
            showScreen('processing-screen');
        }, 500);
    }
}

function resetRecording() {
    isRecording = false;
    recordingSeconds = 0;
    updateTimer();
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

// File Upload
async function handleFileUpload(event) {
    const file = event.target.files[0];
    if (file) {
        console.log('File selected:', file);
        currentAudioBlob = file;
        showScreen('processing-screen');
        await processAudio(file);
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
    const probability = result.percentage || 0;
    
    // Update gauge
    const circumference = 2 * Math.PI * 100; // radius = 100
    const offset = circumference - (probability / 100) * circumference;
    document.getElementById('gauge-circle').style.setProperty('--gauge-offset', offset);
    document.getElementById('gauge-circle').style.strokeDashoffset = offset;
    
    // Update percentage
    document.getElementById('probability-percentage').textContent = `${probability.toFixed(1)}%`;
    
    // Update metric bars with mock data (since API doesn't return these yet)
    // You can update these when the API returns more detailed metrics
    const metricBars = document.querySelectorAll('.metric-bar-fill');
    const metricValues = document.querySelectorAll('.metric-value');
    
    // For now, use placeholder values
    // In the future, you can extract these from the API response if available
    const metrics = [
        { value: 87, label: 'Voice Stability' },
        { value: 23, label: 'Pitch Variation' },
        { value: 8, label: 'Tremor' },
        { value: 15, label: 'Noise Ratio' }
    ];
    
    metricBars.forEach((bar, index) => {
        setTimeout(() => {
            bar.style.width = `${metrics[index].value}%`;
        }, index * 100);
    });
    
    // Update metric values if needed
    // metricValues.forEach((valueEl, index) => {
    //     valueEl.textContent = `${metrics[index].value}%`;
    // });
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

