/**
 * Portfolio summary component displaying user's portfolio information.
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  BarChart3,
  PieChart,
  Activity,
  ArrowUpRight,
  ArrowDownRight
} from 'lucide-react';

const PortfolioSummary = () => {
  const [portfolioData, setPortfolioData] = useState({
    totalValue: 10250.00,
    totalPnL: 1250.00,
    totalPnLPercent: 13.9,
    dayChange: 250.00,
    dayChangePercent: 2.5,
    positions: [
      {
        id: 1,
        symbol: 'AAPL',
        name: 'Apple Inc.',
        quantity: 10,
        averagePrice: 150.00,
        currentPrice: 175.00,
        marketValue: 1750.00,
        unrealizedPnL: 250.00,
        unrealizedPnLPercent: 16.67,
        weight: 17.07
      },
      {
        id: 2,
        symbol: 'GOOGL',
        name: 'Alphabet Inc.',
        quantity: 5,
        averagePrice: 2000.00,
        currentPrice: 2100.00,
        marketValue: 10500.00,
        unrealizedPnL: 500.00,
        unrealizedPnLPercent: 5.0,
        weight: 102.44
      },
      {
        id: 3,
        symbol: 'BTC',
        name: 'Bitcoin',
        quantity: 0.5,
        averagePrice: 40000.00,
        currentPrice: 45000.00,
        marketValue: 22500.00,
        unrealizedPnL: 2500.00,
        unrealizedPnLPercent: 12.5,
        weight: 219.51
      }
    ],
    cashBalance: 1000.00
  });

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatPercent = (percent) => {
    return `${percent >= 0 ? '+' : ''}${percent.toFixed(2)}%`;
  };

  const getChangeColor = (change) => {
    if (change > 0) return 'text-green-600';
    if (change < 0) return 'text-red-600';
    return 'text-gray-600';
  };

  const getChangeIcon = (change) => {
    if (change > 0) return <ArrowUpRight className="w-4 h-4" />;
    if (change < 0) return <ArrowDownRight className="w-4 h-4" />;
    return null;
  };

  return (
    <div className="space-y-6">
      {/* Portfolio Overview */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total Value</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(portfolioData.totalValue)}
              </p>
            </div>
            <DollarSign className="w-8 h-8 text-blue-600" />
          </div>
          <div className={`flex items-center space-x-1 mt-2 ${getChangeColor(portfolioData.dayChange)}`}>
            {getChangeIcon(portfolioData.dayChange)}
            <span className="text-sm font-medium">
              {formatCurrency(portfolioData.dayChange)} ({formatPercent(portfolioData.dayChangePercent)})
            </span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Total P&L</p>
              <p className={`text-2xl font-bold ${getChangeColor(portfolioData.totalPnL)}`}>
                {formatCurrency(portfolioData.totalPnL)}
              </p>
            </div>
            <TrendingUp className="w-8 h-8 text-green-600" />
          </div>
          <div className={`flex items-center space-x-1 mt-2 ${getChangeColor(portfolioData.totalPnLPercent)}`}>
            <span className="text-sm font-medium">
              {formatPercent(portfolioData.totalPnLPercent)}
            </span>
          </div>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Cash Balance</p>
              <p className="text-2xl font-bold text-gray-900">
                {formatCurrency(portfolioData.cashBalance)}
              </p>
            </div>
            <BarChart3 className="w-8 h-8 text-purple-600" />
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Available for trading
          </p>
        </div>

        <div className="bg-white p-6 rounded-lg shadow-sm border border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm font-medium text-gray-600">Positions</p>
              <p className="text-2xl font-bold text-gray-900">
                {portfolioData.positions.length}
              </p>
            </div>
            <PieChart className="w-8 h-8 text-orange-600" />
          </div>
          <p className="text-sm text-gray-500 mt-2">
            Active holdings
          </p>
        </div>
      </div>

      {/* Positions Table */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-semibold text-gray-900">Positions</h3>
        </div>
        
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Symbol
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Quantity
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Avg Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Current Price
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Market Value
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  P&L
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Weight
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {portfolioData.positions.map((position) => (
                <tr key={position.id} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div>
                      <div className="text-sm font-medium text-gray-900">{position.symbol}</div>
                      <div className="text-sm text-gray-500">{position.name}</div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {position.quantity}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(position.averagePrice)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(position.currentPrice)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {formatCurrency(position.marketValue)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className={`flex items-center space-x-1 ${getChangeColor(position.unrealizedPnL)}`}>
                      {getChangeIcon(position.unrealizedPnL)}
                      <span className="text-sm font-medium">
                        {formatCurrency(position.unrealizedPnL)}
                      </span>
                    </div>
                    <div className={`text-xs ${getChangeColor(position.unrealizedPnLPercent)}`}>
                      {formatPercent(position.unrealizedPnLPercent)}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {position.weight.toFixed(1)}%
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Performance Chart Placeholder */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Activity className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Portfolio Performance</h3>
        </div>
        <div className="h-64 bg-gray-50 rounded-lg flex items-center justify-center">
          <div className="text-center text-gray-500">
            <BarChart3 className="w-12 h-12 mx-auto mb-2 opacity-50" />
            <p>Performance chart coming soon...</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioSummary;
