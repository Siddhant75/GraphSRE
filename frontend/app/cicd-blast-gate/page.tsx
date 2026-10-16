import React from 'react';

export default function BlastGatePage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white">Shift-Left CI/CD Blast Gate</h2>
        <p className="text-xs text-gray-400 mt-1">
          Pre-merge structural risk analyzer. Evaluates Tree-sitter AST modifications against upstream topological reachability in FalkorDB.
        </p>
      </div>

      <div className="bg-[#0F172A] border border-red-500/30 rounded-xl p-6 space-y-4">
        <div className="flex justify-between items-start">
          <div>
            <h3 className="text-lg font-semibold text-white">Pull Request #412: Refactor stripe webhook read timeout</h3>
            <p className="text-xs text-gray-400 mt-0.5 font-mono">Target Repository: company/payment-gateway</p>
          </div>
          <span className="px-3 py-1 bg-red-950 text-red-400 border border-red-500/30 rounded text-xs font-semibold uppercase tracking-wider">
            Merge Blocked by Blast Gate
          </span>
        </div>

        <div className="grid grid-cols-3 gap-4 pt-2">
          <div className="bg-[#090D16] p-3 rounded-lg border border-[#1E293B]">
            <span className="text-[11px] text-gray-500">Structural Risk Index (SRI)</span>
            <h4 className="text-base font-bold text-red-400 font-mono mt-1">0.88 / 1.00</h4>
          </div>
          <div className="bg-[#090D16] p-3 rounded-lg border border-[#1E293B]">
            <span className="text-[11px] text-gray-500">Impacted Tier-1 Services</span>
            <h4 className="text-base font-bold text-white font-mono mt-1">3 Services</h4>
          </div>
          <div className="bg-[#090D16] p-3 rounded-lg border border-[#1E293B]">
            <span className="text-[11px] text-gray-500">Calling Endpoints Without Timeout</span>
            <h4 className="text-base font-bold text-amber-400 font-mono mt-1">3 Endpoints</h4>
          </div>
        </div>

        <div className="bg-[#090D16] p-4 rounded-lg border border-[#1E293B] text-xs font-mono text-gray-300">
          <span className="text-gray-500"># Offending diff detected by Tree-sitter AST parser:</span>
          <pre className="mt-1 text-red-400">- response = requests.get(url, timeout=3.0)</pre>
          <pre className="text-red-300">+ response = requests.get(url, timeout=None) # Dangerous: thread starvation</pre>
        </div>
      </div>
    </div>
  );
}
