import React, { useEffect, useRef } from 'react';
import Graph from 'graphology';
import Sigma from 'sigma';

interface NodeData {
  id: string;
  title: string;
  status: string;
  smoothed_ci: number;
  publication_year: number;
}

interface EdgeData {
  source: string;
  target: string;
  polarity: string;
  snippet?: string;
}

interface GraphVisualizerProps {
  nodes: NodeData[];
  edges: EdgeData[];
  showGraveyard: boolean;
  onSelectNode: (node: NodeData) => void;
}

const STATUS_COLORS: Record<string, string> = {
  VALIDATED_CORE: '#10b981',      // Green
  CONTESTED_FRONTIER: '#f59e0b',  // Yellow
  FALSIFIED_DEAD_END: '#ef4444',  // Red
  DOMAIN_CONSTRAINED: '#8b5cf6',  // Purple
  UNREVIEWED: '#64748b'           // Gray
};

export const GraphVisualizer: React.FC<GraphVisualizerProps> = ({ nodes, edges, showGraveyard, onSelectNode }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const rendererRef = useRef<Sigma | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    const graph = new Graph();
    const activeNodes = nodes.filter(n => showGraveyard || n.status !== 'FALSIFIED_DEAD_END');
    const nodeSet = new Set(activeNodes.map(n => n.id));

    activeNodes.forEach((node, idx) => {
      const yearOffset = (node.publication_year - 1800) * 2;
      const yPos = node.status === 'FALSIFIED_DEAD_END' ? -150 :
                   node.status === 'VALIDATED_CORE' ? 100 :
                   node.status === 'DOMAIN_CONSTRAINED' ? 0 : 50;

      graph.addNode(node.id, {
        label: `${node.title} (${node.publication_year})`,
        size: Math.max(8, 15 - node.smoothed_ci * 10),
        color: STATUS_COLORS[node.status] || '#94a3b8',
        x: yearOffset + (idx % 5) * 20,
        y: yPos + (idx % 3) * 30,
        raw: node
      });
    });

    edges.forEach((edge) => {
      if (nodeSet.has(edge.source) && nodeSet.has(edge.target)) {
        try {
          graph.addEdge(edge.source, edge.target, {
            type: 'arrow',
            size: 3,
            color: edge.polarity === 'CONTESTING' ? '#ef4444' :
                   edge.polarity === 'SUPPORTING' ? '#10b981' :
                   edge.polarity === 'DOMAIN_CONSTRAINED' ? '#8b5cf6' : '#64748b',
            label: edge.polarity
          });
        } catch (e) {}
      }
    });

    if (rendererRef.current) {
      rendererRef.current.kill();
    }

    const renderer = new Sigma(graph, containerRef.current, {
      renderEdgeLabels: true,
      minCameraRatio: 0.1,
      maxCameraRatio: 5
    });

    renderer.on('clickNode', (event) => {
      const nodeData = graph.getNodeAttribute(event.node, 'raw');
      if (nodeData) {
        onSelectNode(nodeData);
      }
    });

    rendererRef.current = renderer;

    return () => {
      renderer.kill();
    };
  }, [nodes, edges, showGraveyard]);

  return (
    <div
      ref={containerRef}
      style={{ width: '100%', height: '100%', minHeight: '500px', backgroundColor: '#0f172a' }}
    />
  );
};
