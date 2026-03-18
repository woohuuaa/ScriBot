'use client';
import { useRef, useEffect, useCallback } from 'react';

interface UseMermaidInteractionsProps {
  containerRef: React.RefObject<HTMLDivElement | null>;
  fullscreenContainerRef?: React.RefObject<HTMLDivElement | null>;
  isDragging: boolean;
  isFullscreen: boolean;
  position: { x: number; y: number };
  fullscreenPosition: { x: number; y: number };
  scale: number;
  onPositionChange: (
    position: { x: number; y: number },
    isFullscreen: boolean
  ) => void;
  onScaleChange: (scale: number) => void;
  onDragStart: () => void;
  onDragEnd: () => void;
  onManualPositioning: () => void;
}

const MIN_SCALE = 0.1;
const MAX_SCALE = 5;

export function useMermaidInteractions({
  containerRef,
  fullscreenContainerRef,
  isDragging,
  isFullscreen,
  position,
  fullscreenPosition,
  scale,
  onPositionChange,
  onScaleChange,
  onDragStart,
  onDragEnd,
  onManualPositioning,
}: UseMermaidInteractionsProps) {
  const dragStart = useRef({ x: 0, y: 0 });
  const isDraggingRef = useRef(false);
  const isFullscreenRef = useRef(false);

  // Keep refs in sync with props
  useEffect(() => {
    isDraggingRef.current = isDragging;
    isFullscreenRef.current = isFullscreen;
  }, [isDragging, isFullscreen]);

  // Stable mouse handlers
  const handleMouseDown = useCallback(
    (event: React.MouseEvent<HTMLDivElement>) => {
      event.preventDefault();
      onDragStart();
      isDraggingRef.current = true;
      const currentPos = isFullscreen ? fullscreenPosition : position;
      dragStart.current = {
        x: event.clientX - currentPos.x,
        y: event.clientY - currentPos.y,
      };
    },
    [isFullscreen, position, fullscreenPosition, onDragStart]
  );

  const handleMouseLeave = useCallback(() => {
    if (isDraggingRef.current) {
      onDragEnd();
      isDraggingRef.current = false;
    }
  }, [onDragEnd]);

  // Global mouse events for dragging
  useEffect(() => {
    if (!isDragging) return;

    const handleMouseMove = (event: MouseEvent) => {
      const newPos = {
        x: event.clientX - dragStart.current.x,
        y: event.clientY - dragStart.current.y,
      };
      onPositionChange(newPos, isFullscreen);
    };

    const handleMouseUp = (event: MouseEvent) => {
      const finalPos = {
        x: event.clientX - dragStart.current.x,
        y: event.clientY - dragStart.current.y,
      };
      onPositionChange(finalPos, isFullscreen);
      onManualPositioning();
      onDragEnd();
      isDraggingRef.current = false;
    };

    document.addEventListener('mousemove', handleMouseMove, { passive: true });
    document.addEventListener('mouseup', handleMouseUp, { passive: true });

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [
    isDragging,
    isFullscreen,
    onPositionChange,
    onManualPositioning,
    onDragEnd,
  ]);

  // Wheel zoom for normal mode
  useEffect(() => {
    const element = containerRef.current;
    if (!element || isFullscreen) return;

    const wheelHandler = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY;
      const zoomFactor = delta > 0 ? 0.9 : 1.1;

      const newScale = Math.min(
        Math.max(scale * zoomFactor, MIN_SCALE),
        MAX_SCALE
      );
      onScaleChange(newScale);
      onManualPositioning();
    };

    element.addEventListener('wheel', wheelHandler, { passive: false });
    return () => element.removeEventListener('wheel', wheelHandler);
  }, [scale, onScaleChange, onManualPositioning, isFullscreen]);

  // Wheel zoom for fullscreen mode
  useEffect(() => {
    const element = fullscreenContainerRef?.current;
    if (!element || !isFullscreen) return;

    const wheelHandler = (e: WheelEvent) => {
      e.preventDefault();
      const delta = e.deltaY;
      const zoomFactor = delta > 0 ? 0.9 : 1.1;

      const newScale = Math.min(
        Math.max(scale * zoomFactor, MIN_SCALE),
        MAX_SCALE
      );
      onScaleChange(newScale);
      onManualPositioning();
    };

    element.addEventListener('wheel', wheelHandler, { passive: false });
    return () => element.removeEventListener('wheel', wheelHandler);
  }, [
    scale,
    onScaleChange,
    onManualPositioning,
    isFullscreen,
    fullscreenContainerRef,
  ]);

  return {
    handleMouseDown,
    handleMouseLeave,
  };
}
