'use client';
import React from 'react';

interface MermaidContainerProps {
  children: React.ReactNode;
  isDragging: boolean;
  position: { x: number; y: number };
  scale: number;
  onMouseDown: (event: React.MouseEvent<HTMLDivElement>) => void;
  onMouseLeave: () => void;
  containerRef: React.RefObject<HTMLDivElement | null>;
  interactiveRef: React.RefObject<HTMLDivElement | null>;
}

export function MermaidContainer({
  children,
  isDragging,
  position,
  scale,
  onMouseDown,
  onMouseLeave,
  containerRef,
  interactiveRef,
}: MermaidContainerProps) {
  console.log('Rendering MermaidContainer');
  return (
    <div
      ref={containerRef}
      style={{
        position: 'relative',
        height: '220px',
        width: '100%',
        minWidth: '220px',
        overflow: 'hidden',
        borderRadius: '0.5rem',
        border: '1px solid var(--sl-color-border-accent)',
        backgroundColor: 'rgba(var(--sl-color-bg), 0.5)',
      }}
    >
      {children}

      {/* Chart container with proper clipping */}
      <div
        ref={interactiveRef}
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          overflow: 'hidden',
          cursor: isDragging ? 'grabbing' : 'grab',
        }}
        onMouseDown={onMouseDown}
        onMouseLeave={onMouseLeave}
        role="img"
        aria-label="Interactief Mermaid diagram"
        tabIndex={0}
      >
        <div
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
          className="mermaid"
        >
          <svg />
        </div>
      </div>
    </div>
  );
}
