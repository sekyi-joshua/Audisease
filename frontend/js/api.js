const API_BASE = "http://localhost:8000/api";

/**
 * Upload an audio file to the FastAPI predict endpoint
 * @param {File|Blob} audioFile - The audio file to upload
 * @returns {Promise<Object>} The prediction result from the API
 */
async function predictAudioFile(audioFile) {
    try {
        const formData = new FormData();
        formData.append('file', audioFile, 'audio.wav');

        const response = await fetch(`${API_BASE}/predict`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ detail: 'Unknown error' }));
            throw new Error(errorData.detail || `HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        return data;
    } catch (error) {
        console.error('Error predicting audio:', error);
        throw error;
    }
}
