# Integrated Financial Trading Platform

A comprehensive, full-stack trading platform supporting multiple asset classes with advanced algorithmic trading capabilities, real-time market data, and a modern user interface.

## 🚀 Features

### Core Trading Features
- **Multi-Asset Support**: Stocks, Bonds, Forex, Indices, Commodities, Crypto, ETFs, ATFs, and Real Estate
- **Real-Time Market Data**: Live price updates via WebSocket connections
- **Paper Trading**: Risk-free trading simulation
- **Portfolio Management**: Track positions, P&L, and performance metrics
- **Order Management**: Market, Limit, Stop, and Stop-Limit orders

### Advanced Features
- **Algorithmic Trading**: ML-powered trading strategies
- **Strategy Builder**: Visual strategy creation with React Flow
- **Backtesting**: Historical strategy performance analysis
- **Risk Management**: Position sizing, stop-loss, and take-profit orders
- **Performance Analytics**: Comprehensive reporting and metrics

### Technical Features
- **Microservices Architecture**: Scalable and maintainable
- **Real-Time Updates**: WebSocket-based live data streaming
- **RESTful APIs**: Well-documented and versioned
- **Database Migrations**: Alembic for schema management
- **Docker Support**: Containerized deployment
- **Responsive UI**: Mobile-first design with Tailwind CSS

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Real-Time     │
│   (React)       │◄──►│   (FastAPI)     │◄──►│   (Node.js)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │   PostgreSQL    │              │
         │              │   Database      │              │
         │              └─────────────────┘              │
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         └──────────────►│     Redis      │◄─────────────┘
                        │     Cache       │
                        └─────────────────┘
```

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.12+)
- **Database**: PostgreSQL 15+
- **Cache**: Redis
- **ML Libraries**: TensorFlow, scikit-learn, XGBoost
- **Task Queue**: Celery
- **Authentication**: JWT tokens

### Frontend
- **Framework**: React 18+
- **State Management**: Zustand
- **UI Library**: Tailwind CSS
- **Charts**: Recharts
- **Real-time**: Socket.io
- **Strategy Builder**: React Flow

### Infrastructure
- **Containerization**: Docker
- **Cloud**: AWS (ECS, RDS, ElastiCache, S3, Lambda)
- **CI/CD**: GitHub Actions
- **Monitoring**: CloudWatch

## 📦 Installation

### Prerequisites
- Python 3.12+
- Node.js 18+
- PostgreSQL 15+
- Redis
- Docker (optional)

### Quick Start with Docker

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd trading-platform
   ```

2. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Start the services**
   ```bash
   docker-compose up -d
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Real-time Server: http://localhost:4000

### Manual Installation

1. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   alembic upgrade head
   uvicorn app.main:app --reload
   ```

2. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

3. **Real-time Server Setup**
   ```bash
   cd realtime
   npm install
   npm run dev
   ```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/trading_platform
REDIS_URL=redis://localhost:6379/0

# API Keys
ALPHA_VANTAGE_KEY=your_alpha_vantage_key
COINGECKO_API_KEY=your_coingecko_key
QUANDL_API_KEY=your_quandl_key

# JWT
JWT_SECRET_KEY=your_secret_key
JWT_ALGORITHM=HS256

# AWS (for production)
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
S3_BUCKET_NAME=your_bucket_name
```

### API Keys Required

- **Alpha Vantage**: For stocks, forex, and indices data
- **CoinGecko**: For cryptocurrency data
- **Quandl**: For commodities and real estate data
- **Stripe**: For payment processing (optional)

## 📊 Supported Asset Types

| Asset Type | Data Source | Update Frequency |
|------------|-------------|------------------|
| Stocks | Alpha Vantage | 5 seconds |
| Crypto | CoinGecko | 3 seconds |
| Forex | Alpha Vantage | 10 seconds |
| Commodities | Quandl | 30 seconds |
| Indices | Alpha Vantage | 10 seconds |
| ETFs | Alpha Vantage | 5 seconds |
| Bonds | Mock/API | 60 seconds |
| Real Estate | Alpha Vantage | 1 hour |

## 🚀 Usage

### Basic Trading

1. **Select an Asset**: Choose from the asset list or search
2. **View Real-Time Data**: Monitor live price updates
3. **Place Orders**: Use the trading form to execute trades
4. **Monitor Portfolio**: Track your positions and P&L

### Algorithmic Trading

1. **Create Strategy**: Use the strategy builder
2. **Configure Parameters**: Set risk levels and thresholds
3. **Backtest**: Test on historical data
4. **Deploy**: Activate for live trading

### API Usage

```python
import requests

