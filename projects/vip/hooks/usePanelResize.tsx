import React, { useCallback, useEffect, useRef, useState } from 'react';

interface ResizeData {
  isResizing: boolean;
  panel1: string;
  panel2: string;
  startY: number;
  startFlex1: number;
  startFlex2: number;
  startHeight1: number;
  startHeight2: number;
  panel1Element: HTMLElement;
  panel2Element: HTMLElement;
  containerHeight: number;
}

interface PanelResizeHookProps {
  initialPanelFlex: { [key: string]: number };
  stage1ContainerRef?: React.RefObject<HTMLElement | null>;
  minHeights?: { [key: string]: number };
}

interface PanelResizeHookReturn {
  panelFlex: { [key: string]: number };
  setPanelFlex: React.Dispatch<React.SetStateAction<{ [key: string]: number }>>;
  resizeData: React.MutableRefObject<ResizeData | null>;
  resizeAnimationFrameRef: React.MutableRefObject<number | null>;
  handleResize: (e: MouseEvent) => void;
  handleResizeEnd: () => void;
  handleResizeStart: (e: React.MouseEvent, panel1Key: string, panel2Key: string) => void;
  MIN_PANEL_HEIGHT: number;
}

export const usePanelResize = ({ initialPanelFlex, stage1ContainerRef, minHeights = {} }: PanelResizeHookProps): PanelResizeHookReturn => {
  const [panelFlex, setPanelFlex] = useState(initialPanelFlex);
  const resizeData = useRef<ResizeData | null>(null);
  const resizeAnimationFrameRef = useRef<number | null>(null);
  const DEFAULT_MIN_HEIGHT = 60;

  const handleResizeEnd = useCallback(() => {
    if (resizeAnimationFrameRef.current) {
      cancelAnimationFrame(resizeAnimationFrameRef.current);
      resizeAnimationFrameRef.current = null;
    }
    if (!resizeData.current) return;

    // Reset cursor and user-select
    document.body.style.cursor = '';
    document.body.style.userSelect = '';

    // Remove event listeners
    window.removeEventListener('mousemove', handleResize);
    window.removeEventListener('mouseup', handleResizeEnd);

    // Clear resize data
    resizeData.current = null;
  }, []);

  const handleResize = useCallback((e: MouseEvent) => {
    if (!resizeData.current?.isResizing) return;

    // Use requestAnimationFrame for smoother updates
    if (resizeAnimationFrameRef.current) {
      cancelAnimationFrame(resizeAnimationFrameRef.current);
    }

    resizeAnimationFrameRef.current = requestAnimationFrame(() => {
      const { panel1, panel2, startY, startHeight1, startHeight2, startFlex1, startFlex2, panel1Element, panel2Element, containerHeight } = resizeData.current!;
      const totalHeight = startHeight1 + startHeight2;
      const totalFlex = startFlex1 + startFlex2;

      // Calculate the height change directly from the start position
      const heightChange = e.clientY - startY;
      const newHeight1 = startHeight1 + heightChange;

      // Get panel-specific min heights or use default
      const minHeight1 = minHeights[panel1] || DEFAULT_MIN_HEIGHT;
      const minHeight2 = minHeights[panel2] || DEFAULT_MIN_HEIGHT;

      // Clamp the new height to ensure minimum panel size
      const clampedHeight1 = Math.min(
        Math.max(newHeight1, minHeight1),
        totalHeight - minHeight2
      );

      // Calculate the new flex ratio based on the clamped height
      const newRatio = clampedHeight1 / totalHeight;

      // Calculate new flex values based on the ratio
      const newFlex1 = totalFlex * newRatio;
      const newFlex2 = totalFlex - newFlex1;

      // Update the DOM elements directly for immediate visual feedback
      panel1Element.style.flexGrow = String(newFlex1);
      panel2Element.style.flexGrow = String(newFlex2);

      // Also update the React state for data consistency
      setPanelFlex(prev => ({ ...prev, [panel1]: newFlex1, [panel2]: newFlex2 }));
    });
  }, [minHeights]);

  const handleResizeStart = useCallback((e: React.MouseEvent, panel1Key: string, panel2Key: string) => {
    e.preventDefault();
    if (!stage1ContainerRef?.current) return;

    const panel1Element = stage1ContainerRef.current.querySelector(`[data-panel-key="${panel1Key}"]`) as HTMLElement;
    const panel2Element = stage1ContainerRef.current.querySelector(`[data-panel-key="${panel2Key}"]`) as HTMLElement;

    if (!panel1Element || !panel2Element) return;

    // Calculate initial heights and container height
    const startHeight1 = panel1Element.offsetHeight;
    const startHeight2 = panel2Element.offsetHeight;

    resizeData.current = {
      isResizing: true,
      panel1: panel1Key,
      panel2: panel2Key,
      startY: e.clientY,
      startFlex1: panelFlex[panel1Key],
      startFlex2: panelFlex[panel2Key],
      startHeight1,
      startHeight2,
      panel1Element,
      panel2Element,
      containerHeight: startHeight1 + startHeight2
    };

    document.body.style.cursor = 'row-resize';
    document.body.style.userSelect = 'none';

    window.addEventListener('mousemove', handleResize);
    window.addEventListener('mouseup', handleResizeEnd);
  }, [panelFlex, handleResize, handleResizeEnd, stage1ContainerRef]);

  return {
    panelFlex,
    setPanelFlex,
    resizeData,
    resizeAnimationFrameRef,
    handleResize,
    handleResizeEnd,
    handleResizeStart,
    MIN_PANEL_HEIGHT: DEFAULT_MIN_HEIGHT
  };
};
