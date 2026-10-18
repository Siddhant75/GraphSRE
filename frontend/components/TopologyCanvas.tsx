'use client';
import React, { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
// @ts-ignore
import coseBilkent from 'cytoscape-cose-bilkent';
// @ts-ignore
import dagre from 'cytoscape-dagre';
import { cytoscapeStylesheet } from '@/styles/cytoscapeStyles';
import { useBlackboardStore } from '@/store/useBlackboardStore';
import NodeInspector from '@/components/NodeInspector';
import { ZoomIn, ZoomOut, Maximize2, RefreshCw } from 'lucide-react';

if (typeof window !== 'undefined') {
  try {
    cytoscape.use(coseBilkent);
    cytoscape.use(dagre);
  } catch (e) {
    // Already registered
  }
}

export default function TopologyCanvas() {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);
  const { elements, setSelectedNode } = useBlackboardStore();
  const [activeLayout, setActiveLayout] = useState<'cose-bilkent' | 'dagre'>('cose-bilkent');

  useEffect(() => {
    if (!containerRef.current) return;

    // Defensively sanitize elements:
    // Only allow nodes, and edges whose source and target exist among the nodes.
    const nodeIds = new Set<string>();
    for (const el of elements) {
      if (el?.data && !el.data.source && !el.data.target && el.data.id) {
        nodeIds.add(String(el.data.id));
      }
    }

    const validElements = elements.filter((el) => {
      if (!el?.data) return false;
      if (el.data.source || el.data.target) {
        const hasSource = nodeIds.has(String(el.data.source));
        const hasTarget = nodeIds.has(String(el.data.target));
        return hasSource && hasTarget;
      }
      return Boolean(el.data.id);
    });

    try {
      if (cyRef.current) {
        cyRef.current.destroy();
        cyRef.current = null;
      }

      const cy = cytoscape({
        container: containerRef.current,
        elements: validElements,
        style: cytoscapeStylesheet,
        layout: {
          name: activeLayout,
          animate: true,
          animationDuration: 500,
          padding: 50
        } as any
      });

      cy.on('tap', 'node', (evt) => {
        try {
          setSelectedNode(evt.target.data());
        } catch (e) {
          console.warn("Node tap handler:", e);
        }
      });

      cy.on('tap', (evt) => {
        try {
          if (evt.target === cy) {
            setSelectedNode(null);
          }
        } catch (e) {
          console.warn("Canvas tap handler:", e);
        }
      });

      cyRef.current = cy;
    } catch (err) {
      console.error("Cytoscape initialization caught error:", err);
    }

    return () => {
      if (cyRef.current) {
        try {
          cyRef.current.destroy();
        } catch (e) {}
        cyRef.current = null;
      }
    };
  }, [elements, activeLayout, setSelectedNode]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit(undefined, 50);

  return (
    <div className="relative w-full h-[620px] bg-[#090D16] border border-[#1E293B] rounded-xl overflow-hidden shadow-inner">
      {/* Top Floating Controls */}
      <div className="absolute top-4 left-4 z-20 flex items-center space-x-2 bg-[#0F172A]/90 backdrop-blur px-3 py-1.5 rounded-lg border border-[#1E293B]">
        <button
          onClick={handleZoomIn}
          title="Zoom In"
          className="p-1 hover:bg-[#1E293B] text-gray-300 hover:text-white rounded transition"
        >
          <ZoomIn className="w-4 h-4" />
        </button>
        <button
          onClick={handleZoomOut}
          title="Zoom Out"
          className="p-1 hover:bg-[#1E293B] text-gray-300 hover:text-white rounded transition"
        >
          <ZoomOut className="w-4 h-4" />
        </button>
        <button
          onClick={handleFit}
          title="Fit Graph"
          className="p-1 hover:bg-[#1E293B] text-gray-300 hover:text-white rounded transition"
        >
          <Maximize2 className="w-4 h-4" />
        </button>
        <div className="w-[1px] h-4 bg-[#1E293B]" />
        <button
          onClick={() => setActiveLayout(activeLayout === 'cose-bilkent' ? 'dagre' : 'cose-bilkent')}
          title="Toggle cose-bilkent / dagre layout"
          className="flex items-center space-x-1.5 text-xs text-blue-400 hover:text-blue-300 transition"
        >
          <RefreshCw className="w-3.5 h-3.5" />
          <span className="font-mono text-[11px]">{activeLayout}</span>
        </button>
      </div>

      {/* Node Inspector Overlay */}
      <NodeInspector />

      {/* Cytoscape Container */}
      <div ref={containerRef} className="w-full h-full" />
    </div>
  );
}
