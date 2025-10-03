"""
Asset data handlers for different asset types and data sources.
"""

import asyncio
import json
from typing import Dict, Any, Optional
import httpx
import redis.asyncio as redis

from app.config import settings
from shared.enums.asset_types import AssetType


class AssetHandlerService:
    """Service for handling asset data from various sources."""
    
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_asset_data(self, asset_type: AssetType, symbol: str) -> Dict[str, Any]:
        """Fetch asset data based on type and symbol."""
        # Check cache first
        cache_key = f"asset_data:{asset_type.value}:{symbol}"
        cached_data = await self.redis_client.get(cache_key)
        if cached_data:
            return json.loads(cached_data)
        
        # Fetch from appropriate handler
        handler_map = {
            AssetType.STOCK: self._fetch_stock_data,
            AssetType.CRYPTO: self._fetch_crypto_data,
            AssetType.FOREX: self._fetch_forex_data,
            AssetType.COMMODITY: self._fetch_commodity_data,
            AssetType.INDEX: self._fetch_index_data,
            AssetType.ETF: self._fetch_etf_data,
            AssetType.BOND: self._fetch_bond_data,
            AssetType.REAL_ESTATE: self._fetch_real_estate_data,
            AssetType.ATF: self._fetch_atf_data,
        }
        
        handler = handler_map.get(asset_type)
        if not handler:
            raise ValueError(f"No handler for asset type: {asset_type}")
        
        try:
            data = await handler(symbol)
            # Cache for 5 minutes
            await self.redis_client.setex(cache_key, 300, json.dumps(data))
            return data
        except Exception as e:
            raise Exception(f"Failed to fetch {asset_type.value} data for {symbol}: {str(e)}")
    
    async def _fetch_stock_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch stock data from Alpha Vantage."""
        if not settings.alpha_vantage_key:
            raise ValueError("Alpha Vantage API key not configured")
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "GLOBAL_QUOTE",
            "symbol": symbol,
            "apikey": settings.alpha_vantage_key
        }
        
        response = await self.http_client.get(url, params=params)
        data = response.json()
        
        if "Error Message" in data:
            raise Exception(data["Error Message"])
        
        if "Global Quote" not in data:
            raise Exception("No data available")
        
        quote = data["Global Quote"]
        return {
            "symbol": symbol,
            "name": symbol,  # Would need additional API call for full name
            "price": float(quote.get("05. price", 0)),
            "previous_close": float(quote.get("08. previous close", 0)),
            "day_high": float(quote.get("03. high", 0)),
            "day_low": float(quote.get("04. low", 0)),
            "volume": float(quote.get("06. volume", 0)),
            "change": float(quote.get("09. change", 0)),
            "change_percent": quote.get("10. change percent", "0%").replace("%", ""),
            "metadata": {
                "source": "alpha_vantage",
                "last_refreshed": quote.get("07. latest trading day")
            }
        }
    
    async def _fetch_crypto_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch cryptocurrency data from CoinGecko."""
        # Map common symbols to CoinGecko IDs
        symbol_map = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "ADA": "cardano",
            "DOT": "polkadot",
            "LINK": "chainlink",
            "LTC": "litecoin",
            "BCH": "bitcoin-cash",
            "XRP": "ripple",
            "DOGE": "dogecoin",
            "SOL": "solana"
        }
        
        coin_id = symbol_map.get(symbol.upper(), symbol.lower())
        
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": coin_id,
            "vs_currencies": "usd",
            "include_24hr_change": "true",
            "include_market_cap": "true",
            "include_24hr_vol": "true"
        }
        
        response = await self.http_client.get(url, params=params)
        data = response.json()
        
        if coin_id not in data:
            raise Exception(f"Cryptocurrency {symbol} not found")
        
        coin_data = data[coin_id]
        return {
            "symbol": symbol,
            "name": coin_id.title(),
            "price": coin_data.get("usd", 0),
            "change_percent": coin_data.get("usd_24h_change", 0),
            "market_cap": coin_data.get("usd_market_cap", 0),
            "volume": coin_data.get("usd_24h_vol", 0),
            "metadata": {
                "source": "coingecko",
                "coin_id": coin_id
            }
        }
    
    async def _fetch_forex_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch forex data from Alpha Vantage."""
        if not settings.alpha_vantage_key:
            raise ValueError("Alpha Vantage API key not configured")
        
        # Parse symbol (e.g., "EUR/USD" -> "EUR", "USD")
        if "/" not in symbol:
            raise ValueError("Forex symbol must be in format 'FROM/TO' (e.g., 'EUR/USD')")
        
        from_currency, to_currency = symbol.split("/")
        
        url = "https://www.alphavantage.co/query"
        params = {
            "function": "CURRENCY_EXCHANGE_RATE",
            "from_currency": from_currency,
            "to_currency": to_currency,
            "apikey": settings.alpha_vantage_key
        }
        
        response = await self.http_client.get(url, params=params)
        data = response.json()
        
        if "Error Message" in data:
            raise Exception(data["Error Message"])
        
        if "Realtime Currency Exchange Rate" not in data:
            raise Exception("No data available")
        
        rate_data = data["Realtime Currency Exchange Rate"]
        return {
            "symbol": symbol,
            "name": f"{from_currency}/{to_currency}",
            "price": float(rate_data.get("5. Exchange Rate", 0)),
            "change_percent": 0,  # Would need historical data for change
            "metadata": {
                "source": "alpha_vantage",
                "from_currency": from_currency,
                "to_currency": to_currency,
                "last_refreshed": rate_data.get("6. Last Refreshed")
            }
        }
    
    async def _fetch_commodity_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch commodity data from Quandl."""
        if not settings.quandl_api_key:
            raise ValueError("Quandl API key not configured")
        
        # Map symbols to Quandl dataset codes
        symbol_map = {
            "GOLD": "LBMA/GOLD",
            "SILVER": "LBMA/SILVER",
            "OIL": "CHRIS/CME_CL1",
            "GAS": "CHRIS/CME_NG1"
        }
        
        dataset_code = symbol_map.get(symbol.upper())
        if not dataset_code:
            raise ValueError(f"Unsupported commodity symbol: {symbol}")
        
        url = f"https://www.quandl.com/api/v3/datasets/{dataset_code}.json"
        params = {
            "api_key": settings.quandl_api_key,
            "limit": 1
        }
        
        response = await self.http_client.get(url, params=params)
        data = response.json()
        
        if "error" in data:
            raise Exception(data["error"])
        
        if "dataset" not in data or not data["dataset"]["data"]:
            raise Exception("No data available")
        
        latest_data = data["dataset"]["data"][0]
        return {
            "symbol": symbol,
            "name": data["dataset"]["name"],
            "price": float(latest_data[1]),  # Assuming price is in second column
            "metadata": {
                "source": "quandl",
                "dataset_code": dataset_code,
                "last_refreshed": latest_data[0]  # Assuming date is in first column
            }
        }
    
    async def _fetch_index_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch index data from Alpha Vantage."""
        return await self._fetch_stock_data(symbol)  # Same as stock data
    
    async def _fetch_etf_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch ETF data from Alpha Vantage."""
        return await self._fetch_stock_data(symbol)  # Same as stock data
    
    async def _fetch_bond_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch bond data (mock implementation)."""
        # This would typically connect to a bond data provider
        return {
            "symbol": symbol,
            "name": f"Bond {symbol}",
            "price": 100.0,  # Mock price
            "yield": 2.5,  # Mock yield
            "metadata": {
                "source": "mock",
                "note": "Bond data not implemented"
            }
        }
    
    async def _fetch_real_estate_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch real estate data (REITs) from Alpha Vantage."""
        return await self._fetch_stock_data(symbol)  # REITs trade like stocks
    
    async def _fetch_atf_data(self, symbol: str) -> Dict[str, Any]:
        """Fetch Alternative Investment Fund data (mock implementation)."""
        return {
            "symbol": symbol,
            "name": f"ATF {symbol}",
            "price": 100.0,  # Mock price
            "metadata": {
                "source": "mock",
                "note": "ATF data not implemented"
            }
        }
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()
        await self.redis_client.close()
