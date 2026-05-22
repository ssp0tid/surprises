class PaletteManager {
    constructor() {
        this.hue = 0;
        this.saturation = 100;
        this.lightness = 50;
        this.recentColors = [];
        this.maxRecent = 16;

        this.presetColors = [
            "#000000", "#1d2b53", "#7e2553", "#008751",
            "#ab5236", "#5f574f", "#c2c3c7", "#fff1e8",
            "#ff004d", "#ffa300", "#ffec27", "#00e436",
            "#29adff", "#83769c", "#ff77a8", "#ffccaa"
        ];

        this.hueCanvas = document.getElementById("hue-wheel");
        this.hueCtx = this.hueCanvas ? this.hueCanvas.getContext("2d") : null;
        this.hexInput = document.getElementById("hex-input");
        this.slSquare = document.getElementById("sl-square");
        this.presetEl = document.getElementById("preset-colors");
        this.recentEl = document.getElementById("recent-colors");

        if (this.presetEl) this._renderPresets();
        if (this.hueCanvas) this._renderHueWheel();
        if (this.slSquare) this._renderSLSquare();
        this._bindEvents();
    }

    _renderPresets() {
        this.presetEl.innerHTML = "";
        this.presetColors.forEach(color => {
            const swatch = document.createElement("div");
            swatch.className = "w-5 h-5 rounded cursor-pointer border border-gray-600 hover:border-white";
            swatch.style.backgroundColor = color;
            swatch.addEventListener("click", () => {
                window.AppState.setForegroundColor(color);
            });
            this.presetEl.appendChild(swatch);
        });
    }

    _renderHueWheel() {
        if (!this.hueCtx) return;
        const ctx = this.hueCtx;
        const w = this.hueCanvas.width;
        const h = this.hueCanvas.height;
        const cx = w / 2, cy = h / 2;
        const outerR = Math.min(cx, cy) - 2;
        const innerR = outerR - 15;

        ctx.clearRect(0, 0, w, h);

        for (let angle = 0; angle < 360; angle++) {
            const startAngle = (angle - 1) * Math.PI / 180;
            const endAngle = (angle + 1) * Math.PI / 180;
            ctx.beginPath();
            ctx.arc(cx, cy, outerR, startAngle, endAngle);
            ctx.arc(cx, cy, innerR, endAngle, startAngle, true);
            ctx.closePath();
            ctx.fillStyle = `hsl(${angle}, 100%, 50%)`;
            ctx.fill();
        }

        const indicatorAngle = this.hue * Math.PI / 180;
        const midR = (outerR + innerR) / 2;
        const ix = cx + Math.cos(indicatorAngle) * midR;
        const iy = cy + Math.sin(indicatorAngle) * midR;
        ctx.beginPath();
        ctx.arc(ix, iy, 5, 0, Math.PI * 2);
        ctx.strokeStyle = "#fff";
        ctx.lineWidth = 2;
        ctx.stroke();
    }

    _renderSLSquare() {
        if (!this.slSquare) return;
        const size = 64;
        this.slSquare.style.width = size + "px";
        this.slSquare.style.height = size + "px";
        this.slSquare.style.background =
            `linear-gradient(to bottom, transparent, black), ` +
            `linear-gradient(to right, white, hsl(${this.hue}, 100%, 50%))`;
    }

    renderRecentColors() {
        if (!this.recentEl) return;
        this.recentEl.innerHTML = "";
        this.recentColors.forEach(color => {
            const swatch = document.createElement("div");
            swatch.className = "w-5 h-5 rounded cursor-pointer border border-gray-600 hover:border-white";
            swatch.style.backgroundColor = color;
            swatch.addEventListener("click", () => {
                window.AppState.setForegroundColor(color);
            });
            this.recentEl.appendChild(swatch);
        });
    }

    addRecentColor(color) {
        const idx = this.recentColors.indexOf(color);
        if (idx !== -1) this.recentColors.splice(idx, 1);
        this.recentColors.unshift(color);
        if (this.recentColors.length > this.maxRecent) {
            this.recentColors.pop();
        }
        this.renderRecentColors();
    }

    _bindEvents() {
        if (this.hueCanvas) {
            this.hueCanvas.addEventListener("mousedown", (e) => {
                this._pickHue(e);
                const onMove = (ev) => this._pickHue(ev);
                const onUp = () => {
                    window.removeEventListener("mousemove", onMove);
                    window.removeEventListener("mouseup", onUp);
                };
                window.addEventListener("mousemove", onMove);
                window.addEventListener("mouseup", onUp);
            });
        }

        if (this.slSquare) {
            this.slSquare.addEventListener("mousedown", (e) => {
                this._pickSL(e);
                const onMove = (ev) => this._pickSL(ev);
                const onUp = () => {
                    window.removeEventListener("mousemove", onMove);
                    window.removeEventListener("mouseup", onUp);
                };
                window.addEventListener("mousemove", onMove);
                window.addEventListener("mouseup", onUp);
            });
        }

        if (this.hexInput) {
            this.hexInput.addEventListener("change", () => {
                let val = this.hexInput.value.trim();
                if (!val.startsWith("#")) val = "#" + val;
                if (/^#[0-9a-fA-F]{6}$/.test(val)) {
                    window.AppState.setForegroundColor(val);
                }
            });
        }
    }

    _pickHue(e) {
        const rect = this.hueCanvas.getBoundingClientRect();
        const x = e.clientX - rect.left - rect.width / 2;
        const y = e.clientY - rect.top - rect.height / 2;
        this.hue = (Math.atan2(y, x) * 180 / Math.PI + 360) % 360;
        this._renderHueWheel();
        this._renderSLSquare();
        this._updateColorFromHSL();
    }

    _pickSL(e) {
        const rect = this.slSquare.getBoundingClientRect();
        const x = Math.max(0, Math.min(1, (e.clientX - rect.left) / rect.width));
        const y = Math.max(0, Math.min(1, (e.clientY - rect.top) / rect.height));
        this.saturation = x * 100;
        this.lightness = (1 - y) * 50 + (1 - x) * (1 - y) * 50;
        this._updateColorFromHSL();
    }

    _updateColorFromHSL() {
        const color = this._hslToHex(this.hue, this.saturation, this.lightness);
        window.AppState.setForegroundColor(color);
    }

    setFromHex(hex) {
        if (this.hexInput) this.hexInput.value = hex;
        const { h, s, l } = this._hexToHSL(hex);
        this.hue = h;
        this.saturation = s;
        this.lightness = l;
        this._renderHueWheel();
        this._renderSLSquare();
    }

    _hslToHex(h, s, l) {
        s /= 100;
        l /= 100;
        const a = s * Math.min(l, 1 - l);
        const f = (n) => {
            const k = (n + h / 30) % 12;
            const color = l - a * Math.max(Math.min(k - 3, 9 - k, 1), -1);
            return Math.round(255 * color).toString(16).padStart(2, "0");
        };
        return `#${f(0)}${f(8)}${f(4)}`;
    }

    _hexToHSL(hex) {
        let r = parseInt(hex.slice(1, 3), 16) / 255;
        let g = parseInt(hex.slice(3, 5), 16) / 255;
        let b = parseInt(hex.slice(5, 7), 16) / 255;

        const max = Math.max(r, g, b), min = Math.min(r, g, b);
        let h = 0, s = 0, l = (max + min) / 2;

        if (max !== min) {
            const d = max - min;
            s = l > 0.5 ? d / (2 - max - min) : d / (max + min);
            switch (max) {
                case r: h = ((g - b) / d + (g < b ? 6 : 0)) * 60; break;
                case g: h = ((b - r) / d + 2) * 60; break;
                case b: h = ((r - g) / d + 4) * 60; break;
            }
        }

        return { h, s: s * 100, l: l * 100 };
    }
}

window.PaletteManager = PaletteManager;
