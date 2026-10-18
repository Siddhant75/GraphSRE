'use client';
import React from 'react';
import { Zap, Clock, ShieldAlert } from 'lucide-react';
import { useBlackboardStore } from '@/store/useBlackboardStore';

export default function ShortcutVisualizer() {
  const { triggerShortcutBypass } = useBlackboardStore();

  const handleTestShortcut = async () => {
    try {
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      await fetch(`${baseUrl}/api/incidents/triage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          target_service: 'PaymentService',
          alert_name: 'Repeat HTTP 504 Gateway Timeout',
          metric_value: 2450.0,
          threshold: 2000.0,
          fingerprint: 'fp_repeat_payment_504'
        })
      });
    } catch (e) {
      // Offline fallback
    }
    triggerShortcutBypass();
  };

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
          Direct causal shortcut edge synthesized: <span className="font-mono text-emerald-400">(:Service)-[:SHORTCUT_TO_ROOT_CAUSE]-&gt;(:Function)</span>.
          Bypasses multi-hop RCA for future matching alerts in 0.18s.
        </p>

        <button
          onClick={handleTestShortcut}
          className="mt-3 w-full bg-emerald-600/90 hover:bg-emerald-500 text-white font-bold text-xs py-2 px-3 rounded-lg transition shadow flex items-center justify-center space-x-1.5"
        >
          <Zap className="w-3.5 h-3.5 text-yellow-300" />
          <span>⚡ Test Repeat Outage (O(1) Shortcut)</span>
        </button>
      </div>

      <div className="mt-4 pt-3 border-t border-[#1E293B] grid grid-cols-2 gap-2 text-[11px] font-mono text-gray-400">
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
