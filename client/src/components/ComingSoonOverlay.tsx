interface ComingSoonOverlayProps {
    children: React.ReactNode;
    title?: string;
}

export function ComingSoonOverlay({ children, title = "Coming Soon" }: ComingSoonOverlayProps) {
    return (
        <div className="relative min-h-screen">
            {/* Blurred content behind */}
            <div className="blur-sm opacity-30 pointer-events-none">
                {children}
            </div>

            {/* Overlay */}
            <div className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm flex items-center justify-center">
                <div className="text-center">
                    <div className="w-16 h-16 mx-auto mb-6 rounded-full border-2 border-[#00FFC3] flex items-center justify-center">
                        <svg className="w-8 h-8 text-[#00FFC3]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                        </svg>
                    </div>
                    <h1 className="text-3xl font-semibold text-white mb-2">{title}</h1>
                    <p className="text-gray-400 text-sm">This feature is under development</p>
                </div>
            </div>
        </div>
    );
}
