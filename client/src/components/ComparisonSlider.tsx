import { useState, useRef, useEffect, useCallback } from 'react';
import { MoveHorizontal } from 'lucide-react';

interface ComparisonSliderProps {
    original: string;
    overlay: string; // The heatmap or modified image
    labelOriginal?: string;
    labelOverlay?: string;
}

export function ComparisonSlider({
    original,
    overlay,
    labelOriginal = "Original",
    labelOverlay = "Analysis Heatmap"
}: ComparisonSliderProps) {
    const [position, setPosition] = useState(50);
    const containerRef = useRef<HTMLDivElement>(null);
    const isDragging = useRef(false);

    // Handle Dragging
    const handleMove = useCallback((clientX: number) => {
        if (!containerRef.current) return;

        const rect = containerRef.current.getBoundingClientRect();
        const x = Math.max(0, Math.min(clientX - rect.left, rect.width));
        const percent = Math.max(0, Math.min((x / rect.width) * 100, 100));

        setPosition(percent);
    }, []);

    const handleMouseDown = () => { isDragging.current = true; };
    const handleMouseUp = () => { isDragging.current = false; };
    const handleMouseMove = (e: React.MouseEvent) => {
        if (isDragging.current) handleMove(e.clientX);
    };

    const handleTouchMove = (e: React.TouchEvent) => {
        handleMove(e.touches[0].clientX);
    };

    // Global mouse up to catch dragging outside container
    useEffect(() => {
        const handleGlobalMouseUp = () => { isDragging.current = false; };
        const handleGlobalMouseMove = (e: MouseEvent) => {
            if (isDragging.current) handleMove(e.clientX);
        };

        window.addEventListener('mouseup', handleGlobalMouseUp);
        window.addEventListener('mousemove', handleGlobalMouseMove);
        return () => {
            window.removeEventListener('mouseup', handleGlobalMouseUp);
            window.removeEventListener('mousemove', handleGlobalMouseMove);
        };
    }, [handleMove]);

    return (
        <div
            ref={containerRef}
            className="relative w-full h-[500px] rounded-xl overflow-hidden select-none cursor-col-resize group"
            onMouseDown={handleMouseDown}
            onTouchMove={handleTouchMove}
        >
            {/* Background: Original Image */}
            <img
                src={original}
                alt="Original"
                className="absolute inset-0 w-full h-full object-cover pointer-events-none"
            />

            {/* Foreground: Overlay (Heatmap) - Clipped */}
            <div
                className="absolute inset-0 w-full h-full overflow-hidden pointer-events-none"
                style={{ clipPath: `polygon(0 0, ${position}% 0, ${position}% 100%, 0 100%)` }}
            >
                <img
                    src={overlay}
                    alt="Overlay"
                    className="absolute inset-0 w-full h-full object-cover"
                />
                {/* Helper Badge for Overlay */}
                <div className="absolute top-4 left-4 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-sm text-xs text-white border border-white/10">
                    {labelOverlay}
                </div>
            </div>

            {/* Helper Badge for Original (Visible on right side) */}
            <div
                className="absolute top-4 right-4 px-3 py-1.5 rounded-lg bg-black/60 backdrop-blur-sm text-xs text-white border border-white/10 pointer-events-none transition-opacity duration-300"
                style={{ opacity: position > 90 ? 0 : 1 }}
            >
                {labelOriginal}
            </div>

            {/* Slider Handle */}
            <div
                className="absolute top-0 bottom-0 w-1 bg-white cursor-col-resize shadow-[0_0_10px_rgba(0,0,0,0.5)] z-20 pointer-events-none"
                style={{ left: `${position}%` }}
            >
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-8 h-8 bg-white rounded-full flex items-center justify-center shadow-lg transform group-hover:scale-110 transition-transform">
                    <MoveHorizontal className="w-4 h-4 text-black" />
                </div>
            </div>

            {/* Instructions Overlay (Fades out) */}
            <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 rounded-full bg-black/50 backdrop-blur-md text-xs text-white/80 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">
                Drag to compare
            </div>
        </div>
    );
}
