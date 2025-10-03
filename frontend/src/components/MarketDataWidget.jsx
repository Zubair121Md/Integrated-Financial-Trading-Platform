/**
 * Market data widget for displaying real-time price information.
 */

import React, { useEffect, useState } from 'react';
import { TrendingUp, TrendingDown, Activity, DollarSign, BarChart3 } from 'lucide-react';
import useWebSocket from '../hooks/useWebSocket';

const MarketDataWidget = ({ 
  symbol, 
  assetType, 
  showChart = false,
  className = '' 
}) => {
  const { isConnected, lastMessage, subscribe, unsubscribe } = useWebSocket();
  const [marketData, setMarketData] = useState({
    price: 0,
    change: 0,
    changePercent: 0,
    volume: 0,
    high: 0,
    low: 0,
    open: 0
  });

  useEffect(() => {
    if (symbol && assetType) {
      subscribe(assetType, symbol);
    }

    return () => {
      if (symbol && assetType) {
        unsubscribe(assetType, symbol);
      }
    };
  }, [symbol, assetType, subscribe, unsubscribe]);

  useEffect(() => {
    if (lastMessage && lastMessage.symbol === symbol) {
      const data = lastMessage.data;
      setMarketData({
        price: data.price || data.current_price || 0,
        change: data.change || 0,
        changePercent: data.change_percent || 0,
        volume: data.volume || 0,
        high: data.day_high || data.high_price || 0,
        low: data.day_low || data.low_price || 0,
        open: data.open_price || 0
      });
    }
  }, [lastMessage, symbol]);

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price);
  };

  const formatVolume = (volume) => {
    if (volume >= 1e9) return `${(volume / 1e9).toFixed(1)}B`;
    if (volume >= 1e6) return `${(volume / 1e6).toFixed(1)}M`;
    if (volume >= 1e3) return `${(volume / 1e3).toFixed(1)}K`;
    return volume.toString();
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-500 bg-green-50';
    if (change < 0) return 'text-red-500 bg-red-50';
    return 'text-gray-500 bg-gray-50';
  };

  const getChangeIcon = (change) => {
    if (change > 0) return <TrendingUp className="w-4 h-4" />;
    if (change < 0) return <TrendingDown className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-4 ${className}`}>
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center space-x-2">
          <h3 className="font-semibold text-gray-900">{symbol}</h3>
          <span className="text-xs text-gray-500 uppercase">{assetType}</span>
        </div>
        
        <div className="flex items-center space-x-2">
          <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-gray-500">
            {isConnected ? 'Live' : 'Offline'}
          </span>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <DollarSign className="w-4 h-4 text-gray-500" />
            <span className="text-sm text-gray-600">Price</span>
          </div>
          <div className="text-right">
            <p className="text-lg font-bold text-gray-900">
              {formatPrice(marketData.price)}
            </p>
            <div className={`flex items-center space-x-1 ${getChangeColor(marketData.change)}`}>
              {getChangeIcon(marketData.change)}
              <span className="text-sm font-medium">
                {marketData.change > 0 ? '+' : ''}{marketData.change.toFixed(2)} 
                ({marketData.changePercent > 0 ? '+' : ''}{marketData.changePercent.toFixed(2)}%)
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4 text-sm">
          <div className="flex items-center justify-between">
            <span className="text-gray-600">High</span>
            <span className="font-medium">{formatPrice(marketData.high)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Low</span>
            <span className="font-medium">{formatPrice(marketData.low)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Open</span>
            <span className="font-medium">{formatPrice(marketData.open)}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-gray-600">Volume</span>
            <span className="font-medium">{formatVolume(marketData.volume)}</span>
          </div>
        </div>

        {showChart && (
          <div className="pt-3 border-t border-gray-200">
            <div className="flex items-center space-x-2 text-gray-600">
              <BarChart3 className="w-4 h-4" />
              <span className="text-sm">Chart view available</span>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MarketDataWidget;
