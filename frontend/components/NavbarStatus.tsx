'use client';
import React from 'react';
import { useBlackboardStore } from '@/store/useBlackboardStore';

export default function NavbarStatus() {
  const { severity, lifecycleState } = useBlackboardStore();

  const isHealthy = lifecycleState === 'HEALTHY_MONITORING';
  const isResolved = lifecycleState.startsWith('RESOLVED');

  if (isHealthy) {
    return (
      <span className="px-2.5 py-1 bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 rounded font-semibold flex items-center space-x-1.5">
        <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
        <span>Status: Normal (Healthy)</span>
      </span>
    );
  }

  if (isResolved) {
    return (
      <span className="px-2.5 py-1 bg-emerald-950/80 border border-emerald-500/40 text-emerald-300 rounded font-semibold flex items-center space-x-1.5">
        <span className="w-2 h-2 rounded-full bg-emerald-400 inline-block" />
        <span>Resolved: O(1) Shortcut Compiled</span>
      </span>
    );
  }

  return (
    <span className="px-2.5 py-1 bg-red-950/80 border border-red-500/40 text-red-300 rounded font-semibold flex items-center space-x-1.5">
      <span className="w-2 h-2 rounded-full bg-red-500 animate-ping inline-block" />
      <span>Active Sev: 1 (Outage)</span>
    </span>
  );
}
