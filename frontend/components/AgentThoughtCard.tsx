'use client';
import React from 'react';
import { AgentThought } from '@/store/useBlackboardStore';
import { ShieldAlert, Compass, Brain, Wrench } from 'lucide-react';

interface Props {
  thought: AgentThought;
}

export default function AgentThoughtCard({ thought }: Props) {
  const getBadgeStyle = (agent: string) => {
    switch (agent) {
      case 'Triage':
        return {
          border: 'border-blue-500/30',
          bg: 'bg-blue-950/20',
          text: 'text-blue-400',
          icon: <ShieldAlert className="w-3.5 h-3.5 text-blue-400" />
        };
      case 'RCA':
        return {
          border: 'border-purple-500/30',
          bg: 'bg-purple-950/20',
          text: 'text-purple-400',
          icon: <Compass className="w-3.5 h-3.5 text-purple-400" />
        };
      case 'Memory':
        return {
          border: 'border-emerald-500/30',
          bg: 'bg-emerald-950/20',
          text: 'text-emerald-400',
          icon: <Brain className="w-3.5 h-3.5 text-emerald-400" />
        };
      case 'Remediation':
      default:
        return {
          border: 'border-amber-500/30',
          bg: 'bg-amber-950/20',
          text: 'text-amber-400',
          icon: <Wrench className="w-3.5 h-3.5 text-amber-400" />
        };
    }
  };

  const style = getBadgeStyle(thought.agent);

  return (
    <div className={`p-3.5 rounded-xl border ${style.border} ${style.bg} transition-all duration-200 hover:border-opacity-60 space-y-2`}>
      <div className="flex justify-between items-center">
        <div className="flex items-center space-x-1.5">
          {style.icon}
          <span className={`font-semibold text-xs ${style.text}`}>{thought.agent} Agent</span>
        </div>
        <span className="text-[10px] text-gray-500 font-mono">
          {new Date(thought.timestamp).toLocaleTimeString()}
        </span>
      </div>

      <p className="text-xs text-gray-300 leading-relaxed">{thought.text}</p>

      {thought.cypher_query && (
        <div className="bg-[#090D16] p-2 rounded border border-[#1E293B] font-mono text-[10px] text-blue-300 overflow-x-auto">
          <code>{thought.cypher_query}</code>
        </div>
      )}

      {thought.confidence !== undefined && (
        <div className="text-[10px] text-gray-400 flex justify-between pt-1 border-t border-[#1E293B]">
          <span>Confidence:</span>
          <span className="font-mono font-semibold text-white">{(thought.confidence * 100).toFixed(0)}%</span>
        </div>
      )}
    </div>
  );
}
