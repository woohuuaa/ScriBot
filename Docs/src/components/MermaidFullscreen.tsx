'use client';
import React, { useEffect, memo } from 'react';
import { createPortal } from 'react-dom';

interface MermaidFullscreenProps {
  isFullscreen: boolean;
  fullscreenPosition: { x: number; y: number };
  scale: number;
  isDragging: boolean;
  innerHTML: string;
  theme: 'light' | 'dark';
  onMouseDown: (event: React.MouseEvent<HTMLDivElement>) => void;
  onMouseLeave: () => void;
  onFitToView: () => void;
  onCloseFullscreen: () => void;
  fullscreenInteractiveRef: React.RefObject<HTMLDivElement | null>;
}

// Theme-aware style functions
const getFullscreenOverlayStyle = (theme: 'light' | 'dark') => ({
  position: 'fixed' as const,
  top: 0,
  left: 0,
  right: 0,
  bottom: 0,
  zIndex: 100,
  order: 3,
  backgroundColor:
    theme === 'dark' ? 'rgba(0, 0, 0, 0.85)' : 'rgba(0, 0, 0, 0.2)',
  backdropFilter: 'blur(8px)',
});

const getControlButtonStyle = (theme: 'light' | 'dark') => ({
  borderRadius: 8,
  padding: 12,
  border: `1px solid ${
    theme === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)'
  }`,
  backgroundColor:
    theme === 'dark' ? 'rgba(0,0,0,0.95)' : 'rgba(255,255,255,0.95)',
  color: theme === 'dark' ? 'white' : 'black',
  cursor: 'pointer',
  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
  transition: 'all 0.2s ease',
});

const getZoomIndicatorStyle = (theme: 'light' | 'dark') => ({
  position: 'absolute' as const,
  top: 16,
  left: 16,
  zIndex: 100,
  borderRadius: 8,
  padding: '8px 12px',
  border: `1px solid ${
    theme === 'dark' ? 'rgba(255,255,255,0.2)' : 'rgba(0,0,0,0.2)'
  }`,
  backgroundColor:
    theme === 'dark' ? 'rgba(0,0,0,0.95)' : 'rgba(255,255,255,0.95)',
  color: theme === 'dark' ? 'white' : 'black',
  fontSize: '0.875rem',
  fontWeight: 500,
  boxShadow: '0 4px 12px rgba(0,0,0,0.15)',
});

const getChartContainerStyle = (
  theme: 'light' | 'dark',
  isDragging: boolean
) => ({
  width: '100%',
  height: '100%',
  overflow: 'hidden',
  cursor: isDragging ? 'grabbing' : 'grab',
  background:
    theme === 'dark'
      ? 'linear-gradient(to bottom right, rgba(0,0,0,0.05), rgba(0,0,0,0.1))'
      : 'linear-gradient(to bottom right, rgba(255,255,255,0.05), rgba(255,255,255,0.1))',
  touchAction: 'none' as const,
});

const ChartFullscreenControls = memo(function ChartFullscreenControls({
  onFitToView,
  onCloseFullscreen,
  scale,
  theme,
}: {
  onFitToView: () => void;
  onCloseFullscreen: () => void;
  scale: number;
  theme: 'light' | 'dark';
}) {
  // React Compiler will optimize this computation
  const scaleDisplay = Math.round(scale * 100);

  return (
    <>
      {/* Enhanced Control Panel */}
      <div
        style={{
          position: 'absolute',
          top: 16,
          right: 16,
          zIndex: 9999,
          display: 'flex',
          gap: 8,
        }}
      >
        {/* Refit button */}
        <button
          onClick={onFitToView}
          style={getControlButtonStyle(theme)}
          title="Passend maken (0)"
          aria-label="Diagram passend maken"
        >
          <svg
            width={16}
            height={16}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path d="M1 4v6h6" />
            <path d="M23 20v-6h-6" />
            <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15" />
          </svg>
        </button>

        {/* Close button */}
        <button
          onClick={onCloseFullscreen}
          style={getControlButtonStyle(theme)}
          title="Verlaat fullscreen (Esc)"
          aria-label="Verlaat fullscreen"
        >
          <svg
            width={16}
            height={16}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2 0 0 1-2-2V3m0 18v-3a2 2 0 0 0 2-2h3M3 16h3a2 2 0 0 0 2 2v3" />
          </svg>
        </button>
      </div>

      {/* Enhanced Zoom Indicator */}
      <div style={getZoomIndicatorStyle(theme)}>
        <span
          style={{
            color:
              theme === 'dark' ? 'rgba(255,255,255,0.7)' : 'rgba(0,0,0,0.7)',
          }}
        >
          Zoom:
        </span>
        <span
          style={{
            color: theme === 'dark' ? 'white' : 'black',
            marginLeft: 4,
          }}
        >
          {scaleDisplay}%
        </span>
      </div>
    </>
  );
});

export const MermaidFullscreen = memo(function MermaidFullscreen({
  isFullscreen,
  fullscreenPosition,
  scale,
  isDragging,
  innerHTML,
  theme,
  onMouseDown,
  onMouseLeave,
  onFitToView,
  onCloseFullscreen,
  fullscreenInteractiveRef,
}: MermaidFullscreenProps) {
  if (!isFullscreen) return null;

  // Prevent background scrolling when modal is open
  useEffect(() => {
    if (isFullscreen) {
      document.body.style.overflow = 'hidden';
      return () => {
        document.body.style.overflow = '';
      };
    }
  }, [isFullscreen]);

  // Handle backdrop click to close
  const handleBackdropClick = (e: React.MouseEvent) => {
    if (e.target === e.currentTarget) {
      onCloseFullscreen();
    }
  };

  return createPortal(
    <div
      style={getFullscreenOverlayStyle(theme)}
      onClick={handleBackdropClick}
      role="dialog"
      aria-modal="true"
      aria-labelledby="fullscreen-chart-title"
      aria-describedby="fullscreen-chart-description"
    >
      {/* Hidden title for accessibility */}
      <h2
        id="fullscreen-chart-title"
        style={{
          position: 'absolute',
          left: '-10000px',
          top: 'auto',
          width: '1px',
          height: '1px',
          overflow: 'hidden',
        }}
      >
        Mermaid Diagram - Fullscreen View
      </h2>

      <div
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <ChartFullscreenControls
          onFitToView={onFitToView}
          onCloseFullscreen={onCloseFullscreen}
          scale={scale}
          theme={theme}
        />

        {/* Fullscreen chart container */}
        <div
          ref={fullscreenInteractiveRef}
          style={getChartContainerStyle(theme, isDragging)}
          onMouseDown={onMouseDown}
          onMouseLeave={onMouseLeave}
          role="img"
          aria-label="Volledig scherm Mermaid diagram"
          tabIndex={0}
          id="fullscreen-chart-description"
        >
          <div
            style={{
              transform: `translate(${fullscreenPosition.x}px, ${fullscreenPosition.y}px) scale(${scale})`,
              transformOrigin: 'center',
              transition: isDragging
                ? 'none'
                : 'transform 0.2s cubic-bezier(0.4, 0, 0.2, 1)',
              touchAction: 'none',
              width: '100%',
              height: '100%',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              pointerEvents: 'none', // Make this non-interactive so touch events go to parent
              filter: 'drop-shadow(0 4px 12px rgba(0,0,0,0.15))',
              userSelect: 'none',
            }}
            dangerouslySetInnerHTML={{ __html: innerHTML }}
          />
        </div>
      </div>
    </div>,
    document.body
  );
});
