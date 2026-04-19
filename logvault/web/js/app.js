function logvault() {
  return {
    tab: 'logs',
    logs: [],
    streamLogs: [],
    filters: {
      q: '',
      level: '',
      service: '',
      host: ''
    },
    cursor: null,
    hasMore: false,
    loading: false,
    streamConnected: false,
    eventSource: null,
    analytics: {
      totalLogs: 0,
      logsLast24h: 0,
      errorCount: 0,
      errorRate: 0,
      levels: [],
      services: []
    }
  }
}

function logvault() {
  return {
    tab: 'logs',
    logs: [],
    streamLogs: [],
    filters: { q: '', level: '', service: '', host: '' },
    cursor: null,
    hasMore: false,
    loading: false,
    streamConnected: false,
    eventSource: null,
    analytics: { totalLogs: 0, logsLast24h: 0, errorCount: 0, errorRate: 0, levels: [], services: [] },
    
    init() {
      this.loadLogs()
      this.loadAnalytics()
    },
    
    async loadLogs() {
      this.loading = true
      const params = new URLSearchParams()
      if (this.filters.q) params.append('q', this.filters.q)
      if (this.filters.level) params.append('level', this.filters.level)
      if (this.filters.service) params.append('service', this.filters.service)
      if (this.filters.host) params.append('host', this.filters.host)
      params.append('limit', '100')
      
      try {
        const res = await fetch('/api/v1/logs?' + params)
        const data = await res.json()
        this.logs = data.logs || []
        this.cursor = data.cursor
        this.hasMore = !!data.cursor
      } catch (e) {
        console.error('Failed to load logs:', e)
      }
      this.loading = false
    },
    
    async loadMore() {
      if (!this.cursor) return
      this.loading = true
      const params = new URLSearchParams(this.filters)
      params.append('cursor', this.cursor)
      params.append('limit', '100')
      
      try {
        const res = await fetch('/api/v1/logs?' + params)
        const data = await res.json()
        this.logs = [...this.logs, ...(data.logs || [])]
        this.cursor = data.cursor
        this.hasMore = !!data.cursor
      } catch (e) {
        console.error('Failed to load more logs:', e)
      }
      this.loading = false
    },
    
    clearFilters() {
      this.filters = { q: '', level: '', service: '', host: '' }
      this.loadLogs()
    },
    
    async loadAnalytics() {
      try {
        const [summary, levels] = await Promise.all([
          fetch('/api/v1/analytics/summary').then(r => r.json()),
          fetch('/api/v1/analytics/levels').then(r => r.json())
        ])
        this.analytics = { ...this.analytics, ...summary, levels: levels.by_percentage || [] }
      } catch (e) {
        console.error('Failed to load analytics:', e)
      }
    },
    
    toggleStream() {
      if (this.streamConnected) {
        this.connectStream()
      } else if (this.eventSource) {
        this.eventSource.close()
        this.eventSource = null
      }
    },
    
    connectStream() {
      const params = new URLSearchParams()
      if (this.filters.level) params.append('level', this.filters.level)
      if (this.filters.service) params.append('service', this.filters.service)
      
      this.eventSource = new EventSource('/api/v1/stream?' + params)
      this.eventSource.onmessage = (e) => {
        const log = JSON.parse(e.data)
        this.streamLogs.unshift(log)
        if (this.streamLogs.length > 500) this.streamLogs.pop()
      }
      this.eventSource.onerror = () => {
        this.streamConnected = false
      }
      this.streamConnected = true
    },
    
    formatTime(ts) {
      return new Date(ts).toLocaleString()
    }
  }
}