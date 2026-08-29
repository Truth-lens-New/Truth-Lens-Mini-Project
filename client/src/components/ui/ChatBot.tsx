import React, { useState, useRef, useEffect } from 'react';
import { X, Send } from 'lucide-react';
import { sendChatMessage, ChatMessage } from '../../lib/api';

export function ChatBot() {
    const [isOpen, setIsOpen] = useState(false);
    const [messages, setMessages] = useState<ChatMessage[]>([]);
    const [input, setInput] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    useEffect(() => {
        if (isOpen) scrollToBottom();
    }, [messages, isLoading, isOpen]);

    // Simple Markdown Link Parser
    const renderMessageContent = (text: string) => {
        const linkRegex = /\[([^\]]+)\]\(([^)]+)\)/g;
        const parts = [];
        let lastIndex = 0;
        let match;

        while ((match = linkRegex.exec(text)) !== null) {
            if (match.index > lastIndex) {
                parts.push(text.substring(lastIndex, match.index));
            }
            parts.push(
                <a key={match.index} href={match[2]} target="_blank" rel="noopener noreferrer" className="text-blue-400 dark:text-blue-300 hover:text-blue-500 font-semibold underline decoration-2 underline-offset-2 transition-colors">
                    {match[1]}
                </a>
            );
            lastIndex = linkRegex.lastIndex;
        }

        if (lastIndex < text.length) {
            parts.push(text.substring(lastIndex));
        }

        return parts.length > 0 ? parts : text;
    };

    const handleSend = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!input.trim() || isLoading) return;

        const userMsg = input.trim();
        setInput('');
        const newMessages: ChatMessage[] = [...messages, { role: 'user', content: userMsg }];
        setMessages(newMessages);
        setIsLoading(true);

        try {
            const res = await sendChatMessage(newMessages);
            setMessages(prev => [...prev, { role: 'model', content: res.response }]);
        } catch (err: any) {
            setMessages(prev => [...prev, { role: 'model', content: "Oops! I encountered a network error trying to connect to TruthLens servers." }]);
        } finally {
            setIsLoading(false);
            // Optional: re-focus input if we want, but letting the user tap handles mobile better
        }
    };

    return (
        <>
            <div className="fixed bottom-6 right-6 z-50">
                {!isOpen && (
                    <button
                        onClick={() => setIsOpen(true)}
                        className="flex items-center justify-center w-16 h-16 bg-primary text-primary-foreground rounded-full shadow-lg hover:bg-primary/90 transition-transform transform hover:scale-110 active:scale-95"
                        aria-label="Open Chatbot"
                    >
                        <span className="text-3xl drop-shadow-md">🦉</span>
                    </button>
                )}

                {isOpen && (
                    <div className="flex flex-col w-[360px] h-[500px] max-h-[80vh] bg-card text-card-foreground border rounded-2xl shadow-2xl overflow-hidden animate-in slide-in-from-bottom-5 fade-in duration-300">
                        {/* Header */}
                        <div className="flex items-center justify-between px-4 py-3 border-b bg-muted/30">
                            <div className="flex items-center gap-2">
                                <span className="text-xl">🦉</span>
                                <h3 className="font-semibold text-sm">Lensy</h3>
                            </div>
                            <button onClick={() => setIsOpen(false)} className="p-1 rounded-md hover:bg-muted text-muted-foreground transition-colors">
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Messages Area */}
                        {/* Messages Area */}
                        <div className="flex-1 p-4 overflow-y-auto space-y-4 bg-background/50">
                            {messages.length === 0 && (
                                <div className="text-center text-muted-foreground mt-10">
                                    <div className="w-16 h-16 mx-auto mb-3 bg-primary/10 rounded-full flex items-center justify-center text-4xl shadow-sm">
                                        🦉
                                    </div>
                                    <p className="font-medium text-foreground">Hoot hoot!</p>
                                    <p className="text-sm mt-1">I'm Lensy. Try asking me where to check a video! ✨</p>
                                </div>
                            )}
                            {messages.map((msg, idx) => (
                                <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[85%] rounded-2xl px-4 py-2 text-sm shadow-sm leading-relaxed ${msg.role === 'user' ? 'bg-primary text-primary-foreground rounded-tr-sm' : 'bg-muted rounded-tl-sm border dark:border-white/10'}`}>
                                        {renderMessageContent(msg.content)}
                                    </div>
                                </div>
                            ))}
                            {isLoading && (
                                <div className="flex justify-start">
                                    <div className="bg-muted rounded-2xl rounded-tl-sm px-4 py-3 flex gap-1 items-center shadow-sm">
                                        <span className="w-1.5 h-1.5 rounded-full bg-foreground/40 animate-bounce" style={{ animationDelay: '0ms' }} />
                                        <span className="w-1.5 h-1.5 rounded-full bg-foreground/40 animate-bounce" style={{ animationDelay: '150ms' }} />
                                        <span className="w-1.5 h-1.5 rounded-full bg-foreground/40 animate-bounce" style={{ animationDelay: '300ms' }} />
                                    </div>
                                </div>
                            )}
                            <div ref={messagesEndRef} />
                        </div>

                        {/* Input Form */}
                        <form onSubmit={handleSend} className="p-3 border-t bg-card flex items-center gap-2">
                            <input
                                type="text"
                                placeholder="Ask me anything..."
                                className="flex-1 bg-muted/60 rounded-full px-4 py-2 text-sm outline-none focus:ring-2 focus:ring-primary/50 transition-all border-transparent"
                                value={input}
                                onChange={e => setInput(e.target.value)}
                            />
                            <button
                                type="submit"
                                disabled={!input.trim() || isLoading}
                                className="p-2 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-transform transform active:scale-95"
                                aria-label="Send message"
                            >
                                <Send className="w-4 h-4" />
                            </button>
                        </form>
                    </div>
                )}
            </div>
        </>
    );
}
