'use client';
import React, { useEffect } from 'react';
import { useBlackboardStore } from '@/store/useBlackboardStore';
import AgentThoughtCard from './AgentThoughtCard';
import { Radio } from 'lucide-react';

export default function AgentFeed() {
  const { agentThoughts, wsConnected, initializeWebSocket, incidentId } = useBlackboardStore();

  useEffect(() => {
    const cleanup = initializeWebSocket(incidentId);
    return cleanup;
  }, [incidentId, initializeWebSocket]);

  return (
    <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-4 h-[620px] flex flex-col shadow-inner">
      <div className="flex justify-between items-center mb-3 pb-3 border-b border-[#1E293B]">
        <div className="flex items-center space-x-2">
          <Radio className="w-4 h-4 text-emerald-400 animate-pulse" />
          <h3 className="font-semibold text-xs text-white uppercase tracking-wider">
            Agent Blackboard Live Feed
          </h3>
        </div>
        <div className="flex items-center space-x-1.5 text-[11px] font-mono">
          <span className={`w-2 h-2 rounded-full ${wsConnected ? 'bg-emerald-500' : 'bg-amber-500'}`} />
          <span className="text-gray-400">{wsConnected ? 'LIVE' : 'BUFFERED'}</span>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto space-y-3 pr-1">
        {agentThoughts.map((thought, idx) => (
          <AgentThoughtCard key={idx} thought={thought} />
        ))}
      </div>
    </div>
  );
}
