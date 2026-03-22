import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import Globe from 'react-globe.gl';
import type { GlobeMethods } from 'react-globe.gl';
import * as THREE from 'three';

// ====== DATA ======
interface CityNode {
    lat: number;
    lng: number;
    label: string;
    flagged?: boolean;
    size: number;
    claim: string;
    verdict: 'verified' | 'fake' | 'uncertain';
    confidence: number;
    timestamp: string;
}

const CITIES: CityNode[] = [
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

// Arc connections
const ARC_CONNECTIONS = [
    { from: 0, to: 1 }, { from: 1, to: 2 }, { from: 2, to: 4 },
    { from: 4, to: 7 }, { from: 3, to: 5 }, { from: 5, to: 8 },
    { from: 6, to: 0 }, { from: 8, to: 1 }, { from: 9, to: 2 },
    { from: 7, to: 3 }, { from: 0, to: 4 }, { from: 11, to: 7 },
    { from: 9, to: 0 }, { from: 11, to: 4 },
];

// Ring pulse data for flagged cities
const RINGS_DATA = CITIES
    .filter(c => c.flagged)
    .map(c => ({
        lat: c.lat,
        lng: c.lng,
        maxR: 5,
        propagationSpeed: 3,
        repeatPeriod: 1000,
    }));

// ====== COLORS ======
const THREAT_RED = '#ef4444';
// Cyan/teal accent matching 2D globe theme
const TECH_CYAN = '#22d3ee';

function getVerdictColor(verdict: string) {
    if (verdict === 'verified') return '#22c55e';
    if (verdict === 'fake') return THREAT_RED;
    return '#f59e0b';
}

// ====== COMPONENT ======
export function HeroGlobe3D() {
    const globeRef = useRef<GlobeMethods | undefined>(undefined);
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 0, height: 0 });
    const [globeReady, setGlobeReady] = useState(false);
    const overlayGroupRef = useRef<THREE.Group | null>(null);

    // ===== Responsive sizing =====
    useEffect(() => {
        const updateSize = () => {
            if (containerRef.current) {
                setDimensions({
                    width: containerRef.current.clientWidth,
                    height: containerRef.current.clientHeight,
                });
            }
        };
        updateSize();
        const observer = new ResizeObserver(updateSize);
        if (containerRef.current) observer.observe(containerRef.current);
        return () => observer.disconnect();
    }, []);

    // ===== Globe setup on ready — injects 3D overlay objects =====
    const handleGlobeReady = useCallback(() => {
        setGlobeReady(true);
        if (!globeRef.current) return;

        // Set initial POV
        globeRef.current.pointOfView({ lat: 20, lng: 30, altitude: 2.1 }, 0);

        // Auto-rotate
        const controls = globeRef.current.controls();
        if (controls) {
            controls.autoRotate = true;
            controls.autoRotateSpeed = 0.5;
            controls.enableZoom = false;
            controls.enablePan = false;
            controls.minPolarAngle = Math.PI * 0.3;
            controls.maxPolarAngle = Math.PI * 0.7;
        }

        const scene = globeRef.current.scene();
        if (!scene) return;

        // Remove default lights
        const lightsToRemove = scene.children.filter(
            (c: THREE.Object3D) => c instanceof THREE.Light
        );
        lightsToRemove.forEach((l: THREE.Object3D) => scene.remove(l));

        // ===== LIGHTING: natural sunlight + cool fill =====
        const ambient = new THREE.AmbientLight(0xffffff, 0.55);
        scene.add(ambient);

        const sunLight = new THREE.DirectionalLight(0xfff5e8, 1.3);
        sunLight.position.set(5, 3, 4);
        scene.add(sunLight);

        const fillLight = new THREE.DirectionalLight(0xc8d8ff, 0.3);
        fillLight.position.set(-4, -1, -3);
        scene.add(fillLight);

        const rimLight = new THREE.DirectionalLight(0xffcc77, 0.4);
        rimLight.position.set(-2, 2, -5);
        scene.add(rimLight);

        // ===== TECH OVERLAY GROUP (attached to globe so it rotates with it) =====
        // The globe mesh is the first Object3D child of the scene that's a Mesh
        const globeObj = scene.children.find(
            (c: THREE.Object3D) => c.type === 'Group' || c.type === 'Mesh'
        );
        const overlayParent = globeObj || scene;
        const overlayGroup = new THREE.Group();
        overlayGroupRef.current = overlayGroup;

        // Globe radius in three-globe is 100 units
        const R = 100;

        // --- 1) WIREFRAME SPHERE (dense lat/lng grid) ---
        const wireGeo = new THREE.SphereGeometry(R * 1.002, 48, 36);
        const wireMat = new THREE.MeshBasicMaterial({
            color: new THREE.Color(TECH_CYAN),
            wireframe: true,
            transparent: true,
            opacity: 0.06,
            depthWrite: false,
        });
        const wireframe = new THREE.Mesh(wireGeo, wireMat);
        overlayGroup.add(wireframe);

        // --- 2) BRIGHTER LAT/LNG GRID (major lines every 30°) ---
        const gridMaterial = new THREE.LineBasicMaterial({
            color: new THREE.Color(TECH_CYAN),
            transparent: true,
            opacity: 0.12,
            depthWrite: false,
        });

        // Latitude lines
        for (let lat = -60; lat <= 60; lat += 30) {
            const phi = (90 - lat) * Math.PI / 180;
            const pts: THREE.Vector3[] = [];
            for (let lng = 0; lng <= 360; lng += 3) {
                const theta = lng * Math.PI / 180;
                pts.push(new THREE.Vector3(
                    R * 1.003 * Math.sin(phi) * Math.cos(theta),
                    R * 1.003 * Math.cos(phi),
                    R * 1.003 * Math.sin(phi) * Math.sin(theta),
                ));
            }
            const geo = new THREE.BufferGeometry().setFromPoints(pts);
            overlayGroup.add(new THREE.Line(geo, gridMaterial));
        }

        // Longitude lines
        for (let lng = 0; lng < 360; lng += 30) {
            const theta = lng * Math.PI / 180;
            const pts: THREE.Vector3[] = [];
            for (let lat = -90; lat <= 90; lat += 3) {
                const phi = (90 - lat) * Math.PI / 180;
                pts.push(new THREE.Vector3(
                    R * 1.003 * Math.sin(phi) * Math.cos(theta),
                    R * 1.003 * Math.cos(phi),
                    R * 1.003 * Math.sin(phi) * Math.sin(theta),
                ));
            }
            const geo = new THREE.BufferGeometry().setFromPoints(pts);
            overlayGroup.add(new THREE.Line(geo, gridMaterial));
        }

        // --- 3) EDGE GLOW RING (bright circle at equator-ish) ---
        const glowRingGeo = new THREE.RingGeometry(R * 1.04, R * 1.08, 128);
        const glowRingMat = new THREE.MeshBasicMaterial({
            color: new THREE.Color(TECH_CYAN),
            transparent: true,
            opacity: 0.05,
            side: THREE.DoubleSide,
            depthWrite: false,
        });
        const glowRing = new THREE.Mesh(glowRingGeo, glowRingMat);
        glowRing.rotation.x = Math.PI / 2;
        overlayGroup.add(glowRing);

        overlayParent.add(overlayGroup);

        // --- 4) ORBITAL RINGS (not attached to globe, independent rotation) ---
        const orbitalGroup = new THREE.Group();

        const orbitConfigs = [
            { radius: R * 1.2, tilt: 0.35, opacity: 0.07, segments: 256 },
            { radius: R * 1.35, tilt: -0.5, opacity: 0.04, segments: 256 },
            { radius: R * 1.5, tilt: 0.8, opacity: 0.03, segments: 256 },
        ];

        orbitConfigs.forEach(cfg => {
            const pts: THREE.Vector3[] = [];
            for (let i = 0; i <= cfg.segments; i++) {
                const angle = (i / cfg.segments) * Math.PI * 2;
                pts.push(new THREE.Vector3(
                    cfg.radius * Math.cos(angle),
                    cfg.radius * Math.sin(angle) * 0.35,
                    cfg.radius * Math.sin(angle) * Math.cos(cfg.tilt),
                ));
            }
            const geo = new THREE.BufferGeometry().setFromPoints(pts);
            const mat = new THREE.LineBasicMaterial({
                color: new THREE.Color(TECH_CYAN),
                transparent: true,
                opacity: cfg.opacity,
                depthWrite: false,
            });
            const line = new THREE.Line(geo, mat);
            line.rotation.x = cfg.tilt;
            orbitalGroup.add(line);
        });

        scene.add(orbitalGroup);

        // Slow rotation for orbital rings
        const animateOrbits = () => {
            orbitalGroup.rotation.y += 0.001;
            requestAnimationFrame(animateOrbits);
        };
        animateOrbits();

    }, []);

    // ===== Arc data — smooth flowing arcs =====
    const arcsData = useMemo(() => {
        return ARC_CONNECTIONS.map(c => {
            const from = CITIES[c.from];
            const to = CITIES[c.to];
            const isFlagged = from.flagged || to.flagged;
            return {
                startLat: from.lat,
                startLng: from.lng,
                endLat: to.lat,
                endLng: to.lng,
                color: isFlagged
                    ? [`rgba(239, 68, 68, 0.7)`, `rgba(255, 120, 80, 0.2)`]
                    : [`rgba(34, 211, 238, 0.5)`, `rgba(34, 211, 238, 0.12)`],
                stroke: isFlagged ? 0.5 : 0.3,
            };
        });
    }, []);

    // ===== Point label (tooltip content) =====
    const pointLabel = useCallback((d: object) => {
        const city = d as CityNode;
        const verdictColor = getVerdictColor(city.verdict);
        return `
            <div style="
                background: rgba(8, 10, 18, 0.94);
                backdrop-filter: blur(20px);
                border: 1px solid rgba(34, 211, 238, 0.2);
                border-radius: 12px;
                padding: 12px 16px;
                min-width: 210px;
                font-family: system-ui, -apple-system, sans-serif;
                box-shadow: 0 12px 40px rgba(0,0,0,0.5), 0 0 24px rgba(34,211,238,0.08);
            ">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <span style="color: ${TECH_CYAN}; font-size:12px; font-weight:700; letter-spacing:0.5px;">
                        ${city.label}
                    </span>
                    <span style="color: rgba(255,255,255,0.35); font-size:9px;">
                        ${city.timestamp}
                    </span>
                </div>
                <div style="color: rgba(255,255,255,0.9); font-size:13px; font-weight:500; line-height:1.4; margin-bottom:8px;">
                    "${city.claim}"
                </div>
                <div style="
                    display:inline-flex; align-items:center; gap:6px;
                    background: ${verdictColor}18;
                    border: 1px solid ${verdictColor}30;
                    padding: 3px 10px;
                    border-radius: 20px;
                ">
                    <span style="width:6px;height:6px;border-radius:50%;background:${verdictColor};display:inline-block;"></span>
                    <span style="color:${verdictColor}; font-size:10px; font-weight:700; letter-spacing:0.8px;">
                        ${city.verdict.toUpperCase()}
                    </span>
                    <span style="color:rgba(255,255,255,0.25); font-size:10px;">|</span>
                    <span style="color:rgba(255,255,255,0.55); font-size:10px; font-weight:600;">
                        ${city.confidence}%
                    </span>
                </div>
            </div>
        `;
    }, []);

    // ===== Custom HTML elements for city markers =====
    const cityHtmlElement = useCallback((d: object) => {
        const city = d as CityNode;
        const color = city.flagged ? THREAT_RED
            : city.verdict === 'verified' ? '#22c55e'
                : city.verdict === 'uncertain' ? '#f59e0b'
                    : TECH_CYAN;

        const el = document.createElement('div');
        el.style.cssText = `
            position: relative;
            display: flex;
            flex-direction: column;
            align-items: center;
            pointer-events: none;
        `;

        // Glowing dot
        const dot = document.createElement('div');
        const size = city.flagged ? 10 : 7;
        dot.style.cssText = `
            width: ${size}px;
            height: ${size}px;
            border-radius: 50%;
            background: ${color};
            box-shadow: 0 0 ${size * 2}px ${color}, 0 0 ${size * 4}px ${color}44;
            ${city.flagged ? 'animation: globePulse 1.5s ease-in-out infinite;' : ''}
        `;
        el.appendChild(dot);

        // City label
        const label = document.createElement('div');
        label.style.cssText = `
            margin-top: 4px;
            font-size: 10px;
            font-weight: 600;
            font-family: system-ui, -apple-system, sans-serif;
            color: rgba(255, 255, 255, 0.85);
            text-shadow: 0 1px 4px rgba(0,0,0,0.8), 0 0 8px rgba(0,0,0,0.5);
            white-space: nowrap;
            letter-spacing: 0.3px;
        `;
        label.textContent = city.label;
        el.appendChild(label);

        return el;
    }, []);

    return (
        <div ref={containerRef} className="relative w-full h-full flex items-center justify-center">
            {/* Inject pulse animation keyframes */}
            <style>{`
                @keyframes globePulse {
                    0%, 100% { transform: scale(1); opacity: 1; }
                    50% { transform: scale(1.6); opacity: 0.7; }
                }
            `}</style>

            {/* Globe */}
            <div
                className="transition-opacity duration-1000"
                style={{ opacity: globeReady ? 1 : 0 }}
            >
                {dimensions.width > 0 && (
                    <Globe
                        ref={globeRef}
                        width={dimensions.width}
                        height={dimensions.height}
                        backgroundColor="rgba(0,0,0,0)"

                        // Real Earth texture — blue marble
                        globeImageUrl="//unpkg.com/three-globe/example/img/earth-blue-marble.jpg"
                        bumpImageUrl="//unpkg.com/three-globe/example/img/earth-topology.png"

                        // Warm/cyan atmosphere rim glow
                        showAtmosphere={true}
                        atmosphereColor={TECH_CYAN}
                        atmosphereAltitude={0.15}

                        // Show built-in graticules as base grid
                        showGraticules={true}

                        // HTML city markers with glowing dots + labels
                        htmlElementsData={CITIES}
                        htmlLat="lat"
                        htmlLng="lng"
                        htmlAltitude={0.07}
                        htmlElement={cityHtmlElement}

                        // Glowing city blobs
                        pointsData={CITIES}
                        pointLat="lat"
                        pointLng="lng"
                        pointColor={(d: object) => {
                            const city = d as CityNode;
                            if (city.flagged) return THREAT_RED;
                            if (city.verdict === 'verified') return '#22c55e';
                            if (city.verdict === 'uncertain') return '#f59e0b';
                            return TECH_CYAN;
                        }}
                        pointAltitude={0.06}
                        pointRadius={(d: object) => (d as CityNode).size * 0.45}
                        pointResolution={12}
                        pointLabel={pointLabel}

                        // Smooth arcs — cyan themed
                        arcsData={arcsData}
                        arcStartLat="startLat"
                        arcStartLng="startLng"
                        arcEndLat="endLat"
                        arcEndLng="endLng"
                        arcColor="color"
                        arcStroke="stroke"
                        arcAltitudeAutoScale={0.35}
                        arcDashLength={0.9}
                        arcDashGap={0.15}
                        arcDashAnimateTime={4000}

                        // Pulse rings on flagged cities
                        ringsData={RINGS_DATA}
                        ringLat="lat"
                        ringLng="lng"
                        ringMaxRadius="maxR"
                        ringPropagationSpeed="propagationSpeed"
                        ringRepeatPeriod="repeatPeriod"
                        ringColor={() => (t: number) =>
                            `rgba(239, 68, 68, ${Math.max(0, 0.6 - t * 0.6)})`
                        }

                        onGlobeReady={handleGlobeReady}
                        enablePointerInteraction={true}
                    />
                )}
            </div>

            {/* Loading shimmer */}
            <AnimatePresence>
                {!globeReady && (
                    <motion.div
                        initial={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        transition={{ duration: 0.5 }}
                        className="absolute inset-0 flex items-center justify-center"
                    >
                        <div className="w-48 h-48 rounded-full border border-cyan-500/20 animate-pulse"
                            style={{
                                background: 'radial-gradient(circle, rgba(34,211,238,0.06) 0%, transparent 70%)',
                                boxShadow: '0 0 60px rgba(34,211,238,0.08)',
                            }}
                        />
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Status badge */}
            <motion.div
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: globeReady ? 1 : 0, y: globeReady ? 0 : 10 }}
                transition={{ delay: 1, duration: 0.5 }}
                className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20"
            >
                <div className="px-4 py-2 rounded-full backdrop-blur-xl border text-xs font-medium flex items-center gap-2.5 shadow-lg"
                    style={{
                        background: 'rgba(8, 10, 18, 0.75)',
                        borderColor: 'rgba(34, 211, 238, 0.15)',
                        color: 'rgba(200, 235, 240, 0.85)',
                    }}
                >
                    <span className="relative flex h-2 w-2">
                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-75"
                            style={{ backgroundColor: THREAT_RED }}
                        />
                        <span className="relative inline-flex rounded-full h-2 w-2"
                            style={{ backgroundColor: THREAT_RED }}
                        />
                    </span>
                    3 threats flagged globally
                    <span className="w-px h-3 bg-white/10" />
                    <span className="text-white/40">12 nodes active</span>
                </div>
            </motion.div>
        </div>
    );
}
