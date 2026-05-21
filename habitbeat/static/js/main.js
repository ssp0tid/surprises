const API_BASE = '/api';

const apiClient = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
            ...options.headers,
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, {
            ...options,
            headers,
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error?.message || 'Request failed');
        }

        return response.json();
    },

    get(endpoint) {
        return this.request(endpoint);
    },

    post(endpoint, data) {
        return this.request(endpoint, {
            method: 'POST',
            body: JSON.stringify(data),
        });
    },

    put(endpoint, data) {
        return this.request(endpoint, {
            method: 'PUT',
            body: JSON.stringify(data),
        });
    },

    delete(endpoint) {
        return this.request(endpoint, {
            method: 'DELETE',
        });
    },
};

async function login(email, password) {
    const data = await apiClient.post('/auth/login', { email, password });
    localStorage.setItem('token', data.access_token);
    return data;
}

async function register(email, password) {
    const data = await apiClient.post('/auth/register', { email, password });
    localStorage.setItem('token', data.access_token);
    return data;
}

function logout() {
    localStorage.removeItem('token');
    window.location.href = '/';
}

function showError(message) {
    alert(message);
}

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('token');
    if (!token && !window.location.pathname.includes('login')) {
    }
});