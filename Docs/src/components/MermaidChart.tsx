'use client';
import React, { useRef, useState, useCallback, memo } from 'react';
import { CopyButton } from './CopyButton';
import { MultiLineCodeBlock } from './CodeBlock';
import { MermaidRenderer } from './MermaidRenderer';
import { useMermaidInteractions } from './MermaidInteractions';
import { useTheme } from '../hooks/useTheme';
import { MermaidKeyboard } from './MermaidKeyboard';
import { MermaidTouch } from './MermaidTouch';
import { MermaidPositioning } from './MermaidPositioning';
import { MermaidFullscreen } from './MermaidFullscreen';

// Local lightweight icons (keeps Docs free of extra icon deps)
const RotateCcwIcon = memo(function RotateCcwIcon(
  props: React.SVGProps<SVGSVGElement>
) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M1 4v6h6" />
      <path d="M3.51 15a9 9 0 1 0 .13-6.71L1 10" />
    </svg>
  );
});

const CodeIcon = memo(function CodeIcon(props: React.SVGProps<SVGSVGElement>) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <polyline points="16 18 22 12 16 6" />
      <polyline points="8 6 2 12 8 18" />
    </svg>
  );
});

const ExpandIcon = memo(function ExpandIcon(
  props: React.SVGProps<SVGSVGElement>
) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth={2}
      strokeLinecap="round"
      strokeLinejoin="round"
      {...props}
    >
      <path d="M15 3h6v6" />
      <path d="M9 21H3v-6" />
      <path d="M21 3l-8 8" />
      <path d="M3 21l8-8" />
    </svg>
  );
});

interface Props {
  chartDefinition: string;
}

// Theme-aware style functions
const getContainerStyle = (theme: 'light' | 'dark') => ({
  position: 'relative' as const,
  width: '100%',
  minWidth: 220,
  order: 3,
  zIndex: 50,
  height: 400,
  overflow: 'hidden',
  borderRadius: 10,
  border: '1px solid rgba(0,0,0,0.06)',
  //   backgroundColor: theme === "dark" ? "rgba(0,0,0,0.3)" : "rgba(250,250,250,0.5)",
});

const getControlPanelStyle = (theme: 'light' | 'dark') => ({
  position: 'absolute' as const,
  top: 8,
  right: 8,
  zIndex: 10,
  display: 'flex',
  gap: 6,
  borderRadius: 6,
  padding: 6,
  backgroundColor:
    theme === 'dark' ? 'rgba(0,0,0,0.9)' : 'rgba(255,255,255,0.9)',
  boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  alignItems: 'center' as const,
});

const getButtonStyle = (theme: 'light' | 'dark', isActive = false) => ({
  borderRadius: 6,
  padding: 6,
  border: 'none',
  background: isActive
    ? theme === 'dark'
      ? 'rgba(255,255,255,0.1)'
      : 'rgba(0,0,0,0.06)'
    : 'transparent',
  cursor: 'pointer',
  color: theme === 'dark' ? 'white' : 'black',
});

const getErrorContainerStyle = (theme: 'light' | 'dark') => ({
  position: 'absolute' as const,
  inset: 0,
  backgroundColor:
    theme === 'dark' ? 'rgba(0,0,0,0.6)' : 'rgba(255,255,255,0.6)',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
});

const getErrorBoxStyle = (theme: 'light' | 'dark') => ({
  backgroundColor:
    theme === 'dark' ? 'rgba(239,68,68,0.1)' : 'rgba(255,0,0,0.05)',
  border:
    theme === 'dark'
      ? '1px solid rgba(239,68,68,0.3)'
      : '1px solid rgba(255,0,0,0.2)',
  borderRadius: 8,
  padding: 16,
  boxShadow: '0 4px 12px rgba(0,0,0,0.08)',
});

const getErrorTextStyle = (theme: 'light' | 'dark') => ({
  color: theme === 'dark' ? '#fca5a5' : '#b91c1c',
  width: '100%',
  maxWidth: 360,
  textAlign: 'center' as const,
  fontSize: '0.875rem',
});

function ChartCopyButton({ text }: { text: string }) {
  return (
    <div style={{ position: 'absolute', top: 8, left: 8, zIndex: 10 }}>
      <CopyButton text={text} />
    </div>
  );
}

