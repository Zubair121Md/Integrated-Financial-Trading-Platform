/**
 * Trading form component for executing trades.
 */

import React, { useState } from 'react';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Calculator,
  AlertCircle,
  CheckCircle
} from 'lucide-react';

const TradeForm = ({ selectedAsset, onTradeExecuted }) => {
  const [tradeData, setTradeData] = useState({
    side: 'BUY',
    orderType: 'MARKET',
    quantity: '',
    price: '',
    stopLoss: '',
    takeProfit: '',
    notes: ''
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});
  const [success, setSuccess] = useState(false);

  const orderTypes = [
    { value: 'MARKET', label: 'Market Order' },
    { value: 'LIMIT', label: 'Limit Order' },
    { value: 'STOP', label: 'Stop Order' },
    { value: 'STOP_LIMIT', label: 'Stop Limit Order' }
  ];

  const validateForm = () => {
    const newErrors = {};
    
    if (!tradeData.quantity || parseFloat(tradeData.quantity) <= 0) {
      newErrors.quantity = 'Quantity must be greater than 0';
    }
    
    if (tradeData.orderType === 'LIMIT' && (!tradeData.price || parseFloat(tradeData.price) <= 0)) {
      newErrors.price = 'Price is required for limit orders';
    }
    
    if (tradeData.stopLoss && parseFloat(tradeData.stopLoss) <= 0) {
      newErrors.stopLoss = 'Stop loss must be greater than 0';
    }
    
    if (tradeData.takeProfit && parseFloat(tradeData.takeProfit) <= 0) {
      newErrors.takeProfit = 'Take profit must be greater than 0';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }
    
    setIsSubmitting(true);
    setSuccess(false);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      const trade = {
        assetId: selectedAsset.id || 1,
        symbol: selectedAsset.symbol,
        side: tradeData.side,
        orderType: tradeData.orderType,
        quantity: parseFloat(tradeData.quantity),
        price: tradeData.price ? parseFloat(tradeData.price) : null,
        stopLoss: tradeData.stopLoss ? parseFloat(tradeData.stopLoss) : null,
        takeProfit: tradeData.takeProfit ? parseFloat(tradeData.takeProfit) : null,
        notes: tradeData.notes
      };
      
      console.log('Trade submitted:', trade);
      
      setSuccess(true);
      setTradeData({
        side: 'BUY',
        orderType: 'MARKET',
        quantity: '',
        price: '',
        stopLoss: '',
        takeProfit: '',
        notes: ''
      });
      
      if (onTradeExecuted) {
        onTradeExecuted(trade);
      }
      
      // Reset success message after 3 seconds
      setTimeout(() => setSuccess(false), 3000);
      
    } catch (error) {
      console.error('Trade submission failed:', error);
      setErrors({ submit: 'Failed to submit trade. Please try again.' });
    } finally {
      setIsSubmitting(false);
    }
  };

  const calculateTotal = () => {
    const quantity = parseFloat(tradeData.quantity) || 0;
    const price = parseFloat(tradeData.price) || 0;
    return quantity * price;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center space-x-2 mb-6">
        <Calculator className="w-5 h-5 text-blue-600" />
        <h3 className="text-lg font-semibold text-gray-900">Place Trade</h3>
      </div>

      {success && (
        <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg flex items-center space-x-2">
          <CheckCircle className="w-4 h-4 text-green-600" />
          <span className="text-sm text-green-800">Trade submitted successfully!</span>
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Asset Selection */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Asset
          </label>
          <div className="p-3 bg-gray-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="font-medium text-gray-900">{selectedAsset.symbol}</span>
              <span className="text-sm text-gray-500 uppercase">{selectedAsset.type}</span>
            </div>
          </div>
        </div>

        {/* Trade Side */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Side
          </label>
          <div className="grid grid-cols-2 gap-2">
            <button
              type="button"
              onClick={() => setTradeData({ ...tradeData, side: 'BUY' })}
              className={`flex items-center justify-center space-x-2 p-3 rounded-lg border ${
                tradeData.side === 'BUY'
                  ? 'border-green-500 bg-green-50 text-green-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <TrendingUp className="w-4 h-4" />
              <span className="font-medium">Buy</span>
            </button>
            <button
              type="button"
              onClick={() => setTradeData({ ...tradeData, side: 'SELL' })}
              className={`flex items-center justify-center space-x-2 p-3 rounded-lg border ${
                tradeData.side === 'SELL'
                  ? 'border-red-500 bg-red-50 text-red-700'
                  : 'border-gray-300 bg-white text-gray-700 hover:bg-gray-50'
              }`}
            >
              <TrendingDown className="w-4 h-4" />
              <span className="font-medium">Sell</span>
            </button>
          </div>
        </div>

        {/* Order Type */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Order Type
          </label>
          <select
            value={tradeData.orderType}
            onChange={(e) => setTradeData({ ...tradeData, orderType: e.target.value })}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
          >
            {orderTypes.map((type) => (
              <option key={type.value} value={type.value}>
                {type.label}
              </option>
            ))}
          </select>
        </div>

        {/* Quantity */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Quantity
          </label>
          <input
            type="number"
            step="0.01"
            min="0"
            value={tradeData.quantity}
            onChange={(e) => setTradeData({ ...tradeData, quantity: e.target.value })}
            className={`w-full p-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
              errors.quantity ? 'border-red-500' : 'border-gray-300'
            }`}
            placeholder="Enter quantity"
          />
          {errors.quantity && (
            <p className="mt-1 text-sm text-red-600 flex items-center space-x-1">
              <AlertCircle className="w-4 h-4" />
              <span>{errors.quantity}</span>
            </p>
          )}
        </div>

        {/* Price (for limit orders) */}
        {tradeData.orderType === 'LIMIT' && (
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Price
            </label>
            <div className="relative">
              <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="number"
                step="0.01"
                min="0"
                value={tradeData.price}
                onChange={(e) => setTradeData({ ...tradeData, price: e.target.value })}
                className={`w-full pl-10 pr-3 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                  errors.price ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Enter price"
              />
            </div>
            {errors.price && (
              <p className="mt-1 text-sm text-red-600 flex items-center space-x-1">
                <AlertCircle className="w-4 h-4" />
                <span>{errors.price}</span>
              </p>
            )}
          </div>
        )}

        {/* Stop Loss */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Stop Loss (Optional)
          </label>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="number"
              step="0.01"
              min="0"
              value={tradeData.stopLoss}
              onChange={(e) => setTradeData({ ...tradeData, stopLoss: e.target.value })}
              className={`w-full pl-10 pr-3 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.stopLoss ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter stop loss price"
            />
          </div>
          {errors.stopLoss && (
            <p className="mt-1 text-sm text-red-600 flex items-center space-x-1">
              <AlertCircle className="w-4 h-4" />
              <span>{errors.stopLoss}</span>
            </p>
          )}
        </div>

        {/* Take Profit */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Take Profit (Optional)
          </label>
          <div className="relative">
            <DollarSign className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="number"
              step="0.01"
              min="0"
              value={tradeData.takeProfit}
              onChange={(e) => setTradeData({ ...tradeData, takeProfit: e.target.value })}
              className={`w-full pl-10 pr-3 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 ${
                errors.takeProfit ? 'border-red-500' : 'border-gray-300'
              }`}
              placeholder="Enter take profit price"
            />
          </div>
          {errors.takeProfit && (
            <p className="mt-1 text-sm text-red-600 flex items-center space-x-1">
              <AlertCircle className="w-4 h-4" />
              <span>{errors.takeProfit}</span>
            </p>
          )}
        </div>

        {/* Total Value Display */}
        {tradeData.quantity && tradeData.price && (
          <div className="p-3 bg-blue-50 rounded-lg">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium text-blue-900">Total Value</span>
              <span className="text-lg font-bold text-blue-900">
                ${calculateTotal().toFixed(2)}
              </span>
            </div>
          </div>
        )}

        {/* Notes */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Notes (Optional)
          </label>
          <textarea
            value={tradeData.notes}
            onChange={(e) => setTradeData({ ...tradeData, notes: e.target.value })}
            rows={3}
            className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Add any notes about this trade"
          />
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting}
          className={`w-full py-3 px-4 rounded-lg font-medium ${
            isSubmitting
              ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700 focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
          }`}
        >
          {isSubmitting ? 'Submitting...' : 'Place Trade'}
        </button>

        {errors.submit && (
          <p className="text-sm text-red-600 flex items-center space-x-1">
            <AlertCircle className="w-4 h-4" />
            <span>{errors.submit}</span>
          </p>
        )}
      </form>
    </div>
  );
};

export default TradeForm;
