import React, { useEffect, useRef } from 'react';
import cytoscape from 'cytoscape';

type GraphNode = {
  data?: {
    id?: string;
    label?: string;
    clauseId?: string;
    type?: string;
  };
};

type GraphJson = {
  nodes?: GraphNode[];
  edges?: any[];
};

interface GraphViewerProps {
  graphJson?: GraphJson;
  onSelectClause: (clauseId: string) => void;
}

export function GraphViewer({ graphJson, onSelectClause }: GraphViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clean up previous instance
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    if (!graphJson?.nodes || graphJson.nodes.length === 0) {
      return;
    }

    const clauseNodes = graphJson.nodes.filter((node) => node.data?.type === 'clause');
    // Allow rendering even with just document node - clauses may be extracted later
    // if (clauseNodes.length === 0) {
    //   return;
    // }

    // Transform the graph data for Cytoscape
    const elements: cytoscape.ElementDefinition[] = [
      ...(graphJson.nodes || []).map(node => ({
        data: {
          ...node.data,
          // Extract clause ID from the node ID if it follows the pattern "clause:{uuid}"
          clauseId: node.data?.id?.startsWith('clause:') ? node.data.id.split(':')[1] : undefined
        }
      })),
      ...(graphJson.edges || [])
    ];

    // Create Cytoscape instance
    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node[type = "document"]',
          style: {
            'background-color': '#4689F0',
            'label': 'data(label)',
            'color': '#ffffff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '12px',
            'width': '60px',
            'height': '60px',
            'border-width': '2px',
            'border-color': '#2c5aa0'
          }
        },
        {
          selector: 'node[type = "clause"]',
          style: {
            'background-color': '#10b981',
            'label': 'data(label)',
            'color': '#ffffff',
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': '10px',
            'width': '45px',
            'height': '45px',
            'border-width': '1px',
            'border-color': '#059669'
          }
        },
        {
          selector: 'edge',
          style: {
            'width': 2,
            'line-color': '#cbd5e1',
            'target-arrow-color': '#cbd5e1',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier'
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': '3px',
            'border-color': '#f59e0b'
          }
        },
        {
          selector: 'node:hover',
          style: {
            'border-width': '3px',
            'border-color': '#f59e0b'
          }
        }
      ],
      layout: {
        name: 'cose',
        idealEdgeLength: 100,
        nodeOverlap: 20,
        refresh: 20,
        fit: true,
        padding: 30,
        randomize: false,
        componentSpacing: 100,
        nodeRepulsion: 400000,
        edgeElasticity: 100,
        nestingFactor: 5,
        gravity: 80,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0
      }
    });

    // Handle node clicks
    cy.on('tap', 'node[type = "clause"]', (event: any) => {
      const node = event.target;
      const clauseId = node.data('clauseId');
      if (clauseId && onSelectClause) {
        onSelectClause(clauseId);
      }
    });

    // Add hover effects
    cy.on('mouseover', 'node', (event: any) => {
      event.target.style({
        'border-width': '3px',
        'border-color': '#f59e0b'
      });
    });

    cy.on('mouseout', 'node', (event: any) => {
      event.target.style({
        'border-width': event.target.data('type') === 'document' ? '2px' : '1px',
        'border-color': event.target.data('type') === 'document' ? '#2c5aa0' : '#059669'
      });
    });

    cyRef.current = cy;

    // Cleanup function
    return () => {
      if (cy) {
        cy.destroy();
      }
    };
  }, [graphJson, onSelectClause]);

  if (!graphJson?.nodes || graphJson.nodes.length === 0) {
    return <div className="p-4 text-sm text-[color:var(--ink-500)]">No graph yet.</div>;
  }

  const clauseNodes = graphJson.nodes.filter((node) => node.data?.type === 'clause');

  // Note: We now allow rendering with just document node, but show a helpful message
  // if (clauseNodes.length === 0) {
  //   return <div className="p-4 text-sm text-[color:var(--ink-500)]">No clause nodes available.</div>;
  // }

  return (
    <div ref={containerRef} className="h-full w-full" />
  );
}
