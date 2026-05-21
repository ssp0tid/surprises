const DAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const HOURS = Array.from({ length: 24 }, (_, i) => i);

const COLORS = [
    '#ebedf0',
    '#9be9a8',
    '#40c463',
    '#30a14e',
    '#216e39'
];

function getColorForCount(count, maxCount) {
    if (count === 0) return COLORS[0];
    const ratio = count / maxCount;
    if (ratio < 0.25) return COLORS[1];
    if (ratio < 0.5) return COLORS[2];
    if (ratio < 0.75) return COLORS[3];
    return COLORS[4];
}

async function loadActivity() {
    const loadingId = 'activityLoading';
    const contentId = 'activityContent';
    const errorId = 'activityError';

    showLoading(loadingId);

    try {
        const data = await fetchJSON(apiBase + '/activity');

        const activityData = data.activity;
        const maxCount = Math.max(...activityData.map(a => a.commit_count));

        const activityMap = new Map();
        activityData.forEach(a => {
            activityMap.set(`${a.day}-${a.hour}`, a.commit_count);
        });

        const canvas = document.getElementById('heatmapCanvas');
        if (canvas) {
            const ctx = canvas.getContext('2d');
            const cellWidth = canvas.width / 24;
            const cellHeight = canvas.height / 7;

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            for (let day = 0; day < 7; day++) {
                for (let hour = 0; hour < 24; hour++) {
                    const count = activityMap.get(`${day}-${hour}`) || 0;
                    ctx.fillStyle = getColorForCount(count, maxCount);
                    ctx.fillRect(hour * cellWidth, day * cellHeight, cellWidth - 2, cellHeight - 2);
                }
            }

            ctx.fillStyle = '#333';
            ctx.font = '10px sans-serif';
            ctx.textAlign = 'right';

            for (let day = 0; day < 7; day++) {
                ctx.fillText(DAYS[day], 35, day * cellHeight + cellHeight / 2 + 3);
            }

            ctx.textAlign = 'center';
            for (let hour = 0; hour < 24; hour += 4) {
                ctx.fillText(hour.toString(), hour * cellWidth + cellWidth / 2, canvas.height - 5);
            }
        }

        showContent(contentId, loadingId);

    } catch (error) {
        showError(errorId, error.message);
        hideLoading(loadingId);
    }
}

function renderHeatmapLegend() {
    const legend = document.getElementById('heatmapLegend');
    if (!legend) return;

    let html = '<h6>Legend</h6>';
    html += '<div class="heatmap-scale">';
    html += '<span>Less</span>';

    COLORS.forEach(color => {
        html += `<div class="heatmap-cell" style="background: ${color};"></div>`;
    });

    html += '<span>More</span>';
    html += '</div>';

    legend.innerHTML = html;
}

document.addEventListener('DOMContentLoaded', function() {
    renderHeatmapLegend();
});