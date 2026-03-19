import { AnimatePresence, motion } from 'framer-motion';
import { useCallback, useEffect, useRef, useState } from 'react';

interface GlobeNode {
    lat: number;
    lng: number;
    label: string;
    flagged?: boolean;
    size?: number;
    claim?: string;
    verdict?: 'verified' | 'fake' | 'uncertain';
    confidence?: number;
    timestamp?: string;
}

const NODES: GlobeNode[] = [
    { lat: 40.7, lng: -74, label: 'New York', size: 1.2, claim: 'Stock market crash rumor', verdict: 'fake', confidence: 98, timestamp: '2s ago' },
    { lat: 51.5, lng: -0.1, label: 'London', size: 1.1, claim: 'Royal family announcement', verdict: 'verified', confidence: 95, timestamp: '12s ago' },
    { lat: 35.7, lng: 139.7, label: 'Tokyo', flagged: true, size: 1.3, claim: 'AI-generated election footage', verdict: 'fake', confidence: 99, timestamp: 'Just now' },
    { lat: -33.9, lng: 18.4, label: 'Cape Town', size: 0.8, claim: 'Water supply contamination', verdict: 'uncertain', confidence: 65, timestamp: '5m ago' },
    { lat: 28.6, lng: 77.2, label: 'Delhi', flagged: true, size: 1.4, claim: 'Deepfake celebrity endorsement', verdict: 'fake', confidence: 97, timestamp: '1m ago' },
    { lat: 55.7, lng: 37.6, label: 'Moscow', size: 1.0, claim: 'Diplomatic cable leak', verdict: 'uncertain', confidence: 45, timestamp: '30s ago' },
    { lat: -23.5, lng: -46.6, label: 'São Paulo', flagged: true, size: 1.1, claim: 'Currency devaluation report', verdict: 'fake', confidence: 88, timestamp: '10m ago' },
    { lat: 1.3, lng: 103.8, label: 'Singapore', size: 0.9, claim: 'Tech regulation bill', verdict: 'verified', confidence: 92, timestamp: '15m ago' },
    { lat: 48.8, lng: 2.3, label: 'Paris', size: 1.0, claim: 'Protest attendance figures', verdict: 'uncertain', confidence: 70, timestamp: '8s ago' },
    { lat: 37.8, lng: -122.4, label: 'San Francisco', size: 1.1, claim: 'New AI model release', verdict: 'verified', confidence: 99, timestamp: '1s ago' },
    { lat: -37.8, lng: 144.9, label: 'Melbourne', size: 0.8, claim: 'Public transport strike', verdict: 'verified', confidence: 96, timestamp: '3m ago' },
    { lat: 31.2, lng: 121.5, label: 'Shanghai', size: 1.2, claim: 'Manufacturing data leak', verdict: 'fake', confidence: 91, timestamp: '45s ago' },
];

const CONNECTIONS = [
    [0, 1], [1, 2], [2, 4], [4, 7], [3, 5], [5, 8], [6, 0],
    [8, 1], [9, 2], [7, 3], [0, 4], [6, 3], [10, 2], [11, 7],
    [9, 0], [11, 4], [5, 4], [1, 8],
];

