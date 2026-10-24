import type { V3VerifiedClaim } from '../lib/api';

/**
 * Lets the user switch between ALL claims found in the input.
 * Before this component the page stored every verified claim but only ever
 * rendered verifiedClaims[0], so "Investigated 2 claim(s)" showed one claim.
 *
 * Renders nothing when there is only one claim.
 */
interface ClaimTabsProps {
    claims: V3VerifiedClaim[];
    activeIndex: number;
    onSelect: (index: number) => void;
}

const VERDICT_DOT: Record<V3VerifiedClaim['verdict'], string> = {
    verified_true: 'bg-emerald-500',
    verified_false: 'bg-red-500',
    disputed: 'bg-amber-500',
    unverified: 'bg-slate-400',
    insufficient_evidence: 'bg-yellow-500',
    not_checkable: 'bg-gray-500',
    developing: 'bg-orange-500',
};

const VERDICT_LABEL: Record<V3VerifiedClaim['verdict'], string> = {
    verified_true: 'True',
    verified_false: 'False',
    disputed: 'Disputed',
    unverified: 'Unverified',
    insufficient_evidence: 'Insufficient evidence',
    not_checkable: 'Not checkable',
    developing: 'Developing',
};

const truncate = (text: string, max = 70) =>
    text.length > max ? `${text.slice(0, max - 1).trimEnd()}\u2026` : text;

export function ClaimTabs({ claims, activeIndex, onSelect }: ClaimTabsProps) {
    if (claims.length < 2) return null;

    return (
        <div
            role="tablist"
            aria-label="Investigated claims"
            className="flex gap-2 overflow-x-auto pb-2"
        >
            {claims.map((claim, i) => {
                const active = i === activeIndex;
                return (
                    <button
                        key={`${i}-${claim.original_text}`}
                        role="tab"
                        aria-selected={active}
                        onClick={() => onSelect(i)}
                        title={claim.original_text}
                        className={`flex shrink-0 items-center gap-2 rounded-full border px-4 py-2 text-left text-sm transition-all ${
                            active
                                ? 'border-border bg-muted text-foreground'
                                : 'border-border/50 text-muted-foreground hover:bg-muted/60 hover:text-foreground'
                        }`}
                    >
                        <span
                            className={`h-2 w-2 shrink-0 rounded-full ${VERDICT_DOT[claim.verdict] ?? 'bg-slate-400'}`}
                            aria-hidden="true"
                        />
                        <span className="max-w-[16rem] truncate">{truncate(claim.original_text)}</span>
                        <span className="shrink-0 text-xs opacity-60">
                            {VERDICT_LABEL[claim.verdict] ?? claim.verdict}
                        </span>
                    </button>
                );
            })}
        </div>
    );
}

export default ClaimTabs;
