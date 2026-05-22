class ExportManager {
    exportPNG(scale) {
        const state = window.AppState;
        const w = state.canvasManager.width;
        const h = state.canvasManager.height;
        scale = scale || parseInt(document.getElementById("export-scale").value) || 4;

        const canvas = document.createElement("canvas");
        canvas.width = w * scale;
        canvas.height = h * scale;
        const ctx = canvas.getContext("2d");
        ctx.imageSmoothingEnabled = false;

        const srcCanvas = document.createElement("canvas");
        srcCanvas.width = w;
        srcCanvas.height = h;
        srcCanvas.getContext("2d").putImageData(state.compositeImageData, 0, 0);
        ctx.drawImage(srcCanvas, 0, 0, w * scale, h * scale);

        const link = document.createElement("a");
        link.download = "pixelforge-frame.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    }

    exportSpritesheet() {
        const state = window.AppState;
        const w = state.canvasManager.width;
        const h = state.canvasManager.height;
        const scale = parseInt(document.getElementById("export-scale").value) || 4;
        const frameCount = state.frames.length;

        const canvas = document.createElement("canvas");
        canvas.width = w * scale * frameCount;
        canvas.height = h * scale;
        const ctx = canvas.getContext("2d");
        ctx.imageSmoothingEnabled = false;

        state.frames.forEach((frame, idx) => {
            const imgData = state.animationManager._compositeFrame(frame);
            const srcCanvas = document.createElement("canvas");
            srcCanvas.width = w;
            srcCanvas.height = h;
            srcCanvas.getContext("2d").putImageData(imgData, 0, 0);
            ctx.drawImage(srcCanvas, idx * w * scale, 0, w * scale, h * scale);
        });

        const link = document.createElement("a");
        link.download = "pixelforge-spritesheet.png";
        link.href = canvas.toDataURL("image/png");
        link.click();
    }

    async exportGIF() {
        const state = window.AppState;
        const w = state.canvasManager.width;
        const h = state.canvasManager.height;
        const scale = parseInt(document.getElementById("export-scale").value) || 4;
        const btn = document.getElementById("btn-export-gif");

        const framesPayload = state.frames.map(frame => {
            const imgData = state.animationManager._compositeFrame(frame);
            const canvas = document.createElement("canvas");
            canvas.width = w;
            canvas.height = h;
            canvas.getContext("2d").putImageData(imgData, 0, 0);

            const scaledCanvas = document.createElement("canvas");
            scaledCanvas.width = w * scale;
            scaledCanvas.height = h * scale;
            const sCtx = scaledCanvas.getContext("2d");
            sCtx.imageSmoothingEnabled = false;
            sCtx.drawImage(canvas, 0, 0, w * scale, h * scale);

            return {
                data: scaledCanvas.toDataURL("image/png"),
                duration: frame.duration
            };
        });

        btn.disabled = true;
        btn.textContent = "Exporting...";

        try {
            const response = await fetch("/api/export/gif", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ frames: framesPayload })
            });

            if (!response.ok) {
                const err = await response.json();
                throw new Error(err.error || "Export failed");
            }

            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const link = document.createElement("a");
            link.download = "pixelforge-animation.gif";
            link.href = url;
            link.click();
            URL.revokeObjectURL(url);
        } catch (e) {
            alert("GIF export failed: " + e.message);
        } finally {
            btn.disabled = false;
            btn.textContent = "GIF";
        }
    }
}

window.ExportManager = ExportManager;
