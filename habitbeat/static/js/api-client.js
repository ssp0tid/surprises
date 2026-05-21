const HabitbeatAPI = {
    baseURL: '/api',

    async request(endpoint, options = {}) {
        const token = localStorage.getItem('token');
        const headers = {
            'Content-Type': 'application/json',
        };

        if (token) {
            headers['Authorization'] = `Bearer ${token}`;
        }

        const response = await fetch(`${this.baseURL}${endpoint}`, {
            ...options,
            headers: { ...headers, ...options.headers },
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error?.message || 'API request failed');
        }

        return data;
    },

    auth: {
        async login(email, password) {
            return this.request('/auth/login', {
                method: 'POST',
                body: JSON.stringify({ email, password }),
            });
        },

        async register(email, password) {
            return this.request('/auth/register', {
                method: 'POST',
                body: JSON.stringify({ email, password }),
            });
        },

        async refresh() {
            return this.request('/auth/refresh', { method: 'POST' });
        },

        async logout() {
            return this.request('/auth/logout', { method: 'DELETE' });
        },
    },

    habits: {
        async list(active = true) {
            return this.request(`/habits?active=${active}`);
        },

        async get(id) {
            return this.request(`/habits/${id}`);
        },

        async create(data) {
            return this.request('/habits', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },

        async update(id, data) {
            return this.request(`/habits/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },

        async delete(id) {
            return this.request(`/habits/${id}`, { method: 'DELETE' });
        },

        async checkIn(id, data = {}) {
            return this.request(`/habits/${id}/checkins`, {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },

        async getCheckIns(id, limit = 30) {
            return this.request(`/habits/${id}/checkins?limit=${limit}`);
        },
    },

    categories: {
        async list() {
            return this.request('/categories');
        },

        async create(data) {
            return this.request('/categories', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },

        async update(id, data) {
            return this.request(`/categories/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },

        async delete(id) {
            return this.request(`/categories/${id}`, { method: 'DELETE' });
        },
    },

    analytics: {
        async getStreak(habitId) {
            return this.request(`/analytics/habits/${habitId}/streak`);
        },

        async getHabitAnalytics(habitId, options = {}) {
            const params = new URLSearchParams(options).toString();
            return this.request(`/analytics/habits/${habitId}/analytics?${params}`);
        },

        async getSummary() {
            return this.request('/analytics/summary');
        },
    },

    reminders: {
        async list(status) {
            const params = status ? `?status=${status}` : '';
            return this.request(`/reminders${params}`);
        },

        async create(data) {
            return this.request('/reminders', {
                method: 'POST',
                body: JSON.stringify(data),
            });
        },

        async update(id, data) {
            return this.request(`/reminders/${id}`, {
                method: 'PUT',
                body: JSON.stringify(data),
            });
        },

        async delete(id) {
            return this.request(`/reminders/${id}`, { method: 'DELETE' });
        },
    },
};

if (typeof module !== 'undefined' && module.exports) {
    module.exports = HabitbeatAPI;
}