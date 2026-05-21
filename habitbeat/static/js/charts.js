function renderBarChart(canvasId, data) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = (canvas.width = canvas.parentElement.clientWidth);
    const height = (canvas.height = 300);

    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;
    const barWidth = chartWidth / data.length * 0.8;
    const gap = chartWidth / data.length * 0.2;

    ctx.clearRect(0, 0, width, height);

    ctx.strokeStyle = '#e2e8f0';
    ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) {
        const y = padding + (chartHeight / 4) * i;
        ctx.beginPath();
        ctx.moveTo(padding, y);
        ctx.lineTo(width - padding, y);
        ctx.stroke();
    }

    const maxTarget = Math.max(...data.map(d => d.target));
    data.forEach((item, i) => {
        const x = padding + i * (barWidth + gap);
        const barHeight = (item.completed / maxTarget) * chartHeight;
        const y = padding + chartHeight - barHeight;

        ctx.fillStyle = item.completed > 0 ? '#22c55e' : '#e2e8f0';
        ctx.fillRect(x, y, barWidth, barHeight);

        ctx.fillStyle = '#64748b';
        ctx.font = '12px sans-serif';
        ctx.textAlign = 'center';
        const date = new Date(item.date);
        ctx.fillText(
            `${date.getMonth() + 1}/${date.getDate()}`,
            x + barWidth / 2,
            height - 10
        );
    });
}

function renderLineChart(canvasId, data, options = {}) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    const width = (canvas.width = canvas.parentElement.clientWidth);
    const height = (canvas.height = 300);

    const padding = 40;
    const chartWidth = width - padding * 2;
    const chartHeight = height - padding * 2;

    ctx.clearRect(0, 0, width, height);

    if (data.length === 0) return;

    const maxValue = Math.max(...data.map(d => d.value), options.maxValue || 1);
    const minValue = 0;

    ctx.strokeStyle = options.color || '#6366f1';
    ctx.lineWidth = 2;
    ctx.beginPath();

    data.forEach((item, i) => {
        const x = padding + (i / (data.length - 1 || 1)) * chartWidth;
        const y = padding + chartHeight - ((item.value - minValue) / (maxValue - minValue)) * chartHeight;

        if (i === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });

    ctx.stroke();

    ctx.fillStyle = options.color || '#6366f1';
    data.forEach((item, i) => {
        const x = padding + (i / (data.length - 1 || 1)) * chartWidth;
        const y = padding + chartHeight - ((item.value - minValue) / (maxValue - minValue)) * chartHeight;

        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
    });
}