const ChartControlPanel = memo(function ChartControlPanel({
  onFitToView,
  scale,
  onToggleFullscreen,
  onToggleCode,
  showCode,
  theme,
}: {
  onFitToView: () => void;
  scale: number;
  onToggleFullscreen: () => void;
  onToggleCode: () => void;
  showCode: boolean;
  theme: 'light' | 'dark';
}) {
  const scaleDisplay = Math.round(scale * 100);

  return (
    <div style={getControlPanelStyle(theme)}>
      <button
        onClick={onFitToView}
        title="Passend maken (0)"
        aria-label="Zoom aanpassen (0)"
        style={getButtonStyle(theme)}
      >
        <RotateCcwIcon width={12} height={12} />
      </button>

      <span style={{ fontSize: '0.875rem' }}>{scaleDisplay}%</span>

      <button
        onClick={onToggleCode}
        title="Code tonen/verbergen (C)"
        aria-label="Code tonen/verbergen (C)"
        style={getButtonStyle(theme, showCode)}
      >
        <CodeIcon width={12} height={12} />
      </button>

      <button
        onClick={onToggleFullscreen}
        title="Volledig scherm (F)"
        aria-label="Volledig scherm (F)"
        style={getButtonStyle(theme)}
      >
        <ExpandIcon width={12} height={12} />
      </button>
    </div>
  );
});

