class ToolManager {
    constructor() {
        this.tools = {};
        this.activeTool = null;
        this.activeToolName = "";
    }

    register(name, tool) {
        this.tools[name] = tool;
    }

    setActive(name) {
        if (this.tools[name]) {
            this.activeTool = this.tools[name];
            this.activeToolName = name;
            document.querySelectorAll(".tool-btn").forEach(btn => {
                btn.classList.toggle("active", btn.dataset.tool === name);
            });
        }
    }

    onMouseDown(x, y, e) {
        if (this.activeTool && this.activeTool.onMouseDown) {
            this.activeTool.onMouseDown(x, y, e);
        }
    }

    onMouseMove(x, y, e) {
        if (this.activeTool && this.activeTool.onMouseMove) {
            this.activeTool.onMouseMove(x, y, e);
        }
    }

    onMouseUp(x, y, e) {
        if (this.activeTool && this.activeTool.onMouseUp) {
            this.activeTool.onMouseUp(x, y, e);
        }
    }
}

class PencilTool {
    constructor() {
        this.drawing = false;
        this.lastPos = null;
    }

    onMouseDown(x, y, e) {
        this.drawing = true;
        this.lastPos = { x, y };
        const state = window.AppState;
        const layer = state.getActiveLayer();
        if (!layer || !layer.visible) return;
        const w = state.canvasManager.width;
        const rgba = hexToRGBA(state.foregroundColor);
        this._drawPixel(x, y, layer, w, rgba);
        state.composite();
    }

    onMouseMove(x, y, e) {
        if (!this.drawing) return;
        if (this.lastPos) {
            this._drawLine(this.lastPos.x, this.lastPos.y, x, y);
        }
        this.lastPos = { x, y };
    }

    onMouseUp(x, y, e) {
        this.drawing = false;
        this.lastPos = null;
        window.AppState.pushUndo();
    }

    _drawPixel(x, y, layer, w, rgba) {
        const state = window.AppState;
        if (!state.canvasManager.isInBounds(x, y)) return;
        const idx = (y * w + x) * 4;
        layer.pixels[idx] = rgba.r;
        layer.pixels[idx + 1] = rgba.g;
        layer.pixels[idx + 2] = rgba.b;
        layer.pixels[idx + 3] = rgba.a;
    }

    _drawLine(x0, y0, x1, y1) {
        const state = window.AppState;
        const layer = state.getActiveLayer();
        if (!layer || !layer.visible) return;
        const w = state.canvasManager.width;
        const rgba = hexToRGBA(state.foregroundColor);
        const points = bresenhamLine(x0, y0, x1, y1);
        for (const p of points) {
            this._drawPixel(p.x, p.y, layer, w, rgba);
        }
        state.composite();
    }
}

class EraserTool {
    constructor() {
        this.drawing = false;
        this.lastPos = null;
    }

    onMouseDown(x, y) {
        this.drawing = true;
        this.lastPos = { x, y };
        this._erase(x, y);
    }

    onMouseMove(x, y) {
        if (!this.drawing) return;
        if (this.lastPos) {
            const points = bresenhamLine(this.lastPos.x, this.lastPos.y, x, y);
            for (const p of points) this._erase(p.x, p.y);
        }
        this.lastPos = { x, y };
    }

    onMouseUp() {
        this.drawing = false;
        this.lastPos = null;
        window.AppState.pushUndo();
    }

    _erase(x, y) {
        const state = window.AppState;
        if (!state.canvasManager.isInBounds(x, y)) return;
        const layer = state.getActiveLayer();
        if (!layer || !layer.visible) return;
        const idx = (y * state.canvasManager.width + x) * 4;
        layer.pixels[idx] = 0;
        layer.pixels[idx + 1] = 0;
        layer.pixels[idx + 2] = 0;
        layer.pixels[idx + 3] = 0;
        state.composite();
    }
}

