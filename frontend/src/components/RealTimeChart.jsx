/**
 * Real-time chart component for displaying live market data.
 */

import React, { useEffect, useState, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Activity } from 'lucide-react';
import useWebSocket from '../hooks/useWebSocket';

const RealTimeChart = ({ 
  symbol, 
  assetType, 
  height = 300, 
  showIndicators = true,
  className = '' 
}) => {
  const { isConnected, lastMessage, subscribe, unsubscribe } = useWebSocket();
  const [chartData, setChartData] = useState([]);
  const [priceChange, setPriceChange] = useState(0);
  const [currentPrice, setCurrentPrice] = useState(0);
  const maxDataPoints = 50;
  const chartRef = useRef(null);

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
      const newDataPoint = {
        time: new Date(lastMessage.timestamp).toLocaleTimeString(),
        price: lastMessage.data.price || lastMessage.data.current_price,
        volume: lastMessage.data.volume || 0,
        timestamp: lastMessage.timestamp
      };

      setChartData(prev => {
        const newData = [...prev, newDataPoint];
        return newData.slice(-maxDataPoints);
      });

      if (lastMessage.data.price || lastMessage.data.current_price) {
        const newPrice = lastMessage.data.price || lastMessage.data.current_price;
        setPriceChange(newPrice - currentPrice);
        setCurrentPrice(newPrice);
      }
    }
  }, [lastMessage, symbol, currentPrice]);

  const formatPrice = (price) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(price);
  };

  const formatChange = (change) => {
    const sign = change >= 0 ? '+' : '';
    return `${sign}${change.toFixed(2)}`;
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-500';
    if (change < 0) return 'text-red-500';
    return 'text-gray-500';
  };

  const getChangeIcon = (change) => {
    if (change > 0) return <TrendingUp className="w-4 h-4" />;
    if (change < 0) return <TrendingDown className="w-4 h-4" />;
    return <Activity className="w-4 h-4" />;
  };

  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{`Time: ${label}`}</p>
          <p className="text-gray-700">
            {`Price: ${formatPrice(payload[0].value)}`}
          </p>
          {payload[1] && (
            <p className="text-gray-700">
              {`Volume: ${payload[1].value?.toLocaleString() || 'N/A'}`}
            </p>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center space-x-2">
          <h3 className="text-lg font-semibold text-gray-900">{symbol}</h3>
          <div className={`flex items-center space-x-1 ${getChangeColor(priceChange)}`}>
            {getChangeIcon(priceChange)}
            <span className="text-sm font-medium">
              {formatChange(priceChange)}
            </span>
          </div>
        </div>
        
        <div className="flex items-center space-x-4">
          <div className="text-right">
            <p className="text-2xl font-bold text-gray-900">
              {formatPrice(currentPrice)}
            </p>
            <p className="text-sm text-gray-500">
              {formatChange(priceChange)} ({((priceChange / currentPrice) * 100).toFixed(2)}%)
            </p>
          </div>
          
          <div className="flex items-center space-x-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
            <span className="text-xs text-gray-500">
              {isConnected ? 'Live' : 'Disconnected'}
            </span>
          </div>
        </div>
      </div>

      <div className="h-64">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={chartData} ref={chartRef}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis 
              dataKey="time" 
              stroke="#666"
              fontSize={12}
              tickLine={false}
              axisLine={false}
            />
            <YAxis 
              stroke="#666"
              fontSize={12}
              tickLine={false}
              axisLine={false}
              tickFormatter={(value) => `$${value.toFixed(2)}`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line
              type="monotone"
              dataKey="price"
              stroke="#3b82f6"
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: '#3b82f6' }}
            />
            {showIndicators && (
              <Line
                type="monotone"
                dataKey="volume"
                stroke="#10b981"
                strokeWidth={1}
                dot={false}
                opacity={0.6}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {chartData.length === 0 && (
        <div className="flex items-center justify-center h-64 text-gray-500">
          <div className="text-center">
            <Activity className="w-8 h-8 mx-auto mb-2 opacity-50" />
            <p>Waiting for market data...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default RealTimeChart;