// ====== DETAILED CONTINENT COASTLINES ======
const COASTLINES: number[][][] = [
    [[60, -140], [58, -138], [56, -133], [54, -130], [52, -128], [50, -127], [48, -124], [46, -124], [44, -124], [42, -124], [40, -122], [38, -123], [36, -122], [34, -120], [33, -118], [32, -117], [31, -115], [30, -113], [28, -112], [27, -110], [26, -108], [26, -105], [28, -97], [29, -95], [30, -93], [30, -90], [30, -88], [29, -85], [28, -83], [27, -82], [26, -80], [25, -80], [24, -82], [25, -84], [27, -83], [28, -82], [30, -84], [30, -81], [31, -80], [32, -80], [33, -79], [34, -77], [35, -76], [36, -76], [37, -76], [38, -75], [39, -74], [40, -74], [41, -73], [42, -71], [43, -70], [44, -68], [45, -67], [46, -65], [47, -63], [48, -60], [49, -58], [50, -56], [52, -56], [53, -56], [55, -60], [57, -62], [59, -63], [60, -65], [62, -68], [63, -70], [65, -75], [66, -80], [68, -90], [69, -95], [70, -100], [71, -110], [71, -120], [70, -130], [68, -140], [65, -145], [63, -150], [61, -152], [60, -150], [58, -148], [56, -155], [55, -160], [56, -163], [58, -165], [60, -165], [62, -164], [64, -162], [66, -165], [68, -168], [70, -165], [72, -155], [73, -140], [74, -120], [74, -100], [73, -85], [72, -80], [70, -70], [68, -65], [67, -62], [65, -60], [63, -58], [60, -140]],
    [[72, -55], [73, -58], [75, -60], [77, -62], [78, -68], [79, -72], [80, -60], [81, -45], [82, -35], [83, -30], [82, -25], [80, -20], [78, -18], [76, -19], [74, -20], [73, -22], [72, -25], [70, -22], [68, -26], [67, -30], [66, -35], [65, -40], [64, -45], [64, -50], [65, -52], [67, -53], [69, -54], [71, -55], [72, -55]],
    [[12, -70], [11, -73], [10, -76], [9, -78], [8, -77], [7, -78], [5, -77], [3, -78], [2, -80], [0, -80], [-1, -80], [-3, -80], [-5, -81], [-6, -80], [-5, -78], [-5, -75], [-4, -73], [-3, -70], [-2, -68], [0, -65], [0, -60], [-1, -55], [-2, -50], [-3, -45], [-4, -40], [-5, -35], [-7, -35], [-9, -36], [-10, -37], [-12, -38], [-14, -39], [-16, -40], [-18, -40], [-20, -41], [-22, -42], [-24, -44], [-26, -46], [-28, -48], [-30, -50], [-32, -52], [-34, -54], [-36, -57], [-38, -58], [-40, -62], [-42, -64], [-44, -66], [-46, -68], [-48, -70], [-50, -72], [-52, -70], [-54, -70], [-55, -68], [-54, -65], [-52, -68], [-50, -74], [-48, -72], [-46, -70], [-44, -68], [-42, -65], [-40, -63], [-38, -58], [-36, -56], [-34, -54], [-32, -52], [-30, -50], [-28, -48], [-26, -45], [-24, -42], [-22, -40], [-20, -38], [-18, -36], [-16, -35], [-14, -33], [-12, -32], [-10, -32], [-8, -32], [-6, -30], [-4, -28], [-2, -28], [0, -30], [1, -32], [2, -35], [3, -40], [4, -45], [5, -50], [6, -55], [7, -58], [8, -62], [9, -65], [10, -68], [11, -70], [12, -70]],
    [[36, -6], [37, -5], [38, -4], [39, -3], [40, -2], [41, 0], [42, 2], [43, 3], [44, 5], [45, 7], [44, 8], [43, 10], [42, 12], [41, 13], [40, 15], [39, 16], [38, 18], [37, 20], [36, 22], [35, 24], [36, 26], [37, 28], [38, 30], [40, 28], [42, 28], [44, 28], [45, 26], [46, 24], [47, 20], [48, 18], [49, 16], [50, 14], [51, 12], [52, 10], [53, 8], [54, 9], [55, 10], [56, 11], [57, 12], [58, 14], [59, 16], [60, 18], [61, 20], [62, 22], [63, 20], [64, 18], [65, 16], [66, 14], [67, 13], [68, 15], [69, 17], [70, 20], [71, 23], [70, 26], [69, 28], [70, 30], [71, 28], [70, 25], [68, 28], [66, 25], [64, 22], [62, 25], [60, 22], [58, 18], [56, 15], [54, 12], [52, 6], [51, 4], [50, 2], [49, 0], [48, -2], [47, -3], [46, -2], [45, 0], [44, -2], [43, -4], [42, -6], [41, -8], [40, -8], [39, -9], [37, -8], [36, -6]],
    [[35, -6], [34, -2], [33, 0], [32, 2], [31, 5], [30, 10], [28, 12], [26, 14], [24, 16], [22, 18], [20, 20], [18, 18], [16, 16], [14, 15], [12, 14], [10, 12], [8, 10], [6, 8], [5, 6], [4, 4], [3, 2], [2, 0], [1, 1], [0, 5], [-1, 8], [-2, 10], [-4, 12], [-6, 12], [-8, 14], [-10, 15], [-12, 18], [-14, 22], [-16, 24], [-18, 26], [-20, 28], [-22, 30], [-24, 32], [-26, 34], [-28, 32], [-30, 30], [-32, 28], [-34, 26], [-34, 22], [-34, 18], [-33, 16], [-30, 16], [-28, 14], [-26, 12], [-24, 10], [-22, 8], [-20, 6], [-18, 8], [-16, 10], [-14, 12], [-12, 14], [-10, 13], [-8, 10], [-6, 8], [-5, 5], [-4, 3], [-3, 5], [-2, 8], [-1, 10], [0, 10], [2, 10], [4, 8], [6, 6], [8, 5], [10, 3], [12, 0], [14, -2], [16, -8], [18, -10], [20, -14], [22, -16], [24, -15], [26, -14], [28, -12], [30, -8], [32, -5], [33, -4], [34, -5], [35, -6]],
    [[40, 30], [42, 32], [44, 34], [46, 36], [48, 38], [50, 40], [52, 42], [54, 44], [56, 46], [58, 48], [60, 50], [62, 55], [64, 60], [66, 65], [68, 70], [70, 72], [68, 75], [66, 78], [64, 80], [62, 82], [60, 85], [58, 88], [56, 90], [54, 92], [52, 95], [50, 98], [48, 100], [46, 102], [44, 105], [42, 108], [40, 110], [38, 112], [36, 115], [34, 118], [32, 120], [30, 122], [28, 120], [26, 118], [24, 115], [22, 110], [20, 108], [18, 105], [16, 103], [14, 100], [12, 98], [10, 100], [8, 102], [6, 100], [4, 98], [2, 96], [0, 100], [-2, 102], [-4, 104], [-6, 106], [-8, 108], [-7, 110], [-5, 112], [-3, 110], [0, 108], [2, 106], [4, 105], [6, 108], [8, 110], [10, 105], [8, 98], [6, 96], [4, 95], [2, 96], [0, 96], [-2, 95], [-4, 92], [-6, 90], [-8, 88], [-6, 86], [-4, 84], [-2, 82], [0, 80], [5, 78], [10, 76], [15, 72], [20, 70], [22, 68], [24, 65], [26, 62], [28, 60], [30, 55], [32, 50], [34, 46], [36, 42], [38, 38], [40, 35], [40, 30]],
    [[45, 140], [44, 142], [43, 144], [42, 143], [41, 141], [40, 140], [38, 138], [36, 136], [34, 135], [33, 133], [32, 131], [34, 132], [36, 134], [38, 137], [40, 140], [42, 142], [44, 143], [45, 140]],
    [[38, 126], [37, 127], [36, 128], [35, 129], [34, 127], [35, 126], [36, 126], [37, 127], [38, 126]],
    [[30, 72], [28, 70], [26, 68], [24, 70], [22, 72], [20, 73], [18, 74], [16, 76], [14, 77], [12, 78], [10, 79], [8, 77], [6, 80], [8, 82], [10, 80], [12, 80], [14, 78], [16, 80], [18, 83], [20, 86], [22, 88], [24, 90], [26, 92], [28, 97], [26, 95], [24, 92], [22, 90], [20, 88], [18, 86], [16, 84], [14, 82], [12, 80], [10, 78], [8, 76], [10, 76], [12, 76], [14, 74], [16, 74], [18, 72], [20, 72], [22, 72], [24, 73], [26, 73], [28, 73], [30, 72]],
    [[-12, 136], [-14, 130], [-16, 128], [-18, 124], [-20, 118], [-22, 114], [-24, 114], [-26, 113], [-28, 114], [-30, 115], [-32, 116], [-34, 118], [-35, 120], [-36, 124], [-37, 128], [-38, 136], [-38, 140], [-38, 144], [-37, 147], [-36, 149], [-34, 151], [-32, 152], [-30, 153], [-28, 153], [-26, 152], [-24, 150], [-22, 149], [-20, 148], [-18, 146], [-16, 145], [-14, 140], [-13, 138], [-12, 136]],
    [[-35, 174], [-36, 175], [-37, 176], [-38, 177], [-40, 176], [-42, 174], [-44, 172], [-46, 168], [-45, 167], [-44, 168], [-42, 170], [-40, 172], [-38, 174], [-36, 175], [-35, 174]],
    [[50, -6], [51, -5], [52, -4], [53, -3], [54, -3], [55, -4], [56, -5], [57, -6], [58, -5], [59, -3], [58, -2], [57, -1], [56, 0], [55, 0], [54, 1], [53, 0], [52, -1], [51, -2], [50, -4], [50, -6]],
    [[-2, 96], [-3, 98], [-4, 100], [-5, 102], [-6, 104], [-7, 106], [-8, 108], [-7, 110], [-6, 112], [-5, 114], [-4, 116], [-3, 118], [-2, 116], [-3, 114], [-4, 112], [-5, 110], [-6, 108], [-5, 106], [-4, 104], [-3, 102], [-2, 100], [-2, 96]],
    [[-12, 49], [-14, 48], [-16, 46], [-18, 44], [-20, 44], [-22, 44], [-24, 46], [-25, 47], [-24, 48], [-22, 50], [-20, 50], [-18, 50], [-16, 50], [-14, 50], [-12, 49]],
];