class FillTool {
    onMouseDown(x, y) {
        const state = window.AppState;
        if (!state.canvasManager.isInBounds(x, y)) return;
        const layer = state.getActiveLayer();
        if (!layer || !layer.visible) return;

        const w = state.canvasManager.width;
        const h = state.canvasManager.height;
        const pixels = layer.pixels;
        const idx = (y * w + x) * 4;
        const targetR = pixels[idx], targetG = pixels[idx + 1], targetB = pixels[idx + 2], targetA = pixels[idx + 3];
        const fill = hexToRGBA(state.foregroundColor);

        if (targetR === fill.r && targetG === fill.g && targetB === fill.b && targetA === fill.a) return;

        const visited = new Uint8Array(w * h);
        const queue = [x, y];
        let head = 0;
        visited[y * w + x] = 1;

        while (head < queue.length) {
            const cx = queue[head++];
            const cy = queue[head++];
            const ci = (cy * w + cx) * 4;
            pixels[ci] = fill.r;
            pixels[ci + 1] = fill.g;
            pixels[ci + 2] = fill.b;
            pixels[ci + 3] = fill.a;

            const neighbors = [cx - 1, cy, cx + 1, cy, cx, cy - 1, cx, cy + 1];
            for (let i = 0; i < 8; i += 2) {
                const nx = neighbors[i], ny = neighbors[i + 1];
                if (nx < 0 || nx >= w || ny < 0 || ny >= h) continue;
                const ni = ny * w + nx;
                if (visited[ni]) continue;
                const pi = ni * 4;
                if (pixels[pi] === targetR && pixels[pi + 1] === targetG &&
                    pixels[pi + 2] === targetB && pixels[pi + 3] === targetA) {
                    visited[ni] = 1;
                    queue.push(nx, ny);
                }
            }
        }

        state.composite();
        state.pushUndo();
    }

    onMouseMove() {}
    onMouseUp() {}
}

class LineTool {
    constructor() {
        this.startPos = null;
        this.drawing = false;
        this.previewPixels = null;
    }

    onMouseDown(x, y) {
        this.drawing = true;
        this.startPos = { x, y };
        this.previewPixels = new Uint8ClampedArray(window.AppState.getActiveLayer().pixels);
    }

    onMouseMove(x, y) {
        if (!this.drawing) return;
        const state = window.AppState;
        const layer = state.getActiveLayer();
        layer.pixels.set(this.previewPixels);
        const points = bresenhamLine(this.startPos.x, this.startPos.y, x, y);
        const color = hexToRGBA(state.foregroundColor);
        const w = state.canvasManager.width;
        for (const p of points) {
            if (!state.canvasManager.isInBounds(p.x, p.y)) continue;
            const idx = (p.y * w + p.x) * 4;
            layer.pixels[idx] = color.r;
            layer.pixels[idx + 1] = color.g;
            layer.pixels[idx + 2] = color.b;
            layer.pixels[idx + 3] = color.a;
        }
        state.composite();
    }

    onMouseUp(x, y) {
        if (!this.drawing) return;
        this.drawing = false;
        this.previewPixels = null;
        window.AppState.pushUndo();
    }
}

class RectTool {
    constructor() {
        this.startPos = null;
        this.drawing = false;
        this.previewPixels = null;
    }

    onMouseDown(x, y) {
        this.drawing = true;
        this.startPos = { x, y };
        this.previewPixels = new Uint8ClampedArray(window.AppState.getActiveLayer().pixels);
    }

    onMouseMove(x, y, e) {
        if (!this.drawing) return;
        const state = window.AppState;
        const layer = state.getActiveLayer();
        layer.pixels.set(this.previewPixels);
        const color = hexToRGBA(state.foregroundColor);
        const w = state.canvasManager.width;
        const x0 = Math.min(this.startPos.x, x), y0 = Math.min(this.startPos.y, y);
        const x1 = Math.max(this.startPos.x, x), y1 = Math.max(this.startPos.y, y);

        const filled = e.shiftKey;
        for (let py = y0; py <= y1; py++) {
            for (let px = x0; px <= x1; px++) {
                if (!filled && py !== y0 && py !== y1 && px !== x0 && px !== x1) continue;
                if (!state.canvasManager.isInBounds(px, py)) continue;
                const idx = (py * w + px) * 4;
                layer.pixels[idx] = color.r;
                layer.pixels[idx + 1] = color.g;
                layer.pixels[idx + 2] = color.b;
                layer.pixels[idx + 3] = color.a;
            }
        }
        state.composite();
    }

    onMouseUp() {
        if (!this.drawing) return;
        this.drawing = false;
        this.previewPixels = null;
        window.AppState.pushUndo();
    }
}

class CircleTool {
    constructor() {
        this.startPos = null;
        this.drawing = false;
        this.previewPixels = null;
    }

    onMouseDown(x, y) {
        this.drawing = true;
        this.startPos = { x, y };
        this.previewPixels = new Uint8ClampedArray(window.AppState.getActiveLayer().pixels);
    }

