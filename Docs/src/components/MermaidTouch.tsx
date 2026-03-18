'use client';
import React, { useRef, useEffect } from 'react';

interface MermaidTouchProps {
  containerRef: React.RefObject<HTMLDivElement | null>;
  fullscreenInteractiveRef: React.RefObject<HTMLDivElement | null>;
  isFullscreen: boolean;
  isDragging: boolean;
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

export function MermaidTouch({
  containerRef,
  fullscreenInteractiveRef,
  isFullscreen,
  isDragging,
  position,
  fullscreenPosition,
  scale,
  onPositionChange,
  onScaleChange,
  onDragStart,
  onDragEnd,
  onManualPositioning,
}: MermaidTouchProps) {
  const dragStart = useRef({ x: 0, y: 0 });
  const lastPinchDistance = useRef<number | null>(null);
  const isDraggingRef = useRef(false);
  const isFullscreenRef = useRef(false);
  const positionRef = useRef({ x: 0, y: 0 });
  const fullscreenPositionRef = useRef({ x: 0, y: 0 });

  // Keep refs in sync
  useEffect(() => {
    isDraggingRef.current = isDragging;
    isFullscreenRef.current = isFullscreen;
    positionRef.current = position;
    fullscreenPositionRef.current = fullscreenPosition;
  }, [isDragging, isFullscreen, position, fullscreenPosition]);

  // Touch event handling - using useCallback to prevent re-renders
  useEffect(() => {
    const element = containerRef.current;
    const fullscreenElement = fullscreenInteractiveRef.current;
    const targetElement = isFullscreen ? fullscreenElement : element;

    if (!targetElement) return;

    const handleTouchStart = function (this: HTMLElement, event: TouchEvent) {
      if (event.touches.length === 2) {
        event.preventDefault();
        const touch1 = event.touches[0];
        const touch2 = event.touches[1];
        const distance = Math.sqrt(
          Math.pow(touch1.clientX - touch2.clientX, 2) +
            Math.pow(touch1.clientY - touch2.clientY, 2)
        );
        lastPinchDistance.current = distance;
        onDragEnd();
        isDraggingRef.current = false;
      } else if (event.touches.length === 1) {
        onDragStart();
        isDraggingRef.current = true;
        const touch = event.touches[0];
        const currentPos = isFullscreenRef.current
          ? fullscreenPositionRef.current
          : positionRef.current;
        dragStart.current = {
          x: touch.clientX - currentPos.x,
          y: touch.clientY - currentPos.y,
        };
      }
    };

    const handleTouchMove = function (this: HTMLElement, event: TouchEvent) {
      if (event.touches.length === 2) {
        event.preventDefault();
        if (lastPinchDistance.current !== null) {
          const touch1 = event.touches[0];
          const touch2 = event.touches[1];
          const distance = Math.sqrt(
            Math.pow(touch1.clientX - touch2.clientX, 2) +
              Math.pow(touch1.clientY - touch2.clientY, 2)
          );

          const zoomFactor = distance / lastPinchDistance.current;
          lastPinchDistance.current = distance;

          const newScale = Math.min(
            Math.max(scale * zoomFactor, MIN_SCALE),
            MAX_SCALE
          );
          onScaleChange(newScale);
          onManualPositioning();
        }
      } else if (event.touches.length === 1 && isDraggingRef.current) {
        event.preventDefault();
        onManualPositioning();

        const touch = event.touches[0];
        const newPos = {
          x: touch.clientX - dragStart.current.x,
          y: touch.clientY - dragStart.current.y,
        };

        onPositionChange(newPos, isFullscreenRef.current);
      }
    };

    const handleTouchEnd = function (this: HTMLElement, event: TouchEvent) {
      if (isDraggingRef.current && event.changedTouches.length > 0) {
        const touch = event.changedTouches[0];
        const finalPos = {
          x: touch.clientX - dragStart.current.x,
          y: touch.clientY - dragStart.current.y,
        };

        onManualPositioning();
        onPositionChange(finalPos, isFullscreenRef.current);
      }

      onDragEnd();
      isDraggingRef.current = false;
      lastPinchDistance.current = null;
    };

    targetElement.addEventListener('touchstart', handleTouchStart, {
      passive: false,
    });
    targetElement.addEventListener('touchmove', handleTouchMove, {
      passive: false,
    });
    targetElement.addEventListener('touchend', handleTouchEnd, {
      passive: true,
    });

    return () => {
      targetElement.removeEventListener('touchstart', handleTouchStart);
      targetElement.removeEventListener('touchmove', handleTouchMove);
      targetElement.removeEventListener('touchend', handleTouchEnd);
    };
  }, [
    isFullscreen,
    scale,
    onPositionChange,
    onScaleChange,
    onDragStart,
    onDragEnd,
    onManualPositioning,
  ]);

  return null; // This component only handles touch events
}
