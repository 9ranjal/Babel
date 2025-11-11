import { useEffect, useRef, useState } from 'react';
import cytoscape from 'cytoscape';
import { enqueueAssistantMessage } from '../../lib/chatBus';

type GraphNode = {
  data?: {
    id?: string;
    label?: string;
    clauseId?: string;
    type?: string;
    sizeScore?: number;
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
  const [highlightNonMarket, setHighlightNonMarket] = useState<boolean>(false);
  const selectedNodeRef = useRef<string | null>(null);
  const baseSizeMapRef = useRef<Map<string, { width: number; height: number }>>(new Map());
  const hoveredNodeRef = useRef<string | null>(null);
  const highlightRefreshRef = useRef<(() => void) | null>(null);
  const maintainSelectionRef = useRef<(() => void) | null>(null);
  const breathingStyleElRef = useRef<HTMLStyleElement | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Clean up previous instance
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    selectedNodeRef.current = null;
    hoveredNodeRef.current = null;
    maintainSelectionRef.current = null;

    if (!graphJson?.nodes || graphJson.nodes.length === 0) {
      return;
    }

    // Soft palette inspired by mind-map aesthetic
    const C = {
      nodeFill: '#F6F4F1',
      nodeFillActive: '#F1E9DD',
      nodeFillConnected: '#E8EEF6',
      label: '#000000',
      labelMuted: '#4A4A4A',
      edgeBase: '#B7C2CD',
      edgeStrong: '#5E6471',
    };

    const CATEGORY_COLORS: Record<string, string> = {
      'Economics': '#8BA3C7',
      'Ownership & Dilution': '#9E8BC7',
      'Control & Governance': '#7AA6A3',
      'Transfer & Liquidity': '#C7A189',
      'Information & Oversight': '#7FB7B1',
      'Founder/Team Matters': '#C5A677',
      'Deal Process & Closing': '#A8B2BC',
      'Legal Boilerplate': '#C0B7B0',
      'Company/Structure': '#8F8A87',
    };

    // Transform the graph data for Cytoscape
    const elements: cytoscape.ElementDefinition[] = [
      ...(graphJson.nodes || []).map(node => {
        const d: any = node.data || {};
        const badge = d.badge ? `  [${d.badge}]` : '';
        const displayLabel = (d.label || '').toString() + badge;
        const clauseId =
          d?.clauseId ??
          (typeof d?.id === 'string' && d.id.startsWith('clause:') ? d.id.split(':')[1] : undefined);

        return {
          data: {
            ...d,
            label: displayLabel,
            clauseId
          }
        };
      }),
      ...(graphJson.edges || [])
    ];

    // Create Cytoscape instance
    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        // Bucket color theming
        { selector: 'node[type = "category"][bucket = "Economics"]', style: { 'border-color': '#4C5BD5' } },
        { selector: 'node[type = "category"][bucket = "Ownership & Dilution"]', style: { 'border-color': '#7C3AED' } },
        { selector: 'node[type = "category"][bucket = "Control & Governance"]', style: { 'border-color': '#3AA6A0' } },
        { selector: 'node[type = "category"][bucket = "Transfer & Liquidity"]', style: { 'border-color': '#E76F51' } },
        { selector: 'node[type = "category"][bucket = "Information & Oversight"]', style: { 'border-color': '#2A9D8F' } },
        { selector: 'node[type = "category"][bucket = "Founder/Team Matters"]', style: { 'border-color': '#F4A261' } },
        { selector: 'node[type = "category"][bucket = "Deal Process & Closing"]', style: { 'border-color': '#9AA3AF' } },
        { selector: 'node[type = "category"][bucket = "Legal Boilerplate"]', style: { 'border-color': '#BDBDBD' } },
        { selector: 'node[type = "category"][bucket = "Company/Structure"]', style: { 'border-color': '#6D6875' } },
        {
          selector: 'node[type = "document"]',
          style: {
            'background-color': '#1f4ed8',
            'label': 'data(label)',
            'color': '#000000',
            'text-valign': 'center',
            'text-halign': 'center',
            'text-outline-width': 2,
            'text-outline-color': '#1f4ed8',
            'shape': 'ellipse',
            'font-size': '13px',
            'width': '90px',
            'height': '90px',
            'border-width': '0px',
            'border-color': '#000000'
          }
        },
        {
          selector: 'node[type = "category"]',
          style: {
            'background-color': '#e5e7eb',
            'label': 'data(label)',
            'color': '#000000',
            // Always-visible caption below the circle
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 3,
            'shape': 'ellipse',
            'font-size': '11px',
            'width': 48,
            'height': 48,
            'border-width': '2px',
            'border-color': '#111111',
            'text-outline-width': 2,
            'text-outline-color': '#ffffff',
            'text-opacity': 0.95
          }
        },
        {
          selector: 'node[type = "clause"]',
          style: {
            'background-color': '#e5e7eb',
            'label': 'data(label)',
            'color': '#000000',
            // Compact node; place label outside to reduce bounding box size
            'text-valign': 'bottom',
            'text-halign': 'center',
            'text-margin-y': 2,
            'text-wrap': 'wrap',
            'text-max-width': '160px',
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.8,
            'text-background-shape': 'roundrectangle',
            'text-background-padding': '1px',
            'shape': 'roundrectangle',
            'font-size': '10px',
            'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif',
            'min-zoomed-font-size': 8,
            'width': 'data(size)',
            'height': 'data(size)',
            'border-width': '1px',
            'border-color': '#9ca3af',
            'text-opacity': 0
          }
        },
        // Clause border color by bucket
        { selector: 'node[type = "clause"][bucket = "Economics"]', style: { 'border-color': '#8BA3C7' } },
        { selector: 'node[type = "clause"][bucket = "Ownership & Dilution"]', style: { 'border-color': '#9E8BC7' } },
        { selector: 'node[type = "clause"][bucket = "Control & Governance"]', style: { 'border-color': '#7AA6A3' } },
        { selector: 'node[type = "clause"][bucket = "Transfer & Liquidity"]', style: { 'border-color': '#C7A189' } },
        { selector: 'node[type = "clause"][bucket = "Information & Oversight"]', style: { 'border-color': '#7FB7B1' } },
        { selector: 'node[type = "clause"][bucket = "Founder/Team Matters"]', style: { 'border-color': '#C5A677' } },
        { selector: 'node[type = "clause"][bucket = "Deal Process & Closing"]', style: { 'border-color': '#A8B2BC' } },
        { selector: 'node[type = "clause"][bucket = "Legal Boilerplate"]', style: { 'border-color': '#C0B7B0' } },
        { selector: 'node[type = "clause"][bucket = "Company/Structure"]', style: { 'border-color': '#8F8A87' } },
        // Category fill by bucket (circles) – muted palette
        { selector: 'node[type = "category"]', style: { 'background-color': '#8BA3C7', 'color': '#000000', 'border-color': '#8BA3C7', 'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif', 'text-opacity': 0.95 } },
        { selector: 'node[type = "category"][bucket = "Ownership & Dilution"]', style: { 'background-color': '#9E8BC7', 'color': '#000000', 'border-color': '#9E8BC7', 'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif', 'text-opacity': 0.95 } },
        { selector: 'node[type = "category"][bucket = "Control & Governance"]', style: { 'background-color': '#7AA6A3', 'color': '#000000', 'border-color': '#7AA6A3', 'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif', 'text-opacity': 0.95 } },
        { selector: 'node[type = "category"][bucket = "Transfer & Liquidity"]', style: { 'background-color': '#C7A189', 'color': '#000000', 'border-color': '#C7A189', 'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif', 'text-opacity': 0.95 } },
        { selector: 'node[type = "category"][bucket = "Information & Oversight"]', style: { 'background-color': '#7FB7B1', 'color': '#000000', 'border-color': '#7FB7B1', 'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif', 'text-opacity': 0.95 } },
        { selector: 'node[type = "category"][bucket = "Founder/Team Matters"]', style: { 'background-color': '#C5A677', 'color': '#000000', 'border-color': '#C5A677', 'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif', 'text-opacity': 0.95 } },
        { selector: 'node[type = "category"][bucket = "Deal Process & Closing"]', style: { 'background-color': '#A8B2BC', 'color': '#000000', 'border-color': '#A8B2BC', 'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif', 'text-opacity': 0.95 } },
        { selector: 'node[type = "category"][bucket = "Legal Boilerplate"]', style: { 'background-color': '#C0B7B0', 'color': '#000000', 'border-color': '#C0B7B0', 'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif', 'text-opacity': 0.95 } },
        { selector: 'node[type = "category"][bucket = "Company/Structure"]', style: { 'background-color': '#8F8A87', 'color': '#000000', 'border-color': '#8F8A87', 'font-family': '"SN Pro", "Inter", "Helvetica Neue", Arial, sans-serif', 'text-opacity': 0.95 } },
        {
          selector: 'edge',
          style: {
            'width': 1.2,
            'line-color': '#b3bec8',
            'target-arrow-color': '#b3bec8',
            'target-arrow-shape': 'vee',
            'curve-style': 'bezier',
            'opacity': 0.95
          }
        },
        {
          selector: 'edge[edgeType = "doc-cat"]',
          style: {
            'width': 'mapData(weight, 1, 20, 3, 7)',
            'line-color': '#111111',
            'target-arrow-color': '#111111',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            'opacity': 1.0
          }
        },
        // Bucket tint on edges
        { selector: 'edge[bucket = "Economics"]', style: { 'line-color': '#4C5BD580', 'target-arrow-color': '#4C5BD580' } },
        { selector: 'edge[bucket = "Ownership & Dilution"]', style: { 'line-color': '#7C3AED80', 'target-arrow-color': '#7C3AED80' } },
        { selector: 'edge[bucket = "Control & Governance"]', style: { 'line-color': '#3AA6A080', 'target-arrow-color': '#3AA6A080' } },
        { selector: 'edge[bucket = "Transfer & Liquidity"]', style: { 'line-color': '#E76F5180', 'target-arrow-color': '#E76F5180' } },
        { selector: 'edge[bucket = "Information & Oversight"]', style: { 'line-color': '#2A9D8F80', 'target-arrow-color': '#2A9D8F80' } },
        { selector: 'edge[bucket = "Founder/Team Matters"]', style: { 'line-color': '#F4A26180', 'target-arrow-color': '#F4A26180' } },
        { selector: 'edge[bucket = "Deal Process & Closing"]', style: { 'line-color': '#9AA3AF80', 'target-arrow-color': '#9AA3AF80' } },
        { selector: 'edge[bucket = "Legal Boilerplate"]', style: { 'line-color': '#BDBDBD80', 'target-arrow-color': '#BDBDBD80' } },
        { selector: 'edge[bucket = "Company/Structure"]', style: { 'line-color': '#6D687580', 'target-arrow-color': '#6D687580' } },
        {
          selector: 'edge[edgeType = "cat-clause"]',
          style: {
            'width': 1.8,
            'line-color': '#9ca3af',
            'target-arrow-color': '#9ca3af',
            'target-arrow-shape': 'vee',
            'arrow-scale': 0.9,
            'curve-style': 'bezier',
            'opacity': 0.95
          }
        },
        {
          selector: 'edge[edgeType = "secondary"]',
          style: {
            'width': 1.4,
            'line-color': '#6C5CE7',
            'target-arrow-color': '#6C5CE7',
            'target-arrow-shape': 'vee',
            'curve-style': 'unbundled-bezier',
            'control-point-distances': 80,
            'control-point-weights': 0.4,
            'opacity': 0.9
          }
        },
        {
          selector: 'node:selected',
          style: {
            'border-width': '3px',
            'border-color': '#111111'
          }
        },
        {
          selector: 'node:hover',
          style: {
            'border-width': '3px',
            'border-color': '#111111'
          }
        },
        {
          selector: 'edge.highlighted',
          style: {
            'width': 4,
            'line-color': '#111111',
            'target-arrow-color': '#111111',
            'opacity': 1.0
          }
        },
        {
          selector: 'node.hovered',
          style: {
            'text-outline-width': 0,
            'text-opacity': 0.95
          }
        },
        {
          selector: 'node.focus-active',
          style: {
            'border-width': '3px',
            'border-color': '#111111',
            'text-opacity': 0.95
          }
        },
        {
          selector: 'edge.focus-active',
          style: {
            'width': 3,
            'line-color': '#111111',
            'target-arrow-color': '#111111',
            'opacity': 1.0
          }
        },
        {
          selector: 'node.non-market-muted',
          style: {
            'opacity': 0.35,
            'text-opacity': 0.3
          }
        },
        {
          selector: '.focus-muted',
          style: {
            'opacity': 0.18,
            'text-opacity': 0.25
          }
        },
        {
          selector: 'edge.non-market-edge',
          style: {
            'line-color': '#D95F5F',
            'target-arrow-color': '#D95F5F',
            'width': 2.2,
            'opacity': 1.0
          }
        },
        {
          selector: '.faded',
          style: {
            'opacity': 0.15,
            'text-opacity': 0.2
          }
        },
        {
          selector: 'edge.hidden',
          style: {
            'display': 'none'
          }
        },
        {
          selector: 'node.highlighted',
          style: {
            'border-width': '3px',
            'border-color': '#111111'
          }
        }
      ],
      layout: {
        // Mesh-like force-directed layout for a relaxed cluster look
        name: 'cose',
        animate: false,
        fit: true,
        padding: 80,
        nodeRepulsion: 400000,
        idealEdgeLength: (edge: any) => {
          const t = edge.data('edgeType');
          if (t === 'doc-cat') return 160;
          if (t === 'cat-clause') return 120;
          if (t === 'secondary') return 140;
          return 120;
        },
        edgeElasticity: (edge: any) => {
          const t = edge.data('edgeType');
          if (t === 'secondary') return 80;
          return 100;
        },
        nodeOverlap: 10,
        componentSpacing: 140,
        nestingFactor: 0.9,
        gravity: 1,
        numIter: 1000,
        initialTemp: 200,
        coolingFactor: 0.95,
        minTemp: 1.0
      }
    });

    // Compute degree and normalized size for nodes
    let maxDeg = 0;
    cy.nodes().forEach((n) => {
      const deg = n.connectedEdges().length;
      n.data('degree', deg);
      if (deg > maxDeg) maxDeg = deg;
      if (deg < 2 && n.data('type') === 'clause') {
        n.addClass('lowdeg');
      }
    });
    cy.nodes().forEach((n) => {
      const d = n.data('degree') || 0;
      const sz = 10 + Math.min(1, (maxDeg ? d / maxDeg : 0)) * 14; // 10..24
      if (n.data('type') === 'clause') {
        n.data('size', sz);
      }
    });

    const captureBaseSizes = () => {
      const baseMap = baseSizeMapRef.current;
      baseMap.clear();
      cy.nodes().forEach((node: any) => {
        baseMap.set(node.id(), { width: node.width(), height: node.height() });
      });
    };

    captureBaseSizes();
    cy.on('layoutstop', captureBaseSizes);

    const resetNodeStyles = (node: any) => {
      node.removeStyle('background-color');
      node.removeStyle('color');
      node.removeStyle('text-opacity');
      node.removeStyle('opacity');
      node.removeStyle('text-outline-width');
    };

    const resetEdgeStyles = (edge: any) => {
      edge.removeStyle('width');
      edge.removeStyle('opacity');
      edge.removeStyle('line-color');
      edge.removeStyle('target-arrow-color');
    };

    const resetNodeSize = (node: any) => {
      if (!node || node.empty()) return;
      let base = baseSizeMapRef.current.get(node.id());
      if (!base) {
        base = { width: node.width(), height: node.height() };
        baseSizeMapRef.current.set(node.id(), base);
      }
      if (!base) return;
      node.stop();
      node.animate({ style: { width: base.width, height: base.height } }, { duration: 140, easing: 'ease-out' });
      window.setTimeout(() => {
        node.removeStyle('width');
        node.removeStyle('height');
      }, 160);
      node.removeClass('hovered');
    };

    const clearHoverState = () => {
      const hoveredId = hoveredNodeRef.current;
      if (hoveredId) {
        const hoveredNode = cy.getElementById(hoveredId);
        resetNodeSize(hoveredNode);
        hoveredNodeRef.current = null;
      }
      cy.elements().removeClass('highlighted');
      cy.elements().removeClass('faded');
      cy.nodes().forEach((node: any) => {
        resetNodeStyles(node);
      });
      cy.edges().forEach((edge: any) => {
        resetEdgeStyles(edge);
      });
      highlightRefreshRef.current?.();
    };

    const clampZoom = (zoom: number) => Math.min(Math.max(zoom, 0.2), 4);

    const animateFocusViewport = (elements: any, animate: boolean) => {
      const cyEl = cy;
      if (!cyEl || !elements || elements.empty()) return;
      const padding = 80;
      const bbox = elements.boundingBox();
      const container = cyEl.container();
      const width = container?.clientWidth || 1;
      const height = container?.clientHeight || 1;
      const scaleX = width / (bbox.w + padding);
      const scaleY = height / (bbox.h + padding);
      const targetZoom = clampZoom(Math.max(Math.min(scaleX, scaleY), 1.08));
      const center = { x: bbox.x1 + bbox.w / 2, y: bbox.y1 + bbox.h / 2 };

      const animationOptions = animate
        ? { duration: 500, easing: 'ease-in-out' as const }
        : { duration: 0 };

      cyEl.animate(
        {
          center: { eles: elements },
          zoom: targetZoom,
          pan: {
            x: width / 2 - targetZoom * center.x,
            y: height / 2 - targetZoom * center.y,
          },
        },
        animationOptions
      );
    };

    const applyPersistentFocus = (
      node: any,
      options: { animate?: boolean; preserveZoom?: boolean } = {}
    ) => {
      if (!node || node.empty()) return;
      const { animate = true, preserveZoom = false } = options;

      clearHoverState();

      if (selectedNodeRef.current && selectedNodeRef.current !== node.id()) {
        const previous = cy.getElementById(selectedNodeRef.current);
        resetNodeSize(previous);
        if (previous && previous.length) {
          resetNodeStyles(previous);
        }
      }

      selectedNodeRef.current = node.id();
      const hood = node.closedNeighborhood().add(node);

      cy.elements().removeClass('focus-active');
      cy.elements().removeClass('focus-muted');
      cy.nodes().addClass('focus-muted');
      cy.edges().addClass('focus-muted');

      hood.removeClass('focus-muted');
      hood.nodes().addClass('focus-active');
      hood.edges().addClass('focus-active');

      hood.nodes().forEach((hoodNode: any) => {
        hoodNode.removeClass('hovered');
        hoodNode.style('opacity', 1);
        hoodNode.style('text-opacity', 0.95);
        const type = hoodNode.data('type');
        if (type === 'document') {
          hoodNode.style('background-color', '#1f4ed8');
          hoodNode.style('color', '#000000');
        } else if (type === 'category') {
          const bucket = hoodNode.data('bucket');
          const color = CATEGORY_COLORS[bucket as string] || '#A8B2BC';
          hoodNode.style('background-color', color);
          hoodNode.style('color', '#000000');
        } else {
          hoodNode.style('background-color', hoodNode.id() === node.id() ? C.nodeFillActive : C.nodeFillConnected);
          hoodNode.style('color', C.label);
        }
      });

      hood.edges().forEach((edge: any) => {
        edge.removeClass('focus-muted');
        edge.style('opacity', 1);
      });

      let base = baseSizeMapRef.current.get(node.id());
      if (!base) {
        base = { width: node.width(), height: node.height() };
        baseSizeMapRef.current.set(node.id(), base);
      }
      if (!base) return;
      const targetWidth = base.width * 1.08;
      const targetHeight = base.height * 1.08;
      node.stop();
      if (animate) {
        node.animate({ style: { width: targetWidth, height: targetHeight } }, { duration: 200, easing: 'ease-out' });
      } else {
        node.style('width', targetWidth);
        node.style('height', targetHeight);
      }

      if (!preserveZoom) {
        animateFocusViewport(hood, animate);
      }

      highlightRefreshRef.current?.();
    };

    const clearPersistentFocus = () => {
      if (!selectedNodeRef.current) return;
      const previous = cy.getElementById(selectedNodeRef.current);
      resetNodeSize(previous);
      selectedNodeRef.current = null;
      hoveredNodeRef.current = null;
      cy.elements().removeClass('focus-active');
      cy.elements().removeClass('focus-muted');
      cy.elements().removeClass('highlighted');
      cy.elements().removeClass('faded');
      cy.nodes().forEach((node: any) => {
        resetNodeStyles(node);
      });
      cy.edges().forEach((edge: any) => {
        resetEdgeStyles(edge);
      });
      highlightRefreshRef.current?.();
    };

    maintainSelectionRef.current = () => {
      if (!selectedNodeRef.current) return;
      const currentNode = cy.getElementById(selectedNodeRef.current);
      if (currentNode && currentNode.length) {
        applyPersistentFocus(currentNode, { animate: false, preserveZoom: true });
      }
    };

    // Handle node clicks with persistent focus
    cy.on('tap', 'node', (event: any) => {
      const node = event.target;
      applyPersistentFocus(node);
      const type = node.data('type');
      if (type === 'clause') {
        const clauseId = node.data('clauseId');
        try {
          document.dispatchEvent(new CustomEvent('ui:showChat'));
        } catch {}
        if (clauseId && onSelectClause) {
          onSelectClause(clauseId);
        }
      }
    });

    cy.on('tap', (event: any) => {
      if (event.target === cy) {
        clearPersistentFocus();
      }
    });

    // Hover focus: fade others, emphasize neighborhood with magnification
    cy.on('mouseover', 'node', (e: any) => {
      if (selectedNodeRef.current) return;
      const n = e.target;
      hoveredNodeRef.current = n.id();
      n.addClass('hovered');
      const hood = n.closedNeighborhood().add(n);
      cy.elements().addClass('faded');
      hood.removeClass('faded');
      hood.addClass('highlighted');
      hood.nodes().forEach((node: any) => {
        node.style('text-opacity', 0.95);
        const type = node.data('type');
        if (type === 'document') {
          node.style('background-color', '#1f4ed8');
          node.style('color', '#000000');
        } else if (type === 'category') {
          const bucket = node.data('bucket');
          const color = CATEGORY_COLORS[bucket as string] || '#A8B2BC';
          node.style('background-color', color);
          node.style('color', '#000000');
        } else {
          node.style('color', C.label);
          node.style('background-color', node.id() === n.id() ? C.nodeFillActive : C.nodeFillConnected);
        }
      });
      hood.edges().forEach((edge: any) => {
        edge.style('width', 2.5);
        edge.style('opacity', 0.8);
      });

      const base = baseSizeMapRef.current.get(n.id());
      if (base) {
        n.stop();
        n.animate({ style: { width: base.width * 1.08, height: base.height * 1.08 } }, { duration: 160, easing: 'ease-out' });
      }
    });

    cy.on('mouseout', 'node', () => {
      if (selectedNodeRef.current) return;
      clearHoverState();
    });

    // Zoom-aware decluttering: shrink fonts, dim second-order edges, hide very low-degree at far zoom
    cy.on('zoom', () => {
      const z = cy.zoom();
      const fontClause = z < 0.9 ? 8 : 10;
      const fontCategory = z < 0.9 ? 10 : 11;
      cy.nodes('[type = "clause"]').style('font-size', fontClause);
      // Keep document/category labels always visible; adjust clause labels only
      cy.nodes('[type = "category"]').style('font-size', fontCategory);
      cy.nodes('[type = "clause"]').style('text-opacity', z > 0.9 ? 0.85 : 0.0);
      cy.edges('[edgeType = "secondary"]').style('opacity', z < 0.8 ? 0.6 : 0.9);
      const low = cy.nodes('.lowdeg');
      if (z < 0.65) {
        low.style('display', 'none');
      } else {
        low.style('display', 'element');
      }
    });

    cyRef.current = cy;

    // Cleanup function
    return () => {
      if (cyRef.current) {
        try { cyRef.current.destroy(); } catch {}
      }
    };
  }, [graphJson, onSelectClause]);

  useEffect(() => {
    if (breathingStyleElRef.current) return;
    const styleEl = document.createElement('style');
    styleEl.id = 'graph-viewer-breathing-style';
    styleEl.textContent = `
      @keyframes graph-viewer-breath {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.02); }
      }
      .graph-breathing {
        animation: graph-viewer-breath 9s ease-in-out infinite;
        transform-origin: center;
      }
    `;
    document.head.appendChild(styleEl);
    breathingStyleElRef.current = styleEl;
    return () => {
      if (breathingStyleElRef.current?.parentNode) {
        breathingStyleElRef.current.parentNode.removeChild(breathingStyleElRef.current);
        breathingStyleElRef.current = null;
      }
    };
  }, []);

  // Toggle: Highlight non‑market (fade market/unknown)
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    const normalizeToken = (value: any) => {
      if (typeof value !== 'string') return '';
      return value.trim().toLowerCase().replace(/[\s-]+/g, '_');
    };
    const normalizeTilt = (value: any) => normalizeToken(value);
    const isCategoryClauseEdge = (edge: any) => {
      if (!edge || typeof edge.connectedNodes !== 'function') return false;
      const srcType = edge.source()?.data?.('type');
      const tgtType = edge.target()?.data?.('type');
      return (srcType === 'category' && tgtType === 'clause') || (srcType === 'clause' && tgtType === 'category');
    };

    const applyHighlight = (emitSummary = false) => {
      const clauseNodes = cy.nodes('[type = "clause"]');
      const catEdges = cy.edges().filter(isCategoryClauseEdge);

      clauseNodes.removeClass('non-market-muted');
      catEdges.forEach((edge: any) => {
        edge.removeClass('non-market-edge');
        edge.removeStyle('line-color');
        edge.removeStyle('target-arrow-color');
        edge.removeStyle('width');
        edge.removeStyle('opacity');
      });

      if (!highlightNonMarket) return;

      const investorClauses: Array<{ clauseId?: string; label: string; bucket?: string }> = [];

      clauseNodes.forEach((clauseNode: any) => {
        const tilt = normalizeTilt(clauseNode.data('tilt'));
        if (tilt === 'market' || tilt === 'unknown') {
          clauseNode.addClass('non-market-muted');
        }
        if (tilt === 'investor_friendly' || tilt === 'investor-friendly') {
          investorClauses.push({
            clauseId: clauseNode.data('clauseId') ?? clauseNode.id(),
            label: clauseNode.data('label') || clauseNode.id(),
            bucket: clauseNode.data('bucket'),
          });
          clauseNode
            .connectedEdges()
            .forEach((edge: any) => {
              if (!isCategoryClauseEdge(edge)) return;
              edge.addClass('non-market-edge');
              edge.style('line-color', '#D95F5F');
              edge.style('target-arrow-color', '#D95F5F');
              edge.style('width', 2.2);
              edge.style('opacity', 1.0);
            });
        }
      });

      // Ensure focused node retains highlight when filter is active
      if (selectedNodeRef.current) {
        const currentNode = cy.getElementById(selectedNodeRef.current);
        if (currentNode && currentNode.length) {
          const hood = currentNode.closedNeighborhood().add(currentNode);
          cy.elements().removeClass('focus-muted');
          cy.elements().removeClass('focus-active');
          cy.nodes().addClass('focus-muted');
          cy.edges().addClass('focus-muted');
          hood.removeClass('focus-muted');
          hood.nodes().addClass('focus-active');
          hood.edges().addClass('focus-active');
        }
      }

      if (emitSummary) {
        const uniqueClauses = Array.from(
          investorClauses.reduce((map, clause) => {
            const key = clause.clauseId || clause.label;
            if (!map.has(key)) {
              map.set(key, clause);
            }
            return map;
          }, new Map<string, { clauseId?: string; label: string; bucket?: string }>())
        ).map(([, clause]) => clause);

        const summary = uniqueClauses.length
          ? `Investor-leaning clauses highlighted:\n${uniqueClauses
              .map((clause) => {
                const bucket = clause.bucket ? ` (${clause.bucket})` : '';
                return `• ${clause.label}${bucket}`;
              })
              .join('\n')}`
          : 'No investor-leaning clauses were highlighted.';

        enqueueAssistantMessage(summary);
      }
    };

    highlightRefreshRef.current = () => applyHighlight(false);
    applyHighlight(highlightNonMarket);
    maintainSelectionRef.current?.();
  }, [highlightNonMarket]);

  useEffect(() => {
    const handler = () => {
      const cy = cyRef.current;
      if (!cy) return;
      try {
        cy.resize();
        cy.fit(cy.elements(), 100);
      } catch {}
      maintainSelectionRef.current?.();
    };
    window.addEventListener('resize', handler);
    document.addEventListener('ui:layoutChanged', handler as EventListener);
    return () => {
      window.removeEventListener('resize', handler);
      document.removeEventListener('ui:layoutChanged', handler as EventListener);
    };
  }, []);

  if (!graphJson?.nodes || graphJson.nodes.length === 0) {
    return <div className="p-4 text-sm text-[color:var(--ink-500)]">No graph yet.</div>;
  }

  return (
    <div className="h-full w-full relative" style={{ background: '#F9F6F0' }}>
      {/* Controls */}
      <div className="absolute top-2 left-2 z-20 bg-white/90 border border-gray-200 rounded px-2 py-1 text-xs flex items-center" style={{ backdropFilter: 'saturate(150%) blur(2px)' }}>
        <label className="flex items-center gap-1 cursor-pointer">
          <input
            type="checkbox"
            checked={highlightNonMarket}
            onChange={(e) => setHighlightNonMarket(e.target.checked)}
          />
          <span style={{ color: '#6B6460' }}>Highlight non‑market</span>
        </label>
      </div>
    <div ref={containerRef} className="h-full w-full graph-breathing" />
    </div>
  );
}
