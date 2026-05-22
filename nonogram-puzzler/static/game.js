(function () {
    "use strict";

    let rowClues = [];
    let colClues = [];
    let playerGrid = [];
    let rows = 0;
    let cols = 0;
    let elapsedSeconds = 0;
    let timerInterval = null;
    let timerStarted = false;
    let completed = false;
    let autoSaveInterval = null;

    const board = document.getElementById("board");
    const timerEl = document.getElementById("timer");
    const checkBtn = document.getElementById("check-btn");
    const messageEl = document.getElementById("game-message");

    async function loadGame() {
        let res;
        try {
            res = await fetch("/api/game/" + GAME_ID);
        } catch (err) {
            messageEl.textContent = "Network error. Please check your connection and refresh.";
            return;
        }
        if (!res.ok) {
            messageEl.textContent = "Failed to load game.";
            return;
        }
        const data = await res.json();
        rowClues = data.row_clues;
        colClues = data.col_clues;
        playerGrid = data.player_grid;
        elapsedSeconds = data.elapsed_seconds;
        completed = data.completed;
        rows = rowClues.length;
        cols = colClues.length;

        updateTimerDisplay();
        renderBoard();

        if (completed) {
            messageEl.textContent = "🎉 Puzzle completed!";
            messageEl.classList.add("win");
            checkBtn.disabled = true;
        } else {
            autoSaveInterval = setInterval(autoSave, 30000);
        }
    }

    function renderBoard() {
        const maxRowClueLen = Math.max(...rowClues.map(c => c.length));
        const maxColClueLen = Math.max(...colClues.map(c => c.length));

        const totalCols = maxRowClueLen + cols;
        const totalRows = maxColClueLen + rows;

        board.style.gridTemplateColumns = "repeat(" + totalCols + ", auto)";
        board.style.gridTemplateRows = "repeat(" + totalRows + ", auto)";
        board.innerHTML = "";

        for (let r = 0; r < totalRows; r++) {
            for (let c = 0; c < totalCols; c++) {
                const isClueRow = r < maxColClueLen;
                const isClueCol = c < maxRowClueLen;

                if (isClueRow && isClueCol) {
                    const corner = document.createElement("div");
                    corner.className = "clue-cell corner";
                    board.appendChild(corner);
                } else if (isClueRow) {
                    const cell = document.createElement("div");
                    cell.className = "clue-cell col-clue";
                    const colIdx = c - maxRowClueLen;
                    const clue = colClues[colIdx];
                    const clueOffset = maxColClueLen - clue.length;
                    const clueIdx = r - clueOffset;
                    if (clueIdx >= 0 && clueIdx < clue.length) {
                        cell.textContent = clue[clueIdx];
                    }
                    board.appendChild(cell);
                } else if (isClueCol) {
                    const cell = document.createElement("div");
                    cell.className = "clue-cell row-clue";
                    const rowIdx = r - maxColClueLen;
                    const clue = rowClues[rowIdx];
                    const clueOffset = maxRowClueLen - clue.length;
                    const clueIdx = c - clueOffset;
                    if (clueIdx >= 0 && clueIdx < clue.length) {
                        cell.textContent = clue[clueIdx];
                    }
                    board.appendChild(cell);
                } else {
                    const rowIdx = r - maxColClueLen;
                    const colIdx = c - maxRowClueLen;
                    const cell = document.createElement("div");
                    cell.className = "grid-cell";
                    cell.dataset.row = rowIdx;
                    cell.dataset.col = colIdx;

                    applyCellState(cell, playerGrid[rowIdx][colIdx]);

                    cell.addEventListener("click", function () {
                        if (completed) return;
                        startTimer();
                        handleLeftClick(rowIdx, colIdx, cell);
                    });

                    cell.addEventListener("contextmenu", function (e) {
                        e.preventDefault();
                        if (completed) return;
                        startTimer();
                        handleRightClick(rowIdx, colIdx, cell);
                    });

                    board.appendChild(cell);
                }
            }
        }
    }

    function applyCellState(cell, state) {
        cell.classList.remove("filled", "marked");
        if (state === 1) {
            cell.classList.add("filled");
        } else if (state === 2) {
            cell.classList.add("marked");
        }
    }

    function handleLeftClick(row, col, cell) {
        if (playerGrid[row][col] === 1) {
            playerGrid[row][col] = 0;
        } else {
            playerGrid[row][col] = 1;
        }
        applyCellState(cell, playerGrid[row][col]);
    }

    function handleRightClick(row, col, cell) {
        if (playerGrid[row][col] === 2) {
            playerGrid[row][col] = 0;
        } else {
            playerGrid[row][col] = 2;
        }
        applyCellState(cell, playerGrid[row][col]);
    }

    function startTimer() {
        if (timerStarted) return;
        timerStarted = true;
        timerInterval = setInterval(function () {
            elapsedSeconds++;
            updateTimerDisplay();
        }, 1000);
    }

    function updateTimerDisplay() {
        const mins = Math.floor(elapsedSeconds / 60);
        const secs = elapsedSeconds % 60;
        timerEl.textContent = mins + ":" + (secs < 10 ? "0" : "") + secs;
    }

    async function autoSave() {
        if (completed) return;
        try {
            const res = await fetch("/api/save", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    puzzle_id: GAME_ID,
                    player_grid: playerGrid,
                    elapsed_seconds: elapsedSeconds,
                }),
            });
            if (!res.ok) {
                console.warn("Auto-save failed:", res.status);
            }
        } catch (err) {
            console.warn("Auto-save network error:", err.message);
        }
    }

    checkBtn.addEventListener("click", async function () {
        if (completed) return;

        const res = await fetch("/api/check", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                puzzle_id: GAME_ID,
                player_grid: playerGrid,
                elapsed_seconds: elapsedSeconds,
            }),
        });

        if (!res.ok) {
            messageEl.textContent = "Error checking solution.";
            return;
        }

        const data = await res.json();

        if (data.correct) {
            completed = true;
            clearInterval(timerInterval);
            clearInterval(autoSaveInterval);
            messageEl.textContent = "🎉 Puzzle solved in " + timerEl.textContent + "!";
            messageEl.classList.add("win");
            checkBtn.disabled = true;
        } else {
            messageEl.textContent = "Not quite right. Keep trying!";
            messageEl.classList.remove("win");
            highlightIncorrect();
        }
    });

    function highlightIncorrect() {
        for (let r = 0; r < rows; r++) {
            const rowLine = playerGrid[r].map(function (c) { return c === 1 ? 1 : 0; });
            const expected = rowClues[r];
            const actual = computeClues(rowLine);
            if (JSON.stringify(actual) !== JSON.stringify(expected)) {
                for (let c = 0; c < cols; c++) {
                    const cell = board.querySelector(
                        '[data-row="' + r + '"][data-col="' + c + '"]'
                    );
                    if (cell) {
                        cell.classList.add("incorrect");
                        setTimeout(function () { cell.classList.remove("incorrect"); }, 600);
                    }
                }
            }
        }

        for (let c = 0; c < cols; c++) {
            const colLine = [];
            for (let r = 0; r < rows; r++) {
                colLine.push(playerGrid[r][c] === 1 ? 1 : 0);
            }
            const expected = colClues[c];
            const actual = computeClues(colLine);
            if (JSON.stringify(actual) !== JSON.stringify(expected)) {
                for (let r = 0; r < rows; r++) {
                    const cell = board.querySelector(
                        '[data-row="' + r + '"][data-col="' + c + '"]'
                    );
                    if (cell) {
                        cell.classList.add("incorrect");
                        setTimeout(function () { cell.classList.remove("incorrect"); }, 600);
                    }
                }
            }
        }
    }

    function computeClues(line) {
        var clues = [];
        var count = 0;
        for (var i = 0; i < line.length; i++) {
            if (line[i] === 1) {
                count++;
            } else {
                if (count > 0) clues.push(count);
                count = 0;
            }
        }
        if (count > 0) clues.push(count);
        return clues.length > 0 ? clues : [0];
    }

    loadGame();
})();
