import { Github, Twitter, Linkedin } from 'lucide-react';

export function SiteFooter() {
    return (
        <footer className="bg-background pt-24 pb-12 border-t border-border">
            <div className="max-w-7xl mx-auto px-6">
                <div className="grid grid-cols-2 md:grid-cols-12 gap-12 mb-20">

                    {/* Brand */}
                    <div className="col-span-2 md:col-span-4 space-y-4">
                        <h3 className="text-2xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-primary to-accent">TruthLens</h3>
                        <p className="text-muted-foreground max-w-sm">
                            Restoring trust in digital media through advanced forensic AI and autonomous investigation agents.
                        </p>
                    </div>

                    {/* Links */}
                    <div className="col-span-1 md:col-span-2 space-y-4">
                        <h4 className="font-semibold text-foreground">Product</h4>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li><a href="#" className="hover:text-primary transition-colors">Features</a></li>
                            <li><a href="#" className="hover:text-primary transition-colors">API</a></li>
                            <li><a href="#" className="hover:text-primary transition-colors">Pricing</a></li>
                            <li><a href="#" className="hover:text-primary transition-colors">Changelog</a></li>
                        </ul>
                    </div>

                    <div className="col-span-1 md:col-span-2 space-y-4">
                        <h4 className="font-semibold text-foreground">Company</h4>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li><a href="#" className="hover:text-primary transition-colors">About</a></li>
                            <li><a href="#" className="hover:text-primary transition-colors">Blog</a></li>
                            <li><a href="#" className="hover:text-primary transition-colors">Careers</a></li>
                            <li><a href="#" className="hover:text-primary transition-colors">Contact</a></li>
                        </ul>
                    </div>

                    <div className="col-span-1 md:col-span-2 space-y-4">
                        <h4 className="font-semibold text-foreground">Legal</h4>
                        <ul className="space-y-2 text-sm text-muted-foreground">
                            <li><a href="#" className="hover:text-primary transition-colors">Privacy</a></li>
                            <li><a href="#" className="hover:text-primary transition-colors">Terms</a></li>
                            <li><a href="#" className="hover:text-primary transition-colors">Security</a></li>
                        </ul>
                    </div>

                    <div className="col-span-1 md:col-span-2 space-y-4">
                        <h4 className="font-semibold text-foreground">Social</h4>
                        <div className="flex gap-4">
                            <a href="#" className="p-2 rounded-full bg-secondary hover:bg-primary/10 hover:text-primary transition-colors">
                                <Twitter className="w-4 h-4" />
                            </a>
                            <a href="#" className="p-2 rounded-full bg-secondary hover:bg-primary/10 hover:text-primary transition-colors">
                                <Github className="w-4 h-4" />
                            </a>
                            <a href="#" className="p-2 rounded-full bg-secondary hover:bg-primary/10 hover:text-primary transition-colors">
                                <Linkedin className="w-4 h-4" />
                            </a>
                        </div>
                    </div>
                </div>

                <div className="flex flex-col md:flex-row justify-between items-center py-6 border-t border-border/50 text-sm text-muted-foreground">
                    <p>© 2026 TruthLens Inc. All rights reserved.</p>
                    <div className="flex items-center gap-2 mt-4 md:mt-0">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        <span>Systems Normal</span>
                    </div>
                </div>
            </div>
        </footer>
    );
}
