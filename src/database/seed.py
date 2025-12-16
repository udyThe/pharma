"""
Database seeder - Migrates mock JSON data to SQLite database.
Run this once to initialize the database with mock data.
"""
import json
from pathlib import Path
from datetime import datetime

from .db import get_db_session, init_database
from .models import (
    MarketData, Patent, ClinicalTrial, Competitor, 
    TradeData, InternalDoc, SocialPost, User, UserRole, PatentStatus
)

MOCK_DATA_PATH = Path(__file__).resolve().parent.parent.parent / "mock_data"


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime."""
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except:
            return None


def seed_market_data():
    """Seed market data from iqvia_market_data.json."""
    data_file = MOCK_DATA_PATH / "iqvia_market_data.json"
    if not data_file.exists():
        print("⚠️ iqvia_market_data.json not found")
        return 0
    
    with open(data_file) as f:
        data = json.load(f)
    
    count = 0
    with get_db_session() as db:
        for item in data:
            record = MarketData(
                molecule=item["molecule"],
                region=item["region"],
                therapy_area=item["therapy_area"],
                indication=item.get("indication"),
                market_size_usd_mn=item["market_size_usd_mn"],
                cagr_percent=item["cagr_percent"],
                top_competitors=item.get("top_competitors", []),
                generic_penetration=item.get("generic_penetration"),
                patient_burden=item.get("patient_burden"),
                competition_level=item.get("competition_level")
            )
            db.add(record)
            count += 1
    
    print(f"✅ Seeded {count} market data records")
    return count


def seed_patents():
    """Seed patent data from uspto_patents.json."""
    data_file = MOCK_DATA_PATH / "uspto_patents.json"
    if not data_file.exists():
        print("⚠️ uspto_patents.json not found")
        return 0
    
    with open(data_file) as f:
        data = json.load(f)
    
    count = 0
    with get_db_session() as db:
        for item in data:
            molecule = item["molecule"]
            for patent in item.get("patents", []):
                # Map status string to enum
                status_str = patent.get("status", "Active")
                status_map = {"Active": PatentStatus.ACTIVE, "Expired": PatentStatus.EXPIRED, "Pending": PatentStatus.PENDING}
                status_enum = status_map.get(status_str, PatentStatus.ACTIVE)
                
                record = Patent(
                    molecule=molecule,
                    patent_number=patent["patent_number"],
                    patent_type=patent.get("type"),
                    expiry_date=parse_date(patent.get("expiry_date")),
                    status=status_enum,
                    country="US"
                )
                db.add(record)
                count += 1
    
    print(f"✅ Seeded {count} patent records")
    return count


def seed_clinical_trials():
    """Seed clinical trials from clinical_trials.json."""
    data_file = MOCK_DATA_PATH / "clinical_trials.json"
    if not data_file.exists():
        print("⚠️ clinical_trials.json not found")
        return 0
    
    count = 0
    with open(data_file) as f:
        data = json.load(f)
    
    with get_db_session() as db:
        for item in data:
            indication = item["indication"]
            therapy_area = item.get("therapy_area")
            patient_burden = item.get("patient_burden_score")
            competition_density = item.get("competition_density")
            unmet_need = item.get("unmet_need")
            
            for trial in item.get("active_trials", []):
                record = ClinicalTrial(
                    nct_id=trial["nct_id"],
                    indication=indication,
                    therapy_area=therapy_area,
                    phase=trial["phase"],
                    drug_name=trial["drug_name"],
                    sponsor=trial.get("sponsor"),
                    patient_burden_score=patient_burden,
                    competition_density=competition_density,
                    unmet_need=unmet_need
                )
                db.add(record)
                count += 1
    
    print(f"✅ Seeded {count} clinical trial records")
    return count


def seed_competitors():
    """Seed competitor strategies from competitor_strategies.json."""
    data_file = MOCK_DATA_PATH / "competitor_strategies.json"
    if not data_file.exists():
        print("⚠️ competitor_strategies.json not found")
        return 0
    
    with open(data_file) as f:
        data = json.load(f)
    
    count = 0
    with get_db_session() as db:
        for item in data:
            record = Competitor(
                molecule=item["molecule"],
                competitor_name=item["competitor"],
                predicted_strategy=item.get("predicted_strategy"),
                likelihood=item.get("likelihood"),
                impact=item.get("impact")
            )
            db.add(record)
            count += 1
    
    print(f"✅ Seeded {count} competitor records")
    return count


def seed_trade_data():
    """Seed trade data from exim_trade_data.json."""
    data_file = MOCK_DATA_PATH / "exim_trade_data.json"
    if not data_file.exists():
        print("⚠️ exim_trade_data.json not found")
        return 0
    
    with open(data_file) as f:
        data = json.load(f)
    
    count = 0
    with get_db_session() as db:
        for item in data:
            record = TradeData(
                molecule=item["molecule"],
                total_import_volume_kg=item.get("total_import_volume_kg"),
                major_source_countries=item.get("major_source_countries", []),
                average_price_per_kg=item.get("average_price_per_kg")
            )
            db.add(record)
            count += 1
    
    print(f"✅ Seeded {count} trade data records")
    return count


def seed_internal_docs():
    """Seed internal docs from internal_docs_metadata.json."""
    data_file = MOCK_DATA_PATH / "internal_docs_metadata.json"
    if not data_file.exists():
        print("⚠️ internal_docs_metadata.json not found")
        return 0
    
    with open(data_file) as f:
        data = json.load(f)
    
    count = 0
    with get_db_session() as db:
        for item in data:
            record = InternalDoc(
                doc_id=item["doc_id"],
                title=item["title"],
                summary=item.get("summary"),
                content=item.get("content"),
                tags=item.get("tags", [])
            )
            db.add(record)
            count += 1
    
    print(f"✅ Seeded {count} internal doc records")
    return count


def seed_social_posts():
    """Seed social posts from social_media_posts.json."""
    data_file = MOCK_DATA_PATH / "social_media_posts.json"
    if not data_file.exists():
        print("⚠️ social_media_posts.json not found")
        return 0
    
    with open(data_file) as f:
        data = json.load(f)
    
    count = 0
    with get_db_session() as db:
        for item in data:
            record = SocialPost(
                molecule=item["molecule"],
                source=item.get("source"),
                post_text=item["post_text"],
                sentiment=item.get("sentiment"),
                therapy_area=item.get("therapy_area"),
                complaint_theme=item.get("complaint_theme"),
                post_date=parse_date(item.get("date"))
            )
            db.add(record)
            count += 1
    
    print(f"✅ Seeded {count} social post records")
    return count


def seed_default_users():
    """Create default user accounts."""
    import hashlib
    
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    users = [
        {"username": "admin", "email": "admin@pharma.ai", "password": "admin123", "role": UserRole.ADMIN},
        {"username": "analyst", "email": "analyst@pharma.ai", "password": "analyst123", "role": UserRole.ANALYST},
        {"username": "manager", "email": "manager@pharma.ai", "password": "manager123", "role": UserRole.MANAGER},
        {"username": "demo", "email": "demo@pharma.ai", "password": "demo", "role": UserRole.ANALYST},
    ]
    
    count = 0
    with get_db_session() as db:
        for user_data in users:
            # Check if user already exists
            existing = db.query(User).filter(User.username == user_data["username"]).first()
            if not existing:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    password_hash=hash_password(user_data["password"]),
                    role=user_data["role"]
                )
                db.add(user)
                count += 1
    
    print(f"✅ Created {count} default users")
    return count


def seed_all():
    """Seed all data from mock JSON files."""
    print("\n" + "=" * 50)
    print("  🌱 Seeding Database")
    print("=" * 50 + "\n")
    
    # Initialize tables
    init_database()
    
    # Seed all data
    total = 0
    total += seed_default_users()
    total += seed_market_data()
    total += seed_patents()
    total += seed_clinical_trials()
    total += seed_competitors()
    total += seed_trade_data()
    total += seed_internal_docs()
    total += seed_social_posts()
    
    print(f"\n✅ Total records seeded: {total}")
    print("=" * 50 + "\n")
    
    return total


if __name__ == "__main__":
    seed_all()
