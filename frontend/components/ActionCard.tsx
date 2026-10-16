'use client';
import React, { useState } from 'react';
import { AlertOctagon, Check, Play, ShieldCheck, Undo2 } from 'lucide-react';

export default function ActionCard() {
  const [reverted, setReverted] = useState(false);
  const [forkSimulating, setForkSimulating] = useState(false);
  const [simulationPassed, setSimulationPassed] = useState(false);

  const handleSimulateSandbox = () => {
    setForkSimulating(true);
    setTimeout(() => {
      setForkSimulating(false);
      setSimulationPassed(true);
    }, 1200);
  };

  return (
    <div className="bg-[#0F172A] border border-amber-500/40 rounded-xl p-5 shadow-xl relative overflow-hidden">
      <div className="flex justify-between items-start mb-3">
        <div className="flex items-center space-x-2">
          <AlertOctagon className="w-5 h-5 text-red-400" />
          <div>
            <h4 className="font-bold text-sm text-white">
              Slack-Style HITL Action Card: SEV-1 Incident
            </h4>
            <span className="text-xs text-amber-400 font-mono">Culprit Commit: c3d9a107 (Alice Chen)</span>
          </div>
        </div>
        <span className="px-2.5 py-0.5 bg-emerald-950 border border-emerald-500/30 text-emerald-300 rounded text-xs font-mono">
          C_SRE: 0.97
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs text-gray-300 py-2">
        <div className="space-y-1">
          <p><strong className="text-white">Offending Function:</strong> <span className="font-mono text-purple-300">payment/gateway.py:call_stripe_webhook()</span></p>
          <p><strong className="text-white">Failure Mode:</strong> Stripped socket read timeout inducing connection pool starvation</p>
        </div>
        <div className="space-y-1">
          <p><strong className="text-white">GRAPH.COPY Simulation:</strong> {forkSimulating ? 'Cloning graph & running...' : simulationPassed ? 'SAFE (10% Canary Shift Passed, 0 Errors)' : 'PENDING'}</p>
          <p><strong className="text-white">Blast Radius:</strong> 3 Upstream Services Impacted (CartService, CheckoutService, FrontendAPI)</p>
        </div>
      </div>

      <div className="mt-4 pt-3 border-t border-[#1E293B] flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center space-x-3">
          <button
            onClick={() => setReverted(true)}
            disabled={reverted}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 shadow ${
              reverted
                ? 'bg-emerald-900/60 border border-emerald-500/40 text-emerald-300'
                : 'bg-emerald-600 hover:bg-emerald-500 text-white'
            }`}
          >
            {reverted ? <Check className="w-3.5 h-3.5" /> : <Undo2 className="w-3.5 h-3.5" />}
            <span>{reverted ? 'Canary Rollback In Effect' : '✅ 1-Click Approve Canary Revert'}</span>
          </button>

          <button
            onClick={handleSimulateSandbox}
            disabled={forkSimulating}
            className="px-3.5 py-2 rounded-lg text-xs font-semibold bg-[#1E293B] hover:bg-[#334155] text-gray-200 transition flex items-center space-x-1.5"
          >
            <Play className="w-3.5 h-3.5 text-blue-400" />
            <span>{forkSimulating ? 'Simulating in GRAPH.COPY...' : '🧪 Fork Sandbox Sim'}</span>
          </button>
        </div>

        <span className="text-[11px] text-gray-400 flex items-center space-x-1">
          <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" />
          <span>Autonomous Guardrail: Quorum consensus 0.88 &gt; 0.75 satisfied</span>
        </span>
      </div>
    </div>
  );
}
