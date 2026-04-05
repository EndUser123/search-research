import { createSignal, Accessor } from 'solid-js';

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

interface PanelResizeHookProps<T> {
    initialPanelFlex: T;
    stage1ContainerRef: Accessor<HTMLElement | undefined>;
}

export const createPanelResize = <T extends Record<string, number>>(props: PanelResizeHookProps<T>) => {
    const [panelFlex, setPanelFlex] = createSignal<T>(props.initialPanelFlex);

    let resizeData: ResizeData | null = null;
    let resizeAnimationFrame: number | null = null;
    const MIN_PANEL_HEIGHT = 120;

    const handleResizeEnd = () => {
        if (resizeAnimationFrame) {
            cancelAnimationFrame(resizeAnimationFrame);
            resizeAnimationFrame = null;
        }
        if (!resizeData) return;

        // Reset cursor and user-select
        document.body.style.cursor = '';
        document.body.style.userSelect = '';

        // Remove event listeners
        window.removeEventListener('mousemove', handleResize);
        window.removeEventListener('mouseup', handleResizeEnd);

        // Clear resize data
        resizeData = null;
    };

    const handleResize = (e: MouseEvent) => {
        if (!resizeData?.isResizing) return;

        // Use requestAnimationFrame for smoother updates
        if (resizeAnimationFrame) {
            cancelAnimationFrame(resizeAnimationFrame);
        }

        resizeAnimationFrame = requestAnimationFrame(() => {
            if (!resizeData) return;

            const { panel1, panel2, startY, startHeight1, startHeight2, startFlex1, startFlex2, panel1Element, panel2Element } = resizeData;
            const totalHeight = startHeight1 + startHeight2;
            const totalFlex = startFlex1 + startFlex2;

            // Calculate the height change directly from the start position
            const heightChange = e.clientY - startY;
            const newHeight1 = startHeight1 + heightChange;

            // Clamp the new height to ensure minimum panel size
            const clampedHeight1 = Math.min(
                Math.max(newHeight1, MIN_PANEL_HEIGHT),
                totalHeight - MIN_PANEL_HEIGHT
            );

            // Calculate the new flex ratio based on the clamped height
            const newRatio = clampedHeight1 / totalHeight;

            // Calculate new flex values based on the ratio
            const newFlex1 = totalFlex * newRatio;
            const newFlex2 = totalFlex - newFlex1;

            // Update the DOM elements directly for immediate visual feedback
            panel1Element.style.flexGrow = String(newFlex1);
            panel2Element.style.flexGrow = String(newFlex2);

            // Also update the Solid signal for data consistency
            setPanelFlex(prev => ({ ...prev, [panel1]: newFlex1, [panel2]: newFlex2 }));
        });
    };

    const handleResizeStart = (e: MouseEvent, panel1Key: string, panel2Key: string) => {
        e.preventDefault();

        // In Solid, props.stage1ContainerRef will be the element itself if passed correctly,
        // or we might need to pass a function that returns it if it's not mounted yet.
        // Assuming it's mounted when user clicks.
        const container = props.stage1ContainerRef();
        if (!container) return;

        const panel1Element = container.querySelector(`[data-panel-key="${panel1Key}"]`) as HTMLElement;
        const panel2Element = container.querySelector(`[data-panel-key="${panel2Key}"]`) as HTMLElement;

        if (!panel1Element || !panel2Element) return;

        // Calculate initial heights and container height
        const startHeight1 = panel1Element.offsetHeight;
        const startHeight2 = panel2Element.offsetHeight;

        resizeData = {
            isResizing: true,
            panel1: panel1Key,
            panel2: panel2Key,
            startY: e.clientY,
            startFlex1: panelFlex()[panel1Key],
            startFlex2: panelFlex()[panel2Key],
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
    };

    return {
        panelFlex,
        setPanelFlex,
        handleResizeStart,
        MIN_PANEL_HEIGHT
    };
};
