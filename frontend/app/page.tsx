'use client';
import React from 'react';
import TopologyCanvas from '@/components/TopologyCanvas';
import AgentFeed from '@/components/AgentFeed';
import QuorumMeter from '@/components/QuorumMeter';
import ActionCard from '@/components/ActionCard';
import ChaosPanel from '@/components/ChaosPanel';
import ShortcutVisualizer from '@/components/ShortcutVisualizer';
import CypherConsole from '@/components/CypherConsole';
import { useBlackboardStore } from '@/store/useBlackboardStore';

export default function WarRoomPage() {
  const { incidentId, severity, blastRadius, lifecycleState } = useBlackboardStore();

  return (
    <div className="space-y-6">
      {/* Top Status & Quorum Row */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-4">
          <span className="text-xs text-gray-400 font-mono">Incident ID</span>
          <h3 className="text-lg font-bold text-white mt-1 font-mono">{incidentId}</h3>
          <span className="text-[11px] text-emerald-400 font-medium">State: {lifecycleState}</span>
        </div>
        <div className="bg-[#0F172A] border border-red-500/30 rounded-xl p-4">
          <span className="text-xs text-red-400 font-semibold font-mono">Dynamic Severity</span>
          <h3 className="text-lg font-bold text-red-400 mt-1">
            {severity} {severity === 'SEV_1' ? '(Critical Outage)' : '(Monitoring)'}
          </h3>
          <span className="text-[11px] text-gray-400">PageRank: 0.884 | Tier: 1</span>
        </div>
        <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-4">
          <span className="text-xs text-gray-400 font-mono">Blast Radius</span>
          <h3 className="text-lg font-bold text-white mt-1">{blastRadius} Microservices</h3>
          <span className="text-[11px] text-gray-400">
            {blastRadius > 0 ? 'Cart, Checkout, FrontendAPI' : 'All systems operating within baseline'}
          </span>
        </div>
        <QuorumMeter />
      </div>

      {/* Main Grid: Cytoscape Canvas on Left (2 cols), Live Deliberation Feed on Right (1 col) */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <TopologyCanvas />
        </div>
        <div className="lg:col-span-1">
          <AgentFeed />
        </div>
      </div>

      {/* Human-in-the-Loop Action Card & Shortcut Visualizer */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <ActionCard />
        </div>
        <div className="lg:col-span-1">
          <ShortcutVisualizer />
        </div>
      </div>

      {/* Chaos Injection Controller */}
      <ChaosPanel />

      {/* Live OpenCypher & GraphBLAS Execution Stream Terminal */}
      <CypherConsole />
    </div>
  );
}
