class AnimationManager {
    constructor() {
        this.stripEl = document.getElementById("frames-strip");
        this.playbackCanvas = document.getElementById("playback-canvas");
        this.playbackCtx = this.playbackCanvas.getContext("2d");
        this.isPlaying = false;
        this.playbackTimer = null;
    }

    renderStrip() {
        const state = window.AppState;
        this.stripEl.innerHTML = "";

        state.frames.forEach((frame, idx) => {
            const thumb = document.createElement("canvas");
            thumb.width = 48;
            thumb.height = 48;
            thumb.className = "frame-thumb" + (idx === state.activeFrameIdx ? " active" : "");
            thumb.dataset.idx = idx;

            const ctx = thumb.getContext("2d");
            ctx.imageSmoothingEnabled = false;

            const tempCanvas = document.createElement("canvas");
            tempCanvas.width = state.canvasManager.width;
            tempCanvas.height = state.canvasManager.height;
            const tempCtx = tempCanvas.getContext("2d");
            const imgData = this._compositeFrame(frame);
            tempCtx.putImageData(imgData, 0, 0);
            ctx.drawImage(tempCanvas, 0, 0, 48, 48);

            thumb.addEventListener("click", () => {
                state.activeFrameIdx = idx;
                state.activeLayerIdx = Math.min(state.activeLayerIdx, frame.layers.length - 1);
                state.composite();
                this.renderStrip();
                state.layerManager.renderList();
            });

            this.stripEl.appendChild(thumb);
        });
    }

    addFrame() {
        const state = window.AppState;
        if (state.frames.length >= 64) return;

        const w = state.canvasManager.width;
        const h = state.canvasManager.height;
        const newFrame = {
            id: Date.now(),
            duration: 100,
            layers: [{
                id: Date.now() + 1,
                name: "Layer 1",
                pixels: new Uint8ClampedArray(w * h * 4),
                opacity: 100,
                visible: true
            }]
        };
        state.frames.splice(state.activeFrameIdx + 1, 0, newFrame);
        state.activeFrameIdx++;
        state.activeLayerIdx = 0;
        state.composite();
        this.renderStrip();
        state.layerManager.renderList();
    }

    duplicateFrame() {
        const state = window.AppState;
        if (state.frames.length >= 64) return;

        const src = state.getCurrentFrame();
        const dup = {
            id: Date.now(),
            duration: src.duration,
            layers: src.layers.map(l => ({
                id: Date.now() + Math.random(),
                name: l.name,
                pixels: new Uint8ClampedArray(l.pixels),
                opacity: l.opacity,
                visible: l.visible
            }))
        };
        state.frames.splice(state.activeFrameIdx + 1, 0, dup);
        state.activeFrameIdx++;
        state.composite();
        this.renderStrip();
        state.layerManager.renderList();
    }

    deleteFrame() {
        const state = window.AppState;
        if (state.frames.length <= 1) return;

        state.frames.splice(state.activeFrameIdx, 1);
        if (state.activeFrameIdx >= state.frames.length) {
            state.activeFrameIdx = state.frames.length - 1;
        }
        state.activeLayerIdx = 0;
        state.composite();
        this.renderStrip();
        state.layerManager.renderList();
    }

    play() {
        if (this.isPlaying) {
            this.stop();
            return;
        }

        const state = window.AppState;
        if (state.frames.length < 2) return;

        this.isPlaying = true;
        const modal = document.getElementById("modal-playback");
        modal.classList.remove("hidden");

        const scale = 4;
        this.playbackCanvas.width = state.canvasManager.width * scale;
        this.playbackCanvas.height = state.canvasManager.height * scale;
        this.playbackCtx.imageSmoothingEnabled = false;

        let frameIdx = 0;
        const playFrame = () => {
            if (!this.isPlaying) return;
            const frame = state.frames[frameIdx];
            const imgData = this._compositeFrame(frame);

            const tempCanvas = document.createElement("canvas");
            tempCanvas.width = state.canvasManager.width;
            tempCanvas.height = state.canvasManager.height;
            tempCanvas.getContext("2d").putImageData(imgData, 0, 0);

            this.playbackCtx.clearRect(0, 0, this.playbackCanvas.width, this.playbackCanvas.height);
            this.playbackCtx.drawImage(tempCanvas, 0, 0, this.playbackCanvas.width, this.playbackCanvas.height);

            frameIdx = (frameIdx + 1) % state.frames.length;
            this.playbackTimer = setTimeout(playFrame, frame.duration);
        };
        playFrame();
    }

    stop() {
        this.isPlaying = false;
        if (this.playbackTimer) {
            clearTimeout(this.playbackTimer);
            this.playbackTimer = null;
        }
        document.getElementById("modal-playback").classList.add("hidden");
    }

    _compositeFrame(frame) {
        const state = window.AppState;
        const w = state.canvasManager.width;
        const h = state.canvasManager.height;
        const result = new ImageData(w, h);

        for (const layer of frame.layers) {
            if (!layer.visible || !layer.pixels) continue;
            const opacity = layer.opacity / 100;

            for (let i = 0; i < w * h * 4; i += 4) {
                const srcA = (layer.pixels[i + 3] / 255) * opacity;
                if (srcA === 0) continue;

                const dstA = result.data[i + 3] / 255;
                const outA = srcA + dstA * (1 - srcA);

                if (outA > 0) {
                    result.data[i] = Math.round((layer.pixels[i] * srcA + result.data[i] * dstA * (1 - srcA)) / outA);
                    result.data[i + 1] = Math.round((layer.pixels[i + 1] * srcA + result.data[i + 1] * dstA * (1 - srcA)) / outA);
                    result.data[i + 2] = Math.round((layer.pixels[i + 2] * srcA + result.data[i + 2] * dstA * (1 - srcA)) / outA);
                    result.data[i + 3] = Math.round(outA * 255);
                }
            }
        }
        return result;
    }

    renderOnionSkin(compositeData) {
        const state = window.AppState;
        if (!state.onionSkinning) return compositeData;

        const w = state.canvasManager.width;
        const h = state.canvasManager.height;
        const result = new ImageData(new Uint8ClampedArray(compositeData.data), w, h);

        const prevIdx = state.activeFrameIdx - 1;
        if (prevIdx >= 0) {
            const prevFrame = state.frames[prevIdx];
            const prevData = this._compositeFrame(prevFrame);
            const ghostAlpha = 0.3;

            for (let i = 0; i < w * h * 4; i += 4) {
                if (prevData.data[i + 3] === 0) continue;
                const srcA = (prevData.data[i + 3] / 255) * ghostAlpha;
                const dstA = result.data[i + 3] / 255;
                const outA = srcA + dstA * (1 - srcA);

                if (outA > 0) {
                    result.data[i] = Math.round((prevData.data[i] * srcA + result.data[i] * dstA * (1 - srcA)) / outA);
                    result.data[i + 1] = Math.round((prevData.data[i + 1] * srcA + result.data[i + 1] * dstA * (1 - srcA)) / outA);
                    result.data[i + 2] = Math.round((prevData.data[i + 2] * srcA + result.data[i + 2] * dstA * (1 - srcA)) / outA);
                    result.data[i + 3] = Math.round(outA * 255);
                }
            }
        }

        return result;
    }

    getFrameDuration() {
        const state = window.AppState;
        const frame = state.getCurrentFrame();
        return frame ? frame.duration : 100;
    }

    setFrameDuration(ms) {
        const state = window.AppState;
        const frame = state.getCurrentFrame();
        if (frame) {
            frame.duration = Math.max(16, Math.min(5000, ms));
        }
    }
}

window.AnimationManager = AnimationManager;
