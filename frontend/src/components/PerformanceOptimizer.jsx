/**
 * Performance optimization component for the trading platform.
 */

import React, { useState, useEffect, useMemo, useCallback } from 'react';
import { 
  Activity, 
  Zap, 
  TrendingUp, 
  AlertTriangle,
  CheckCircle,
  Clock
} from 'lucide-react';

const PerformanceOptimizer = () => {
  const [performanceMetrics, setPerformanceMetrics] = useState({
    apiLatency: 0,
    websocketLatency: 0,
    renderTime: 0,
    memoryUsage: 0,
    cacheHitRate: 0
  });

  const [optimizations, setOptimizations] = useState([]);
  const [isOptimizing, setIsOptimizing] = useState(false);

  // Simulate performance monitoring
  useEffect(() => {
    const interval = setInterval(() => {
      setPerformanceMetrics({
        apiLatency: Math.random() * 100 + 50, // 50-150ms
        websocketLatency: Math.random() * 50 + 10, // 10-60ms
        renderTime: Math.random() * 16 + 8, // 8-24ms
        memoryUsage: Math.random() * 20 + 10, // 10-30MB
        cacheHitRate: Math.random() * 20 + 80 // 80-100%
      });
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  // Memoized performance analysis
  const performanceAnalysis = useMemo(() => {
    const issues = [];
    const recommendations = [];

    if (performanceMetrics.apiLatency > 100) {
      issues.push({
        type: 'warning',
        message: 'High API latency detected',
        impact: 'Medium',
        suggestion: 'Consider enabling response caching'
      });
    }

    if (performanceMetrics.websocketLatency > 30) {
      issues.push({
        type: 'warning',
        message: 'WebSocket connection slow',
        impact: 'High',
        suggestion: 'Check network connection or switch servers'
      });
    }

    if (performanceMetrics.renderTime > 16) {
      issues.push({
        type: 'error',
        message: 'Slow rendering detected',
        impact: 'High',
        suggestion: 'Optimize component rendering or reduce data complexity'
      });
    }

    if (performanceMetrics.memoryUsage > 25) {
      issues.push({
        type: 'warning',
        message: 'High memory usage',
        impact: 'Medium',
        suggestion: 'Clear unused data or implement data pagination'
      });
    }

    if (performanceMetrics.cacheHitRate < 85) {
      issues.push({
        type: 'info',
        message: 'Low cache hit rate',
        impact: 'Low',
        suggestion: 'Review caching strategy and TTL settings'
      });
    }

    // Generate recommendations
    if (issues.length === 0) {
      recommendations.push({
        type: 'success',
        message: 'Performance is optimal',
        action: 'Continue monitoring'
      });
    } else {
      recommendations.push({
        type: 'optimize',
        message: 'Apply automatic optimizations',
        action: 'Run optimization'
      });
    }

    return { issues, recommendations };
  }, [performanceMetrics]);

  const handleOptimize = useCallback(async () => {
    setIsOptimizing(true);
    
    // Simulate optimization process
    await new Promise(resolve => setTimeout(resolve, 2000));
    
    setOptimizations(prev => [
      ...prev,
      {
        id: Date.now(),
        type: 'success',
        message: 'Applied performance optimizations',
        timestamp: new Date().toISOString()
      }
    ]);
    
    setIsOptimizing(false);
  }, []);

  const getStatusColor = (value, thresholds) => {
    if (value <= thresholds.good) return 'text-green-600';
    if (value <= thresholds.warning) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getStatusIcon = (value, thresholds) => {
    if (value <= thresholds.good) return <CheckCircle className="w-4 h-4" />;
    if (value <= thresholds.warning) return <AlertTriangle className="w-4 h-4" />;
    return <AlertTriangle className="w-4 h-4" />;
  };

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <Activity className="w-5 h-5 text-blue-600" />
          <h3 className="text-lg font-semibold text-gray-900">Performance Monitor</h3>
        </div>
        <button
          onClick={handleOptimize}
          disabled={isOptimizing}
          className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
            isOptimizing
              ? 'bg-gray-400 text-white cursor-not-allowed'
              : 'bg-blue-600 text-white hover:bg-blue-700'
          }`}
        >
          {isOptimizing ? (
            <>
              <Clock className="w-4 h-4 animate-spin" />
              <span>Optimizing...</span>
            </>
          ) : (
            <>
              <Zap className="w-4 h-4" />
              <span>Optimize</span>
            </>
          )}
        </button>
      </div>

      {/* Performance Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 mb-6">
        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">API Latency</span>
            <div className={`flex items-center space-x-1 ${getStatusColor(performanceMetrics.apiLatency, { good: 50, warning: 100 })}`}>
              {getStatusIcon(performanceMetrics.apiLatency, { good: 50, warning: 100 })}
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {performanceMetrics.apiLatency.toFixed(0)}ms
          </p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">WebSocket</span>
            <div className={`flex items-center space-x-1 ${getStatusColor(performanceMetrics.websocketLatency, { good: 20, warning: 30 })}`}>
              {getStatusIcon(performanceMetrics.websocketLatency, { good: 20, warning: 30 })}
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {performanceMetrics.websocketLatency.toFixed(0)}ms
          </p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Render Time</span>
            <div className={`flex items-center space-x-1 ${getStatusColor(performanceMetrics.renderTime, { good: 16, warning: 20 })}`}>
              {getStatusIcon(performanceMetrics.renderTime, { good: 16, warning: 20 })}
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {performanceMetrics.renderTime.toFixed(1)}ms
          </p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Memory</span>
            <div className={`flex items-center space-x-1 ${getStatusColor(performanceMetrics.memoryUsage, { good: 15, warning: 25 })}`}>
              {getStatusIcon(performanceMetrics.memoryUsage, { good: 15, warning: 25 })}
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {performanceMetrics.memoryUsage.toFixed(1)}MB
          </p>
        </div>

        <div className="bg-gray-50 p-4 rounded-lg">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-medium text-gray-600">Cache Hit</span>
            <div className={`flex items-center space-x-1 ${getStatusColor(100 - performanceMetrics.cacheHitRate, { good: 5, warning: 15 })}`}>
              {getStatusIcon(100 - performanceMetrics.cacheHitRate, { good: 5, warning: 15 })}
            </div>
          </div>
          <p className="text-2xl font-bold text-gray-900">
            {performanceMetrics.cacheHitRate.toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Issues and Recommendations */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Issues */}
        <div>
          <h4 className="text-md font-semibold text-gray-900 mb-3">Performance Issues</h4>
          <div className="space-y-2">
            {performanceAnalysis.issues.length === 0 ? (
              <div className="flex items-center space-x-2 text-green-600">
                <CheckCircle className="w-4 h-4" />
                <span className="text-sm">No performance issues detected</span>
              </div>
            ) : (
              performanceAnalysis.issues.map((issue, index) => (
                <div key={index} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                  <div className={`mt-0.5 ${
                    issue.type === 'error' ? 'text-red-600' :
                    issue.type === 'warning' ? 'text-yellow-600' : 'text-blue-600'
                  }`}>
                    <AlertTriangle className="w-4 h-4" />
                  </div>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-gray-900">{issue.message}</p>
                    <p className="text-xs text-gray-600 mt-1">
                      Impact: {issue.impact} • {issue.suggestion}
                    </p>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Recommendations */}
        <div>
          <h4 className="text-md font-semibold text-gray-900 mb-3">Recommendations</h4>
          <div className="space-y-2">
            {performanceAnalysis.recommendations.map((rec, index) => (
              <div key={index} className="flex items-start space-x-3 p-3 bg-blue-50 rounded-lg">
                <div className={`mt-0.5 ${
                  rec.type === 'success' ? 'text-green-600' : 'text-blue-600'
                }`}>
                  <TrendingUp className="w-4 h-4" />
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{rec.message}</p>
                  <p className="text-xs text-gray-600 mt-1">{rec.action}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Recent Optimizations */}
      {optimizations.length > 0 && (
        <div className="mt-6">
          <h4 className="text-md font-semibold text-gray-900 mb-3">Recent Optimizations</h4>
          <div className="space-y-2">
            {optimizations.slice(-3).map((opt) => (
              <div key={opt.id} className="flex items-center space-x-3 p-3 bg-green-50 rounded-lg">
                <CheckCircle className="w-4 h-4 text-green-600" />
                <div className="flex-1">
                  <p className="text-sm font-medium text-gray-900">{opt.message}</p>
                  <p className="text-xs text-gray-600">
                    {new Date(opt.timestamp).toLocaleString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PerformanceOptimizer;
