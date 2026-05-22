let chart = null;

function initSSE(slug) {
    const evtSource = new EventSource(`/api/polls/${slug}/stream`);
    evtSource.onmessage = function(event) {
        const data = JSON.parse(event.data);
        renderChart(data);
        renderResultsList(data);
        document.getElementById('total-votes').textContent = data.total_votes;
    };
    evtSource.onerror = function() {
        evtSource.close();
        setTimeout(() => initSSE(slug), 5000);
    };
}

function renderChart(data) {
    const ctx = document.getElementById('results-chart');
    if (!ctx) return;

    const labels = data.options.map(o => o.text);
    const votes = data.options.map(o => o.votes);
    const colors = generateColors(data.options.length);

    if (chart) {
        chart.data.labels = labels;
        chart.data.datasets[0].data = votes;
        chart.data.datasets[0].backgroundColor = colors;
        chart.update();
    } else {
        chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: 'Votes',
                    data: votes,
                    backgroundColor: colors,
                    borderRadius: 4
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: { stepSize: 1 }
                    }
                }
            }
        });
    }
}

function renderResultsList(data) {
    const container = document.getElementById('results-list');
    if (!container) return;

    container.innerHTML = data.options.map(o => {
        const pct = data.total_votes > 0 ? ((o.votes / data.total_votes) * 100).toFixed(1) : '0.0';
        return `<div class="flex justify-between items-center text-sm">
            <span class="text-gray-700">${escapeHtml(o.text)}</span>
            <span class="text-gray-500 font-medium">${o.votes} (${pct}%)</span>
        </div>`;
    }).join('');
}

function generateColors(count) {
    const palette = [
        '#6366f1', '#8b5cf6', '#ec4899', '#f43f5e', '#f97316',
        '#eab308', '#22c55e', '#14b8a6', '#06b6d4', '#3b82f6',
        '#a855f7', '#d946ef', '#f59e0b', '#10b981', '#0ea5e9',
        '#ef4444', '#84cc16', '#64748b', '#f472b6', '#34d399'
    ];
    return palette.slice(0, count);
}

function initVoteForm(slug) {
    const form = document.getElementById('vote-form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        submitVote(slug);
    });
}

function submitVote(slug) {
    const form = document.getElementById('vote-form');
    const errorEl = document.getElementById('vote-error');
    const checked = form.querySelectorAll('input[name="option"]:checked');

    if (checked.length === 0) {
        errorEl.textContent = 'Please select at least one option.';
        errorEl.classList.remove('hidden');
        return;
    }

    const optionIds = Array.from(checked).map(el => parseInt(el.value));

    fetch(`/api/polls/${slug}/vote`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ option_ids: optionIds })
    })
    .then(res => res.json().then(data => ({ ok: res.ok, data })))
    .then(({ ok, data }) => {
        if (ok) {
            form.classList.add('hidden');
            document.getElementById('vote-success').classList.remove('hidden');
        } else {
            errorEl.textContent = data.error || 'Failed to submit vote.';
            errorEl.classList.remove('hidden');
        }
    })
    .catch(() => {
        errorEl.textContent = 'Network error. Please try again.';
        errorEl.classList.remove('hidden');
    });
}

function validateForm() {
    const title = document.getElementById('title');
    const options = document.querySelectorAll('#options-container input[name="option"]');
    const filledOptions = Array.from(options).filter(o => o.value.trim());

    if (!title.value.trim()) return 'Title is required.';
    if (filledOptions.length < 2) return 'At least 2 options are required.';
    return null;
}

function addOption() {
    const container = document.getElementById('options-container');
    const count = container.querySelectorAll('.option-row').length;
    if (count >= 20) return;

    const row = document.createElement('div');
    row.className = 'flex gap-2 option-row';
    row.innerHTML = `
        <input type="text" name="option" maxlength="200" required
               class="flex-1 border border-gray-300 rounded-md px-3 py-2 focus:outline-none focus:ring-2 focus:ring-indigo-500"
               placeholder="Option ${count + 1}">
        <button type="button" onclick="removeOption(this)" class="text-red-500 hover:text-red-700 px-2" title="Remove">✕</button>
    `;
    container.appendChild(row);
}

function removeOption(btn) {
    const container = document.getElementById('options-container');
    if (container.querySelectorAll('.option-row').length <= 2) return;
    btn.closest('.option-row').remove();
}

