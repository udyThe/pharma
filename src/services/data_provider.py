"""
Data provider for live external data sources.
Validates payloads, caches in Redis, and returns normalized dicts.
"""
from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field, ValidationError
from tavily import TavilyClient

from src.config.settings import settings
from src.infra.redis_client import get_redis_client


class MarketItem(BaseModel):
    molecule: str
    region: Optional[str] = ""
    therapy_area: Optional[str] = ""
    indication: Optional[str] = ""
    market_size_usd_mn: Optional[float] = None
    cagr_percent: Optional[float] = None
    top_competitors: Optional[List[str]] = None
    generic_penetration: Optional[str] = None
    patient_burden: Optional[str] = None
    competition_level: Optional[str] = None


class PatentEntry(BaseModel):
    molecule: str
    patent_number: str
    type: Optional[str] = None
    expiry_date: Optional[str] = None
    status: Optional[str] = "Active"


class ClinicalTrialEntry(BaseModel):
    nct_id: str
    indication: Optional[str] = None
    therapy_area: Optional[str] = None
    phase: Optional[str] = None
    drug_name: Optional[str] = None
    sponsor: Optional[str] = None
    patient_burden_score: Optional[float] = None
    competition_density: Optional[str] = None
    unmet_need: Optional[str] = None


class CompetitorEntry(BaseModel):
    molecule: Optional[str] = None
    competitor: Optional[str] = None
    strategy: Optional[str] = None
    likelihood: Optional[str] = None
    impact: Optional[str] = None


class SocialEntry(BaseModel):
    molecule: Optional[str] = None
    sentiment: Optional[float] = 0
    source: Optional[str] = None
    complaint: Optional[str] = None
    post: Optional[str] = None


def _client():
    headers = {}
    if settings.DATA_API_KEY:
        headers["Authorization"] = f"Bearer {settings.DATA_API_KEY}"
    return httpx.Client(timeout=8.0, headers=headers)


def _cache_key(prefix: str, url: str) -> str:
    return f"cache:{prefix}:{hashlib.sha256(url.encode()).hexdigest()}"


def _get(url: str, prefix: str) -> Optional[List[Dict[str, Any]]]:
    if not url:
        return None
    redis = get_redis_client()
    key = _cache_key(prefix, url)
    if redis:
        cached = redis.get(key)
        if cached:
            import json

            try:
                return json.loads(cached)
            except Exception:
                pass
    try:
        with _client() as client:
            resp = client.get(url)
            resp.raise_for_status()
            data = resp.json()
            if isinstance(data, dict) and "results" in data:
                data = data["results"]
            if not isinstance(data, list):
                return None
            if redis:
                import json

                redis.setex(key, settings.RAG_CACHE_TTL, json.dumps(data))
            return data
    except Exception:
        return None


def _tavily_search(query: str, max_results: int = 3) -> Optional[List[Dict[str, Any]]]:
    """Fallback search using Tavily when no structured API is available."""
    if not settings.TAVILY_API_KEY:
        return None
    try:
        client = TavilyClient(api_key=settings.TAVILY_API_KEY)
        res = client.search(query=query, max_results=max_results, search_depth="advanced", include_answer=True)
        return res.get("results", [])
    except Exception:
        return None


def fetch_market_data() -> Optional[List[Dict[str, Any]]]:
    raw = _get(settings.MARKET_API_URL, "market")
    if not raw:
        search = _tavily_search("pharma market size CAGR competitive landscape")
        if search:
            fallback = []
            for r in search:
                fallback.append(
                    MarketItem(
                        molecule=r.get("title", "Unknown"),
                        region="Global",
                        therapy_area="Mixed",
                        indication="",
                        market_size_usd_mn=None,
                        cagr_percent=None,
                        top_competitors=[],
                        generic_penetration=None,
                        patient_burden=None,
                        competition_level=None,
                    ).model_dump()
                )
            return fallback or None
        return None
    valid = []
    for item in raw:
        try:
            valid.append(MarketItem(**item).model_dump())
        except ValidationError:
            continue
    return valid or None


