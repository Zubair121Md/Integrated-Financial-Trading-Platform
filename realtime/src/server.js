/**
 * Real-time market data server for the trading platform.
 * Handles WebSocket connections and market data streaming.
 */

const express = require('express');
const http = require('http');
const socketIo = require('socket.io');
const redis = require('redis');
const fetch = require('node-fetch');
const cors = require('cors');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const io = socketIo(server, {
  cors: {
    origin: ["http://localhost:3000", "http://localhost:4000"],
    methods: ["GET", "POST"]
  }
});

// Redis client
const redisClient = redis.createClient({
  url: process.env.REDIS_URL || 'redis://localhost:6379/0'
});

// Market data handlers for different asset types
const marketDataHandlers = {
  STOCK: async (symbol) => {
    const apiKey = process.env.ALPHA_VANTAGE_KEY;
    if (!apiKey) return null;
    
    const url = `https://www.alphavantage.co/query?function=TIME_SERIES_INTRADAY&symbol=${symbol}&interval=1min&apikey=${apiKey}`;
    const response = await fetch(url);
    const data = await response.json();
    
    if (data['Error Message']) {
      throw new Error(data['Error Message']);
    }
    
    return data;
  },
  
  CRYPTO: async (symbol) => {
    const url = `https://api.coingecko.com/api/v3/simple/price?ids=${symbol}&vs_currencies=usd&include_24hr_change=true`;
    const response = await fetch(url);
    const data = await response.json();
    
    return data;
  },
  
  FOREX: async (symbol) => {
    const apiKey = process.env.ALPHA_VANTAGE_KEY;
    if (!apiKey) return null;
    
    const [from, to] = symbol.split('/');
    const url = `https://www.alphavantage.co/query?function=FX_INTRADAY&from_symbol=${from}&to_symbol=${to}&interval=1min&apikey=${apiKey}`;
    const response = await fetch(url);
    const data = await response.json();
    
    if (data['Error Message']) {
      throw new Error(data['Error Message']);
    }
    
    return data;
  }
};

// Polling intervals for different asset types (in milliseconds)
const pollingIntervals = {
  STOCK: 5000,    // 5 seconds
  CRYPTO: 3000,   // 3 seconds
  FOREX: 10000,   // 10 seconds
  BOND: 60000,    // 1 minute
  COMMODITY: 30000, // 30 seconds
  INDEX: 10000,   // 10 seconds
  ETF: 5000,      // 5 seconds
  ATF: 300000,    // 5 minutes
  REAL_ESTATE: 3600000 // 1 hour
};

// Active subscriptions
const subscriptions = new Map();

// Connect to Redis
redisClient.connect().catch(console.error);

// Middleware
app.use(cors());
app.use(express.json());

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    connections: io.engine.clientsCount
  });
});

// Socket.IO connection handling
io.on('connection', (socket) => {
  console.log(`Client connected: ${socket.id}`);
  
  // Subscribe to market data
  socket.on('subscribe', async ({ assetType, symbol }) => {
    const subscriptionKey = `${assetType}:${symbol}`;
    console.log(`Subscribing to ${subscriptionKey}`);
    
    // Add to subscriptions map
    if (!subscriptions.has(subscriptionKey)) {
      subscriptions.set(subscriptionKey, new Set());
    }
    subscriptions.get(subscriptionKey).add(socket.id);
    
    // Start polling if this is the first subscriber
    if (subscriptions.get(subscriptionKey).size === 1) {
      startPolling(assetType, symbol);
    }
    
    socket.emit('subscribed', { assetType, symbol });
  });
  
  // Unsubscribe from market data
  socket.on('unsubscribe', ({ assetType, symbol }) => {
    const subscriptionKey = `${assetType}:${symbol}`;
    console.log(`Unsubscribing from ${subscriptionKey}`);
    
    if (subscriptions.has(subscriptionKey)) {
      subscriptions.get(subscriptionKey).delete(socket.id);
      
      // Stop polling if no more subscribers
      if (subscriptions.get(subscriptionKey).size === 0) {
        stopPolling(subscriptionKey);
        subscriptions.delete(subscriptionKey);
      }
    }
    
    socket.emit('unsubscribed', { assetType, symbol });
  });
  
  // Handle disconnection
  socket.on('disconnect', () => {
    console.log(`Client disconnected: ${socket.id}`);
    
    // Remove from all subscriptions
    for (const [key, subscribers] of subscriptions.entries()) {
      subscribers.delete(socket.id);
      if (subscribers.size === 0) {
        stopPolling(key);
        subscriptions.delete(key);
      }
    }
  });
});

// Polling management
const pollingTimers = new Map();

function startPolling(assetType, symbol) {
  const subscriptionKey = `${assetType}:${symbol}`;
  const interval = pollingIntervals[assetType] || 10000;
  
  const timer = setInterval(async () => {
    try {
      const handler = marketDataHandlers[assetType];
      if (!handler) {
        console.warn(`No handler for asset type: ${assetType}`);
        return;
      }
      
      const data = await handler(symbol);
      if (data) {
        // Cache the data in Redis
        await redisClient.setEx(
          `market_data:${subscriptionKey}`, 
          60, 
          JSON.stringify(data)
        );
        
        // Emit to all subscribers
        const subscribers = subscriptions.get(subscriptionKey);
        if (subscribers) {
          subscribers.forEach(socketId => {
            io.to(socketId).emit('market_update', {
              assetType,
              symbol,
              data,
              timestamp: new Date().toISOString()
            });
          });
        }
      }
    } catch (error) {
      console.error(`Error fetching data for ${subscriptionKey}:`, error.message);
    }
  }, interval);
  
  pollingTimers.set(subscriptionKey, timer);
  console.log(`Started polling for ${subscriptionKey} every ${interval}ms`);
}

function stopPolling(subscriptionKey) {
  const timer = pollingTimers.get(subscriptionKey);
  if (timer) {
    clearInterval(timer);
    pollingTimers.delete(subscriptionKey);
    console.log(`Stopped polling for ${subscriptionKey}`);
  }
}

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('SIGTERM received, shutting down gracefully');
  
  // Clear all polling timers
  for (const timer of pollingTimers.values()) {
    clearInterval(timer);
  }
  
  // Close Redis connection
  redisClient.quit();
  
  // Close server
  server.close(() => {
    console.log('Server closed');
    process.exit(0);
  });
});

const PORT = process.env.PORT || 4000;
server.listen(PORT, () => {
  console.log(`🚀 Real-time server running on port ${PORT}`);
  console.log(`📊 Market data streaming enabled`);
  console.log(`🔗 WebSocket endpoint: ws://localhost:${PORT}`);
});