    onMouseMove(x, y, e) {
        if (!this.drawing) return;
        const state = window.AppState;
        const layer = state.getActiveLayer();
        layer.pixels.set(this.previewPixels);
        const color = hexToRGBA(state.foregroundColor);
        const w = state.canvasManager.width;

        const cx = Math.round((this.startPos.x + x) / 2);
        const cy = Math.round((this.startPos.y + y) / 2);
        const rx = Math.abs(x - this.startPos.x) / 2;
        const ry = Math.abs(y - this.startPos.y) / 2;
        const filled = e.shiftKey;

        const points = midpointEllipse(cx, cy, Math.round(rx), Math.round(ry), filled);
        for (const p of points) {
            if (!state.canvasManager.isInBounds(p.x, p.y)) continue;
            const idx = (p.y * w + p.x) * 4;
            layer.pixels[idx] = color.r;
            layer.pixels[idx + 1] = color.g;
            layer.pixels[idx + 2] = color.b;
            layer.pixels[idx + 3] = color.a;
        }
        state.composite();
    }

    onMouseUp() {
        if (!this.drawing) return;
        this.drawing = false;
        this.previewPixels = null;
        window.AppState.pushUndo();
    }
}

class EyedropperTool {
    onMouseDown(x, y) {
        this._pick(x, y);
    }

    onMouseMove(x, y, e) {
        if (e.buttons & 1) this._pick(x, y);
    }

    onMouseUp() {}

    _pick(x, y) {
        const state = window.AppState;
        if (!state.canvasManager.isInBounds(x, y)) return;
        const w = state.canvasManager.width;
        const idx = (y * w + x) * 4;
        const data = state.compositeImageData.data;
        const r = data[idx], g = data[idx + 1], b = data[idx + 2];
        state.setForegroundColor(rgbToHex(r, g, b));
    }
}

class SelectionTool {
    constructor() {
        this.selecting = false;
        this.moving = false;
        this.selection = null;
        this.startPos = null;
        this.selectedPixels = null;
        this.moveOffset = null;
    }

    onMouseDown(x, y, e) {
        const state = window.AppState;
        if (this.selection && this._isInSelection(x, y)) {
            this.moving = true;
            this.moveOffset = { x: x - this.selection.x, y: y - this.selection.y };
        } else {
            if (this.selectedPixels) this._commitSelection();
            this.selecting = true;
            this.startPos = { x, y };
            this.selection = null;
        }
    }

    onMouseMove(x, y) {
        const state = window.AppState;
        if (this.selecting) {
            this.selection = {
                x: Math.min(this.startPos.x, x),
                y: Math.min(this.startPos.y, y),
                w: Math.abs(x - this.startPos.x) + 1,
                h: Math.abs(y - this.startPos.y) + 1
            };
            state.composite();
        } else if (this.moving && this.selection) {
            this.selection.x = x - this.moveOffset.x;
            this.selection.y = y - this.moveOffset.y;
            state.composite();
        }
    }

    onMouseUp(x, y) {
        if (this.selecting) {
            this.selecting = false;
            if (this.selection && this.selection.w > 0 && this.selection.h > 0) {
                this._captureSelection();
            }
        } else if (this.moving) {
            this.moving = false;
            window.AppState.pushUndo();
        }
    }

    _isInSelection(x, y) {
        if (!this.selection) return false;
        return x >= this.selection.x && x < this.selection.x + this.selection.w &&
               y >= this.selection.y && y < this.selection.y + this.selection.h;
    }

    _captureSelection() {
        const state = window.AppState;
        const layer = state.getActiveLayer();
        if (!layer) return;
        const w = state.canvasManager.width;
        const sel = this.selection;
        this.selectedPixels = new Uint8ClampedArray(sel.w * sel.h * 4);

        for (let sy = 0; sy < sel.h; sy++) {
            for (let sx = 0; sx < sel.w; sx++) {
                const srcX = sel.x + sx, srcY = sel.y + sy;
                if (!state.canvasManager.isInBounds(srcX, srcY)) continue;
                const srcIdx = (srcY * w + srcX) * 4;
                const dstIdx = (sy * sel.w + sx) * 4;
                this.selectedPixels[dstIdx] = layer.pixels[srcIdx];
                this.selectedPixels[dstIdx + 1] = layer.pixels[srcIdx + 1];
                this.selectedPixels[dstIdx + 2] = layer.pixels[srcIdx + 2];
                this.selectedPixels[dstIdx + 3] = layer.pixels[srcIdx + 3];
                layer.pixels[srcIdx] = 0;
                layer.pixels[srcIdx + 1] = 0;
                layer.pixels[srcIdx + 2] = 0;
                layer.pixels[srcIdx + 3] = 0;
            }
        }
        state.composite();
    }

