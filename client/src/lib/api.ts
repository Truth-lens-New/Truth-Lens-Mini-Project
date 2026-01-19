const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:7000';

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

// === V3 API (TruthLens Investigation Pipeline) ===

export interface V3InvestigateRequest {
    text: string;
}

export interface V3EvidenceItem {
    text_preview: string;
    source_url?: string;
    source_domain: string;
    source_type: string;
    stance: 'supports' | 'refutes' | 'neutral';
    stance_confidence?: number;
    trust_score: number;
}

export interface V3VerifiedClaim {
    original_text: string;
    claim_type: string;
    verdict: 'verified_true' | 'verified_false' | 'disputed' | 'unverified' | 'insufficient_evidence' | 'not_checkable';
    confidence: number;
    evidence_summary: string;
    evidence_count: number;
    sources_checked: number;
    investigation_time_ms: number;
    evidence: V3EvidenceItem[];
}

export interface V3InvestigateResponse {
    success: boolean;
    verified_claims: V3VerifiedClaim[];
    metadata: {
        input_type: string;
        total_processing_time_ms: number;
        claims_found: number;
        claims_verified: number;
        investigated_at: string;
    };
}

export interface V3AnalyzeResponse {
    input_type: string;
    claims: {
        original_text: string;
        claim_type: string;
        type_confidence: number;
        is_checkable: boolean;
        evidence_strategy: string;
        status: string;
    }[];
    total_claims: number;
    checkable_claims: number;
}

/**
 * Analyze text using V3 pipeline - extracts and classifies claims
 */
export async function analyzeClaimV3(text: string): Promise<V3AnalyzeResponse> {
    const response = await fetch(`${API_URL}/api/v3/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
    });

    if (!response.ok) {
        throw new Error('Analysis failed');
    }

    return response.json();
}

/**
 * Investigate a claim using V3 pipeline - full evidence gathering and verdict
 */
export async function investigateClaim(content: string, inputType: 'text' | 'url' = 'text'): Promise<V3InvestigateResponse> {
    const token = localStorage.getItem('token');
    const headers: HeadersInit = {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
    };

    const response = await fetch(`${API_URL}/api/v3/investigate`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ content, input_type: inputType }),
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        // Handle Pydantic validation errors (array of objects) and string errors
        let errorMessage = 'Investigation failed';
        if (Array.isArray(errorData.detail)) {
            errorMessage = errorData.detail.map((e: any) => e.msg || e.message || JSON.stringify(e)).join(', ');
        } else if (typeof errorData.detail === 'string') {
            errorMessage = errorData.detail;
        }
        throw new Error(errorMessage);
    }

    return response.json();
}

/**
 * Check V3 API health
 */
export async function checkV3Health(): Promise<{ status: string; version: string; phase: number }> {
    const response = await fetch(`${API_URL}/api/v3/health`);
    return response.json();
}
