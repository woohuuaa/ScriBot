'use client';
import { useRef, useEffect, useCallback, memo } from 'react';
import mermaid, { type MermaidConfig } from 'mermaid';
interface MermaidRendererProps {
  chartDefinition: string;
  theme?: 'light' | 'dark';
  onRenderComplete?: (html: string) => void;
  onError?: (error: string) => void;
  onLoadingChange?: (isLoading: boolean) => void;
}

export const MermaidRenderer = memo(function MermaidRenderer({
  chartDefinition,
  theme,
  onRenderComplete,
  onError,
  onLoadingChange,
}: MermaidRendererProps) {
  const idRef = useRef(
    `mermaid-${Math.random().toString(36).substring(2, 15)}`
  );
  console.log('MermaidRenderer initialized with id:', idRef.current);

  // Stable chart rendering function with lazy loading
  const renderChart = useCallback(async () => {
    setTimeout(async () => {
      try {
        // Lazy import mermaid only when needed

        const config: MermaidConfig = {
          startOnLoad: false,
          theme: theme === 'dark' ? 'dark' : 'null',
          // themeVariables: {
          //   primaryColor: theme === "dark" ? "#3b82f6" : "#2563eb",
          // },
          securityLevel: 'strict' as const,
          fontFamily: 'Geist Mono, monospace',
        };

        mermaid.initialize(config);
        const { svg } = await mermaid.render(
          idRef.current,
          chartDefinition.replaceAll('\\n', '')
        );

        // Parse and enhance the SVG for better responsive behavior
        const parser = new DOMParser();
        const svgDoc = parser.parseFromString(svg, 'image/svg+xml');
        const svgElement = svgDoc.querySelector('svg');

        if (svgElement) {
          // Preserve original dimensions in viewBox if not already present
          if (!svgElement.getAttribute('viewBox')) {
            const originalWidth = svgElement.getAttribute('width') || '800';
            const originalHeight = svgElement.getAttribute('height') || '600';
            svgElement.setAttribute(
              'viewBox',
              `0 0 ${parseFloat(originalWidth)} ${parseFloat(originalHeight)}`
            );
          }

          // Make SVG responsive with proper aspect ratio preservation
          svgElement.setAttribute('width', '100%');
          svgElement.setAttribute('height', '100%');
          svgElement.setAttribute('preserveAspectRatio', 'xMidYMid meet');

          // Set CSS to center and contain within parent with padding
          svgElement.setAttribute(
            'style',
            `
               max-width: calc(100% - 20px);
               max-height: calc(100% - 20px);
               margin: 20px;
               display: block;
             `
          );

          //  // Override node fill colors for blue backgrounds
          //  const blueColor = theme === 'dark' ? '#3b82f6' : '#2563eb';
          //  const nodeElements = svgElement.querySelectorAll('.node');
          //  nodeElements.forEach(node => {
          //    const rects = node.querySelectorAll('rect');
          //    rects.forEach(rect => {
          //      rect.setAttribute('fill', blueColor);
          //    });
          //  });

          const enhancedSvg = new XMLSerializer().serializeToString(svgElement);
          onRenderComplete?.(enhancedSvg);
          onLoadingChange?.(false);
        } else {
          onRenderComplete?.(svg);
          onLoadingChange?.(false);
        }
      } catch (e) {
        if (e instanceof Error) {
          if (!e.message.includes('firstChild')) {
            console.warn('Rendering mermaid chart:', e);
          }
        }
        // Clean up any DOM elements that mermaid might have created
        const createdElement = document.getElementById(idRef.current);
        if (createdElement) {
          createdElement.remove();
        }

        onError?.('Kan diagram niet weergeven. Controleer de diagram syntax.');
        onLoadingChange?.(false);
      }
    }, 5);
  }, [chartDefinition, theme, onRenderComplete, onError, onLoadingChange]);

  useEffect(() => {
    console.log('Rendering mermaid chart...');
    renderChart();

    // Cleanup function to remove any created DOM elements
    return () => {
      const createdElement = document.getElementById(idRef.current);
      if (createdElement) {
        createdElement.remove();
      }
    };
  }, [renderChart]);

  return <></>; // This component only handles rendering logic
});