document.addEventListener('DOMContentLoaded', function() {
    const createForm = document.getElementById('create-form');
    if (createForm) {
        createForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const errorEl = document.getElementById('form-error');

            const validationError = validateForm();
            if (validationError) {
                errorEl.textContent = validationError;
                errorEl.classList.remove('hidden');
                return;
            }

            const title = document.getElementById('title').value.trim();
            const description = document.getElementById('description').value.trim();
            const pollType = document.getElementById('poll-type').value;
            const allowComments = document.getElementById('allow-comments').checked;
            const options = Array.from(document.querySelectorAll('#options-container input[name="option"]'))
                .map(el => el.value.trim())
                .filter(v => v);

            fetch('/api/polls', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    title,
                    description,
                    options,
                    poll_type: pollType,
                    allow_comments: allowComments
                })
            })
            .then(res => res.json().then(data => ({ ok: res.ok, data })))
            .then(({ ok, data }) => {
                if (ok) {
                    createForm.classList.add('hidden');
                    const panel = document.getElementById('success-panel');
                    panel.classList.remove('hidden');
                    document.getElementById('vote-url').value = window.location.origin + data.vote_url;
                    document.getElementById('results-url').value = window.location.origin + data.results_url;
                    document.getElementById('manage-url').value = window.location.origin + data.manage_url;
                } else {
                    errorEl.textContent = data.error || 'Failed to create poll.';
                    errorEl.classList.remove('hidden');
                }
            })
            .catch(() => {
                errorEl.textContent = 'Network error. Please try again.';
                errorEl.classList.remove('hidden');
            });
        });
    }
});

function copyToClipboard(inputId) {
    const input = document.getElementById(inputId);
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(input.value);
    } else {
        input.select();
        document.execCommand('copy');
    }
}

function closePoll(slug, token) {
    if (!confirm('Close this poll? No more votes will be accepted.')) return;

    fetch(`/api/polls/${slug}/close`, {
        method: 'POST',
        headers: { 'X-Admin-Token': token }
    })
    .then(res => res.json().then(data => ({ ok: res.ok, data })))
    .then(({ ok, data }) => {
        const msg = document.getElementById('manage-message');
        if (ok) {
            msg.textContent = 'Poll closed successfully.';
            msg.className = 'mt-4 text-sm text-green-700';
            const btn = document.getElementById('close-btn');
            if (btn) btn.remove();
        } else {
            msg.textContent = data.error || 'Failed to close poll.';
            msg.className = 'mt-4 text-sm text-red-600';
        }
        msg.classList.remove('hidden');
    });
}

function deletePoll(slug, token) {
    if (!confirm('Delete this poll permanently? This cannot be undone.')) return;

    fetch(`/api/polls/${slug}`, {
        method: 'DELETE',
        headers: { 'X-Admin-Token': token }
    })
    .then(res => res.json().then(data => ({ ok: res.ok, data })))
    .then(({ ok, data }) => {
        if (ok) {
            window.location.href = '/?deleted=1';
        } else {
            const msg = document.getElementById('manage-message');
            msg.textContent = data.error || 'Failed to delete poll.';
            msg.className = 'mt-4 text-sm text-red-600';
            msg.classList.remove('hidden');
        }
    });
}

function initComments(slug) {
    loadComments(slug);

    const form = document.getElementById('comment-form');
    if (!form) return;

    form.addEventListener('submit', function(e) {
        e.preventDefault();
        const text = document.getElementById('comment-text').value.trim();
        const author = document.getElementById('comment-author').value.trim();

        if (!text) return;

        fetch(`/api/polls/${slug}/comments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text, author })
        })
        .then(res => res.json().then(data => ({ ok: res.ok, data })))
        .then(({ ok, data }) => {
            if (ok) {
                document.getElementById('comment-text').value = '';
                loadComments(slug);
            }
        });
    });
}

function loadComments(slug) {
    fetch(`/api/polls/${slug}/comments`)
        .then(res => res.json())
        .then(data => {
            const container = document.getElementById('comments-list');
            if (!container) return;

            if (data.comments.length === 0) {
                container.innerHTML = '<p class="text-gray-400 text-sm">No comments yet.</p>';
                return;
            }

            container.innerHTML = data.comments.map(c => `
                <div class="border-b border-gray-100 pb-2">
                    <div class="flex justify-between items-baseline">
                        <span class="font-medium text-sm text-gray-800">${escapeHtml(c.author)}</span>
                        <span class="text-xs text-gray-400">${c.created_at}</span>
                    </div>
                    <p class="text-sm text-gray-600 mt-1">${escapeHtml(c.text)}</p>
                </div>
            `).join('');
        });
}

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}