def fetch_patent_data() -> Optional[List[Dict[str, Any]]]:
    raw = _get(settings.PATENT_API_URL, "patent")
    if not raw:
        search = _tavily_search("drug patent expiry status")
        if search:
            normalized = []
            for r in search:
                normalized.append(
                    PatentEntry(
                        molecule=r.get("title", "Unknown"),
                        patent_number="N/A",
                        type="Unknown",
                        expiry_date="Unknown",
                        status="Unknown",
                    ).model_dump()
                )
            return normalized or None
        return None
    normalized: List[PatentEntry] = []
    for entry in raw:
        if "patents" in entry:
            mol = entry.get("molecule", "")
            for p in entry.get("patents", []):
                try:
                    normalized.append(
                        PatentEntry(
                            molecule=mol,
                            patent_number=p.get("patent_number"),
                            type=p.get("type") or p.get("patent_type"),
                            expiry_date=p.get("expiry_date"),
                            status=p.get("status", "Active"),
                        )
                    )
                except ValidationError:
                    continue
        else:
            try:
                normalized.append(PatentEntry(**entry))
            except ValidationError:
                continue
    return [n.model_dump() for n in normalized] or None


def fetch_clinical_data() -> Optional[List[Dict[str, Any]]]:
    raw = _get(settings.CLINICAL_API_URL, "clinical")
    if not raw:
        search = _tavily_search("clinical trial oncology phase III immunotherapy")
        if search:
            normalized = []
            for r in search:
                normalized.append(
                    ClinicalTrialEntry(
                        nct_id="N/A",
                        indication=r.get("title", "Unknown"),
                        therapy_area="Unknown",
                        phase="Unknown",
                        drug_name=r.get("title", "Unknown"),
                        sponsor="Unknown",
                        patient_burden_score=None,
                        competition_density=None,
                        unmet_need=None,
                    ).model_dump()
                )
            return normalized or None
        return None
    normalized: List[ClinicalTrialEntry] = []
    for entry in raw:
        if "active_trials" in entry:
            indication = entry.get("indication")
            therapy_area = entry.get("therapy_area")
            for trial in entry.get("active_trials", []):
                try:
                    normalized.append(
                        ClinicalTrialEntry(
                            nct_id=trial.get("nct_id"),
                            indication=indication,
                            therapy_area=therapy_area,
                            phase=trial.get("phase"),
                            drug_name=trial.get("drug_name"),
                            sponsor=trial.get("sponsor"),
                            patient_burden_score=entry.get("patient_burden_score"),
                            competition_density=entry.get("competition_density"),
                            unmet_need=entry.get("unmet_need"),
                        )
                    )
                except ValidationError:
                    continue
        else:
            try:
                normalized.append(ClinicalTrialEntry(**entry))
            except ValidationError:
                continue
    return [n.model_dump() for n in normalized] or None


def fetch_competitor_data() -> Optional[List[Dict[str, Any]]]:
    raw = _get(settings.COMPETITOR_API_URL, "competitor")
    if not raw:
        search = _tavily_search("pharma competitor strategy launch generic")
        if search:
            normalized = []
            for r in search:
                normalized.append(
                    CompetitorEntry(
                        molecule=None,
                        competitor=r.get("title"),
                        strategy=r.get("content", "")[:200],
                        likelihood="Unknown",
                        impact=None,
                    ).model_dump()
                )
            return normalized or None
        return None
    normalized = []
    for entry in raw:
        try:
            normalized.append(
                CompetitorEntry(
                    molecule=entry.get("molecule"),
                    competitor=entry.get("competitor") or entry.get("company"),
                    strategy=entry.get("predicted_strategy") or entry.get("strategy"),
                    likelihood=entry.get("likelihood"),
                    impact=entry.get("impact"),
                ).model_dump()
            )
        except ValidationError:
            continue
    return normalized or None


def fetch_social_data() -> Optional[List[Dict[str, Any]]]:
    raw = _get(settings.SOCIAL_API_URL, "social")
    if not raw:
        search = _tavily_search("patient complaints drug side effects cost convenience")
        if search:
            normalized = []
            for r in search:
                normalized.append(
                    SocialEntry(
                        molecule=None,
                        sentiment=0,
                        source=r.get("url"),
                        complaint="",
                        post=r.get("content", "")[:280],
                    ).model_dump()
                )
            return normalized or None
        return None
    normalized = []
    for entry in raw:
        try:
            normalized.append(
                SocialEntry(
                    molecule=entry.get("molecule"),
                    sentiment=entry.get("sentiment", 0),
                    source=entry.get("source"),
                    complaint=entry.get("complaint_theme") or entry.get("complaint"),
                    post=entry.get("post_text") or entry.get("post"),
                ).model_dump()
            )
        except ValidationError:
            continue
    return normalized or None

