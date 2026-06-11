import React, { useEffect, useState, useCallback } from 'react';
import { api } from '../services/api';
import { 
  ReactFlow, 
  Background, 
  Controls, 
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { Search, Loader2, Network, HelpCircle, GitFork } from 'lucide-react';

export const GraphDiscovery: React.FC = () => {
  const [nodes, setNodes, onNodesChange] = useNodesState<any>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<any>([]);
  const [loading, setLoading] = useState(true);
  const [rawGraphData, setRawGraphData] = useState<any>(null);
  
  // Filtering & Search states
  const [searchNode, setSearchNode] = useState('');
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [nodeFilter, setNodeFilter] = useState('ALL');
  
  // Path Discovery states (Module 10)
  const [sourceNode, setSourceNode] = useState('');
  const [targetNode, setTargetNode] = useState('');
  const [pathResults, setPathResults] = useState<any[]>([]);
  const [pathLoading, setPathLoading] = useState(false);

  const fetchGraph = async () => {
    setLoading(true);
    try {
      const res = await api.get('/graph/data');
      setRawGraphData(res.data);
      processGraphData(res.data, 'ALL');
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const processGraphData = (data: any, filter: string) => {
    if (!data) return;

    // Filter nodes if needed
    const filteredNodes = data.nodes.filter((n: any) => {
      if (filter === 'ALL') return true;
      return n.label === filter;
    });

    // Create unique IDs list
    const nodeIds = new Set(filteredNodes.map((n: any) => n.id));

    // Filter links that connect to filtered nodes
    const filteredLinks = data.links.filter((l: any) => {
      return nodeIds.has(l.source) && nodeIds.has(l.target);
    });

    // Arrange nodes in a simple grid/circle layout
    const flowNodes = filteredNodes.map((n: any, idx: number) => {
      const angle = (idx / filteredNodes.length) * 2 * Math.PI;
      const radius = 250 + Math.random() * 50;
      const x = 400 + radius * Math.cos(angle);
      const y = 300 + radius * Math.sin(angle);

      // Node colors based on label
      let color = '#3b82f6'; // Concept
      if (n.label === 'Paper') color = '#ef4444';
      if (n.label === 'Author') color = '#10b981';
      if (n.label === 'Technology') color = '#8b5cf6';
      if (n.label === 'Research Topics') color = '#f59e0b';

      return {
        id: n.id,
        data: { label: `${n.label}: ${n.id}` },
        position: { x, y },
        style: {
          border: `1.5px solid ${color}`,
          boxShadow: `0 0 10px ${color}33`
        },
        raw: n
      };
    });

    const flowEdges = filteredLinks.map((l: any, idx: number) => ({
      id: `edge_${idx}`,
      source: l.source,
      target: l.target,
      label: l.type,
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#64748b'
      },
      style: { stroke: '#475569' }
    }));

    setNodes(flowNodes);
    setEdges(flowEdges);
  };

  useEffect(() => {
    fetchGraph();
  }, []);

  const handleFilterChange = (filter: string) => {
    setNodeFilter(filter);
    processGraphData(rawGraphData, filter);
  };

  const handleNodeClick = (_: any, node: any) => {
    setSelectedNode(node.raw);
  };

  // Find paths (Module 10)
  const handleFindPath = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sourceNode || !targetNode) return;
    setPathLoading(true);
    try {
      const res = await api.get(`/graph/paths?source=${encodeURIComponent(sourceNode)}&target=${encodeURIComponent(targetNode)}`);
      setPathResults(res.data);
      
      // Highlight edges in the path
      if (res.data && res.data.length > 0) {
        const pathSeq = res.data[0].path_sequence || [];
        const pathEdges = new Set<string>();
        
        for (let i = 0; i < pathSeq.length - 2; i += 2) {
          pathEdges.add(`${pathSeq[i]}_${pathSeq[i+2]}`);
          pathEdges.add(`${pathSeq[i+2]}_${pathSeq[i]}`);
        }

        setEdges((eds) => 
          eds.map((edge) => {
            const match = pathEdges.has(`${edge.source}_${edge.target}`) || pathEdges.has(`${edge.target}_${edge.source}`);
            return {
              ...edge,
              style: match ? { stroke: '#e11d48', strokeWidth: 3.5 } : { stroke: '#475569' }
            };
          })
        );
      }
    } catch (err) {
      console.error(err);
    } finally {
      setPathLoading(false);
    }
  };

  // Search node helper
  const handleSearchNode = (e: React.FormEvent) => {
    e.preventDefault();
    const found = nodes.find(n => n.id.toLowerCase().includes(searchNode.toLowerCase()));
    if (found) {
      setSelectedNode(found.raw);
      // Highlight that node by zooming in (custom state focus or react flow instance focus helper)
    }
  };

  if (loading) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center flex-col gap-3">
        <Loader2 className="h-8 w-8 text-indigo-500 animate-spin" />
        <p className="text-slate-400 text-sm">Mapping Neo4j Cypher coordinates...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold bg-gradient-to-r from-white to-slate-400 bg-clip-text text-transparent flex items-center gap-3">
            <Network className="h-8 w-8 text-indigo-500" />
            Knowledge Graph Explorer
          </h1>
          <p className="text-slate-400 text-sm mt-1">
            Navigate through papers, authors, and extracted concept topologies in real-time.
          </p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Sidebar Controls */}
        <div className="space-y-6 lg:col-span-1">
          {/* Node Filter */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-3">
            <h3 className="text-sm font-bold text-slate-200">Category Filter</h3>
            <div className="flex flex-wrap gap-2">
              {['ALL', 'Paper', 'Author', 'Concept', 'Technology', 'Research Topics'].map((type) => (
                <button
                  key={type}
                  onClick={() => handleFilterChange(type)}
                  className={`text-xs px-3 py-1.5 rounded-lg border transition-all ${
                    nodeFilter === type
                      ? 'bg-blue-600/20 border-blue-500 text-blue-400 font-medium'
                      : 'border-slate-800 text-slate-400 hover:border-slate-700 hover:text-white'
                  }`}
                >
                  {type}
                </button>
              ))}
            </div>
          </div>

          {/* Path Discovery (Module 10 Multi-hop routing query) */}
          <div className="glass-panel p-5 rounded-2xl border border-slate-800 space-y-4">
            <div className="flex items-center gap-2 text-indigo-400">
              <GitFork className="h-4.5 w-4.5" />
              <h3 className="text-sm font-bold text-slate-200">Path Discovery</h3>
            </div>
            
            <form onSubmit={handleFindPath} className="space-y-3">
              <div>
                <label className="block text-[10px] uppercase font-semibold text-slate-400 mb-1">Source Concept</label>
                <input
                  type="text"
                  value={sourceNode}
                  onChange={(e) => setSourceNode(e.target.value)}
                  placeholder="e.g. Transformer Architecture"
                  className="w-full px-3 py-2 rounded-lg glass-input text-xs"
                />
              </div>
              <div>
                <label className="block text-[10px] uppercase font-semibold text-slate-400 mb-1">Target Concept</label>
                <input
                  type="text"
                  value={targetNode}
                  onChange={(e) => setTargetNode(e.target.value)}
                  placeholder="e.g. Healthcare Diagnostics"
                  className="w-full px-3 py-2 rounded-lg glass-input text-xs"
                />
              </div>
              <button
                type="submit"
                className="w-full bg-indigo-600 hover:bg-indigo-500 text-white text-xs font-semibold py-2 rounded-lg transition-all"
              >
                {pathLoading ? 'Traversing graph...' : 'Find Shortest Path'}
              </button>
            </form>

            {pathResults.length > 0 && (
              <div className="pt-3 border-t border-slate-800/60 space-y-2">
                <p className="text-[10px] text-slate-400 uppercase font-semibold">Path Found:</p>
                <div className="bg-slate-900/60 p-3 rounded-xl border border-slate-850 text-xs">
                  {pathResults[0].path_sequence?.map((node: string, index: number) => {
                    const isNode = index % 2 === 0;
                    return (
                      <span key={index} className={isNode ? 'text-blue-400 font-medium' : 'text-slate-500 mx-1'}>
                        {node} {isNode && index < pathResults[0].path_sequence.length - 1 ? '→' : ''}
                      </span>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Graph Display Area */}
        <div className="lg:col-span-3 flex flex-col h-[70vh] border border-slate-850 rounded-2xl overflow-hidden glass-panel relative">
          
          {/* Node Search overlay */}
          <div className="absolute top-4 left-4 z-10 flex gap-2 w-72">
            <form onSubmit={handleSearchNode} className="flex-1 relative">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-500" />
              <input
                type="text"
                placeholder="Search concepts..."
                value={searchNode}
                onChange={(e) => setSearchNode(e.target.value)}
                className="w-full pl-8 pr-3 py-2 rounded-lg glass-input text-xs bg-slate-950/80"
              />
            </form>
          </div>

          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            fitView
          >
            <Controls />
            <MiniMap style={{ background: '#070b13' }} />
            <Background color="#1e293b" gap={16} />
          </ReactFlow>

          {/* Selected Node Panel Overlay */}
          {selectedNode && (
            <div className="absolute bottom-4 right-4 z-10 w-80 glass-card p-4 rounded-xl border border-blue-500/30 text-xs space-y-2 max-h-60 overflow-y-auto">
              <div className="flex justify-between items-center">
                <span className="font-bold text-slate-200 capitalize">{selectedNode.label}: {selectedNode.name}</span>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-slate-500 hover:text-white"
                >
                  ✕
                </button>
              </div>
              <div className="text-slate-400 space-y-1">
                {Object.entries(selectedNode.properties || {}).map(([k, v]: any) => (
                  <div key={k}>
                    <span className="font-semibold text-slate-350">{k}:</span> {v.toString()}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
export default GraphDiscovery;
