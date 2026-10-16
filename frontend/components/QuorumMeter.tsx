'use client';
import React from 'react';
import { useBlackboardStore } from '@/store/useBlackboardStore';
import { Scale } from 'lucide-react';

export default function QuorumMeter() {
  const { wcs } = useBlackboardStore();
  const percentage = Math.min(100, Math.round((wcs / 1.0) * 100));
  const quorumReached = wcs >= 0.75;

  return (
    <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-4 flex flex-col justify-between">
      <div className="flex justify-between items-center mb-1">
        <div className="flex items-center space-x-1.5">
          <Scale className="w-3.5 h-3.5 text-emerald-400" />
          <span className="text-xs text-gray-400 font-mono">Consensus Quorum (WCS)</span>
        </div>
        <span className={`text-xs font-bold font-mono ${quorumReached ? 'text-emerald-400' : 'text-amber-400'}`}>
          {wcs.toFixed(2)} / 0.75 threshold
        </span>
      </div>

      {/* Meter Bar */}
      <div className="w-full bg-[#1E293B] h-2.5 rounded-full overflow-hidden my-2 relative">
        <div
          className={`h-full transition-all duration-500 rounded-full ${
            quorumReached ? 'bg-gradient-to-r from-emerald-500 to-teal-400' : 'bg-amber-500'
          }`}
          style={{ width: `${percentage}%` }}
        />
        {/* 75% Threshold Marker Line */}
        <div className="absolute top-0 bottom-0 left-[75%] w-[2px] bg-red-400/80 shadow-sm" />
      </div>

      <div className="flex justify-between items-center text-[10px] text-gray-400 font-mono">
        <span>Triage: APPROVE (0.20)</span>
        <span>RCA: APPROVE (0.35)</span>
        <span>Memory: APPROVE (0.35)</span>
      </div>
    </div>
  );
}
