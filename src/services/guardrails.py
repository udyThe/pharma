"""
Guardrails Service
Input validation, content filtering, and safety checks for the Pharma AI system.
"""
import re
from typing import Tuple, List, Optional, Dict
from dataclasses import dataclass
from enum import Enum


class RiskLevel(Enum):
    """Risk classification for queries."""
    SAFE = "safe"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    BLOCKED = "blocked"


@dataclass
class ValidationResult:
    """Result of input validation."""
    is_valid: bool
    risk_level: RiskLevel
    message: str
    sanitized_input: str
    flags: List[str]


class GuardrailsService:
    """
    Input validation and content filtering for pharmaceutical AI queries.
    Ensures safe, compliant, and appropriate usage of the system.
    """
    
    # Blocked topics - queries that should not be processed
    BLOCKED_PATTERNS = [
        r'\b(synthesiz|manufactur|make|creat|produc)\b.*(drug|narcotic|controlled substance)',
        r'\b(illegal|illicit)\b.*\b(drug|substance)',
        r'\bhow to (make|create|synthesize)\b',
        r'\b(suicide|self.?harm|overdose)\b.*\b(method|how|way)',
        r'\bpurchase.*(prescription|controlled)\b.*without',
        r'\bfake|counterfeit|forge\b.*\b(prescription|medication)',
    ]
    
    # Sensitive topics - require careful handling
    SENSITIVE_PATTERNS = [
        r'\b(off.?label|unapproved)\b.*use',
        r'\bexperimental\b.*treatment',
        r'\bcontrolled substance|schedule [iv]+\b',
        r'\badverse event|side effect|death\b',
        r'\brecall|warning letter|fda action\b',
    ]
    
    # PII patterns to detect and sanitize
    PII_PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b(\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b(?:\d{4}[-\s]?){3}\d{4}\b',
        'patient_id': r'\b(patient|mrn|medical record)[\s:#]*\d+\b',
    }
    
    # Maximum query length
    MAX_QUERY_LENGTH = 2000
    
    # Minimum query length
    MIN_QUERY_LENGTH = 3
    
    def validate_query(self, query: str) -> Tuple[bool, Dict]:
        """
        Validate a query and return safety status.
        
        Args:
            query: User query string
            
        Returns:
            Tuple of (is_safe, result_dict with 'reason' key if blocked)
        """
        result = self.validate_input(query)
        return result.is_valid, {"reason": result.message, "flags": result.flags}
    
    def sanitize_input(self, query: str) -> str:
        """
        Sanitize user input by removing potentially harmful content.
        
        Args:
            query: Raw user input
            
        Returns:
            Sanitized query string
        """
        result = self.validate_input(query)
        return result.sanitized_input if result.sanitized_input else query.strip()
    
    def filter_response(self, response: str) -> str:
        """
        Filter AI response to remove PII and add disclaimers.
        
        Args:
            response: Raw AI response
            
        Returns:
            Filtered response string
        """
        filtered, _ = self.validate_output(response)
        return filtered
    
    @classmethod
    def validate_input(cls, query: str) -> ValidationResult:
        """
        Validate and sanitize user input.
        
        Args:
            query: Raw user input
            
        Returns:
            ValidationResult with validation status and sanitized input
        """
        flags = []
        risk_level = RiskLevel.SAFE
        
        # Check for empty input
        if not query or not query.strip():
            return ValidationResult(
                is_valid=False,
                risk_level=RiskLevel.BLOCKED,
                message="Please enter a query.",
                sanitized_input="",
                flags=["empty_input"]
            )
        
        # Strip and normalize whitespace
        sanitized = " ".join(query.split())
        
        # Check length
        if len(sanitized) < cls.MIN_QUERY_LENGTH:
            return ValidationResult(
                is_valid=False,
                risk_level=RiskLevel.BLOCKED,
                message="Query is too short. Please be more specific.",
                sanitized_input=sanitized,
                flags=["too_short"]
            )
        
        if len(sanitized) > cls.MAX_QUERY_LENGTH:
            flags.append("truncated")
            sanitized = sanitized[:cls.MAX_QUERY_LENGTH]
            risk_level = RiskLevel.LOW
        
        # Check for blocked content
        query_lower = sanitized.lower()
        for pattern in cls.BLOCKED_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return ValidationResult(
                    is_valid=False,
                    risk_level=RiskLevel.BLOCKED,
                    message="I cannot assist with this type of request. Please ask about legitimate pharmaceutical business intelligence topics.",
                    sanitized_input="",
                    flags=["blocked_content"]
                )
        
        # Check for sensitive content
        for pattern in cls.SENSITIVE_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                flags.append("sensitive_content")
                if risk_level.value == "safe":
                    risk_level = RiskLevel.MEDIUM
        
        # Check and sanitize PII
        pii_found = []
        for pii_type, pattern in cls.PII_PATTERNS.items():
            if re.search(pattern, sanitized, re.IGNORECASE):
                pii_found.append(pii_type)
                # Redact PII
                sanitized = re.sub(pattern, f"[REDACTED_{pii_type.upper()}]", sanitized, flags=re.IGNORECASE)
        
        if pii_found:
            flags.extend([f"pii_{p}" for p in pii_found])
            if risk_level.value in ["safe", "low"]:
                risk_level = RiskLevel.MEDIUM
        
        # Check for injection attempts
        injection_patterns = [
            r'<script',
            r'javascript:',
            r'\{\{.*\}\}',
            r'\$\{.*\}',
            r'<!--',
            r'-->'
        ]
        
        for pattern in injection_patterns:
            if re.search(pattern, sanitized, re.IGNORECASE):
                flags.append("injection_attempt")
                sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE)
                risk_level = RiskLevel.HIGH
        
        # Build message based on flags
        message = "Query validated successfully."
        if "sensitive_content" in flags:
            message = "Note: This query involves sensitive topics. Responses will include appropriate disclaimers."
        if any(f.startswith("pii_") for f in flags):
            message = "Personal information has been redacted for privacy."
        
        return ValidationResult(
            is_valid=True,
            risk_level=risk_level,
            message=message,
            sanitized_input=sanitized,
            flags=flags
        )
    
    @classmethod
    def validate_output(cls, response: str) -> Tuple[str, List[str]]:
        """
        Validate and filter AI output before returning to user.
        
        Args:
            response: Raw AI response
            
        Returns:
            Tuple of (filtered_response, warning_flags)
        """
        flags = []
        filtered = response
        
        # Check for any PII that might have leaked into response
        for pii_type, pattern in cls.PII_PATTERNS.items():
            if re.search(pattern, filtered, re.IGNORECASE):
                filtered = re.sub(pattern, f"[REDACTED]", filtered, flags=re.IGNORECASE)
                flags.append(f"output_pii_{pii_type}")
        
        # Add medical disclaimer if response contains treatment/dosage info
        dosage_patterns = [
            r'\b\d+\s*(mg|mcg|ml|g)\b',
            r'\b(take|administer|dose|dosage)\b',
            r'\btreatment\s+recommend',
        ]
        
        needs_disclaimer = any(re.search(p, filtered, re.IGNORECASE) for p in dosage_patterns)
        
        if needs_disclaimer and "DISCLAIMER" not in filtered.upper():
            disclaimer = "\n\n---\n*⚕️ Disclaimer: This information is for business intelligence purposes only. Always consult healthcare professionals for medical advice.*"
            filtered += disclaimer
            flags.append("disclaimer_added")
        
        return filtered, flags
    
    @classmethod
    def check_rate_abuse(cls, user_id: Optional[int], query: str, recent_queries: List[str]) -> Tuple[bool, str]:
        """
        Check for potential rate abuse or spam patterns.
        
        Args:
            user_id: User identifier
            query: Current query
            recent_queries: List of user's recent queries
            
        Returns:
            Tuple of (is_abusive, reason)
        """
        if not recent_queries:
            return False, ""
        
        # Check for repeated identical queries
        identical_count = sum(1 for q in recent_queries[-10:] if q.lower().strip() == query.lower().strip())
        if identical_count >= 3:
            return True, "Please avoid submitting identical queries repeatedly."
        
        # Check for very similar queries (potential automation)
        similar_count = 0
        for recent in recent_queries[-10:]:
            # Simple similarity check
            if len(set(query.lower().split()) & set(recent.lower().split())) > len(query.split()) * 0.8:
                similar_count += 1
        
        if similar_count >= 5:
            return True, "Unusual query pattern detected. Please slow down."
        
        return False, ""
    
    @classmethod
    def get_safe_response_for_blocked(cls) -> str:
        """Get a safe response for blocked queries."""
        return """I apologize, but I cannot assist with this request.

I'm designed to help with legitimate pharmaceutical business intelligence, including:
- Market analysis and competitive intelligence
- Patent and IP landscape research
- Clinical trial pipeline analysis
- Regulatory pathway assessments
- Strategic planning support

Please rephrase your query to focus on business-appropriate topics, or ask a different question."""


class ContentModerator:
    """
    Content moderation for ensuring appropriate responses.
    """
    
    # Topics that require extra care
    SENSITIVE_THERAPY_AREAS = [
        "oncology", "mental health", "pediatric", "reproductive",
        "addiction", "hiv", "aids", "terminal"
    ]
    
    @classmethod
    def add_context_warnings(cls, response: str, query: str) -> str:
        """Add appropriate context warnings based on query topic."""
        query_lower = query.lower()
        
        warnings = []
        
        # Check for off-label discussion
        if "off-label" in query_lower or "off label" in query_lower:
            warnings.append("⚠️ *Off-label use discussions are for informational purposes. Prescribing decisions should be made by licensed healthcare providers.*")
        
        # Check for sensitive therapy areas
        for area in cls.SENSITIVE_THERAPY_AREAS:
            if area in query_lower:
                if area in ["oncology", "terminal"]:
                    warnings.append("💙 *This topic involves serious health conditions. Information provided is for business analysis only.*")
                elif area == "mental health":
                    warnings.append("💚 *Mental health is important. This analysis is for business purposes only.*")
                break
        
        if warnings:
            response = response + "\n\n---\n" + "\n".join(warnings)
        
        return response
