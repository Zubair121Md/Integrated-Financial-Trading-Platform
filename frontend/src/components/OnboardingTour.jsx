/**
 * Onboarding tour component for new users.
 */

import React, { useState, useEffect } from 'react';
import { 
  ChevronRight, 
  ChevronLeft, 
  X, 
  TrendingUp, 
  BarChart3, 
  Settings,
  Zap,
  Shield,
  DollarSign
} from 'lucide-react';

const OnboardingTour = ({ isOpen, onClose, onComplete }) => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isVisible, setIsVisible] = useState(false);

  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
    }
  }, [isOpen]);

  const steps = [
    {
      title: "Welcome to Trading Platform",
      description: "Your comprehensive trading solution with real-time data, algorithmic strategies, and advanced analytics.",
      icon: <TrendingUp className="w-8 h-8 text-blue-600" />,
      features: ["Real-time market data", "Multi-asset trading", "Advanced analytics"]
    },
    {
      title: "Dashboard Overview",
      description: "Monitor your portfolio, track performance, and access all trading tools from one place.",
      icon: <BarChart3 className="w-8 h-8 text-green-600" />,
      features: ["Portfolio summary", "Live charts", "Quick actions"]
    },
    {
      title: "Trading Interface",
      description: "Execute trades with confidence using our intuitive trading interface with real-time data.",
      icon: <DollarSign className="w-8 h-8 text-yellow-600" />,
      features: ["One-click trading", "Order management", "Risk controls"]
    },
    {
      title: "Algorithmic Trading",
      description: "Create and deploy automated trading strategies using our ML-powered tools.",
      icon: <Zap className="w-8 h-8 text-purple-600" />,
      features: ["Strategy builder", "ML predictions", "Backtesting"]
    },
    {
      title: "Security & Safety",
      description: "Your data and funds are protected with enterprise-grade security measures.",
      icon: <Shield className="w-8 h-8 text-red-600" />,
      features: ["Encrypted data", "Secure trading", "Audit trails"]
    }
  ];

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      handleComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleComplete = () => {
    setIsVisible(false);
    onComplete();
  };

  const handleClose = () => {
    setIsVisible(false);
    onClose();
  };

  if (!isVisible) return null;

  const currentStepData = steps[currentStep];

  return (
    <div className="fixed inset-0 z-50 overflow-hidden">
      {/* Backdrop */}
      <div className="absolute inset-0 bg-black bg-opacity-50" onClick={handleClose} />
      
      {/* Tour Content */}
      <div className="relative flex items-center justify-center min-h-screen p-4">
        <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
          {/* Header */}
          <div className="flex items-center justify-between p-6 border-b border-gray-200">
            <div className="flex items-center space-x-3">
              {currentStepData.icon}
              <div>
                <h2 className="text-2xl font-bold text-gray-900">
                  {currentStepData.title}
                </h2>
                <p className="text-sm text-gray-500">
                  Step {currentStep + 1} of {steps.length}
                </p>
              </div>
            </div>
            <button
              onClick={handleClose}
              className="p-2 text-gray-400 hover:text-gray-600 transition-colors"
            >
              <X className="w-6 h-6" />
            </button>
          </div>

          {/* Content */}
          <div className="p-6">
            <p className="text-lg text-gray-700 mb-6">
              {currentStepData.description}
            </p>

            {/* Features */}
            <div className="space-y-3 mb-8">
              {currentStepData.features.map((feature, index) => (
                <div key={index} className="flex items-center space-x-3">
                  <div className="w-2 h-2 bg-blue-600 rounded-full" />
                  <span className="text-gray-600">{feature}</span>
                </div>
              ))}
            </div>

            {/* Progress Bar */}
            <div className="w-full bg-gray-200 rounded-full h-2 mb-6">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              />
            </div>

            {/* Navigation */}
            <div className="flex items-center justify-between">
              <button
                onClick={handlePrevious}
                disabled={currentStep === 0}
                className={`flex items-center space-x-2 px-4 py-2 rounded-lg transition-colors ${
                  currentStep === 0
                    ? 'text-gray-400 cursor-not-allowed'
                    : 'text-gray-600 hover:text-gray-800 hover:bg-gray-100'
                }`}
              >
                <ChevronLeft className="w-4 h-4" />
                <span>Previous</span>
              </button>

              <div className="flex space-x-2">
                {steps.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentStep(index)}
                    className={`w-3 h-3 rounded-full transition-colors ${
                      index === currentStep
                        ? 'bg-blue-600'
                        : 'bg-gray-300 hover:bg-gray-400'
                    }`}
                  />
                ))}
              </div>

              <button
                onClick={handleNext}
                className="flex items-center space-x-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                <span>{currentStep === steps.length - 1 ? 'Get Started' : 'Next'}</span>
                <ChevronRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingTour;
