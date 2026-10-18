'use client';
import React, { useState, useEffect, useRef } from 'react';
import { Terminal, Copy, Check, ArrowDownCircle, Cpu, Trash2 } from 'lucide-react';
import { useBlackboardStore } from '@/store/useBlackboardStore';

interface CypherLogEntry {
  id: string;
  timestamp: string;
  query: string;
  latency: string;
  type: 'TOPOLOGY' | 'TRAVERSAL' | 'VECTOR' | 'FORK' | 'SHORTCUT';
  status: 'SUCCESS' | 'EXECUTED';
}

const INITIAL_LOGS: CypherLogEntry[] = [
  {
    id: 'log_01',
    timestamp: '11:20:02.140',
    query: 'GRAPH.QUERY graphsre_production "MATCH (s:Service {name: \'PaymentService\'})<-[:DEPENDS_ON*1..3]-(upstream) RETURN upstream"',
    latency: '0.84ms',
    type: 'TOPOLOGY',
    status: 'SUCCESS'
  },
  {
    id: 'log_02',
    timestamp: '11:20:02.328',
    query: 'GRAPH.QUERY graphsre_production "MATCH (s:Service)-[:EXPOSES]->(e)-[:IMPLEMENTED_BY]->(f)-[:CALLS*0..6]->(target)-[:MODIFIED_BY]->(c) RETURN target, c"',
    latency: '0.92ms',
    type: 'TRAVERSAL',
    status: 'SUCCESS'
  },
  {
    id: 'log_03',
    timestamp: '11:20:02.510',
    query: 'GRAPH.QUERY graphsre_production "CALL db.idx.vector.queryNodes(\'PastIncident\', \'embedding\', 3, vecf32($vec)) YIELD node, score"',
    latency: '1.14ms',
    type: 'VECTOR',
    status: 'SUCCESS'
  },
  {
    id: 'log_04',
    timestamp: '11:20:02.990',
    query: 'GRAPH.COPY graphsre_production sandbox_inc_98a12c -> OK',
    latency: '7.80ms',
    type: 'FORK',
    status: 'SUCCESS'
  },
  {
    id: 'log_05',
    timestamp: '11:20:03.112',
    query: 'GRAPH.QUERY graphsre_production "MATCH (s:Service)-[r:SHORTCUT_TO_ROOT_CAUSE]->(f) RETURN f"',
    latency: '0.12ms',
    type: 'SHORTCUT',
    status: 'SUCCESS'
  }
];

