import { createContext, useContext, ReactNode } from 'react';
import { useScroll, MotionValue } from 'framer-motion';

interface LandingScrollContextType {
    scrollY: MotionValue<number>;
    scrollYProgress: MotionValue<number>;
    containerRef: React.RefObject<HTMLDivElement | null>; // Fix: explicit null type to match useRef default
}

const LandingScrollContext = createContext<LandingScrollContextType | undefined>(undefined);

export function LandingScrollProvider({ children }: { children: ReactNode }) {
    // We rely on window scroll now for better native feel
    const { scrollY, scrollYProgress } = useScroll();

    return (
        <LandingScrollContext.Provider value={{ scrollY, scrollYProgress, containerRef: { current: null } }}>
            <div className="w-full relative">
                {children}
            </div>
        </LandingScrollContext.Provider>
    );
}

export function useLandingScroll() {
    const context = useContext(LandingScrollContext);
    if (!context) {
        throw new Error('useLandingScroll must be used within a LandingScrollProvider');
    }
    return context;
}
