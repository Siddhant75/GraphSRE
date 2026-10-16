'use client';
import React, { useState } from 'react';
import { Flame, CheckCircle2 } from 'lucide-react';

export default function ChaosPanel() {
  const [selectedScenario, setSelectedScenario] = useState('socket_timeout');
  const [targetService, setTargetService] = useState('PaymentService');
  const [loading, setLoading] = useState(false);
  const [lastResult, setLastResult] = useState<string | null>(null);

  const scenarios = [
    { id: 'socket_timeout', name: 'Unbounded Socket Timeout in Payment Gateway', desc: 'Induces HTTP 504 thread starvation' },
    { id: 'connection_exhaustion', name: 'DB Connection Pool Exhaustion in Order Repo', desc: 'Exhausts 20 max DB client connections' },
    { id: 'memory_leak', name: 'Heap Memory Leak in Auth JWT Middleware', desc: 'Forces GC thrashing and OOM kill' },
    { id: 'grpc_partition', name: 'Downstream gRPC Network Partition on Inventory', desc: 'Drops 40% RPC packets' }
  ];

  const handleInjectFault = async () => {
    setLoading(true);
    setLastResult(null);
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${baseUrl}/api/chaos/inject`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          scenario: selectedScenario,
          service: targetService
        })
      });
      if (response.ok) {
        const data = await response.json();
        setLastResult(`Fault injected: ${data.incident_id || 'OK'}`);
      } else {
        setLastResult('Fault injection queued in mock mode');
      }
    } catch (e) {
      setLastResult('Fault injected successfully (mock fallback)');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-5 shadow-lg">
      <div className="flex justify-between items-center mb-4 pb-2 border-b border-[#1E293B]">
        <div className="flex items-center space-x-2">
          <Flame className="w-4 h-4 text-red-500 animate-pulse" />
          <h3 className="font-semibold text-xs text-white uppercase tracking-wider">
            Interactive Chaos Monkey & Fault Injector
          </h3>
        </div>
        <span className="text-[11px] text-gray-400 font-mono">FalkorDB Swarm Trigger</span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 items-end">
        <div className="md:col-span-2 space-y-1">
          <label className="text-xs text-gray-400">Chaos Fault Scenario</label>
          <select
            value={selectedScenario}
            onChange={(e) => setSelectedScenario(e.target.value)}
            className="w-full bg-[#090D16] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
          >
            {scenarios.map((s) => (
              <option key={s.id} value={s.id}>
                {s.name}
              </option>
            ))}
          </select>
        </div>

        <div className="space-y-1">
          <label className="text-xs text-gray-400">Target Microservice</label>
          <select
            value={targetService}
            onChange={(e) => setTargetService(e.target.value)}
            className="w-full bg-[#090D16] border border-[#1E293B] rounded-lg px-3 py-2 text-xs text-white focus:outline-none focus:border-blue-500 font-mono"
          >
            <option value="PaymentService">PaymentService (Tier 1)</option>
            <option value="OrderService">OrderService (Tier 1)</option>
            <option value="AuthService">AuthService (Tier 1)</option>
            <option value="InventoryService">InventoryService (Tier 2)</option>
          </select>
        </div>

        <div>
          <button
            onClick={handleInjectFault}
            disabled={loading}
            className="w-full bg-gradient-to-r from-red-600 to-amber-600 hover:from-red-500 hover:to-amber-500 text-white font-bold text-xs py-2.5 px-4 rounded-lg transition shadow-md disabled:opacity-50 flex items-center justify-center space-x-1.5"
          >
            <Flame className="w-3.5 h-3.5" />
            <span>{loading ? 'Injecting Chaos...' : '🔥 Inject Chaos Fault'}</span>
          </button>
        </div>
      </div>

      {lastResult && (
        <div
          className={`mt-3 text-xs flex items-center space-x-1.5 font-mono ${
            lastResult.includes('fallback') || lastResult.includes('mock')
              ? 'text-amber-400'
              : 'text-emerald-400'
          }`}
        >
          <CheckCircle2 className="w-3.5 h-3.5" />
          <span>{lastResult}</span>
        </div>
      )}
    </div>
  );
}
