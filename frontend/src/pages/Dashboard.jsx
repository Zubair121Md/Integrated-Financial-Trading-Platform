/**
 * Main dashboard page for the trading platform.
 */

import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  BarChart3, 
  Activity,
  Plus,
  Settings,
  Bell,
  User
} from 'lucide-react';
import RealTimeChart from '../components/RealTimeChart';
import MarketDataWidget from '../components/MarketDataWidget';
import TradeForm from '../components/TradeForm';
import PortfolioSummary from '../components/PortfolioSummary';
import useWebSocket from '../hooks/useWebSocket';

const Dashboard = () => {
  const [activeTab, setActiveTab] = useState('overview');
  const [selectedAsset, setSelectedAsset] = useState({ symbol: 'AAPL', type: 'STOCK' });
  const { isConnected } = useWebSocket();

  const tabs = [
    { id: 'overview', label: 'Overview', icon: BarChart3 },
    { id: 'trading', label: 'Trading', icon: Activity },
    { id: 'portfolio', label: 'Portfolio', icon: TrendingUp },
    { id: 'strategies', label: 'Strategies', icon: Settings },
    { id: 'reports', label: 'Reports', icon: TrendingDown }
  ];

  const popularAssets = [
    { symbol: 'AAPL', type: 'STOCK', name: 'Apple Inc.' },
    { symbol: 'GOOGL', type: 'STOCK', name: 'Alphabet Inc.' },
    { symbol: 'MSFT', type: 'STOCK', name: 'Microsoft Corporation' },
    { symbol: 'BTC', type: 'CRYPTO', name: 'Bitcoin' },
    { symbol: 'ETH', type: 'CRYPTO', name: 'Ethereum' },
    { symbol: 'TSLA', type: 'STOCK', name: 'Tesla Inc.' }
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'overview':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <RealTimeChart 
                symbol={selectedAsset.symbol} 
                assetType={selectedAsset.type}
                height={400}
              />
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Quick Stats</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-blue-50 p-4 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <DollarSign className="w-5 h-5 text-blue-600" />
                      <span className="text-sm font-medium text-blue-900">Portfolio Value</span>
                    </div>
                    <p className="text-2xl font-bold text-blue-900 mt-1">$10,250.00</p>
                    <p className="text-sm text-blue-700">+2.5% today</p>
                  </div>
                  <div className="bg-green-50 p-4 rounded-lg">
                    <div className="flex items-center space-x-2">
                      <TrendingUp className="w-5 h-5 text-green-600" />
                      <span className="text-sm font-medium text-green-900">Total P&L</span>
                    </div>
                    <p className="text-2xl font-bold text-green-900 mt-1">+$1,250.00</p>
                    <p className="text-sm text-green-700">+13.9% overall</p>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {popularAssets.map((asset) => (
                <MarketDataWidget
                  key={`${asset.type}-${asset.symbol}`}
                  symbol={asset.symbol}
                  assetType={asset.type}
                  className="cursor-pointer hover:shadow-md transition-shadow"
                  onClick={() => setSelectedAsset(asset)}
                />
              ))}
            </div>
          </div>
        );
      
      case 'trading':
        return (
          <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2">
                <RealTimeChart 
                  symbol={selectedAsset.symbol} 
                  assetType={selectedAsset.type}
                  height={500}
                />
              </div>
              <div>
                <TradeForm selectedAsset={selectedAsset} />
              </div>
            </div>
          </div>
        );
      
      case 'portfolio':
        return (
          <div className="space-y-6">
            <PortfolioSummary />
          </div>
        );
      
      case 'strategies':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Trading Strategies</h3>
              <p className="text-gray-600">Strategy management coming soon...</p>
            </div>
          </div>
        );
      
      case 'reports':
        return (
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Performance Reports</h3>
              <p className="text-gray-600">Reports and analytics coming soon...</p>
            </div>
          </div>
        );
      
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center space-x-4">
              <h1 className="text-xl font-bold text-gray-900">Trading Platform</h1>
              <div className="flex items-center space-x-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`} />
                <span className="text-sm text-gray-600">
                  {isConnected ? 'Live Data' : 'Offline'}
                </span>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <Bell className="w-5 h-5" />
              </button>
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <Settings className="w-5 h-5" />
              </button>
              <button className="p-2 text-gray-400 hover:text-gray-600">
                <User className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Navigation Tabs */}
      <div className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <nav className="flex space-x-8">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`flex items-center space-x-2 py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-blue-500 text-blue-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{tab.label}</span>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {renderTabContent()}
      </main>
    </div>
  );
};

export default Dashboard;
