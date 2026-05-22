class LayerManager {
    constructor() {
        this.listEl = document.getElementById("layers-list");
    }

    renderList() {
        const state = window.AppState;
        const frame = state.getCurrentFrame();
        if (!frame) return;

        this.listEl.innerHTML = "";
        const layers = frame.layers.slice().reverse();

        layers.forEach((layer, revIdx) => {
            const realIdx = frame.layers.length - 1 - revIdx;
            const item = document.createElement("div");
            item.className = "layer-item" + (realIdx === state.activeLayerIdx ? " active" : "");
            item.draggable = true;
            item.dataset.idx = realIdx;

            const visBtn = document.createElement("button");
            visBtn.className = "text-xs w-6 h-6 flex items-center justify-center rounded " +
                (layer.visible ? "bg-purple-600" : "bg-gray-600");
            visBtn.textContent = layer.visible ? "👁" : "—";
            visBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                layer.visible = !layer.visible;
                state.composite();
                this.renderList();
            });

            const nameSpan = document.createElement("span");
            nameSpan.className = "text-sm flex-1 truncate";
            nameSpan.textContent = layer.name;
            nameSpan.addEventListener("dblclick", () => {
                const input = document.createElement("input");
                input.type = "text";
                input.value = layer.name;
                input.className = "bg-gray-700 text-sm rounded px-1 w-full border border-gray-500";
                nameSpan.replaceWith(input);
                input.focus();
                input.select();
                const finish = () => {
                    layer.name = input.value || layer.name;
                    this.renderList();
                };
                input.addEventListener("blur", finish);
                input.addEventListener("keydown", (e) => {
                    if (e.key === "Enter") finish();
                });
            });

            const opacityInput = document.createElement("input");
            opacityInput.type = "range";
            opacityInput.min = "0";
            opacityInput.max = "100";
            opacityInput.value = layer.opacity;
            opacityInput.className = "w-12 h-3";
            opacityInput.addEventListener("input", () => {
                layer.opacity = parseInt(opacityInput.value);
                state.composite();
            });

            const delBtn = document.createElement("button");
            delBtn.className = "text-xs text-red-400 hover:text-red-300 px-1";
            delBtn.textContent = "×";
            delBtn.addEventListener("click", (e) => {
                e.stopPropagation();
                if (frame.layers.length <= 1) return;
                frame.layers.splice(realIdx, 1);
                if (state.activeLayerIdx >= frame.layers.length) {
                    state.activeLayerIdx = frame.layers.length - 1;
                }
                state.composite();
                this.renderList();
            });

            item.addEventListener("click", () => {
                state.activeLayerIdx = realIdx;
                this.renderList();
            });

            item.addEventListener("dragstart", (e) => {
                e.dataTransfer.setData("text/plain", realIdx.toString());
            });

            item.addEventListener("dragover", (e) => {
                e.preventDefault();
                item.classList.add("border-t-2", "border-purple-400");
            });

            item.addEventListener("dragleave", () => {
                item.classList.remove("border-t-2", "border-purple-400");
            });

            item.addEventListener("drop", (e) => {
                e.preventDefault();
                item.classList.remove("border-t-2", "border-purple-400");
                const fromIdx = parseInt(e.dataTransfer.getData("text/plain"));
                const toIdx = realIdx;
                if (fromIdx === toIdx) return;
                const [moved] = frame.layers.splice(fromIdx, 1);
                frame.layers.splice(toIdx, 0, moved);
                state.activeLayerIdx = toIdx;
                state.composite();
                this.renderList();
            });

            item.appendChild(visBtn);
            item.appendChild(nameSpan);
            item.appendChild(opacityInput);
            item.appendChild(delBtn);
            this.listEl.appendChild(item);
        });
    }

    addLayer() {
        const state = window.AppState;
        const frame = state.getCurrentFrame();
        if (!frame || frame.layers.length >= 8) return;

        const w = state.canvasManager.width;
        const h = state.canvasManager.height;
        const newLayer = {
            id: Date.now(),
            name: "Layer " + (frame.layers.length + 1),
            pixels: new Uint8ClampedArray(w * h * 4),
            opacity: 100,
            visible: true
        };
        frame.layers.push(newLayer);
        state.activeLayerIdx = frame.layers.length - 1;
        state.composite();
        this.renderList();
    }

    mergeDown() {
        const state = window.AppState;
        const frame = state.getCurrentFrame();
        if (!frame || state.activeLayerIdx <= 0) return;

        const upper = frame.layers[state.activeLayerIdx];
        const lower = frame.layers[state.activeLayerIdx - 1];
        const w = state.canvasManager.width;
        const h = state.canvasManager.height;

        for (let i = 0; i < w * h * 4; i += 4) {
            const ua = upper.pixels[i + 3] / 255 * (upper.opacity / 100);
            const la = lower.pixels[i + 3] / 255 * (lower.opacity / 100);
            const outA = ua + la * (1 - ua);

            if (outA > 0) {
                lower.pixels[i] = Math.round((upper.pixels[i] * ua + lower.pixels[i] * la * (1 - ua)) / outA);
                lower.pixels[i + 1] = Math.round((upper.pixels[i + 1] * ua + lower.pixels[i + 1] * la * (1 - ua)) / outA);
                lower.pixels[i + 2] = Math.round((upper.pixels[i + 2] * ua + lower.pixels[i + 2] * la * (1 - ua)) / outA);
                lower.pixels[i + 3] = Math.round(outA * 255);
            }
        }
        lower.opacity = 100;

        frame.layers.splice(state.activeLayerIdx, 1);
        state.activeLayerIdx--;
        state.composite();
        this.renderList();
        state.pushUndo();
    }

    flattenAll() {
        const state = window.AppState;
        const frame = state.getCurrentFrame();
        if (!frame || frame.layers.length <= 1) return;

        while (frame.layers.length > 1) {
            state.activeLayerIdx = frame.layers.length - 1;
            this.mergeDown();
        }
        frame.layers[0].name = "Flattened";
        state.activeLayerIdx = 0;
        state.composite();
        this.renderList();
    }

    duplicateLayer() {
        const state = window.AppState;
        const frame = state.getCurrentFrame();
        if (!frame || frame.layers.length >= 8) return;

        const src = frame.layers[state.activeLayerIdx];
        const dup = {
            id: Date.now(),
            name: src.name + " copy",
            pixels: new Uint8ClampedArray(src.pixels),
            opacity: src.opacity,
            visible: src.visible
        };
        frame.layers.splice(state.activeLayerIdx + 1, 0, dup);
        state.activeLayerIdx++;
        state.composite();
        this.renderList();
    }
}

window.LayerManager = LayerManager;