# Get asset data
response = requests.get('http://localhost:8000/api/v1/assets/symbol/AAPL')
asset_data = response.json()

# Place a trade
trade_data = {
    "asset_id": 1,
    "side": "BUY",
    "order_type": "MARKET",
    "quantity": 10
}
response = requests.post('http://localhost:8000/api/v1/trades/', json=trade_data)
```

## 🧪 Testing

### Backend Tests
```bash
cd backend
pytest
```

### Frontend Tests
```bash
cd frontend
npm test
```

### Integration Tests
```bash
# Test API connections
python scripts/fetch_test.py
```

## 📈 Performance

- **Real-time Updates**: < 100ms latency
- **API Response Time**: < 200ms average
- **Database Queries**: Optimized with indexes
- **Caching**: Redis for frequently accessed data
- **Scalability**: Horizontal scaling support

## 🔒 Security

- **Authentication**: JWT-based token system
- **Rate Limiting**: API request throttling
- **Input Validation**: Pydantic models
- **HTTPS**: SSL/TLS encryption
- **Audit Trails**: Complete transaction logging

## 🚀 Deployment

### AWS Deployment

1. **Build and push Docker images**
   ```bash
   aws ecr create-repository --repository-name trading-platform-backend
   docker build -t trading-platform-backend ./backend
   docker tag trading-platform-backend:latest <account>.dkr.ecr.<region>.amazonaws.com/trading-platform-backend:latest
   docker push <account>.dkr.ecr.<region>.amazonaws.com/trading-platform-backend:latest
   ```

2. **Deploy to ECS**
   ```bash
   aws ecs create-cluster --cluster-name trading-platform
   aws ecs create-service --cluster trading-platform --service-name backend --task-definition trading-platform-backend
   ```

### Environment-Specific Configuration

- **Development**: Local Docker setup
- **Staging**: AWS ECS with RDS
- **Production**: Multi-AZ deployment with CloudFront

## 📚 API Documentation

### Endpoints

- **Assets**: `/api/v1/assets/`
- **Trades**: `/api/v1/trades/`
- **Users**: `/api/v1/users/`
- **Strategies**: `/api/v1/strategies/`
- **ML**: `/api/v1/ml/`
- **Reports**: `/api/v1/reports/`

### WebSocket Events

- **Subscribe**: `subscribe` - Subscribe to asset updates
- **Unsubscribe**: `unsubscribe` - Unsubscribe from asset updates
- **Market Update**: `market_update` - Real-time price data

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

- **Documentation**: [API Docs](http://localhost:8000/docs)
- **Issues**: GitHub Issues
- **Discussions**: GitHub Discussions

## 🗺️ Roadmap

### Phase 6-13 (Upcoming)
- [ ] Subscription and Payment Integration
- [ ] Advanced ML Models (XGBoost, VGG)
- [ ] High-Frequency Trading Support
- [ ] Mobile Applications
- [ ] Advanced Analytics Dashboard
- [ ] Social Trading Features
- [ ] Regulatory Compliance Tools

## 📊 Project Status

- ✅ Phase 1: Project Planning and Architecture
- ✅ Phase 2: Environment Setup
- ✅ Phase 3: Database Design and Backend
- ✅ Phase 4: Real-Time Market Data
- ✅ Phase 5: Frontend Dashboard
- 🔄 Phase 6: Subscriptions and Strategies (In Progress)
- ⏳ Phase 7-13: Advanced Features (Planned)

---

**Built with ❤️ for the trading community**
