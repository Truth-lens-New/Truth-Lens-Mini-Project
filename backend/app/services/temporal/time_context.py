
"""
Time Context Service.

Analyzes the temporal aspect of claims (freshness, stability).
Did this happen yesterday? Or 10 years ago?
"""

from datetime import datetime, timedelta
from typing import List, Optional
import re

from app.models.domain import TemporalContext, TemporalState
from app.models.evidence import VerifiedClaim

class TimeContextService:
    
    def analyze(self, claim: VerifiedClaim) -> TemporalContext:
        """
        Analyze temporal context of a verified claim.
        """
        now = datetime.now()
        
        # 1. Extract dates from evidence
        evidence_dates = self._extract_dates(claim)
        
        # 2. Calculate Freshness (how new is the latest evidence)
        if not evidence_dates:
            return TemporalContext(state=TemporalState.UNKNOWN)
            
        newest_date = max(evidence_dates)
        oldest_date = min(evidence_dates)
        
        age_hours = (now - newest_date).total_seconds() / 3600
        
        # 3. Determine State
        state = TemporalState.UNKNOWN
        stability = 0.5
        
        if age_hours < 24:
            state = TemporalState.DEVELOPING
            stability = 0.2  # Very unstable
        elif age_hours > 24 * 365:
            state = TemporalState.HISTORICAL
            stability = 1.0  # History doesn't change much
        elif age_hours > 24 * 30:
            state = TemporalState.STABILIZED
            stability = 0.9
        else:
            state = TemporalState.CONTESTED # Recent but not breaking
            stability = 0.6
            
        return TemporalContext(
            first_seen=oldest_date,
            last_updated=newest_date,
            evidence_freshness_hours=age_hours,
            state=state,
            stability_score=stability
        )
        
    def _extract_dates(self, claim: VerifiedClaim) -> List[datetime]:
        """Attempt to extract dates from evidence text snippets."""
        dates = []
        # Regex for YYYY-MM-DD or standard formats
        # This is a basic implementation. Ideally uses dateparser lib.
        date_pattern = r'(\d{4}-\d{2}-\d{2})'
        
        for evidence in claim.evidence_items:
            matches = re.findall(date_pattern, evidence.text)
            for m in matches:
                try:
                    dates.append(datetime.strptime(m, "%Y-%m-%d"))
                except ValueError:
                    pass
                    
        # If no dates found, check if "published_date" metadata exists (mock)
        if not dates:
             # Fallback: assume some evidence is recent if it mentions "today" or "yesterday"
             for evidence in claim.evidence_items:
                 if "today" in evidence.text.lower():
                     dates.append(datetime.now())
                 elif "yesterday" in evidence.text.lower():
                     dates.append(datetime.now() - timedelta(days=1))
        
        return dates

def get_time_context_service() -> TimeContextService:
    return TimeContextService()
