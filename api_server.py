const express = require('express');
const crypto = require('crypto');
const app = express();

app.disable('x-powered-by');
app.use(express.json({ limit: '10kb' }));

const API_KEY = process.env.API_KEY || 'Render:Luau.api';

app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

let cachedPayload = null;
let cacheTime = 0;
const CACHE_TTL = 300000;

app.get('/payload', (req, res) => {
  const { 'x-api-key': key, 'x-timestamp': ts, 'x-signature': sig } = req.headers;
  
  if (key !== API_KEY) return res.status(401).end();
  
  const expected = crypto.createHash('sha256')
    .update(API_KEY + ts)
    .digest('hex');
    
  if (sig !== expected) return res.status(401).end();
  
  if (cachedPayload && Date.now() - cacheTime < CACHE_TTL) {
    return res.json(cachedPayload);
  }
  
  cachedPayload = {
    language: 'luau',
    code: 'print("Hello from Render!")'
  };
  cacheTime = Date.now();
  
  res.json(cachedPayload);
});

app.listen(process.env.PORT || 3000);