export default function CypherConsole() {
  const [logs, setLogs] = useState<CypherLogEntry[]>(INITIAL_LOGS);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { lifecycleState } = useBlackboardStore();

  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, autoScroll]);

  // Reactively stream new queries when lifecycle state changes
  useEffect(() => {
    const now = new Date().toTimeString().split(' ')[0] + '.' + Math.floor(Math.random() * 900 + 100);
    if (lifecycleState === 'DETECTED') {
      setLogs((prev) => [
        ...prev,
        {
          id: `log_${Date.now()}_1`,
          timestamp: now,
          query: 'GRAPH.QUERY graphsre_production "MATCH (s:Service {name: \'PaymentService\'})<-[:DEPENDS_ON*1..3]-(upstream) RETURN upstream, s"',
          latency: '0.84ms',
          type: 'TOPOLOGY',
          status: 'SUCCESS'
        }
      ]);
    } else if (lifecycleState === 'HYPOTHESIS_FORMED') {
      setLogs((prev) => [
        ...prev,
        {
          id: `log_${Date.now()}_2`,
          timestamp: now,
          query: 'GRAPH.QUERY graphsre_production "MATCH (s:Service)-[:EXPOSES]->(e)-[:IMPLEMENTED_BY]->(f)-[:CALLS*0..6]->(target)-[:MODIFIED_BY]->(c) RETURN target, c"',
          latency: '0.92ms',
          type: 'TRAVERSAL',
          status: 'SUCCESS'
        },
        {
          id: `log_${Date.now()}_3`,
          timestamp: now,
          query: 'GRAPH.QUERY graphsre_production "CALL db.idx.vector.queryNodes(\'PastIncident\', \'embedding\', 3, vecf32($vec)) YIELD node, score"',
          latency: '1.14ms',
          type: 'VECTOR',
          status: 'SUCCESS'
        }
      ]);
    } else if (lifecycleState === 'RESOLVED_SHORTCUT_COMPILED') {
      setLogs((prev) => [
        ...prev,
        {
          id: `log_${Date.now()}_4`,
          timestamp: now,
          query: 'GRAPH.COPY graphsre_production sandbox_inc_98a12c -> OK',
          latency: '7.80ms',
          type: 'FORK',
          status: 'SUCCESS'
        },
        {
          id: `log_${Date.now()}_5`,
          timestamp: now,
          query: 'GRAPH.QUERY graphsre_production "MERGE (a:Alert)-[r:CAUSED_BY_SHORTCUT]->(fn:Function) RETURN r"',
          latency: '0.65ms',
          type: 'SHORTCUT',
          status: 'SUCCESS'
        }
      ]);
    } else if (lifecycleState === 'RESOLVED_VIA_SHORTCUT') {
      setLogs((prev) => [
        ...prev,
        {
          id: `log_${Date.now()}_6`,
          timestamp: now,
          query: 'GRAPH.QUERY graphsre_production "MATCH (s:Service)-[r:SHORTCUT_TO_ROOT_CAUSE]->(f) RETURN f"',
          latency: '0.12ms',
          type: 'SHORTCUT',
          status: 'SUCCESS'
        }
      ]);
    }
  }, [lifecycleState]);

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 1500);
  };

  const handleClear = () => {
    setLogs([]);
  };

  const getTypeBadgeClass = (type: CypherLogEntry['type']) => {
    switch (type) {
      case 'TOPOLOGY':
        return 'bg-blue-950 text-blue-300 border-blue-500/30';
      case 'TRAVERSAL':
        return 'bg-purple-950 text-purple-300 border-purple-500/30';
      case 'VECTOR':
        return 'bg-amber-950 text-amber-300 border-amber-500/30';
      case 'FORK':
        return 'bg-cyan-950 text-cyan-300 border-cyan-500/30';
      case 'SHORTCUT':
        return 'bg-emerald-950 text-emerald-300 border-emerald-500/30';
      default:
        return 'bg-gray-800 text-gray-300 border-gray-600/30';
    }
  };

  return (
    <div className="bg-[#090D16] border border-[#1E293B] rounded-xl overflow-hidden shadow-2xl">
      {/* Console Dock Header */}
      <div className="bg-[#0F172A] px-4 py-3 border-b border-[#1E293B] flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center space-x-3">
          <div className="flex items-center space-x-1.5">
            <Terminal className="w-4 h-4 text-emerald-400" />
            <h3 className="font-bold text-xs text-white uppercase tracking-wider">
              FalkorDB Live OpenCypher & GraphBLAS Execution Stream
            </h3>
          </div>
          <span className="flex items-center space-x-1 px-2.5 py-0.5 rounded text-[10px] font-mono bg-purple-950/80 text-purple-300 border border-purple-500/40">
            <Cpu className="w-3 h-3 text-purple-400" />
            <span>GraphBLAS v9.1 Sparse Matrix Linear Algebra</span>
          </span>
        </div>

        {/* Controls */}
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setAutoScroll(!autoScroll)}
            className={`px-2.5 py-1 rounded text-[11px] font-mono flex items-center space-x-1 transition border ${
              autoScroll
                ? 'bg-emerald-950/70 border-emerald-500/40 text-emerald-300'
                : 'bg-[#1E293B] border-transparent text-gray-400 hover:text-gray-200'
            }`}
          >
            <ArrowDownCircle className="w-3 h-3" />
            <span>Auto-Scroll: {autoScroll ? 'ON' : 'OFF'}</span>
          </button>

          <button
            onClick={handleClear}
            className="p-1.5 bg-[#1E293B] hover:bg-[#334155] text-gray-400 hover:text-gray-200 rounded transition"
            title="Clear Stream"
          >
            <Trash2 className="w-3 h-3" />
          </button>
        </div>
      </div>

      {/* Query Stream Terminal Body */}
      <div
        ref={scrollRef}
        className="p-4 font-mono text-xs max-h-56 overflow-y-auto space-y-2.5 scrollbar-thin scrollbar-thumb-gray-800"
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 italic py-4 text-center">
            Execution stream buffer cleared. Waiting for FalkorDB query execution...
          </div>
        ) : (
          logs.map((log) => (
            <div
              key={log.id}
              className="group flex items-start justify-between bg-[#0F172A]/70 hover:bg-[#0F172A] p-2.5 rounded-lg border border-[#1E293B]/70 hover:border-[#334155] transition text-left"
            >
              <div className="flex items-start space-x-2.5 flex-1 min-w-0 pr-3">
                <span className="text-[10px] text-gray-500 pt-0.5 whitespace-nowrap">{log.timestamp}</span>
                <span
                  className={`px-1.5 py-0.5 rounded text-[9px] font-bold uppercase border whitespace-nowrap ${getTypeBadgeClass(
                    log.type
                  )}`}
                >
                  {log.type}
                </span>
                <span className="text-gray-200 break-all leading-relaxed">
                  {log.query.startsWith('GRAPH.COPY') ? (
                    <span className="text-cyan-400 font-semibold">{log.query}</span>
                  ) : (
                    <>
                      <span className="text-pink-400 font-semibold">GRAPH.QUERY </span>
                      <span className="text-amber-300">graphsre_production </span>
                      <span className="text-emerald-300">
                        "{log.query.replace(/^GRAPH\.QUERY\s+graphsre_production\s+"?|"?$/g, '')}"
                      </span>
                    </>
                  )}
                </span>
              </div>

              <div className="flex items-center space-x-2 whitespace-nowrap">
                <span className="px-2 py-0.5 bg-emerald-950/80 border border-emerald-500/40 text-emerald-400 rounded text-[10px] font-bold">
                  {log.latency}
                </span>

                <button
                  onClick={() => handleCopy(log.id, log.query)}
                  className="p-1 hover:bg-[#1E293B] text-gray-400 hover:text-white rounded transition"
                  title="Copy Query"
                >
                  {copiedId === log.id ? (
                    <Check className="w-3.5 h-3.5 text-emerald-400" />
                  ) : (
                    <Copy className="w-3.5 h-3.5 opacity-60 group-hover:opacity-100" />
                  )}
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
