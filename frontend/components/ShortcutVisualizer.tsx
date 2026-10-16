'use client';
import React from 'react';
import { Zap, Clock, ShieldAlert } from 'lucide-react';

export default function ShortcutVisualizer() {
  return (
    <div className="bg-[#0F172A] border border-emerald-500/30 rounded-xl p-5 shadow-lg flex flex-col justify-between">
      <div>
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center space-x-1.5">
            <Zap className="w-4 h-4 text-emerald-400" />
            <h4 className="font-semibold text-xs text-white uppercase tracking-wider">
              O(1) Self-Curating Shortcut Net
            </h4>
          </div>
          <span className="px-2 py-0.5 bg-emerald-950 text-emerald-300 rounded font-mono text-[10px] border border-emerald-500/30">
            Active Bypass
          </span>
        </div>

        <p className="text-xs text-gray-300 leading-relaxed">
          Direct causal shortcut edge synthesized: <span className="font-mono text-emerald-400">(:Alert)-[:CAUSED_BY_SHORTCUT]-&gt;(:Function)</span>.
          Bypasses multi-hop RCA for future matching alerts.
        </p>
      </div>

      <div className="pt-3 border-t border-[#1E293B] grid grid-cols-2 gap-2 text-[11px] font-mono text-gray-400">
        <div className="flex items-center space-x-1">
          <Clock className="w-3 h-3 text-emerald-400" />
          <span>Half-Life: 30 days</span>
        </div>
        <div className="flex items-center space-x-1">
          <ShieldAlert className="w-3 h-3 text-amber-400" />
          <span>Code Mod Penalty: -70%</span>
        </div>
      </div>
    </div>
  );
}
