'use client';
import React from 'react';
import { useBlackboardStore } from '@/store/useBlackboardStore';
import { X, Activity, GitCommit, Code, Server, AlertTriangle } from 'lucide-react';

export default function NodeInspector() {
  const { selectedNode, setSelectedNode } = useBlackboardStore();
  if (!selectedNode) return null;

  const renderIcon = (type: string) => {
    switch (type) {
      case 'Service': return <Server className="w-4 h-4 text-blue-400" />;
      case 'Function': return <Code className="w-4 h-4 text-purple-400" />;
      case 'Commit': return <GitCommit className="w-4 h-4 text-amber-400" />;
      case 'Alert': return <AlertTriangle className="w-4 h-4 text-red-400" />;
      default: return <Activity className="w-4 h-4 text-gray-400" />;
    }
  };

  return (
    <div className="absolute right-4 top-4 w-80 bg-[#0F172A]/95 backdrop-blur border border-[#1E293B] rounded-xl p-4 shadow-2xl z-30">
      <div className="flex justify-between items-center pb-2 mb-3 border-b border-[#1E293B]">
        <div className="flex items-center space-x-2">
          {renderIcon(selectedNode.type)}
          <h3 className="font-semibold text-xs text-white uppercase tracking-wider">{selectedNode.type} Inspector</h3>
        </div>
        <button
          onClick={() => setSelectedNode(null)}
          className="text-gray-400 hover:text-white transition p-1 rounded hover:bg-[#1E293B]"
        >
          <X className="w-3.5 h-3.5" />
        </button>
      </div>

      <div className="space-y-2 text-xs">
        <div>
          <span className="text-gray-400">Node ID:</span>
          <p className="font-mono text-white break-all">{selectedNode.id}</p>
        </div>
        <div>
          <span className="text-gray-400">Label / Name:</span>
          <p className="font-semibold text-white">{selectedNode.label}</p>
        </div>

        {selectedNode.status && (
          <div>
            <span className="text-gray-400">Runtime Health:</span>
            <p className={`font-bold ${selectedNode.status === 'CRITICAL' ? 'text-red-400' : 'text-emerald-400'}`}>
              {selectedNode.status}
            </p>
          </div>
        )}

        {selectedNode.file_path && (
          <div>
            <span className="text-gray-400">Source Path:</span>
            <p className="font-mono text-gray-300 break-all text-[11px]">{selectedNode.file_path}:{selectedNode.line_start}</p>
          </div>
        )}

        {selectedNode.author && (
          <div>
            <span className="text-gray-400">Git Author:</span>
            <p className="text-amber-300">{selectedNode.author}</p>
          </div>
        )}

        {selectedNode.ast_hash && (
          <div>
            <span className="text-gray-400">Tree-sitter AST Hash:</span>
            <p className="font-mono text-[10px] text-gray-400 break-all">{selectedNode.ast_hash.slice(0, 16)}...</p>
          </div>
        )}
      </div>
    </div>
  );
}
