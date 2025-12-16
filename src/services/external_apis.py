"""
External APIs Service
Clients for free pharmaceutical data APIs with caching support.
"""
import httpx
from typing import Optional, Dict, List, Any
from dataclasses import dataclass
from datetime import datetime
import json


@dataclass
class DrugInfo:
    """Standard drug information structure."""
    name: str
    synonyms: List[str]
    molecular_formula: Optional[str] = None
    molecular_weight: Optional[float] = None
    description: Optional[str] = None
    mechanism_of_action: Optional[str] = None
    indications: List[str] = None
    source: str = "unknown"
    fetched_at: datetime = None
    
    def __post_init__(self):
        if self.indications is None:
            self.indications = []
        if self.fetched_at is None:
            self.fetched_at = datetime.utcnow()


@dataclass  
class ClinicalTrialInfo:
    """Clinical trial information structure."""
    nct_id: str
    title: str
    status: str
    phase: str
    drug_name: str
    indication: str
    sponsor: Optional[str] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    enrollment: Optional[int] = None
    source: str = "clinicaltrials.gov"
    fetched_at: datetime = None
    
    def __post_init__(self):
        if self.fetched_at is None:
            self.fetched_at = datetime.utcnow()


class PubChemClient:
    """Client for PubChem REST API (free, no API key required)."""
    
    BASE_URL = "https://pubchem.ncbi.nlm.nih.gov/rest/pug"
    
    @classmethod
    def search_compound(cls, name: str, timeout: float = 10.0) -> Optional[DrugInfo]:
        """
        Search for a compound by name.
        
        Args:
            name: Drug/compound name to search
            timeout: Request timeout in seconds
            
        Returns:
            DrugInfo if found, None otherwise
        """
        try:
            # Get compound ID first
            url = f"{cls.BASE_URL}/compound/name/{name}/cids/JSON"
            
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url)
                
                if response.status_code != 200:
                    return None
                    
                data = response.json()
                cids = data.get("IdentifierList", {}).get("CID", [])
                
                if not cids:
                    return None
                
                cid = cids[0]
                
                # Get compound properties
                props_url = f"{cls.BASE_URL}/compound/cid/{cid}/property/MolecularFormula,MolecularWeight,IUPACName/JSON"
                props_response = client.get(props_url)
                
                props = {}
                if props_response.status_code == 200:
                    props_data = props_response.json()
                    properties = props_data.get("PropertyTable", {}).get("Properties", [{}])[0]
                    props = {
                        "molecular_formula": properties.get("MolecularFormula"),
                        "molecular_weight": properties.get("MolecularWeight"),
                    }
                
                # Get synonyms
                syn_url = f"{cls.BASE_URL}/compound/cid/{cid}/synonyms/JSON"
                syn_response = client.get(syn_url)
                
                synonyms = []
                if syn_response.status_code == 200:
                    syn_data = syn_response.json()
                    synonyms = syn_data.get("InformationList", {}).get("Information", [{}])[0].get("Synonym", [])[:10]
                
                return DrugInfo(
                    name=name,
                    synonyms=synonyms,
                    molecular_formula=props.get("molecular_formula"),
                    molecular_weight=props.get("molecular_weight"),
                    source="pubchem"
                )
                
        except Exception as e:
            print(f"PubChem API error: {e}")
            return None


class ChEMBLClient:
    """Client for ChEMBL REST API (free, no API key required)."""
    
    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"
    
    @classmethod
    def search_molecule(cls, name: str, timeout: float = 10.0) -> Optional[DrugInfo]:
        """
        Search for a molecule by name.
        
        Args:
            name: Drug/molecule name
            timeout: Request timeout in seconds
            
        Returns:
            DrugInfo if found, None otherwise
        """
        try:
            url = f"{cls.BASE_URL}/molecule/search.json"
            params = {"q": name, "limit": 5}
            
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                molecules = data.get("molecules", [])
                
                if not molecules:
                    return None
                
                mol = molecules[0]
                mol_props = mol.get("molecule_properties", {}) or {}
                
                # Get drug indications if available
                indications = []
                if mol.get("molecule_chembl_id"):
                    ind_url = f"{cls.BASE_URL}/drug_indication.json"
                    ind_params = {"molecule_chembl_id": mol["molecule_chembl_id"], "limit": 10}
                    ind_response = client.get(ind_url, params=ind_params)
                    
                    if ind_response.status_code == 200:
                        ind_data = ind_response.json()
                        for ind in ind_data.get("drug_indications", []):
                            if ind.get("mesh_heading"):
                                indications.append(ind["mesh_heading"])
                
                return DrugInfo(
                    name=mol.get("pref_name") or name,
                    synonyms=[s.get("molecule_synonym") for s in mol.get("molecule_synonyms", []) if s.get("molecule_synonym")][:10],
                    molecular_formula=mol_props.get("full_molformula"),
                    molecular_weight=float(mol_props["full_mwt"]) if mol_props.get("full_mwt") else None,
                    description=mol.get("description"),
                    mechanism_of_action=mol.get("mechanism_of_action"),
                    indications=indications,
                    source="chembl"
                )
                
        except Exception as e:
            print(f"ChEMBL API error: {e}")
            return None


