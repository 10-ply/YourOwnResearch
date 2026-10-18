import React, { useState, useEffect } from 'react';
import { GraphVisualizer } from './components/GraphVisualizer';
import { ShieldCheck, Flame, Skull, Compass, Search, Filter } from 'lucide-react';

interface NodeData {
  id: string;
  doi: string;
  title: string;
  publication_year: number;
  authors: string[];
  status: string;
  raw_ci: number;
  smoothed_ci: number;
  constraint_density: number;
}

interface EdgeData {
  source: string;
  target: string;
  polarity: string;
  snippet?: string;
}

export default function App() {
  const [nodes, setNodes] = useState<NodeData[]>([]);
  const [edges, setEdges] = useState<EdgeData[]>([]);
  const [showGraveyard, setShowGraveyard] = useState(true);
  const [selectedNode, setSelectedNode] = useState<NodeData | null>(null);
  const [hypothesis, setHypothesis] = useState('');
  const [evalResult, setEvalResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchGraphData();
  }, []);

  const fetchGraphData = async () => {
    try {
      const res = await fetch('/api/graph/full');
      const data = await res.json();
      setNodes(data.nodes || []);
      setEdges(data.edges || []);
    } catch (err) {
      console.error("Failed to load graph data", err);
    }
  };

  const handleEvaluateClaim = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!hypothesis.trim()) return;
    setLoading(true);
    try {
      const res = await fetch('/api/claim/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ hypothesis })
      });
      const data = await res.json();
      setEvalResult(data);
    } catch (err) {
      console.error("Claim evaluation failed", err);
    } finally {
      setLoading(false);
    }
  };

  const getNodeIncomingEdges = (nodeId: string) => {
    return edges.filter(e => e.target === nodeId);
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', width: '100vw', backgroundColor: '#0b0f19' }}>
      <header style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 24px', borderBottom: '1px solid #1e293b', backgroundColor: '#0f172a' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <Compass style={{ color: '#38bdf8' }} size={28} />
          <div>
            <h1 style={{ margin: 0, fontSize: '18px', fontWeight: 'bold', color: '#f8fafc' }}>EpistemeGraph</h1>
            <p style={{ margin: 0, fontSize: '12px', color: '#94a3b8' }}>Automated Scientific Cladistics & Refutation Engine</p>
          </div>
        </div>

        <div style={{ display: 'flex', gap: '16px', fontSize: '13px' }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#10b981' }}>
            <ShieldCheck size={16} /> VALIDATED_CORE
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#f59e0b' }}>
            <Flame size={16} /> CONTESTED_FRONTIER
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#ef4444' }}>
            <Skull size={16} /> FALSIFIED_DEAD_END
          </span>
          <span style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#8b5cf6' }}>
            <Compass size={16} /> DOMAIN_CONSTRAINED
          </span>
        </div>

        <button
          onClick={() => setShowGraveyard(!showGraveyard)}
          style={{
            display: 'flex', alignItems: 'center', gap: '8px',
            padding: '8px 16px', borderRadius: '6px', border: '1px solid #334155',
            backgroundColor: showGraveyard ? '#1e293b' : '#0f172a', color: '#f8fafc', fontWeight: 'medium'
          }}
        >
          <Filter size={16} />
          {showGraveyard ? "Hide Graveyard of Pseudologic" : "Show Graveyard of Pseudologic"}
        </button>
      </header>

      <div style={{ display: 'flex', flex: 1, position: 'relative', overflow: 'hidden' }}>
        <div style={{ flex: 1, height: '100%' }}>
          <GraphVisualizer
            nodes={nodes}
            edges={edges}
            showGraveyard={showGraveyard}
            onSelectNode={(node) => setSelectedNode(node)}
          />
        </div>

        <div style={{ width: '380px', borderLeft: '1px solid #1e293b', backgroundColor: '#0f172a', padding: '20px', overflowY: 'auto' }}>
          <div style={{ marginBottom: '24px', padding: '16px', backgroundColor: '#1e293b', borderRadius: '8px' }}>
            <h3 style={{ margin: '0 0 12px 0', fontSize: '14px', color: '#38bdf8', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Search size={16} /> System 1 Claim Evaluator
            </h3>
            <form onSubmit={handleEvaluateClaim}>
              <textarea
                value={hypothesis}
                onChange={(e) => setHypothesis(e.target.value)}
                placeholder="Enter natural language scientific hypothesis..."
                rows={3}
                style={{ width: '100%', boxSizing: 'border-box', padding: '8px', borderRadius: '6px', border: '1px solid #334155', backgroundColor: '#0f172a', color: '#e2e8f0', resize: 'none', fontSize: '12px' }}
              />
              <button
                type="submit"
                disabled={loading}
                style={{ width: '100%', marginTop: '8px', padding: '8px', borderRadius: '6px', backgroundColor: '#0284c7', color: '#fff', border: 'none', fontWeight: 'bold' }}
              >
                {loading ? 'Evaluating...' : 'Evaluate Hypothesis'}
              </button>
            </form>

            {evalResult && (
              <div style={{ marginTop: '12px', fontSize: '12px', color: '#cbd5e1' }}>
                <p><strong>Predicted Polarity:</strong> <span style={{ color: evalResult.system1_analysis?.polarity === 'CONTESTING' ? '#ef4444' : '#10b981' }}>{evalResult.system1_analysis?.polarity}</span></p>
                <p><strong>System 1 Confidence:</strong> {(evalResult.system1_analysis?.confidence * 100).toFixed(1)}%</p>
                <p><strong>Evidential Verdict:</strong> {evalResult.overall_evidential_verdict}</p>
              </div>
            )}
          </div>

          {selectedNode ? (
            <div style={{ padding: '16px', backgroundColor: '#1e293b', borderRadius: '8px' }}>
              <h2 style={{ fontSize: '16px', margin: '0 0 8px 0', color: '#f8fafc' }}>{selectedNode.title}</h2>
              <p style={{ fontSize: '12px', color: '#94a3b8', margin: '0 0 12px 0' }}>
                Year: {selectedNode.publication_year} | DOI: {selectedNode.doi}
              </p>
              <div style={{ marginBottom: '12px' }}>
                <span style={{
                  padding: '4px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 'bold',
                  backgroundColor: selectedNode.status === 'VALIDATED_CORE' ? '#065f46' :
                                   selectedNode.status === 'FALSIFIED_DEAD_END' ? '#991b1b' :
                                   selectedNode.status === 'DOMAIN_CONSTRAINED' ? '#5b21b6' : '#9a3412',
                  color: '#fff'
                }}>
                  {selectedNode.status}
                </span>
              </div>
              <p style={{ fontSize: '13px' }}><strong>Bayesian Contestation Index:</strong> {selectedNode.smoothed_ci?.toFixed(3)}</p>
              <p style={{ fontSize: '13px' }}><strong>Raw Contestation Index:</strong> {selectedNode.raw_ci?.toFixed(3)}</p>
              <p style={{ fontSize: '13px' }}><strong>Constraint Edge Density:</strong> {(selectedNode.constraint_density * 100).toFixed(1)}%</p>

              <h4 style={{ margin: '16px 0 8px 0', fontSize: '13px', color: '#38bdf8' }}>Citation Snippets & Contexts</h4>
              {getNodeIncomingEdges(selectedNode.id).map((edge, idx) => (
                <div key={idx} style={{ padding: '8px', marginBottom: '8px', backgroundColor: '#0f172a', borderRadius: '4px', borderLeft: `3px solid ${edge.polarity === 'CONTESTING' ? '#ef4444' : '#10b981'}` }}>
                  <p style={{ margin: '0 0 4px 0', fontSize: '11px', fontWeight: 'bold', color: edge.polarity === 'CONTESTING' ? '#ef4444' : '#10b981' }}>
                    [{edge.polarity}] from {edge.source}
                  </p>
                  <p style={{ margin: 0, fontSize: '11px', fontStyle: 'italic', color: '#cbd5e1' }}>
                    "{edge.snippet || 'No citation context snippet extracted.'}"
                  </p>
                </div>
              ))}
            </div>
          ) : (
            <div style={{ textAlign: 'center', color: '#64748b', marginTop: '40px' }}>
              <p>Click any node on the cladogram to view paper details, citation contexts, and Bayesian refutation statistics.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
