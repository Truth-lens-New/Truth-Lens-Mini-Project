"""
Wikidata Verifier

Verifies factual claims against Wikidata using SPARQL.
Phase 2B: Async implementation using httpx.
"""

import re
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class WikidataResult:
    """Result from Wikidata verification."""
    verified: Optional[bool]  # True, False, or None if can't verify
    actual_value: Optional[str]
    claimed_value: str
    entity_id: Optional[str]
    property_id: Optional[str]
    source: str = "Wikidata"
    reason: str = ""


class WikidataVerifier:
    """
    Verify factual claims against Wikidata (Async).
    
    Examples that can be verified:
    - "India's capital is Delhi" → Query P36 (capital) for Q668 (India)
    - "Modi was born in 1950" → Query P569 (birth date) for Modi entity
    
    Usage:
        verifier = WikidataVerifier()
        result = await verifier.quick_fact_check("India's capital is Mumbai")
    """
    
    WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
    WIKIDATA_API = "https://www.wikidata.org/w/api.php"
    
    # Common Wikidata property IDs
    PROPERTIES = {
        "capital": "P36",
        "capital of": "P36",
        "population": "P1082",
        "birth date": "P569",
        "born": "P569",
        "death date": "P570",
        "died": "P570",
        "head of state": "P35",
        "head of government": "P6",
        "prime minister": "P6",
        "president": "P35",
        "country": "P17",
        "located in": "P131",
        "location": "P131",
        "founder": "P112",
        "founded by": "P112",
        "ceo": "P169",
        "chief executive": "P169",
    }
    
    def __init__(self):
        # We use short timeouts for Wikidata to avoid blocking
        self.timeout = 10
    
    async def verify_claim(self, entity_name: str, property_name: str, 
                     claimed_value: str) -> WikidataResult:
        """
        Verify a factual claim against Wikidata (Async).
        
        Args:
            entity_name: The subject (e.g., "India")
            property_name: The property (e.g., "capital")
            claimed_value: What the claim says (e.g., "Mumbai")
        """
        # Step 1: Find entity ID
        entity_id = await self._find_entity(entity_name)
        if not entity_id:
            return WikidataResult(
                verified=None,
                actual_value=None,
                claimed_value=claimed_value,
                entity_id=None,
                property_id=None,
                reason=f"Entity '{entity_name}' not found in Wikidata"
            )
        
        # Step 2: Get property ID
        property_name_lower = property_name.lower().strip()
        property_id = self.PROPERTIES.get(property_name_lower)
        if not property_id:
            return WikidataResult(
                verified=None,
                actual_value=None,
                claimed_value=claimed_value,
                entity_id=entity_id,
                property_id=None,
                reason=f"Property '{property_name}' not supported"
            )
        
        # Step 3: Query actual value (SPARQL)
        actual_value = await self._get_property_value(entity_id, property_id)
        if not actual_value:
            return WikidataResult(
                verified=None,
                actual_value=None,
                claimed_value=claimed_value,
                entity_id=entity_id,
                property_id=property_id,
                reason="Property value not found in Wikidata"
            )
        
        # Step 4: Compare values
        verified = self._compare_values(claimed_value, actual_value)
        
        return WikidataResult(
            verified=verified,
            actual_value=actual_value,
            claimed_value=claimed_value,
            entity_id=entity_id,
            property_id=property_id,
            source=f"Wikidata {entity_id}",
            reason="Verified against Wikidata" if verified else f"Wikidata shows: {actual_value}"
        )
    
    async def _find_entity(self, name: str) -> Optional[str]:
        """Find Wikidata entity ID (Q-number) async."""
        params = {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
            "limit": 1
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.WIKIDATA_API, 
                    params=params, 
                    timeout=self.timeout,
                    headers={"User-Agent": "TruthLens/1.0"}
                )
                data = response.json()
                if data.get("search"):
                    return data["search"][0]["id"]
        except Exception as e:
            print(f"Wikidata entity search error: {e}")
        return None
    
    async def _get_property_value(self, entity_id: str, property_id: str) -> Optional[str]:
        """Get property value from Wikidata via SPARQL (Async)."""
        query = f"""
        SELECT ?valueLabel WHERE {{
            wd:{entity_id} wdt:{property_id} ?value.
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """
        
        try:
            # Execute SPARQL query via HTTP POST
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    self.WIKIDATA_ENDPOINT,
                    params={"query": query, "format": "json"},
                    headers={"Accept": "application/json", "User-Agent": "TruthLens/1.0"},
                    timeout=self.timeout
                )
                if response.status_code != 200:
                    return None
                    
                data = response.json()
                bindings = data.get("results", {}).get("bindings", [])
                if bindings:
                    return bindings[0]["valueLabel"]["value"]
        except Exception as e:
            print(f"SPARQL query error: {e}")
        return None
    
    def _compare_values(self, claimed: str, actual: str) -> bool:
        """Compare claimed value with actual value (fuzzy match)."""
        claimed_norm = claimed.lower().strip()
        actual_norm = actual.lower().strip()
        
        # Exact match
        if claimed_norm == actual_norm:
            return True
        
        # Partial match
        if claimed_norm in actual_norm or actual_norm in claimed_norm:
            return True
        
        # Handle variations
        if "delhi" in claimed_norm and "delhi" in actual_norm:
            return True
        
        return False
    
    async def quick_fact_check(self, claim_text: str) -> Optional[WikidataResult]:
        """
        Attempt to extract and verify a factual claim (Async).
        
        Returns None if pattern not recognized.
        """
        # Pattern: "X is the capital of Y"
        capital_match = re.search(
            r"(.+?)\s+is\s+the\s+capital\s+of\s+(.+?)[\.\?]?$",
            claim_text,
            re.IGNORECASE
        )
        if capital_match:
            claimed_capital = capital_match.group(1).strip()
            country = capital_match.group(2).strip()
            return await self.verify_claim(country, "capital", claimed_capital)
        
        # Pattern: "The capital of X is Y"
        capital_match2 = re.search(
            r"the\s+capital\s+of\s+(.+?)\s+is\s+(.+?)[\.\?]?$",
            claim_text,
            re.IGNORECASE
        )
        if capital_match2:
            country = capital_match2.group(1).strip()
            claimed_capital = capital_match2.group(2).strip()
            return await self.verify_claim(country, "capital", claimed_capital)
        
        # Simple Date check: "X born in YEAR"
        birth_match = re.search(
            r"(.+?)\s+was\s+born\s+in\s+(\d{4})",
            claim_text,
            re.IGNORECASE
        )
        if birth_match:
            person = birth_match.group(1).strip()
            year = birth_match.group(2)
            result = await self.verify_claim(person, "born", year)
            if result.actual_value and year in result.actual_value:
                result.verified = True
            return result
            
        return None


# Singleton instance
_verifier_instance: Optional[WikidataVerifier] = None


def get_wikidata_verifier() -> WikidataVerifier:
    """Get singleton instance of WikidataVerifier."""
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = WikidataVerifier()
    return _verifier_instance