class ClinicalTrialsClient:
    """Client for ClinicalTrials.gov API v2 (free, no API key required)."""
    
    BASE_URL = "https://clinicaltrials.gov/api/v2"
    
    @classmethod
    def search_trials(cls, drug_name: str = None, indication: str = None, 
                      limit: int = 10, timeout: float = 15.0) -> List[ClinicalTrialInfo]:
        """
        Search for clinical trials.
        
        Args:
            drug_name: Drug/intervention name to search
            indication: Disease/condition to search
            limit: Max number of results
            timeout: Request timeout
            
        Returns:
            List of ClinicalTrialInfo objects
        """
        try:
            url = f"{cls.BASE_URL}/studies"
            
            # Build query
            query_parts = []
            if drug_name:
                query_parts.append(drug_name)
            if indication:
                query_parts.append(indication)
            
            params = {
                "query.term": " ".join(query_parts),
                "pageSize": limit,
                "format": "json"
            }
            
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                studies = data.get("studies", [])
                
                results = []
                for study in studies:
                    protocol = study.get("protocolSection", {})
                    id_module = protocol.get("identificationModule", {})
                    status_module = protocol.get("statusModule", {})
                    design_module = protocol.get("designModule", {})
                    desc_module = protocol.get("descriptionModule", {})
                    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
                    
                    # Get phase
                    phases = design_module.get("phases", [])
                    phase = phases[0] if phases else "N/A"
                    
                    # Get conditions
                    conditions = protocol.get("conditionsModule", {}).get("conditions", [])
                    indication_str = conditions[0] if conditions else "Unknown"
                    
                    # Get interventions (drugs)
                    interventions = protocol.get("armsInterventionsModule", {}).get("interventions", [])
                    drug = drug_name or "Unknown"
                    for interv in interventions:
                        if interv.get("type") == "DRUG":
                            drug = interv.get("name", drug)
                            break
                    
                    results.append(ClinicalTrialInfo(
                        nct_id=id_module.get("nctId", ""),
                        title=id_module.get("briefTitle", ""),
                        status=status_module.get("overallStatus", "Unknown"),
                        phase=phase,
                        drug_name=drug,
                        indication=indication_str,
                        sponsor=sponsor_module.get("leadSponsor", {}).get("name"),
                        start_date=status_module.get("startDateStruct", {}).get("date"),
                        completion_date=status_module.get("completionDateStruct", {}).get("date"),
                        enrollment=design_module.get("enrollmentInfo", {}).get("count")
                    ))
                
                return results
                
        except Exception as e:
            print(f"ClinicalTrials.gov API error: {e}")
            return []


class OpenFDAClient:
    """Client for OpenFDA API (free, no API key required for basic usage)."""
    
    BASE_URL = "https://api.fda.gov/drug"
    
    @classmethod
    def search_drug(cls, name: str, timeout: float = 10.0) -> Optional[Dict[str, Any]]:
        """
        Search for FDA drug information.
        
        Args:
            name: Drug brand or generic name
            timeout: Request timeout
            
        Returns:
            Dict with drug info if found, None otherwise
        """
        try:
            # Try drugsfda endpoint for approved drugs
            url = f"{cls.BASE_URL}/drugsfda.json"
            params = {
                "search": f'openfda.brand_name:"{name}" OR openfda.generic_name:"{name}"',
                "limit": 1
            }
            
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return None
                
                drug = results[0]
                openfda = drug.get("openfda", {})
                products = drug.get("products", [])
                
                return {
                    "brand_names": openfda.get("brand_name", []),
                    "generic_names": openfda.get("generic_name", []),
                    "manufacturer": openfda.get("manufacturer_name", []),
                    "substance_names": openfda.get("substance_name", []),
                    "route": openfda.get("route", []),
                    "pharm_class": openfda.get("pharm_class_epc", []),
                    "products": [
                        {
                            "dosage_form": p.get("dosage_form"),
                            "route": p.get("route"),
                            "marketing_status": p.get("marketing_status")
                        }
                        for p in products[:5]
                    ],
                    "source": "openfda",
                    "fetched_at": datetime.utcnow().isoformat()
                }
                
        except Exception as e:
            print(f"OpenFDA API error: {e}")
            return None
    
    @classmethod
    def get_adverse_events(cls, drug_name: str, limit: int = 10, timeout: float = 10.0) -> List[Dict]:
        """
        Get adverse event reports for a drug.
        
        Args:
            drug_name: Drug name to search
            limit: Max number of results
            timeout: Request timeout
            
        Returns:
            List of adverse event summaries
        """
        try:
            url = f"{cls.BASE_URL}/event.json"
            params = {
                "search": f'patient.drug.medicinalproduct:"{drug_name}"',
                "count": "patient.reaction.reactionmeddrapt.exact",
                "limit": limit
            }
            
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)
                
                if response.status_code != 200:
                    return []
                
                data = response.json()
                return data.get("results", [])
                
        except Exception as e:
            print(f"OpenFDA adverse events API error: {e}")
            return []


# Convenience functions
def fetch_drug_info(name: str) -> Optional[DrugInfo]:
    """
    Fetch drug information from multiple sources.
    Tries PubChem first, then ChEMBL.
    
    Args:
        name: Drug/compound name
        
    Returns:
        DrugInfo if found from any source, None otherwise
    """
    # Try PubChem first (usually faster)
    info = PubChemClient.search_compound(name)
    if info:
        return info
    
    # Try ChEMBL as fallback
    info = ChEMBLClient.search_molecule(name)
    if info:
        return info
    
    return None


def fetch_clinical_trials(drug_name: str = None, indication: str = None, limit: int = 10) -> List[ClinicalTrialInfo]:
    """
    Fetch clinical trials from ClinicalTrials.gov.
    
    Args:
        drug_name: Drug name to search
        indication: Disease/condition
        limit: Max results
        
    Returns:
        List of ClinicalTrialInfo
    """
    return ClinicalTrialsClient.search_trials(drug_name, indication, limit)


def fetch_fda_drug_info(name: str) -> Optional[Dict]:
    """
    Fetch FDA drug information.
    
    Args:
        name: Drug name
        
    Returns:
        Dict with FDA drug info or None
    """
    return OpenFDAClient.search_drug(name)