function project(lat: number, lng: number, rotation: number, tilt: number, radius: number, cx: number, cy: number) {
    const phi = ((90 - lat) * Math.PI) / 180;
    const theta = ((lng + rotation) * Math.PI) / 180;
    const x3d = radius * Math.sin(phi) * Math.cos(theta);
    const y3d = radius * Math.cos(phi);
    const z3d = radius * Math.sin(phi) * Math.sin(theta);

    const cosT = Math.cos(tilt);
    const sinT = Math.sin(tilt);
    const y = y3d * cosT - z3d * sinT;
    const z = y3d * sinT + z3d * cosT;

    return { x: cx + x3d, y: cy - y, z, visible: z > -radius * 0.1 };
}

interface Particle {
    angle: number;
    distance: number;
    speed: number;
    size: number;
    opacity: number;
    orbitTilt: number;
}

function createParticles(count: number): Particle[] {
    return Array.from({ length: count }, () => ({
        angle: Math.random() * Math.PI * 2,
        distance: 0.85 + Math.random() * 0.6,
        speed: 0.002 + Math.random() * 0.004,
        size: 0.5 + Math.random() * 2,
        opacity: 0.2 + Math.random() * 0.5,
        orbitTilt: (Math.random() - 0.5) * 1.2,
    }));
}