export function MermaidChart({ chartDefinition }: Props) {
  const theme = useTheme();

  // Component state - React Compiler will optimize state updates
  const [innerHTML, setInnerHTML] = useState('');
  const [position, setPosition] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);
  const [isDragging, setIsDragging] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isManuallyPositioned, setIsManuallyPositioned] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [fullscreenPosition, setFullscreenPosition] = useState({ x: 0, y: 0 });
  const [showCode, setShowCode] = useState(false);

  // Refs for DOM elements and stable references
  const containerRef = useRef<HTMLDivElement>(null);
  const interactiveRef = useRef<HTMLDivElement>(null);
  const fullscreenInteractiveRef = useRef<HTMLDivElement>(null);
  const refPre = useRef<HTMLDivElement>(null);

  // Action handlers - React Compiler will optimize these, but we use useCallback to prevent re-renders
  const handlePositionChange = useCallback(
    (newPosition: { x: number; y: number }, isFullscreenMode: boolean) => {
      if (isFullscreenMode) {
        setFullscreenPosition(newPosition);
      } else {
        setPosition(newPosition);
      }
    },
    []
  );

  const handleScaleChange = useCallback((newScale: number) => {
    setScale(newScale);
  }, []);

  const handleDragStart = useCallback(() => {
    setIsDragging(true);
  }, []);

  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
  }, []);

  const handleManualPositioning = useCallback(() => {
    setIsManuallyPositioned(true);
  }, []);

  const handlePositionReset = useCallback(() => {
    setScale(1);
    setPosition({ x: 0, y: 0 });
    setFullscreenPosition({ x: 0, y: 0 });
    setIsManuallyPositioned(false);
  }, []);

  const toggleFullscreen = useCallback(() => {
    setIsFullscreen(prev => !prev);
  }, []);

  const closeFullscreen = useCallback(() => {
    setIsFullscreen(false);
  }, []);

  const toggleCode = useCallback(() => {
    setShowCode(prev => !prev);
  }, []);

  const fitToView = useCallback(() => {
    handlePositionReset();
  }, [handlePositionReset]);

  // Chart rendering handlers
  const handleRenderComplete = useCallback(
    (html: string) => {
      setInnerHTML(html);
      if (refPre.current) {
        refPre.current.innerHTML = html;
      }
      setIsLoading(false);
      setError(null);

      // Reset positioning after successful render
      requestAnimationFrame(() => {
        handlePositionReset();
      });
    },
    [handlePositionReset]
  );

  const handleRenderError = useCallback((errorMessage: string) => {
    setError(errorMessage);
    setIsLoading(false);
  }, []);

  const handleLoadingChange = useCallback((loading: boolean) => {
    setIsLoading(loading);
  }, []);

  // Get interaction handlers
  const interactions = useMermaidInteractions({
    containerRef: interactiveRef,
    fullscreenContainerRef: fullscreenInteractiveRef,
    isDragging,
    isFullscreen,
    position,
    fullscreenPosition,
    scale,
    onPositionChange: handlePositionChange,
    onScaleChange: handleScaleChange,
    onDragStart: handleDragStart,
    onDragEnd: handleDragEnd,
    onManualPositioning: handleManualPositioning,
  });

  return (
    <div ref={containerRef} style={getContainerStyle(theme)}>
      {/* Show mermaid code while chart is loading */}
      {innerHTML.length < 1 && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            overflow: 'auto',
            padding: 16,
          }}
        >
          <MultiLineCodeBlock language="mermaid" text={chartDefinition} />
        </div>
      )}

      {/* Render chart logic */}
      <MermaidRenderer
        chartDefinition={chartDefinition}
        theme={theme}
        onRenderComplete={handleRenderComplete}
        onError={handleRenderError}
        onLoadingChange={handleLoadingChange}
      />
      {/* Interaction handlers */}
      <MermaidKeyboard
        isFullscreen={isFullscreen}
        containerRef={containerRef}
        onToggleFullscreen={toggleFullscreen}
        onFitToView={fitToView}
        onCloseFullscreen={closeFullscreen}
      />
      <MermaidTouch
        containerRef={interactiveRef}
        fullscreenInteractiveRef={fullscreenInteractiveRef}
        isFullscreen={isFullscreen}
        isDragging={isDragging}
        position={position}
        fullscreenPosition={fullscreenPosition}
        scale={scale}
        onPositionChange={handlePositionChange}
        onScaleChange={handleScaleChange}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onManualPositioning={handleManualPositioning}
      />
      <MermaidPositioning
        isFullscreen={isFullscreen}
        isManuallyPositioned={isManuallyPositioned}
        isDragging={isDragging}
        onPositionReset={handlePositionReset}
      />
      {/* UI Components */}
      <ChartCopyButton text={chartDefinition} />
      <ChartControlPanel
        onFitToView={fitToView}
        scale={scale}
        onToggleFullscreen={toggleFullscreen}
        onToggleCode={toggleCode}
        showCode={showCode}
        theme={theme}
      />
      {/* Error State */}
      {error && !isLoading && innerHTML.length < 1 && (
        <div style={getErrorContainerStyle(theme)}>
          <div style={getErrorBoxStyle(theme)}>
            <p style={getErrorTextStyle(theme)}>{error}</p>
          </div>
        </div>
      )}
      {/* Code Display */}
      {showCode && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            marginTop: 48,
            overflow: 'auto',
            paddingBottom: 8,
          }}
        >
          <div>
            <MultiLineCodeBlock language="mermaid" text={chartDefinition} />
          </div>
        </div>
      )}

      <div
        ref={interactiveRef}
        style={{
          position: 'absolute',
          inset: 0,
          overflow: 'hidden',
          cursor: isDragging ? 'grabbing' : 'grab',
          display: showCode ? 'none' : 'block',
        }}
        onMouseDown={interactions.handleMouseDown}
        onMouseLeave={interactions.handleMouseLeave}
        role="img"
        aria-label="Interactief Mermaid diagram"
        tabIndex={0}
      >
        <div
          ref={refPre}
          style={{
            transform: `translate(${position.x}px, ${position.y}px) scale(${scale})`,
            transformOrigin: 'center',
            transition: isDragging ? 'none' : 'transform 0.1s ease-out',
            touchAction: 'none',
            width: '100%',
            height: '100%',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
            userSelect: 'none',
          }}
        >
          <svg />
        </div>
      </div>
      {/* Fullscreen Modal */}
      <MermaidFullscreen
        key={isFullscreen ? 'fullscreen' : 'normal'}
        isFullscreen={isFullscreen}
        fullscreenPosition={fullscreenPosition}
        scale={scale}
        isDragging={isDragging}
        innerHTML={innerHTML}
        theme={theme}
        onMouseDown={interactions.handleMouseDown}
        onMouseLeave={interactions.handleMouseLeave}
        onFitToView={fitToView}
        onCloseFullscreen={closeFullscreen}
        fullscreenInteractiveRef={fullscreenInteractiveRef}
      />
    </div>
  );
}
