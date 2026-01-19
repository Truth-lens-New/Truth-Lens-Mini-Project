const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface User {
    id: string;
    email: string;
}

export interface AuthResponse {
    access_token: string;
    token_type: string;
    user?: User;
}

export interface AnalyzeRequest {
    text?: string;
    url?: string;
    user_id?: string;
}

export interface DomainTrust {
    domain: string | null;
    score: string | number;
}

export interface FactCheck {
    found: boolean;
    rating?: string | null;
    summary?: string | null;
    url?: string;
}

export interface EvidenceItem {
    title: string | null;
    description?: string | null;
    url: string | null;
    source: string | null;
    domain?: string | null;
    stance: string;
    snippet?: string;
}

export interface AnalyzeResponse {
    id?: string;
    claim?: string;
    verdict: string;
    confidence: string;
    explanation: string;
    domain_trust: DomainTrust;
    factcheck: FactCheck;
    evidence: EvidenceItem[];
    claims?: string[];
    stance_summary?: { supports: number; refutes: number; discuss: number; unrelated: number };
    created_at?: string;
}

export interface HistoryItem {
    id: number;
    claim: string;
    verdict: string;
    confidence: string;
    explanation?: string;
    created_at: string;
}

// Helper for authorized fetch
async function authFetch(url: string, options: RequestInit = {}) {
    const token = localStorage.getItem('token');
    const headers = {
        'Content-Type': 'application/json',
        ...options.headers,
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    } as HeadersInit;

    const response = await fetch(`${API_URL}${url}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        logout();
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'API request failed');
    }

    return response.json();
}

// --- Auth ---

export async function login(data: { email?: string; password?: string }): Promise<AuthResponse> {
    const response = await fetch(`${API_URL}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email: data.email, password: data.password }),
    });

    if (!response.ok) {
        throw new Error('Login failed');
    }

    const result = await response.json();
    localStorage.setItem('token', result.access_token);
    return result;
}

export async function register(data: { email: string; password?: string }): Promise<User> {
    return authFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export function logout() {
    localStorage.removeItem('token');
}

export function isAuthenticated(): boolean {
    return !!localStorage.getItem('token');
}

// --- Analysis ---

export async function analyzeClaim(data: AnalyzeRequest): Promise<AnalyzeResponse> {
    return authFetch('/api/v1/analyze', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

export async function extractClaim(data: { text?: string; url?: string }): Promise<{ primary_claim: string; claim?: string }> {
    return authFetch('/api/v1/extract-claim', {
        method: 'POST',
        body: JSON.stringify(data),
    });
}

// --- History ---

export async function getHistory(): Promise<HistoryItem[]> {
    return authFetch('/api/v1/history');
}

export async function deleteHistoryItem(id: number): Promise<void> {
    return authFetch(`/api/v1/history/${id}`, {
        method: 'DELETE',
    });
}

export async function clearAllHistory(): Promise<void> {
    return authFetch('/api/v1/history', {
        method: 'DELETE',
    });
}

// --- Media Analysis (Deepfake Detection) ---

export interface MediaAnalysisResponse {
    verdict: 'FAKE' | 'REAL';
    confidence: number;
    confidence_level: 'high' | 'medium' | 'low';
    real_probability: number;
    fake_probability: number;
    model: string;
    metadata?: Record<string, string | boolean>;
    evidence?: string[];
    heatmap?: string;
}

export async function analyzeMedia(file: File): Promise<MediaAnalysisResponse> {
    const token = localStorage.getItem('token');
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_URL}/api/v1/analyze-media`, {
        method: 'POST',
        headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: formData,
    });

    if (response.status === 401) {
        logout();
        window.location.href = '/login';
        throw new Error('Unauthorized');
    }

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Media analysis failed');
    }

    return response.json();
}