    _commitSelection() {
        if (!this.selectedPixels || !this.selection) return;
        const state = window.AppState;
        const layer = state.getActiveLayer();
        if (!layer) return;
        const w = state.canvasManager.width;
        const sel = this.selection;

        for (let sy = 0; sy < sel.h; sy++) {
            for (let sx = 0; sx < sel.w; sx++) {
                const dstX = sel.x + sx, dstY = sel.y + sy;
                if (!state.canvasManager.isInBounds(dstX, dstY)) continue;
                const srcIdx = (sy * sel.w + sx) * 4;
                if (this.selectedPixels[srcIdx + 3] === 0) continue;
                const dstIdx = (dstY * w + dstX) * 4;
                layer.pixels[dstIdx] = this.selectedPixels[srcIdx];
                layer.pixels[dstIdx + 1] = this.selectedPixels[srcIdx + 1];
                layer.pixels[dstIdx + 2] = this.selectedPixels[srcIdx + 2];
                layer.pixels[dstIdx + 3] = this.selectedPixels[srcIdx + 3];
            }
        }
        this.selectedPixels = null;
        this.selection = null;
        state.composite();
        state.pushUndo();
    }

    deleteSelection() {
        this.selectedPixels = null;
        this.selection = null;
        window.AppState.composite();
        window.AppState.pushUndo();
    }
}

function bresenhamLine(x0, y0, x1, y1) {
    const points = [];
    let dx = Math.abs(x1 - x0), dy = Math.abs(y1 - y0);
    let sx = x0 < x1 ? 1 : -1, sy = y0 < y1 ? 1 : -1;
    let err = dx - dy;

    while (true) {
        points.push({ x: x0, y: y0 });
        if (x0 === x1 && y0 === y1) break;
        let e2 = 2 * err;
        if (e2 > -dy) { err -= dy; x0 += sx; }
        if (e2 < dx) { err += dx; y0 += sy; }
    }
    return points;
}

function midpointEllipse(cx, cy, rx, ry, filled) {
    const points = [];
    if (rx === 0 && ry === 0) {
        points.push({ x: cx, y: cy });
        return points;
    }
    if (rx === 0) {
        for (let y = cy - ry; y <= cy + ry; y++) points.push({ x: cx, y });
        return points;
    }
    if (ry === 0) {
        for (let x = cx - rx; x <= cx + rx; x++) points.push({ x, y: cy });
        return points;
    }

    const addPoints = (x, y) => {
        if (filled) {
            for (let px = cx - x; px <= cx + x; px++) {
                points.push({ x: px, y: cy + y });
                points.push({ x: px, y: cy - y });
            }
        } else {
            points.push({ x: cx + x, y: cy + y });
            points.push({ x: cx - x, y: cy + y });
            points.push({ x: cx + x, y: cy - y });
            points.push({ x: cx - x, y: cy - y });
        }
    };

    let x = 0, y = ry;
    let rx2 = rx * rx, ry2 = ry * ry;
    let p = ry2 - rx2 * ry + 0.25 * rx2;

    while (2 * ry2 * x <= 2 * rx2 * y) {
        addPoints(x, y);
        x++;
        if (p < 0) {
            p += 2 * ry2 * x + ry2;
        } else {
            y--;
            p += 2 * ry2 * x - 2 * rx2 * y + ry2;
        }
    }

    p = ry2 * (x + 0.5) * (x + 0.5) + rx2 * (y - 1) * (y - 1) - rx2 * ry2;
    while (y >= 0) {
        addPoints(x, y);
        y--;
        if (p > 0) {
            p += rx2 - 2 * rx2 * y;
        } else {
            x++;
            p += 2 * ry2 * x - 2 * rx2 * y + rx2;
        }
    }

    return points;
}

function hexToRGBA(hex) {
    hex = hex.replace("#", "");
    return {
        r: parseInt(hex.substring(0, 2), 16),
        g: parseInt(hex.substring(2, 4), 16),
        b: parseInt(hex.substring(4, 6), 16),
        a: 255
    };
}

function rgbToHex(r, g, b) {
    return "#" + [r, g, b].map(v => v.toString(16).padStart(2, "0")).join("");
}

window.ToolManager = ToolManager;
window.PencilTool = PencilTool;
window.EraserTool = EraserTool;
window.FillTool = FillTool;
window.LineTool = LineTool;
window.RectTool = RectTool;
window.CircleTool = CircleTool;
window.EyedropperTool = EyedropperTool;
window.SelectionTool = SelectionTool;
window.bresenhamLine = bresenhamLine;
window.midpointEllipse = midpointEllipse;
window.hexToRGBA = hexToRGBA;
window.rgbToHex = rgbToHex;
