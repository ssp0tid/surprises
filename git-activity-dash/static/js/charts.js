let contributorsChart = null;
let messagesChart = null;

async function loadContributors() {
    const loadingId = 'contributorsLoading';
    const contentId = 'contributorsContent';
    const errorId = 'contributorsError';

    showLoading(loadingId);

    try {
        const data = await fetchJSON(apiBase + '/contributors');

        const tableBody = document.getElementById('contributorsTableBody');
        tableBody.innerHTML = data.contributors.slice(0, 20).map((c, i) => `
            <tr>
                <td>${i + 1}</td>
                <td>${c.name}</td>
                <td>${c.email}</td>
                <td>${c.commit_count}</td>
                <td>${formatDate(c.first_commit)}</td>
                <td>${formatDate(c.last_commit)}</td>
            </tr>
        `).join('');

        const ctx = document.getElementById('contributorsChart');
        if (ctx) {
            if (contributorsChart) contributorsChart.destroy();

            contributorsChart = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.contributors.slice(0, 10).map(c => c.name.substring(0, 15)),
                    datasets: [{
                        label: 'Commits',
                        data: data.contributors.slice(0, 10).map(c => c.commit_count),
                        backgroundColor: '#3498db',
                        borderColor: '#2980b9',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: { display: false },
                        title: {
                            display: true,
                            text: 'Top 10 Contributors'
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                stepSize: 1
                            }
                        }
                    }
                }
            });
        }

        showContent(contentId, loadingId);

    } catch (error) {
        showError(errorId, error.message);
        hideLoading(loadingId);
    }
}

async function loadCommits(page = 1) {
    const loadingId = 'commitsLoading';
    const contentId = 'commitsContent';
    const errorId = 'commitsError';

    showLoading(loadingId);

    try {
        const data = await fetchJSON(apiBase + '/commits?page=' + page + '&per_page=25');

        const tableBody = document.getElementById('commitsTableBody');
        tableBody.innerHTML = data.commits.map(c => `
            <tr>
                <td><code class="sha-link">${c.short_sha}</code></td>
                <td>${c.author.name}</td>
                <td class="commit-message" title="${c.message_first_line}">${c.message_first_line}</td>
                <td>${formatDate(c.date)}</td>
                <td>+${c.insertions} -${c.deletions}</td>
            </tr>
        `).join('');

        const pagination = document.getElementById('commitsPagination');
        if (pagination) {
            const totalPages = data.pagination.pages;
            let paginationHtml = '';

            if (page > 1) {
                paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="loadCommits(${page - 1}); return false;">Previous</a></li>`;
            }

            for (let i = Math.max(1, page - 2); i <= Math.min(totalPages, page + 2); i++) {
                const active = i === page ? 'active' : '';
                paginationHtml += `<li class="page-item ${active}"><a class="page-link" href="#" onclick="loadCommits(${i}); return false;">${i}</a></li>`;
            }

            if (page < totalPages) {
                paginationHtml += `<li class="page-item"><a class="page-link" href="#" onclick="loadCommits(${page + 1}); return false;">Next</a></li>`;
            }

            pagination.innerHTML = paginationHtml;
        }

        showContent(contentId, loadingId);

    } catch (error) {
        showError(errorId, error.message);
        hideLoading(loadingId);
    }
}

async function loadMessages() {
    const loadingId = 'messagesLoading';
    const contentId = 'messagesContent';
    const errorId = 'messagesError';

    showLoading(loadingId);

    try {
        const data = await fetchJSON(apiBase + '/messages');

        const tableBody = document.getElementById('messagesTableBody');
        tableBody.innerHTML = data.messages.map(m => `
            <tr>
                <td>${m.category}</td>
                <td>${m.count}</td>
                <td>${m.percentage}%</td>
                <td>${m.examples.join('<br>')}</td>
            </tr>
        `).join('');

        const ctx = document.getElementById('messagesChart');
        if (ctx) {
            if (messagesChart) messagesChart.destroy();

            messagesChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: data.messages.map(m => m.category),
                    datasets: [{
                        data: data.messages.map(m => m.count),
                        backgroundColor: [
                            '#3498db', '#e74c3c', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right'
                        }
                    }
                }
            });
        }

        showContent(contentId, loadingId);

    } catch (error) {
        showError(errorId, error.message);
        hideLoading(loadingId);
    }
}

async function loadFiles() {
    const loadingId = 'filesLoading';
    const contentId = 'filesContent';
    const errorId = 'filesError';

    showLoading(loadingId);

    try {
        const data = await fetchJSON(apiBase + '/files?limit=20');

        const tableBody = document.getElementById('filesTableBody');
        tableBody.innerHTML = data.files.slice(0, 20).map(f => `
            <tr>
                <td><code>${f.path}</code></td>
                <td>${f.change_count}</td>
                <td class="text-success">+${f.insertions}</td>
                <td class="text-danger">-${f.deletions}</td>
                <td>${formatDate(f.last_changed)}</td>
            </tr>
        `).join('');

        showContent(contentId, loadingId);
    } catch (error) {
        showError(errorId, error.message);
        hideLoading(loadingId);
    }
}

async function loadBranches() {
    const loadingId = 'branchesLoading';
    const contentId = 'branchesContent';
    const errorId = 'branchesError';

    showLoading(loadingId);

    try {
        const data = await fetchJSON(apiBase + '/branches');

        const tableBody = document.getElementById('branchesTableBody');
        tableBody.innerHTML = data.branches.map(b => `
            <tr>
                <td>
                    ${b.is_current ? '<span class="badge bg-primary branch-current">current</span> ' : ''}
                    ${b.is_remote ? '<span class="badge bg-secondary branch-remote">remote</span> ' : ''}
                    ${b.name}
                </td>
                <td>${b.is_remote ? 'Remote' : 'Local'}</td>
                <td><code>${b.last_commit_sha}</code></td>
                <td>${formatDate(b.last_commit_date)}</td>
            </tr>
        `).join('');

        showContent(contentId, loadingId);

    } catch (error) {
        showError(errorId, error.message);
        hideLoading(loadingId);
    }
}

document.addEventListener('DOMContentLoaded', function() {
    const path = window.repoPath || document.querySelector('main')?.dataset?.repoPath;
    if (!path) return;

    const tabs = document.getElementById('dashboardTabs');
    if (!tabs) return;

    tabs.addEventListener('shown.bs.tab', function(event) {
        const targetId = event.target.getAttribute('data-bs-target');

        if (targetId === '#overview' || targetId === '#commits') {
            loadCommits(1);
        } else if (targetId === '#contributors') {
            loadContributors();
        } else if (targetId === '#activity') {
            loadActivity();
        } else if (targetId === '#files') {
            loadFiles();
        } else if (targetId === '#branches') {
            loadBranches();
        } else if (targetId === '#messages') {
            loadMessages();
        }
    });
});