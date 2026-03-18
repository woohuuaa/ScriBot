'use client';
import { useEffect } from 'react';

interface MermaidKeyboardProps {
  isFullscreen: boolean;
  containerRef: React.RefObject<HTMLDivElement | null>;
  onToggleFullscreen: () => void;
  onFitToView: () => void;
  onCloseFullscreen: () => void;
}

export function MermaidKeyboard({
  isFullscreen,
  containerRef,
  onToggleFullscreen,
  onFitToView,
  onCloseFullscreen,
}: MermaidKeyboardProps) {
  useEffect(() => {
    const handleKeydown = (e: KeyboardEvent) => {
      // Don't interfere with input fields
      if (
        e.target instanceof HTMLInputElement ||
        e.target instanceof HTMLTextAreaElement
      ) {
        return;
      }

      const diagramContainer = containerRef.current;
      const isDialogFocused =
        diagramContainer &&
        (diagramContainer.contains(e.target as Node) ||
          diagramContainer === e.target ||
          document.activeElement === diagramContainer ||
          diagramContainer.contains(document.activeElement));

      if (!isFullscreen && !isDialogFocused) {
        return; // Only handle shortcuts when diagram is focused or in fullscreen
      }

      if (e.key === 'Escape' && isFullscreen) {
        e.preventDefault();
        onCloseFullscreen();
      } else if (
        e.key === 'f' &&
        !e.ctrlKey &&
        !e.metaKey &&
        (isDialogFocused || isFullscreen)
      ) {
        e.preventDefault();
        onToggleFullscreen();
      } else if (e.key === '0' && (isDialogFocused || isFullscreen)) {
        e.preventDefault();
        onFitToView();
      }
    };

    document.addEventListener('keydown', handleKeydown);
    return () => document.removeEventListener('keydown', handleKeydown);
  }, [isFullscreen, onToggleFullscreen, onFitToView, onCloseFullscreen]);

  return null; // This component only handles keyboard events
}
