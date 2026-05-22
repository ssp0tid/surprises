class CanvasManager {
    constructor(canvasEl, containerEl) {
        this.canvas = canvasEl;
        this.ctx = canvasEl.getContext("2d");
        this.container = containerEl;
        this.width = 16;
        this.height = 16;
        this.zoom = 8;
        this.panX = 0;
        this.panY = 0;
        this.showGrid = true;
        this.isPanning = false;
        this.lastPanPos = null;
        this.spaceHeld = false;

        this._bindEvents();
        this.resize();
    }

    setSize(w, h) {
        this.width = w;
        this.height = h;
        this.zoom = Math.min(Math.floor(Math.min(
            this.container.clientWidth / w,
            this.container.clientHeight / h
        ) * 0.8), 32);
        this.panX = 0;
        this.panY = 0;
        this.resize();
    }

    resize() {
        const dpr = window.devicePixelRatio || 1;
        const displayW = this.container.clientWidth;
        const displayH = this.container.clientHeight;
        this.canvas.width = displayW * dpr;
        this.canvas.height = displayH * dpr;
        this.canvas.style.width = displayW + "px";
        this.canvas.style.height = displayH + "px";
        this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
        this.render();
    }

    getOrigin() {
        const totalW = this.width * this.zoom;
        const totalH = this.height * this.zoom;
        const ox = (this.container.clientWidth - totalW) / 2 + this.panX;
        const oy = (this.container.clientHeight - totalH) / 2 + this.panY;
        return { ox, oy };
    }

    canvasToPixel(clientX, clientY) {
        const rect = this.canvas.getBoundingClientRect();
        const mx = clientX - rect.left;
        const my = clientY - rect.top;
        const { ox, oy } = this.getOrigin();
        const px = Math.floor((mx - ox) / this.zoom);
        const py = Math.floor((my - oy) / this.zoom);
        return { x: px, y: py };
    }

    isInBounds(x, y) {
        return x >= 0 && x < this.width && y >= 0 && y < this.height;
    }

    render() {
        const ctx = this.ctx;
        const { ox, oy } = this.getOrigin();
        const totalW = this.width * this.zoom;
        const totalH = this.height * this.zoom;

        ctx.clearRect(0, 0, this.container.clientWidth, this.container.clientHeight);

        // Transparency checkerboard background
        const checkSize = this.zoom < 4 ? this.zoom : Math.max(4, this.zoom / 2);
        for (let y = 0; y < this.height; y++) {
            for (let x = 0; x < this.width; x++) {
                const isLight = (x + y) % 2 === 0;
                ctx.fillStyle = isLight ? "#ffffff" : "#cccccc";
                ctx.fillRect(ox + x * this.zoom, oy + y * this.zoom, this.zoom, this.zoom);
            }
        }

        // Render layers (composited by app.js)
        if (window.AppState && window.AppState.compositeImageData) {
            const tempCanvas = document.createElement("canvas");
            tempCanvas.width = this.width;
            tempCanvas.height = this.height;
            const tempCtx = tempCanvas.getContext("2d");
            tempCtx.putImageData(window.AppState.compositeImageData, 0, 0);

            ctx.imageSmoothingEnabled = false;
            ctx.drawImage(tempCanvas, ox, oy, totalW, totalH);
        }

        // Grid overlay
        if (this.showGrid && this.zoom >= 4) {
            ctx.strokeStyle = "rgba(255,255,255,0.15)";
            ctx.lineWidth = 0.5;
            ctx.beginPath();
            for (let x = 0; x <= this.width; x++) {
                ctx.moveTo(ox + x * this.zoom, oy);
                ctx.lineTo(ox + x * this.zoom, oy + totalH);
            }
            for (let y = 0; y <= this.height; y++) {
                ctx.moveTo(ox, oy + y * this.zoom);
                ctx.lineTo(ox + totalW, oy + y * this.zoom);
            }
            ctx.stroke();
        }

        // Canvas border
        ctx.strokeStyle = "rgba(139, 92, 246, 0.5)";
        ctx.lineWidth = 1;
        ctx.strokeRect(ox - 0.5, oy - 0.5, totalW + 1, totalH + 1);
    }

    _bindEvents() {
        this.canvas.addEventListener("wheel", (e) => {
            e.preventDefault();
            const oldZoom = this.zoom;
            if (e.deltaY < 0) {
                this.zoom = Math.min(32, this.zoom + (this.zoom < 8 ? 1 : 2));
            } else {
                this.zoom = Math.max(1, this.zoom - (this.zoom <= 8 ? 1 : 2));
            }
            if (this.zoom !== oldZoom) {
                const rect = this.canvas.getBoundingClientRect();
                const mx = e.clientX - rect.left;
                const my = e.clientY - rect.top;
                const { ox, oy } = this.getOrigin();
                this.panX += (mx - ox) * (1 - this.zoom / oldZoom);
                this.panY += (my - oy) * (1 - this.zoom / oldZoom);
                this._updateZoomIndicator();
                this.render();
            }
        }, { passive: false });

        this.canvas.addEventListener("mousedown", (e) => {
            if (e.button === 1 || this.spaceHeld) {
                this.isPanning = true;
                this.lastPanPos = { x: e.clientX, y: e.clientY };
                e.preventDefault();
            }
        });

        window.addEventListener("mousemove", (e) => {
            if (this.isPanning && this.lastPanPos) {
                this.panX += e.clientX - this.lastPanPos.x;
                this.panY += e.clientY - this.lastPanPos.y;
                this.lastPanPos = { x: e.clientX, y: e.clientY };
                this.render();
            }
        });

        window.addEventListener("mouseup", () => {
            this.isPanning = false;
            this.lastPanPos = null;
        });

        window.addEventListener("keydown", (e) => {
            if (e.code === "Space") {
                this.spaceHeld = true;
                this.canvas.style.cursor = "grab";
            }
        });

        window.addEventListener("keyup", (e) => {
            if (e.code === "Space") {
                this.spaceHeld = false;
                this.canvas.style.cursor = "";
            }
        });

        window.addEventListener("resize", () => this.resize());
    }

    _updateZoomIndicator() {
        const el = document.getElementById("zoom-indicator");
        if (el) el.textContent = this.zoom + "x";
    }

    setGrid(show) {
        this.showGrid = show;
        this.render();
    }

    zoomIn() {
        this.zoom = Math.min(32, this.zoom + (this.zoom < 8 ? 1 : 2));
        this._updateZoomIndicator();
        this.render();
    }

    zoomOut() {
        this.zoom = Math.max(1, this.zoom - (this.zoom <= 8 ? 1 : 2));
        this._updateZoomIndicator();
        this.render();
    }
}

window.CanvasManager = CanvasManager;
