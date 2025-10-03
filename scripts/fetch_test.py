#!/usr/bin/env python3
"""
Test script to verify API connections and data fetching.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

# Add the backend directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

load_dotenv()

def test_alpha_vantage():
    """Test Alpha Vantage API connection."""
    api_key = os.getenv('ALPHA_VANTAGE_KEY')
    if not api_key:
        print("❌ ALPHA_VANTAGE_KEY not found in environment variables")
        return False
    
    url = "https://www.alphavantage.co/query"
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': 'AAPL',
        'apikey': api_key
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'Error Message' in data:
            print(f"❌ Alpha Vantage Error: {data['Error Message']}")
            return False
        
        if 'Time Series (Daily)' in data:
            print("✅ Alpha Vantage API connection successful")
            print(f"📊 Sample data for AAPL: {list(data['Time Series (Daily)'].keys())[:3]}")
            return True
        else:
            print("❌ Unexpected response format from Alpha Vantage")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Alpha Vantage connection failed: {e}")
        return False

def test_coingecko():
    """Test CoinGecko API connection."""
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {
        'ids': 'bitcoin',
        'vs_currencies': 'usd',
        'include_24hr_change': 'true'
    }
    
    try:
        response = requests.get(url, params=params, timeout=10)
        data = response.json()
        
        if 'bitcoin' in data:
            print("✅ CoinGecko API connection successful")
            print(f"₿ Bitcoin price: ${data['bitcoin']['usd']}")
            return True
        else:
            print("❌ Unexpected response format from CoinGecko")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"❌ CoinGecko connection failed: {e}")
        return False

def test_redis():
    """Test Redis connection."""
    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
        client = redis.from_url(redis_url)
        client.ping()
        print("✅ Redis connection successful")
        return True
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        return False

def test_database():
    """Test PostgreSQL connection."""
    try:
        from sqlalchemy import create_engine
        database_url = os.getenv('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/trading_platform')
        engine = create_engine(database_url)
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            print("✅ PostgreSQL connection successful")
            return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        return False

def main():
    """Run all tests."""
    print("🧪 Testing API connections and data fetching...\n")
    
    tests = [
        ("Alpha Vantage", test_alpha_vantage),
        ("CoinGecko", test_coingecko),
        ("Redis", test_redis),
        ("PostgreSQL", test_database),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"Testing {name}...")
        result = test_func()
        results.append((name, result))
        print()
    
    # Summary
    print("📋 Test Summary:")
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {name}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The platform is ready to go.")
    else:
        print("⚠️  Some tests failed. Please check your configuration.")

if __name__ == "__main__":
    main()
