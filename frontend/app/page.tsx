import React from 'react';
import TopologyCanvas from '@/components/TopologyCanvas';

export default function WarRoomPage() {
  return (
    <div className="space-y-6">
      {/* Top Status Bar */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-4">
          <span className="text-xs text-gray-400 font-mono">Incident ID</span>
          <h3 className="text-lg font-bold text-white mt-1 font-mono">inc_98a12c</h3>
          <span className="text-[11px] text-emerald-400">State: INVESTIGATING</span>
        </div>
        <div className="bg-[#0F172A] border border-red-500/30 rounded-xl p-4">
          <span className="text-xs text-red-400 font-semibold font-mono">Dynamic Severity</span>
          <h3 className="text-lg font-bold text-red-400 mt-1">SEV_1 (Critical Outage)</h3>
          <span className="text-[11px] text-gray-400">PageRank: 0.884 | Tier: 1</span>
        </div>
        <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-4">
          <span className="text-xs text-gray-400 font-mono">Upstream Blast Radius</span>
          <h3 className="text-lg font-bold text-white mt-1">3 Microservices</h3>
          <span className="text-[11px] text-gray-400">CartService, Checkout, FrontendAPI</span>
        </div>
        <div className="bg-[#0F172A] border border-emerald-500/30 rounded-xl p-4">
          <span className="text-xs text-emerald-400 font-mono">Quorum Consensus</span>
          <h3 className="text-lg font-bold text-emerald-400 mt-1 font-mono">0.88 / 0.75</h3>
          <span className="text-[11px] text-emerald-300">Quorum Reached (3/3 Agents)</span>
        </div>
      </div>

      {/* Main Graph & Feed Placeholder Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TopologyCanvas />
        </div>
        <div className="lg:col-span-1 bg-[#0F172A] border border-[#1E293B] rounded-xl p-6 min-h-[600px] flex items-center justify-center text-gray-400">
          Agent Blackboard Live Feed Placeholder
        </div>
      </div>
    </div>
  );
}