interface TooltipData {
    x: number;
    y: number;
    node: GlobeNode;
}

export function HeroGlobe() {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const rotationRef = useRef(0);
    const tiltRef = useRef(-0.3);
    const particlesRef = useRef<Particle[]>(createParticles(60));
    const [isDark, setIsDark] = useState(false);
    const [tooltip, setTooltip] = useState<TooltipData | null>(null);
    const animId = useRef<number>(undefined);

    // Drag state
    const dragRef = useRef({
        isDragging: false,
        lastX: 0,
        lastY: 0,
        velocityX: 0,
        velocityY: 0,
        lastDragTime: 0,       // timestamp of last drag release
        autoResumeDelay: 2000, // ms before auto-rotation resumes
    });

    // Store projected nodes for hit-testing
    const projectedNodesRef = useRef<{ x: number; y: number; z: number; visible: boolean; radius: number }[]>([]);

    useEffect(() => {
        const check = () => setIsDark(document.documentElement.classList.contains('dark'));
        check();
        const observer = new MutationObserver(check);
        observer.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
        return () => observer.disconnect();
    }, []);

    // ===== DRAG HANDLERS =====
    const handleMouseDown = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
        dragRef.current.isDragging = true;
        dragRef.current.lastX = e.clientX;
        dragRef.current.lastY = e.clientY;
        dragRef.current.velocityX = 0;
        dragRef.current.velocityY = 0;
    }, []);

    const handleMouseMove = useCallback((e: React.MouseEvent<HTMLCanvasElement>) => {
        const drag = dragRef.current;

        if (drag.isDragging) {
            const dx = e.clientX - drag.lastX;
            const dy = e.clientY - drag.lastY;
            rotationRef.current -= dx * 0.4;
            tiltRef.current = Math.max(-1.2, Math.min(1.2, tiltRef.current + dy * 0.005));
            drag.velocityX = -dx * 0.4;
            drag.velocityY = dy;
            drag.lastX = e.clientX;
            drag.lastY = e.clientY;
            setTooltip(null); // hide tooltip while dragging
            return;
        }

        // Hit-test nodes for tooltip
        const canvas = canvasRef.current;
        if (!canvas) return;
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;

        let found = false;
        for (let i = 0; i < projectedNodesRef.current.length; i++) {
            const pn = projectedNodesRef.current[i];
            if (!pn.visible) continue;
            const dist = Math.hypot(mx - pn.x, my - pn.y);
            if (dist < pn.radius + 8) {
                setTooltip({ x: pn.x, y: pn.y, node: NODES[i] });
                found = true;
                break;
            }
        }
        if (!found) setTooltip(null);
    }, []);

    const handleMouseUp = useCallback(() => {
        dragRef.current.isDragging = false;
        dragRef.current.lastDragTime = Date.now();
    }, []);

    const handleMouseLeave = useCallback(() => {
        dragRef.current.isDragging = false;
        dragRef.current.lastDragTime = Date.now();
        setTooltip(null);
    }, []);

    // Touch support
    const handleTouchStart = useCallback((e: React.TouchEvent<HTMLCanvasElement>) => {
        if (e.touches.length === 1) {
            dragRef.current.isDragging = true;
            dragRef.current.lastX = e.touches[0].clientX;
            dragRef.current.lastY = e.touches[0].clientY;
        }
    }, []);

    const handleTouchMove = useCallback((e: React.TouchEvent<HTMLCanvasElement>) => {
        if (e.touches.length === 1 && dragRef.current.isDragging) {
            const dx = e.touches[0].clientX - dragRef.current.lastX;
            const dy = e.touches[0].clientY - dragRef.current.lastY;
            rotationRef.current -= dx * 0.4;
            tiltRef.current = Math.max(-1.2, Math.min(1.2, tiltRef.current + dy * 0.005));
            dragRef.current.lastX = e.touches[0].clientX;
            dragRef.current.lastY = e.touches[0].clientY;
            e.preventDefault();
        }
    }, []);

    const handleTouchEnd = useCallback(() => {
        dragRef.current.isDragging = false;
        dragRef.current.lastDragTime = Date.now();
    }, []);

    const draw = useCallback(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        const dpr = window.devicePixelRatio || 1;
        const w = canvas.clientWidth;
        const h = canvas.clientHeight;
        canvas.width = w * dpr;
        canvas.height = h * dpr;
        ctx.scale(dpr, dpr);
        ctx.clearRect(0, 0, w, h);

        const cx = w / 2;
        const cy = h / 2;
        const radius = Math.min(w, h) * 0.36;
        const tilt = tiltRef.current;
        const time = Date.now() / 1000;
        const drag = dragRef.current;

        // ===== AUTO-ROTATION with momentum and resume =====
        if (!drag.isDragging) {
            const timeSinceDrag = Date.now() - drag.lastDragTime;

            // Apply inertia/momentum after release
            if (Math.abs(drag.velocityX) > 0.01) {
                rotationRef.current += drag.velocityX;
                drag.velocityX *= 0.95; // friction
            }

            // Smoothly resume auto-rotation after delay
            if (timeSinceDrag > drag.autoResumeDelay) {
                const resumeT = Math.min(1, (timeSinceDrag - drag.autoResumeDelay) / 1500);
                rotationRef.current += 0.15 * resumeT;
            }
        }

        const rot = rotationRef.current;

        // ===== COLOR SCHEME =====
        const primary = isDark ? [34, 211, 238] : [60, 80, 140];
        const threat = [239, 68, 68];
        const pStr = `${primary[0]}, ${primary[1]}, ${primary[2]}`;
        const tStr = `${threat[0]}, ${threat[1]}, ${threat[2]}`;

        // ===== BACKGROUND PARTICLES =====
        particlesRef.current.forEach(p => {
            p.angle += p.speed;
            const px = cx + Math.cos(p.angle) * radius * p.distance;
            const py = cy + Math.sin(p.angle + p.orbitTilt) * radius * p.distance * 0.6;
            const pulse = 0.5 + 0.5 * Math.sin(time * 2 + p.angle);
            ctx.beginPath();
            ctx.arc(px, py, p.size * pulse, 0, Math.PI * 2);
            ctx.fillStyle = `rgba(${pStr}, ${p.opacity * pulse * 0.4})`;
            ctx.fill();
        });

        // ===== OUTER ATMOSPHERE GLOW =====
        for (let i = 3; i >= 0; i--) {
            const glowR = radius + 20 + i * 25;
            const glow = ctx.createRadialGradient(cx, cy, radius * 0.8, cx, cy, glowR);
            glow.addColorStop(0, 'transparent');
            glow.addColorStop(0.5, `rgba(${pStr}, ${isDark ? 0.04 : 0.06})`);
            glow.addColorStop(1, 'transparent');
            ctx.fillStyle = glow;
            ctx.fillRect(0, 0, w, h);
        }

        // ===== GLOBE SPHERE BASE =====
        const sphereGrad = ctx.createRadialGradient(
            cx - radius * 0.25, cy - radius * 0.25, radius * 0.05,
            cx, cy, radius
        );
        if (isDark) {
            sphereGrad.addColorStop(0, 'rgba(18, 28, 48, 0.7)');
            sphereGrad.addColorStop(0.4, 'rgba(10, 18, 32, 0.5)');
            sphereGrad.addColorStop(0.8, 'rgba(5, 12, 22, 0.4)');
            sphereGrad.addColorStop(1, 'rgba(34, 211, 238, 0.1)');
        } else {
            sphereGrad.addColorStop(0, 'rgba(245, 247, 252, 0.15)');
            sphereGrad.addColorStop(0.5, 'rgba(235, 238, 248, 0.1)');
            sphereGrad.addColorStop(0.85, 'rgba(210, 215, 235, 0.12)');
            sphereGrad.addColorStop(1, 'rgba(160, 170, 200, 0.1)');
        }
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fillStyle = sphereGrad;
        ctx.fill();

        // ===== SPHERE EDGE GLOW =====
        const edgeGlow = ctx.createRadialGradient(cx, cy, radius * 0.88, cx, cy, radius * 1.06);
        edgeGlow.addColorStop(0, 'transparent');
        edgeGlow.addColorStop(0.6, `rgba(${pStr}, ${isDark ? 0.18 : 0.25})`);
        edgeGlow.addColorStop(1, `rgba(${pStr}, 0.03)`);
        ctx.beginPath();
        ctx.arc(cx, cy, radius * 1.06, 0, Math.PI * 2);
        ctx.fillStyle = edgeGlow;
        ctx.fill();

        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(${pStr}, ${isDark ? 0.3 : 0.35})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // ===== ULTRA-DENSE GRID =====
        ctx.save();
        const gridAlphaBase = isDark ? 0.06 : 0.14;
        const gridAlphaMajor = isDark ? 0.14 : 0.28;

        for (let lat = -80; lat <= 80; lat += 4) {
            ctx.beginPath();
            let firstPoint = true;
            const isMajor = lat % 20 === 0;
            for (let lng = 0; lng <= 360; lng += 2) {
                const p = project(lat, lng, rot, tilt, radius, cx, cy);
                if (!p.visible) { firstPoint = true; continue; }
                const depthFade = 0.3 + (p.z / radius + 1) * 0.35;
                const alpha = (isMajor ? gridAlphaMajor : gridAlphaBase) * depthFade;
                ctx.strokeStyle = `rgba(${pStr}, ${alpha})`;
                if (firstPoint) { ctx.moveTo(p.x, p.y); firstPoint = false; }
                else ctx.lineTo(p.x, p.y);
            }
            ctx.lineWidth = isMajor ? 0.9 : 0.35;
            ctx.stroke();
        }

        for (let lng = 0; lng < 360; lng += 4) {
            ctx.beginPath();
            let firstPoint = true;
            const isMajor = lng % 20 === 0;
            for (let lat = -90; lat <= 90; lat += 2) {
                const p = project(lat, lng, rot, tilt, radius, cx, cy);
                if (!p.visible) { firstPoint = true; continue; }
                const depthFade = 0.3 + (p.z / radius + 1) * 0.35;
                const alpha = (isMajor ? gridAlphaMajor : gridAlphaBase) * depthFade;
                ctx.strokeStyle = `rgba(${pStr}, ${alpha})`;
                if (firstPoint) { ctx.moveTo(p.x, p.y); firstPoint = false; }
                else ctx.lineTo(p.x, p.y);
            }
            ctx.lineWidth = isMajor ? 0.9 : 0.35;
            ctx.stroke();
        }
        ctx.restore();

        // ===== CONTINENT COASTLINES =====
        COASTLINES.forEach(path => {
            ctx.beginPath();
            let started = false;
            for (let i = 0; i < path.length; i++) {
                const p = project(path[i][0], path[i][1], rot, tilt, radius * 0.995, cx, cy);
                if (!p.visible) { started = false; continue; }
                if (!started) { ctx.moveTo(p.x, p.y); started = true; }
                else ctx.lineTo(p.x, p.y);
            }
            if (started) {
                ctx.closePath();
                ctx.fillStyle = isDark ? `rgba(${pStr}, 0.08)` : `rgba(${pStr}, 0.15)`;
                ctx.fill();
            }

            ctx.beginPath();
            started = false;
            for (let i = 0; i < path.length; i++) {
                const p = project(path[i][0], path[i][1], rot, tilt, radius * 0.995, cx, cy);
                if (!p.visible) { started = false; continue; }
                if (!started) { ctx.moveTo(p.x, p.y); started = true; }
                else ctx.lineTo(p.x, p.y);
            }
            ctx.strokeStyle = `rgba(${pStr}, ${isDark ? 0.45 : 0.55})`;
            ctx.lineWidth = isDark ? 1.4 : 1.8;
            ctx.stroke();
        });

        // ===== DATA STREAM CONNECTIONS =====
        const projectedNodes = NODES.map(n => project(n.lat, n.lng, rot, tilt, radius, cx, cy));

        CONNECTIONS.forEach(([i, j]) => {
            const a = projectedNodes[i];
            const b = projectedNodes[j];
            if (!a.visible || !b.visible) return;

            const isFlagged = NODES[i].flagged || NODES[j].flagged;
            const streamColor = isFlagged ? tStr : pStr;

            const midX = (a.x + b.x) / 2;
            const midY = (a.y + b.y) / 2;
            const dist = Math.hypot(b.x - a.x, b.y - a.y);
            const centerDx = midX - cx;
            const centerDy = midY - cy;
            const centerDist = Math.hypot(centerDx, centerDy) || 1;
            const outX = centerDx / centerDist;
            const outY = centerDy / centerDist;

            const flyHeight = dist * 0.55 + radius * 0.18;
            const cpX = midX + outX * flyHeight;
            const cpY = midY + outY * flyHeight;

            const grad = ctx.createLinearGradient(a.x, a.y, b.x, b.y);
            grad.addColorStop(0, `rgba(${streamColor}, 0.08)`);
            grad.addColorStop(0.3, `rgba(${streamColor}, 0.4)`);
            grad.addColorStop(0.7, `rgba(${streamColor}, 0.4)`);
            grad.addColorStop(1, `rgba(${streamColor}, 0.08)`);

            ctx.beginPath();
            ctx.moveTo(a.x, a.y);
            ctx.quadraticCurveTo(cpX, cpY, b.x, b.y);
            ctx.strokeStyle = grad;
            ctx.lineWidth = isFlagged ? 1.8 : 1.2;
            ctx.setLineDash([3, 5]);
            ctx.lineDashOffset = -(time * 50);
            ctx.stroke();
            ctx.setLineDash([]);

            for (let pIdx = 0; pIdx < 2; pIdx++) {
                const tParam = ((time * 0.35 + i * 0.15 + pIdx * 0.5) % 1);
                const tInv = 1 - tParam;
                const pulseX = tInv * tInv * a.x + 2 * tInv * tParam * cpX + tParam * tParam * b.x;
                const pulseY = tInv * tInv * a.y + 2 * tInv * tParam * cpY + tParam * tParam * b.y;

                const glowSize = isFlagged ? 16 : 12;
                const pulseGlow = ctx.createRadialGradient(pulseX, pulseY, 0, pulseX, pulseY, glowSize);
                pulseGlow.addColorStop(0, `rgba(${streamColor}, 0.7)`);
                pulseGlow.addColorStop(0.3, `rgba(${streamColor}, 0.3)`);
                pulseGlow.addColorStop(1, 'transparent');
                ctx.fillStyle = pulseGlow;
                ctx.fillRect(pulseX - glowSize, pulseY - glowSize, glowSize * 2, glowSize * 2);

                ctx.beginPath();
                ctx.arc(pulseX, pulseY, isFlagged ? 3 : 2.5, 0, Math.PI * 2);
                ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
                ctx.fill();
                ctx.beginPath();
                ctx.arc(pulseX, pulseY, isFlagged ? 4.5 : 3.5, 0, Math.PI * 2);
                ctx.strokeStyle = `rgba(${streamColor}, 0.6)`;
                ctx.lineWidth = 1;
                ctx.stroke();
            }
        });

        // ===== NODES (store projected positions for hit-testing) =====
        const storedNodes: typeof projectedNodesRef.current = [];

        projectedNodes.forEach((p, i) => {
            if (!p.visible) {
                storedNodes.push({ x: 0, y: 0, z: 0, visible: false, radius: 0 });
                return;
            }
            const node = NODES[i];
            const isFlagged = node.flagged;
            const colStr = isFlagged ? tStr : pStr;
            const sz = (node.size || 1) * (3 + (p.z / radius) * 2);

            storedNodes.push({ x: p.x, y: p.y, z: p.z, visible: true, radius: sz });

            // Outer halo
            const haloRadius = sz * 6;
            const halo = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, haloRadius);
            halo.addColorStop(0, `rgba(${colStr}, 0.3)`);
            halo.addColorStop(0.4, `rgba(${colStr}, 0.1)`);
            halo.addColorStop(1, 'transparent');
            ctx.fillStyle = halo;
            ctx.fillRect(p.x - haloRadius, p.y - haloRadius, haloRadius * 2, haloRadius * 2);

            if (isFlagged) {
                for (let r = 0; r < 2; r++) {
                    const ripple = (time * 0.8 + i + r) % 2;
                    const rr = sz + ripple * 15;
                    const ra = Math.max(0, 0.4 - ripple * 0.2);
                    ctx.beginPath();
                    ctx.arc(p.x, p.y, rr, 0, Math.PI * 2);
                    ctx.strokeStyle = `rgba(${tStr}, ${ra})`;
                    ctx.lineWidth = 1;
                    ctx.stroke();
                }
            }

            const coreGrad = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, sz);
            coreGrad.addColorStop(0, 'rgba(255, 255, 255, 0.95)');
            coreGrad.addColorStop(0.3, `rgba(${colStr}, 0.9)`);
            coreGrad.addColorStop(1, `rgba(${colStr}, 0.3)`);
            ctx.beginPath();
            ctx.arc(p.x, p.y, sz, 0, Math.PI * 2);
            ctx.fillStyle = coreGrad;
            ctx.fill();

            // Label
            const label = node.label;
            ctx.font = '500 9px system-ui, sans-serif';
            const metrics = ctx.measureText(label);
            const labelX = p.x + sz + 6;
            const labelY = p.y + 3;
            const padding = 3;
            const pillW = metrics.width + padding * 2;
            const pillH = 14;

            ctx.fillStyle = isDark ? 'rgba(10, 15, 25, 0.5)' : 'rgba(255, 255, 255, 0.75)';
            ctx.beginPath();
            ctx.roundRect(labelX - padding, labelY - pillH / 2 - 1, pillW, pillH, 3);
            ctx.fill();

            ctx.fillStyle = isDark ? 'rgba(255, 255, 255, 0.75)' : 'rgba(30, 20, 60, 0.8)';
            ctx.fillText(label, labelX, labelY);
        });

        projectedNodesRef.current = storedNodes;

        // ===== ORBITAL RINGS =====
        [
            { r: 1.15, alpha: isDark ? 0.06 : 0.1, dash: [2, 8], w: 0.8, speedMul: 0.3 },
            { r: 1.25, alpha: isDark ? 0.04 : 0.07, dash: [1, 12], w: 0.5, speedMul: -0.2 },
            { r: 1.35, alpha: isDark ? 0.03 : 0.05, dash: [3, 15], w: 0.4, speedMul: 0.15 },
        ].forEach(ring => {
            ctx.save();
            ctx.translate(cx, cy);
            ctx.rotate(time * ring.speedMul);
            ctx.beginPath();
            ctx.ellipse(0, 0, radius * ring.r, radius * ring.r * 0.35, 0.3, 0, Math.PI * 2);
            ctx.strokeStyle = `rgba(${pStr}, ${ring.alpha})`;
            ctx.lineWidth = ring.w;
            ctx.setLineDash(ring.dash);
            ctx.stroke();
            ctx.setLineDash([]);
            ctx.restore();
        });

        // ===== SPECULAR HIGHLIGHT =====
        const specular = ctx.createRadialGradient(
            cx - radius * 0.3, cy - radius * 0.35, 0,
            cx - radius * 0.3, cy - radius * 0.35, radius * 0.5
        );
        specular.addColorStop(0, isDark ? 'rgba(255, 255, 255, 0.04)' : 'rgba(255, 255, 255, 0.2)');
        specular.addColorStop(1, 'transparent');
        ctx.beginPath();
        ctx.arc(cx, cy, radius, 0, Math.PI * 2);
        ctx.fillStyle = specular;
        ctx.fill();

        animId.current = requestAnimationFrame(draw);
    }, [isDark]);

    useEffect(() => {
        animId.current = requestAnimationFrame(draw);
        return () => { if (animId.current) cancelAnimationFrame(animId.current); };
    }, [draw]);

    return (
        <div className="relative w-full h-full flex items-center justify-center">
            <canvas
                ref={canvasRef}
                className="w-full h-full"
                style={{ maxWidth: 620, maxHeight: 620, cursor: 'grab' }}
                onMouseDown={handleMouseDown}
                onMouseMove={handleMouseMove}
                onMouseUp={handleMouseUp}
                onMouseLeave={handleMouseLeave}
                onTouchStart={handleTouchStart}
                onTouchMove={handleTouchMove}
                onTouchEnd={handleTouchEnd}
            />

            {/* Node Tooltip */}
            <AnimatePresence>
                {tooltip && (
                    <motion.div
                        key={tooltip.node.label}
                        initial={{ opacity: 0, scale: 0.85, y: 5 }}
                        animate={{ opacity: 1, scale: 1, y: 0 }}
                        exit={{ opacity: 0, scale: 0.85, y: 5 }}
                        transition={{ duration: 0.15 }}
                        className="absolute pointer-events-none z-20"
                        style={{
                            left: tooltip.x,
                            top: tooltip.y - 60,
                            transform: 'translateX(-50%)',
                        }}
                    >
                        <div className={`
              px-3 py-2 rounded-lg shadow-xl backdrop-blur-md border text-xs min-w-[140px]
              ${isDark
                                ? 'bg-gray-900/90 border-gray-700 text-gray-100'
                                : 'bg-white/95 border-gray-200 text-gray-800'
                            }
            `}>
                            <div className="font-semibold text-xs text-muted-foreground mb-1 flex justify-between items-center">
                                <span>Recent Check in {tooltip.node.label}</span>
                                <span className="text-[9px] opacity-70">{tooltip.node.timestamp}</span>
                            </div>

                            <div className="font-medium text-sm leading-tight mb-2">
                                "{tooltip.node.claim}"
                            </div>

                            <div className={`
                                inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide border
                                ${tooltip.node.verdict === 'verified' ? 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20' :
                                    tooltip.node.verdict === 'fake' ? 'bg-red-500/10 text-red-500 border-red-500/20' :
                                        'bg-amber-500/10 text-amber-500 border-amber-500/20'}
                            `}>
                                {tooltip.node.verdict === 'verified' && <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />}
                                {tooltip.node.verdict === 'fake' && <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
                                {tooltip.node.verdict === 'uncertain' && <span className="w-1.5 h-1.5 rounded-full bg-amber-500" />}
                                {tooltip.node.verdict?.toUpperCase()}
                                <span className="opacity-50 mx-0.5">|</span>
                                {tooltip.node.confidence}% CONFIDENCE
                            </div>
                            {/* Arrow */}
                            <div className={`absolute left-1/2 -translate-x-1/2 -bottom-1 w-2 h-2 rotate-45 border-r border-b 
                ${isDark ? 'bg-gray-900/90 border-gray-700' : 'bg-white/95 border-gray-200'}`}
                            />
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Status badge */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.5 }}
                className="absolute bottom-4 left-1/2 -translate-x-1/2 px-3 py-1.5 rounded-full bg-card/80 backdrop-blur-md border border-border text-xs font-medium text-muted-foreground flex items-center gap-2 shadow-lg"
            >
                <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500" />
                </span>
                3 threats flagged globally
            </motion.div>
        </div>
    );
}
