/**
 * Face Verification Module
 * Handles face detection, enrollment, and verification using face-api.js
 */

class FaceVerification {
    constructor() {
        this.modelsLoaded = false;
        this.video = null;
        this.canvas = null;
        this.faceDescriptor = null;
        this.isProcessing = false;
    }

    /**
     * Load face-api.js models
     */
    async loadModels() {
        if (this.modelsLoaded) return;

        // Use CDN for models - more reliable than local hosting
        const MODEL_URL = 'https://cdn.jsdelivr.net/npm/@vladmandic/face-api/model';

        try {
            await Promise.all([
                faceapi.nets.tinyFaceDetector.loadFromUri(MODEL_URL),
                faceapi.nets.faceLandmark68Net.loadFromUri(MODEL_URL),
                faceapi.nets.faceRecognitionNet.loadFromUri(MODEL_URL)
            ]);

            this.modelsLoaded = true;
            console.log('Face-api models loaded successfully');
            return true;
        } catch (error) {
            console.error('Error loading models:', error);
            throw new Error('Failed to load face recognition models');
        }
    }

    /**
     * Initialize camera and video stream
     */
    async startVideo(videoElement) {
        this.video = videoElement;

        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                video: {
                    width: { ideal: 640 },
                    height: { ideal: 480 },
                    facingMode: 'user'
                }
            });

            this.video.srcObject = stream;

            return new Promise((resolve) => {
                this.video.onloadedmetadata = () => {
                    this.video.play();
                    resolve();
                };
            });
        } catch (error) {
            console.error('Error accessing camera:', error);
            throw new Error('Failed to access camera. Please grant camera permissions.');
        }
    }

    /**
     * Stop video stream
     */
    stopVideo() {
        if (this.video && this.video.srcObject) {
            const tracks = this.video.srcObject.getTracks();
            tracks.forEach(track => track.stop());
            this.video.srcObject = null;
        }
    }

    /**
     * Detect face and extract descriptor
     */
    async detectFace() {
        if (!this.video || this.isProcessing) return null;

        this.isProcessing = true;

        try {
            const detections = await faceapi
                .detectSingleFace(this.video, new faceapi.TinyFaceDetectorOptions())
                .withFaceLandmarks()
                .withFaceDescriptor();

            this.isProcessing = false;
            return detections;
        } catch (error) {
            console.error('Error detecting face:', error);
            this.isProcessing = false;
            return null;
        }
    }

    /**
     * Capture face descriptor for enrollment
     */
    async captureFaceDescriptor() {
        const detection = await this.detectFace();

        if (!detection) {
            throw new Error('No face detected. Please ensure your face is clearly visible.');
        }

        this.faceDescriptor = Array.from(detection.descriptor);
        return this.faceDescriptor;
    }

    /**
     * Verify face against stored descriptor
     */
    async verifyFace(storedDescriptor) {
        const detection = await this.detectFace();

        if (!detection) {
            return { verified: false, error: 'No face detected' };
        }

        const currentDescriptor = detection.descriptor;
        const distance = faceapi.euclideanDistance(currentDescriptor, storedDescriptor);

        // Threshold: 0.6 is a common value (lower = more strict)
        const threshold = 0.6;
        const verified = distance < threshold;

        return {
            verified,
            distance,
            threshold,
            confidence: Math.max(0, (1 - distance) * 100).toFixed(1)
        };
    }

    /**
     * Draw face detection box on canvas
     */
    drawDetection(detection, canvas) {
        if (!detection || !canvas) return;

        const ctx = canvas.getContext('2d');
        const displaySize = { width: canvas.width, height: canvas.height };

        faceapi.matchDimensions(canvas, displaySize);

        const resizedDetections = faceapi.resizeResults(detection, displaySize);

        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Draw box
        faceapi.draw.drawDetections(canvas, resizedDetections);

        // Draw landmarks
        faceapi.draw.drawFaceLandmarks(canvas, resizedDetections);
    }

    /**
     * Continuous face detection with callback
     */
    startContinuousDetection(onDetection, interval = 500) {
        const detect = async () => {
            const detection = await this.detectFace();
            if (onDetection) {
                onDetection(detection);
            }
        };

        const intervalId = setInterval(detect, interval);
        return intervalId;
    }

    /**
     * Stop continuous detection
     */
    stopContinuousDetection(intervalId) {
        if (intervalId) {
            clearInterval(intervalId);
        }
    }
}

// Export for use in other scripts
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FaceVerification;
}
