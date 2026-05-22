const AppState = {
    canvasManager: null,
    toolManager: null,
    layerManager: null,
    paletteManager: null,
    animationManager: null,
    exportManager: null,

    frames: [],
    activeFrameIdx: 0,
    activeLayerIdx: 0,

    foregroundColor: "#000000",
    backgroundColor: "#ffffff",

    undoStack: [],
    redoStack: [],
    maxHistory: 50,

    compositeImageData: null,
    onionSkinning: false,
    projectId: null,

    init() {
        const canvasEl = document.getElementById("main-canvas");
        const containerEl = document.getElementById("canvas-container");

        this.canvasManager = new CanvasManager(canvasEl, containerEl);
        this.toolManager = new ToolManager();
        this.layerManager = new LayerManager();
        this.paletteManager = new PaletteManager();
        this.animationManager = new AnimationManager();
        this.exportManager = new ExportManager();

        this._registerTools();
        this._initProject(16, 16);
        this._bindEvents();
        this._updateColorDisplay();

        this.toolManager.setActive("pencil");
        this.composite();
        this.layerManager.renderList();
        this.animationManager.renderStrip();
    },

    _registerTools() {
        this.toolManager.register("pencil", new PencilTool());
        this.toolManager.register("eraser", new EraserTool());
        this.toolManager.register("fill", new FillTool());
        this.toolManager.register("line", new LineTool());
        this.toolManager.register("rect", new RectTool());
        this.toolManager.register("circle", new CircleTool());
        this.toolManager.register("eyedropper", new EyedropperTool());
        this.toolManager.register("selection", new SelectionTool());
    },

    _initProject(w, h) {
        this.frames = [{
            id: Date.now(),
            duration: 100,
            layers: [{
                id: Date.now() + 1,
                name: "Layer 1",
                pixels: new Uint8ClampedArray(w * h * 4),
                opacity: 100,
                visible: true
            }]
        }];
        this.activeFrameIdx = 0;
        this.activeLayerIdx = 0;
        this.undoStack = [];
        this.redoStack = [];
        this.canvasManager.setSize(w, h);
    },

    getCurrentFrame() {
        return this.frames[this.activeFrameIdx] || null;
    },

    getActiveLayer() {
        const frame = this.getCurrentFrame();
        if (!frame) return null;
        return frame.layers[this.activeLayerIdx] || null;
    },

    composite() {
        const frame = this.getCurrentFrame();
        if (!frame) return;

        const w = this.canvasManager.width;
        const h = this.canvasManager.height;
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

        if (this.onionSkinning) {
            this.compositeImageData = this.animationManager.renderOnionSkin(result);
        } else {
            this.compositeImageData = result;
        }

        this.canvasManager.render();
    },

    pushUndo() {
        const snapshot = this._takeSnapshot();
        this.undoStack.push(snapshot);
        if (this.undoStack.length > this.maxHistory) {
            this.undoStack.shift();
        }
        this.redoStack = [];
    },

    undo() {
        if (this.undoStack.length === 0) return;
        const current = this._takeSnapshot();
        this.redoStack.push(current);
        const prev = this.undoStack.pop();
        this._restoreSnapshot(prev);
        this.composite();
        this.layerManager.renderList();
    },

    redo() {
        if (this.redoStack.length === 0) return;
        const current = this._takeSnapshot();
        this.undoStack.push(current);
        const next = this.redoStack.pop();
        this._restoreSnapshot(next);
        this.composite();
        this.layerManager.renderList();
    },

    _takeSnapshot() {
        const frame = this.getCurrentFrame();
        return {
            frameIdx: this.activeFrameIdx,
            layerIdx: this.activeLayerIdx,
            layers: frame.layers.map(l => ({
                id: l.id,
                name: l.name,
                pixels: new Uint8ClampedArray(l.pixels),
                opacity: l.opacity,
                visible: l.visible
            }))
        };
    },

    _restoreSnapshot(snapshot) {
        this.activeFrameIdx = snapshot.frameIdx;
        this.activeLayerIdx = snapshot.layerIdx;
        const frame = this.getCurrentFrame();
        frame.layers = snapshot.layers;
    },

    setForegroundColor(color) {
        this.foregroundColor = color;
        this._updateColorDisplay();
        this.paletteManager.setFromHex(color);
        this.paletteManager.addRecentColor(color);
    },

    setBackgroundColor(color) {
        this.backgroundColor = color;
        this._updateColorDisplay();
    },

    swapColors() {
        const tmp = this.foregroundColor;
        this.foregroundColor = this.backgroundColor;
        this.backgroundColor = tmp;
        this._updateColorDisplay();
        this.paletteManager.setFromHex(this.foregroundColor);
    },

    _updateColorDisplay() {
        document.getElementById("color-fg").style.backgroundColor = this.foregroundColor;
        document.getElementById("color-bg").style.backgroundColor = this.backgroundColor;
        document.getElementById("hex-input").value = this.foregroundColor;
    },

    _bindEvents() {
        const canvas = this.canvasManager.canvas;
        let isDrawing = false;

        canvas.addEventListener("mousedown", (e) => {
            if (e.button !== 0 || this.canvasManager.spaceHeld) return;
            const { x, y } = this.canvasManager.canvasToPixel(e.clientX, e.clientY);
            isDrawing = true;
            this.toolManager.onMouseDown(x, y, e);
        });

        canvas.addEventListener("mousemove", (e) => {
            if (!isDrawing) return;
            const { x, y } = this.canvasManager.canvasToPixel(e.clientX, e.clientY);
            this.toolManager.onMouseMove(x, y, e);
        });

        window.addEventListener("mouseup", (e) => {
            if (!isDrawing) return;
            isDrawing = false;
            const { x, y } = this.canvasManager.canvasToPixel(e.clientX, e.clientY);
            this.toolManager.onMouseUp(x, y, e);
        });

        document.querySelectorAll(".tool-btn").forEach(btn => {
            btn.addEventListener("click", () => {
                this.toolManager.setActive(btn.dataset.tool);
            });
        });

        document.getElementById("toggle-grid").addEventListener("change", (e) => {
            this.canvasManager.setGrid(e.target.checked);
        });

        document.getElementById("canvas-size").addEventListener("change", (e) => {
            const size = parseInt(e.target.value);
            if (confirm("Changing canvas size will reset the project. Continue?")) {
                this._initProject(size, size);
                this.composite();
                this.layerManager.renderList();
                this.animationManager.renderStrip();
            }
        });

        document.getElementById("btn-new").addEventListener("click", () => {
            if (confirm("Create a new project? Unsaved changes will be lost.")) {
                const size = parseInt(document.getElementById("canvas-size").value);
                this._initProject(size, size);
                this.projectId = null;
                this.composite();
                this.layerManager.renderList();
                this.animationManager.renderStrip();
            }
        });

        document.getElementById("btn-save").addEventListener("click", () => this._saveProject());
        document.getElementById("btn-load").addEventListener("click", () => this._showLoadModal());
        document.getElementById("btn-modal-close").addEventListener("click", () => {
            document.getElementById("modal-load").classList.add("hidden");
        });

        document.getElementById("btn-add-layer").addEventListener("click", () => this.layerManager.addLayer());
        document.getElementById("btn-merge-layer").addEventListener("click", () => this.layerManager.mergeDown());
        document.getElementById("btn-flatten").addEventListener("click", () => this.layerManager.flattenAll());

        document.getElementById("btn-add-frame").addEventListener("click", () => this.animationManager.addFrame());
        document.getElementById("btn-dup-frame").addEventListener("click", () => this.animationManager.duplicateFrame());
        document.getElementById("btn-del-frame").addEventListener("click", () => this.animationManager.deleteFrame());
        document.getElementById("btn-play").addEventListener("click", () => this.animationManager.play());
        document.getElementById("btn-stop-playback").addEventListener("click", () => this.animationManager.stop());

        document.getElementById("toggle-onion").addEventListener("change", (e) => {
            this.onionSkinning = e.target.checked;
            this.composite();
        });

        document.getElementById("frame-duration").addEventListener("change", (e) => {
            this.animationManager.setFrameDuration(parseInt(e.target.value));
        });

        document.getElementById("btn-export-png").addEventListener("click", () => this.exportManager.exportPNG());
        document.getElementById("btn-export-sheet").addEventListener("click", () => this.exportManager.exportSpritesheet());
        document.getElementById("btn-export-gif").addEventListener("click", () => this.exportManager.exportGIF());

        window.addEventListener("keydown", (e) => {
            if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

            const key = e.key.toLowerCase();
            if (e.ctrlKey || e.metaKey) {
                if (key === "z") { e.preventDefault(); this.undo(); }
                else if (key === "y") { e.preventDefault(); this.redo(); }
                else if (key === "s") { e.preventDefault(); this._saveProject(); }
                return;
            }

            const toolKeys = { b: "pencil", e: "eraser", g: "fill", l: "line", r: "rect", c: "circle", i: "eyedropper", m: "selection" };
            if (toolKeys[key]) {
                this.toolManager.setActive(toolKeys[key]);
            } else if (key === "x") {
                this.swapColors();
            } else if (key === "+" || key === "=") {
                this.canvasManager.zoomIn();
            } else if (key === "-") {
                this.canvasManager.zoomOut();
            } else if (key === "delete" || key === "backspace") {
                const tool = this.toolManager.activeTool;
                if (tool instanceof SelectionTool && tool.selection) {
                    tool.deleteSelection();
                }
            }
        });
    },

    async _saveProject() {
        const data = {
            layers: this.frames[this.activeFrameIdx].layers.map(l => ({
                id: l.id,
                name: l.name,
                pixels: Array.from(l.pixels),
                opacity: l.opacity,
                visible: l.visible
            })),
            frames: this.frames.map(f => ({
                id: f.id,
                duration: f.duration,
                layers: f.layers.map(l => ({
                    id: l.id,
                    name: l.name,
                    pixels: Array.from(l.pixels),
                    opacity: l.opacity,
                    visible: l.visible
                }))
            })),
            activeFrame: this.activeFrameIdx,
            activeLayer: this.activeLayerIdx,
            foregroundColor: this.foregroundColor,
            backgroundColor: this.backgroundColor
        };

        try {
            if (this.projectId) {
                const res = await fetch(`/api/projects/${this.projectId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ data })
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.error || "Save failed");
                }
            } else {
                const name = prompt("Project name:", "My Pixel Art");
                if (!name) return;

                const w = this.canvasManager.width;
                const h = this.canvasManager.height;
                const res = await fetch("/api/projects", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ name, width: w, height: h })
                });
                if (!res.ok) {
                    const err = await res.json();
                    throw new Error(err.error || "Create failed");
                }
                const result = await res.json();
                this.projectId = result.id;

                const saveRes = await fetch(`/api/projects/${this.projectId}`, {
                    method: "PUT",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ data, name })
                });
                if (!saveRes.ok) {
                    const err = await saveRes.json();
                    throw new Error(err.error || "Save failed");
                }
            }
        } catch (e) {
            alert("Save failed: " + e.message);
        }
    },

    async _showLoadModal() {
        const modal = document.getElementById("modal-load");
        const listEl = document.getElementById("projects-list");
        modal.classList.remove("hidden");
        listEl.innerHTML = "<p class='text-gray-400 text-sm'>Loading...</p>";

        try {
            const res = await fetch("/api/projects");
            const projects = await res.json();

            if (projects.length === 0) {
                listEl.innerHTML = "<p class='text-gray-400 text-sm'>No saved projects.</p>";
                return;
            }

            listEl.innerHTML = "";
            projects.forEach(p => {
                const item = document.createElement("div");
                item.className = "flex items-center justify-between bg-gray-700 rounded px-3 py-2";

                const info = document.createElement("div");
                info.innerHTML = `<div class="text-sm font-medium">${p.name}</div><div class="text-xs text-gray-400">${p.width}×${p.height} — ${p.updated_at}</div>`;

                const actions = document.createElement("div");
                actions.className = "flex gap-2";

                const loadBtn = document.createElement("button");
                loadBtn.className = "text-xs bg-purple-600 hover:bg-purple-500 px-3 py-1 rounded";
                loadBtn.textContent = "Load";
                loadBtn.addEventListener("click", () => this._loadProject(p.id));

                const delBtn = document.createElement("button");
                delBtn.className = "text-xs bg-red-700 hover:bg-red-600 px-2 py-1 rounded";
                delBtn.textContent = "Del";
                delBtn.addEventListener("click", async () => {
                    if (confirm(`Delete "${p.name}"?`)) {
                        await fetch(`/api/projects/${p.id}`, { method: "DELETE" });
                        this._showLoadModal();
                    }
                });

                actions.appendChild(loadBtn);
                actions.appendChild(delBtn);
                item.appendChild(info);
                item.appendChild(actions);
                listEl.appendChild(item);
            });
        } catch (e) {
            listEl.innerHTML = `<p class='text-red-400 text-sm'>Failed to load projects: ${e.message}</p>`;
        }
    },

    async _loadProject(id) {
        try {
            const res = await fetch(`/api/projects/${id}`);
            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error || "Failed to load project");
            }
            const project = await res.json();

            this.projectId = project.id;
            this.canvasManager.setSize(project.width, project.height);
            document.getElementById("canvas-size").value = project.width.toString();

            const data = project.data;
            if (data.frames && data.frames.length > 0) {
                this.frames = data.frames.map(f => ({
                    id: f.id,
                    duration: f.duration || 100,
                    layers: f.layers.map(l => ({
                        id: l.id,
                        name: l.name,
                        pixels: new Uint8ClampedArray(l.pixels),
                        opacity: l.opacity,
                        visible: l.visible
                    }))
                }));
            } else {
                this.frames = [{
                    id: Date.now(),
                    duration: 100,
                    layers: (data.layers || []).map(l => ({
                        id: l.id,
                        name: l.name,
                        pixels: l.pixels ? new Uint8ClampedArray(l.pixels) : new Uint8ClampedArray(project.width * project.height * 4),
                        opacity: l.opacity,
                        visible: l.visible
                    }))
                }];
            }

            this.activeFrameIdx = data.activeFrame || 0;
            this.activeLayerIdx = data.activeLayer || 0;
            if (data.foregroundColor) this.foregroundColor = data.foregroundColor;
            if (data.backgroundColor) this.backgroundColor = data.backgroundColor;

            this.undoStack = [];
            this.redoStack = [];
            this._updateColorDisplay();
            this.paletteManager.setFromHex(this.foregroundColor);
            this.composite();
            this.layerManager.renderList();
            this.animationManager.renderStrip();

            document.getElementById("modal-load").classList.add("hidden");
        } catch (e) {
            alert("Load failed: " + e.message);
        }
    }
};

window.AppState = AppState;
document.addEventListener("DOMContentLoaded", () => AppState.init());
