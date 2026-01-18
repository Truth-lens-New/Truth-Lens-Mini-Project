"""
Wikidata Verifier

Verifies factual claims against Wikidata using SPARQL.
Phase 2A: Synchronous implementation.
"""

import re
import httpx
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

try:
    from SPARQLWrapper import SPARQLWrapper, JSON
    SPARQL_AVAILABLE = True
except ImportError:
    SPARQL_AVAILABLE = False
    print("Warning: SPARQLWrapper not installed. Run: pip install SPARQLWrapper")


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
    Verify factual claims against Wikidata.
    
    Examples that can be verified:
    - "India's capital is Delhi" → Query P36 (capital) for Q668 (India)
    - "Modi was born in 1950" → Query P569 (birth date) for Modi entity
    - "The Eiffel Tower is in Paris" → Query P131 (located in)
    
    Usage:
        verifier = WikidataVerifier()
        result = verifier.quick_fact_check("India's capital is Mumbai")
        # Returns WikidataResult(verified=False, actual_value="New Delhi", ...)
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
        "currency": "P38",
        "official language": "P37",
        "continent": "P30",
        "area": "P2046",
    }
    
    def __init__(self):
        if SPARQL_AVAILABLE:
            self.sparql = SPARQLWrapper(self.WIKIDATA_ENDPOINT)
            self.sparql.setReturnFormat(JSON)
            self.sparql.addCustomHttpHeader("User-Agent", "TruthLens/1.0")
        else:
            self.sparql = None
    
    def verify_claim(self, entity_name: str, property_name: str, 
                     claimed_value: str) -> WikidataResult:
        """
        Verify a factual claim against Wikidata.
        
        Args:
            entity_name: The subject (e.g., "India")
            property_name: The property (e.g., "capital")
            claimed_value: What the claim says (e.g., "Mumbai")
            
        Returns:
            WikidataResult with verification status
        """
        if not SPARQL_AVAILABLE:
            return WikidataResult(
                verified=None,
                actual_value=None,
                claimed_value=claimed_value,
                entity_id=None,
                property_id=None,
                reason="SPARQLWrapper not installed"
            )
        
        # Step 1: Find entity ID
        entity_id = self._find_entity(entity_name)
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
        
        # Step 3: Query actual value
        actual_value = self._get_property_value(entity_id, property_id)
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
    
    def _find_entity(self, name: str) -> Optional[str]:
        """Find Wikidata entity ID (Q-number) for a name."""
        params = {
            "action": "wbsearchentities",
            "search": name,
            "language": "en",
            "format": "json",
            "limit": 1
        }
        
        try:
            response = httpx.get(
                self.WIKIDATA_API, 
                params=params, 
                timeout=10,
                headers={"User-Agent": "TruthLens/1.0"}
            )
            data = response.json()
            if data.get("search"):
                return data["search"][0]["id"]
        except Exception as e:
            print(f"Wikidata entity search error: {e}")
        return None
    
    def _get_property_value(self, entity_id: str, property_id: str) -> Optional[str]:
        """Get property value from Wikidata via SPARQL."""
        query = f"""
        SELECT ?valueLabel WHERE {{
            wd:{entity_id} wdt:{property_id} ?value.
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
        }}
        LIMIT 1
        """
        
        try:
            self.sparql.setQuery(query)
            results = self.sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])
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
        
        # Partial match (one contains the other)
        if claimed_norm in actual_norm or actual_norm in claimed_norm:
            return True
        
        # Handle common variations
        # "New Delhi" vs "Delhi"
        if "delhi" in claimed_norm and "delhi" in actual_norm:
            return True
        
        return False
    
    def quick_fact_check(self, claim_text: str) -> Optional[WikidataResult]:
        """
        Attempt to extract and verify a factual claim.
        
        Tries to parse common patterns like:
        - "X is the capital of Y"
        - "X was born in YEAR"
        - "X is located in Y"
        
        Returns None if pattern not recognized.
        """
        claim_lower = claim_text.lower()
        
        # Pattern: "X is the capital of Y"
        capital_match = re.search(
            r"(.+?)\s+is\s+the\s+capital\s+of\s+(.+?)[\.\?]?$",
            claim_text,
            re.IGNORECASE
        )
        if capital_match:
            claimed_capital = capital_match.group(1).strip()
            country = capital_match.group(2).strip()
            return self.verify_claim(country, "capital", claimed_capital)
        
        # Pattern: "The capital of X is Y"
        capital_match2 = re.search(
            r"the\s+capital\s+of\s+(.+?)\s+is\s+(.+?)[\.\?]?$",
            claim_text,
            re.IGNORECASE
        )
        if capital_match2:
            country = capital_match2.group(1).strip()
            claimed_capital = capital_match2.group(2).strip()
            return self.verify_claim(country, "capital", claimed_capital)
        
        # Pattern: "X was born in YEAR"
        birth_match = re.search(
            r"(.+?)\s+was\s+born\s+in\s+(\d{4})",
            claim_text,
            re.IGNORECASE
        )
        if birth_match:
            person = birth_match.group(1).strip()
            year = birth_match.group(2)
            result = self.verify_claim(person, "birth date", year)
            # For dates, check if year matches
            if result.actual_value and year in result.actual_value:
                result.verified = True
            return result
        
        # Pattern: "X is located in Y" / "X is in Y"
        location_match = re.search(
            r"(.+?)\s+is\s+(?:located\s+)?in\s+(.+?)[\.\?]?$",
            claim_text,
            re.IGNORECASE
        )
        if location_match:
            place = location_match.group(1).strip()
            location = location_match.group(2).strip()
            return self.verify_claim(place, "located in", location)
        
        return None


# Singleton instance
_verifier_instance: Optional[WikidataVerifier] = None


def get_wikidata_verifier() -> WikidataVerifier:
    """Get singleton instance of WikidataVerifier."""
    global _verifier_instance
    if _verifier_instance is None:
        _verifier_instance = WikidataVerifier()
    return _verifier_instance
