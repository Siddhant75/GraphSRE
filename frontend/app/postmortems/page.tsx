import React from 'react';

export default function PostmortemsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-bold text-white">Episodic Vector Memory & Postmortems</h2>
        <p className="text-xs text-gray-400 mt-1">
          384-dimensional dense embeddings stored in FalkorDB HNSW vector index for instant cosine similarity matching.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-6 space-y-3">
          <div className="flex justify-between items-start">
            <span className="text-xs bg-emerald-950 text-emerald-400 px-2.5 py-1 rounded border border-emerald-500/30 font-semibold font-mono">
              MTTR: 78 seconds (SLA &lt; 90s)
            </span>
            <span className="text-xs text-gray-500 font-mono">postmortem_inc_historical_01</span>
          </div>
          <h3 className="text-base font-semibold text-white">Unbounded Socket Read Timeout in Payment Gateway</h3>
          <p className="text-xs text-gray-400 leading-relaxed">
            Root Cause: Ingestion of commit removing HTTP socket read timeouts caused worker thread starvation across connection pools.
          </p>
          <div className="pt-2 border-t border-[#1E293B] text-xs flex justify-between text-gray-400">
            <span>Cosine Vector Similarity: <strong className="text-emerald-400">0.941</strong></span>
            <span>Runbook: <strong className="text-blue-400">RB-NET-042</strong></span>
          </div>
        </div>

        <div className="bg-[#0F172A] border border-[#1E293B] rounded-xl p-6 space-y-3">
          <div className="flex justify-between items-start">
            <span className="text-xs bg-emerald-950 text-emerald-400 px-2.5 py-1 rounded border border-emerald-500/30 font-semibold font-mono">
              MTTR: 62 seconds (SLA &lt; 90s)
            </span>
            <span className="text-xs text-gray-500 font-mono">postmortem_inc_historical_02</span>
          </div>
          <h3 className="text-base font-semibold text-white">PostgreSQL Connection Leak in Order Processing</h3>
          <p className="text-xs text-gray-400 leading-relaxed">
            Root Cause: Unclosed database session during async exception handling exhausted pool max size of 20 connections.
          </p>
          <div className="pt-2 border-t border-[#1E293B] text-xs flex justify-between text-gray-400">
            <span>Cosine Vector Similarity: <strong className="text-purple-400">0.892</strong></span>
            <span>Runbook: <strong className="text-blue-400">RB-DB-018</strong></span>
          </div>
        </div>
      </div>
    </div>
  );
}
