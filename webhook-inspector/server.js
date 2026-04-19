const express = require('express');
const cors = require('cors');
const path = require('path');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true, limit: '10mb' }));
app.use(express.static(path.join(__dirname, 'public')));

let requests = [];
let sseClients = [];

app.get('/events', (req, res) => {
  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.flushHeaders();

  sseClients.push(res);
  console.log(`SSE client connected. Total clients: ${sseClients.length}`);

  res.write(`data: ${JSON.stringify({ type: 'connected' })}\n\n`);

  req.on('close', () => {
    sseClients = sseClients.filter(client => client !== res);
    console.log(`SSE client disconnected. Total clients: ${sseClients.length}`);
  });
});

function broadcastNewRequest(request) {
  const data = JSON.stringify({ type: 'new-request', data: request });
  sseClients.forEach(client => {
    client.write(data + '\n\n');
  });
}

app.all('/webhook', (req, res) => {
  const requestData = {
    id: `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
    timestamp: new Date().toISOString(),
    method: req.method,
    path: req.path,
    query: req.query,
    headers: req.headers,
    body: req.body,
    contentType: req.headers['content-type'] || 'unknown',
    ip: req.ip || req.connection.remoteAddress
  };

  requests.unshift(requestData);

  if (requests.length > 100) {
    requests = requests.slice(0, 100);
  }

  console.log(`[${req.method}] ${req.path} - ${requestData.id}`);

  broadcastNewRequest(requestData);

  res.json({
    success: true,
    message: 'Webhook received',
    requestId: requestData.id,
    timestamp: requestData.timestamp
  });
});

app.all('/webhook/*', (req, res, next) => {
  req.url = req.url.replace('/webhook', '');
  app._router.handle(req, res, next);
});

app.get('/api/requests', (req, res) => {
  res.json(requests);
});

app.delete('/api/requests', (req, res) => {
  requests = [];
  sseClients.forEach(client => {
    client.write(`data: ${JSON.stringify({ type: 'cleared' })}\n\n`);
  });
  res.json({ success: true, message: 'All requests cleared' });
});

app.get('/api/requests/:id', (req, res) => {
  const request = requests.find(r => r.id === req.params.id);
  if (request) {
    res.json(request);
  } else {
    res.status(404).json({ error: 'Request not found' });
  }
});

app.get('/', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`
╔═══════════════════════════════════════════════════╗
║           Webhook Inspector Running              ║
╠═══════════════════════════════════════════════════╣
║  Webhook URL: http://localhost:${PORT}/webhook       ║
║  UI:          http://localhost:${PORT}                 ║
║  SSE:        http://localhost:${PORT}/events          ║
╚═══════════════════════════════════════════════════╝
  `);
});

module.exports = app;