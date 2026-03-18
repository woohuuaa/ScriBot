'use client';
import { useEffect, useRef } from 'react';

interface MermaidPositioningProps {
  isFullscreen: boolean;
  isManuallyPositioned: boolean;
  isDragging: boolean;
  onPositionReset: () => void;
}

export function MermaidPositioning({
  isFullscreen,
  isManuallyPositioned,
  isDragging,
  onPositionReset,
}: MermaidPositioningProps) {
  const previousFullscreen = useRef(isFullscreen);

  // Auto-center when switching modes or when not manually positioned - but not during dragging
  useEffect(() => {
    if (!isManuallyPositioned && !isDragging) {
      const timer = setTimeout(() => {
        onPositionReset();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, [isFullscreen, isManuallyPositioned, isDragging, onPositionReset]);

  // Reset positioning when entering/exiting fullscreen
  useEffect(() => {
    if (previousFullscreen.current !== isFullscreen) {
      previousFullscreen.current = isFullscreen;

      // Small delay to ensure DOM is ready
      setTimeout(() => {
        onPositionReset();
      }, 50);
    }
  }, [isFullscreen, onPositionReset]);

  return null; // This component only handles positioning logic
}
