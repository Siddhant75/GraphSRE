'use client';
import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('ErrorBoundary caught an error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="bg-[#0F172A] border border-amber-500/40 rounded-xl p-6 text-center shadow-xl my-4">
          <div className="flex justify-center mb-3">
            <AlertTriangle className="w-8 h-8 text-amber-400" />
          </div>
          <h3 className="text-white font-bold text-sm mb-1">
            {this.props.fallbackTitle || 'Component Visual Recovered'}
          </h3>
          <p className="text-gray-400 text-xs mb-4 font-mono max-w-lg mx-auto">
            {this.state.error?.message || 'A visual render error was caught and isolated.'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            className="inline-flex items-center space-x-1.5 px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg text-xs font-semibold transition"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Reset Visual Canvas</span>
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}
