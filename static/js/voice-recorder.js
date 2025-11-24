/**
 * Speech Verification Module
 * Uses browser's built-in Speech Recognition API for simple verification
 */

class SpeechVerifier {
    constructor() {
        this.recognition = null;
        this.isListening = false;
        this.targetPhrase = "";
    }

    /**
     * Initialize speech recognition
     */
    init() {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            throw new Error('Speech recognition not supported in this browser');
        }

        this.recognition = new SpeechRecognition();
        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = 'en-US';

        return true;
    }

    /**
     * Generate a random verification phrase
     */
    generatePhrase() {
        const words = [
            ['Hello', 'Hi', 'Greetings'],
            ['my name is', 'I am', 'this is'],
            ['attending', 'checking in', 'present'],
            ['today', 'now', 'here']
        ];

        const phrase = words.map(group => group[Math.floor(Math.random() * group.length)]).join(' ');
        this.targetPhrase = phrase;
        return phrase;
    }

    /**
     * Start listening for speech
     */
    startListening(onResult, onError) {
        if (!this.recognition) {
            onError('Speech recognition not initialized');
            return;
        }

        this.isListening = true;

        this.recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript.toLowerCase().trim();
            const confidence = event.results[0][0].confidence;

            // Simple matching - check if transcript contains key words from target phrase
            const targetWords = this.targetPhrase.toLowerCase().split(' ');
            const matchedWords = targetWords.filter(word => transcript.includes(word));
            const matchPercentage = (matchedWords.length / targetWords.length) * 100;

            onResult({
                transcript: transcript,
                confidence: confidence,
                matched: matchPercentage >= 60, // 60% word match threshold
                matchPercentage: matchPercentage
            });
        };

        this.recognition.onerror = (event) => {
            this.isListening = false;
            onError(event.error);
        };

        this.recognition.onend = () => {
            this.isListening = false;
        };

        try {
            this.recognition.start();
        } catch (e) {
            this.isListening = false;
            onError(e.message);
        }
    }

    /**
     * Stop listening
     */
    stopListening() {
        if (this.recognition && this.isListening) {
            this.recognition.stop();
            this.isListening = false;
        }
    }
}
