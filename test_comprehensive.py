"""
Comprehensive Test Suite for Pharma Agentic AI
Tests 50+ scenarios across all tools and functionality.
"""
import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

# Test results storage
results = {"passed": [], "failed": []}

def test(name, condition, details=""):
    """Record a test result."""
    if condition:
        results["passed"].append((name, details))
        print(f"  [PASS] {name}")
    else:
        results["failed"].append((name, details))
        print(f"  [FAIL] {name} - {details}")
    return condition


def load_json(filename):
    """Load a JSON file from mock_data."""
    path = PROJECT_ROOT / "mock_data" / filename
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


# ============================================================
# SECTION 1: MOCK DATA FILE TESTS (8 tests)
# ============================================================
def test_mock_data_files():
    print("\n" + "=" * 60)
    print("  SECTION 1: MOCK DATA FILES (8 tests)")
    print("=" * 60)
    
    files = {
        "iqvia_market_data.json": 15,
        "exim_trade_data.json": 15,
        "clinical_trials.json": 10,
        "competitor_strategies.json": 20,
        "social_media_posts.json": 20,
        "uspto_patents.json": 15,
        "web_search_results.json": 5,
        "internal_docs_metadata.json": 5,
    }
    
    for filename, min_entries in files.items():
        data = load_json(filename)
        if data:
            test(f"{filename} exists and valid", 
                 len(data) >= min_entries, 
                 f"Has {len(data)} entries (min: {min_entries})")
        else:
            test(f"{filename} exists and valid", False, "File not found or invalid")


# ============================================================
# SECTION 2: IQVIA TOOL TESTS (8 tests)
# ============================================================
def test_iqvia_data():
    print("\n" + "=" * 60)
    print("  SECTION 2: IQVIA MARKET INTELLIGENCE (8 tests)")
    print("=" * 60)
    
    data = load_json("iqvia_market_data.json")
    if not data:
        test("IQVIA data loaded", False, "File not found")
        return
    
    # Test 1: Data loaded
    test("IQVIA data loaded", len(data) > 0, f"{len(data)} entries")
    
    # Test 2: Respiratory therapy area
    respiratory = [d for d in data if "respiratory" in d.get("therapy_area", "").lower()]
    test("Respiratory entries exist", len(respiratory) >= 3, f"Found {len(respiratory)}")
    
    # Test 3: Oncology therapy area
    oncology = [d for d in data if "oncology" in d.get("therapy_area", "").lower()]
    test("Oncology entries exist", len(oncology) >= 2, f"Found {len(oncology)}")
    
    # Test 4: India region
    india = [d for d in data if "india" in d.get("region", "").lower()]
    test("India region entries exist", len(india) >= 5, f"Found {len(india)}")
    
    # Test 5: Low competition markets
    low_comp = [d for d in data if d.get("competition_level", "").lower() == "low"]
    test("Low competition markets exist", len(low_comp) >= 3, f"Found {len(low_comp)}")
    
    # Test 6: Market size data
    has_market = all("market_size_usd_mn" in d for d in data[:10])
    test("Market size data present", has_market)
    
    # Test 7: CAGR data
    has_cagr = all("cagr_percent" in d for d in data[:10])
    test("CAGR data present", has_cagr)
    
    # Test 8: Specific molecule (Sitagliptin)
    sitagliptin = [d for d in data if "sitagliptin" in d.get("molecule", "").lower()]
    test("Sitagliptin entry exists", len(sitagliptin) >= 1)


# ============================================================
# SECTION 3: PATENT TOOL TESTS (8 tests)
# ============================================================
def test_patent_data():
    print("\n" + "=" * 60)
    print("  SECTION 3: PATENT LANDSCAPE (8 tests)")
    print("=" * 60)
    
    data = load_json("uspto_patents.json")
    if not data:
        test("Patent data loaded", False, "File not found")
        return
    
    # Test 1: Data loaded
    test("Patent data loaded", len(data) > 0, f"{len(data)} molecules")
    
    # Test 2: Pembrolizumab patents
    pembro = [d for d in data if "pembrolizumab" in d.get("molecule", "").lower()]
    test("Pembrolizumab patents exist", len(pembro) >= 1)
    if pembro:
        patents = pembro[0].get("patents", [])
        test("Pembrolizumab has multiple patents", len(patents) >= 2, f"Has {len(patents)} patents")
    
    # Test 3: Sitagliptin expired
    sita = [d for d in data if "sitagliptin" in d.get("molecule", "").lower()]
    if sita:
        patents = sita[0].get("patents", [])
        expired = [p for p in patents if p.get("status", "").lower() == "expired"]
        test("Sitagliptin patents expired", len(expired) >= 1, f"{len(expired)} expired")
    
    # Test 4: Semaglutide (Ozempic) active
    sema = [d for d in data if "semaglutide" in d.get("molecule", "").lower()]
    if sema:
        patents = sema[0].get("patents", [])
        active = [p for p in patents if p.get("status", "").lower() == "active"]
        test("Semaglutide has active patents", len(active) >= 2, f"{len(active)} active")
    
    # Test 5: Patent expiry dates present
    has_dates = all(
        all("expiry_date" in p for p in d.get("patents", []))
        for d in data[:10]
    )
    test("Expiry dates present", has_dates)
    
    # Test 6: Patent types present
    types_found = set()
    for d in data:
        for p in d.get("patents", []):
            types_found.add(p.get("type", ""))
    test("Multiple patent types exist", len(types_found) >= 3, f"Types: {len(types_found)}")
    
    # Test 7: Paracetamol (Dolo) is generic
    para = [d for d in data if "paracetamol" in d.get("molecule", "").lower()]
    test("Paracetamol entry exists", len(para) >= 1)


# ============================================================
# SECTION 4: COMPETITOR TOOL TESTS (8 tests)
# ============================================================
def test_competitor_data():
    print("\n" + "=" * 60)
    print("  SECTION 4: COMPETITOR INTELLIGENCE (8 tests)")
    print("=" * 60)
    
    data = load_json("competitor_strategies.json")
    if not data:
        test("Competitor data loaded", False, "File not found")
        return
    
    # Test 1: Data loaded
    test("Competitor data loaded", len(data) > 0, f"{len(data)} entries")
    
    # Test 2: Rivaroxaban competitors
    riva = [d for d in data if "rivaroxaban" in d.get("molecule", "").lower()]
    test("Rivaroxaban competitor data exists", len(riva) >= 2, f"Found {len(riva)}")
    
    # Test 3: High likelihood threats
    high = [d for d in data if d.get("likelihood", "").lower() == "high"]
    test("High likelihood threats exist", len(high) >= 3, f"Found {len(high)}")
    
    # Test 4: Multiple competitors
    competitors = set(d.get("competitor", "") for d in data)
    test("Multiple competitors tracked", len(competitors) >= 5, f"Found {len(competitors)}")
    
    # Test 5: Teva as competitor
    teva = [d for d in data if "teva" in d.get("competitor", "").lower()]
    test("Teva competitor data exists", len(teva) >= 1)
    
    # Test 6: Sun Pharma as competitor
    sun = [d for d in data if "sun" in d.get("competitor", "").lower()]
    test("Sun Pharma competitor data exists", len(sun) >= 1)
    
    # Test 7: Strategy field present
    has_strategy = all("predicted_strategy" in d for d in data)
    test("Predicted strategies present", has_strategy)
    
    # Test 8: Impact field present
    has_impact = all("impact" in d for d in data)
    test("Impact assessments present", has_impact)


# ============================================================
# SECTION 5: CLINICAL TRIALS TESTS (6 tests)
# ============================================================
def test_clinical_data():
    print("\n" + "=" * 60)
    print("  SECTION 5: CLINICAL TRIALS (6 tests)")
    print("=" * 60)
    
    data = load_json("clinical_trials.json")
    if not data:
        test("Clinical data loaded", False, "File not found")
        return
    
    # Test 1: Data loaded
    test("Clinical data loaded", len(data) > 0, f"{len(data)} indications")
    
    # Test 2: COPD indication
    copd = [d for d in data if "copd" in d.get("indication", "").lower()]
    if copd:
        trials = copd[0].get("active_trials", [])
        test("COPD trials exist", len(trials) >= 2, f"Found {len(trials)} trials")
    
    # Test 3: Cancer indications
    cancer = [d for d in data if any(x in d.get("indication", "").lower() for x in ["cancer", "carcinoma", "melanoma"])]
    test("Cancer indications exist", len(cancer) >= 3, f"Found {len(cancer)}")
    
    # Test 4: Phase III trials
    phase3_count = 0
    for d in data:
        for trial in d.get("active_trials", []):
            if "iii" in trial.get("phase", "").lower():
                phase3_count += 1
    test("Phase III trials exist", phase3_count >= 5, f"Found {phase3_count}")
    
    # Test 5: Unmet need data
    has_unmet = sum(1 for d in data if d.get("unmet_need"))
    test("Unmet need data present", has_unmet >= 5, f"Found {has_unmet}")
    
    # Test 6: Competition density data
    has_comp = sum(1 for d in data if d.get("competition_density"))
    test("Competition density present", has_comp >= 5, f"Found {has_comp}")


# ============================================================
# SECTION 6: EXIM TRADE TESTS (6 tests)
# ============================================================
def test_exim_data():
    print("\n" + "=" * 60)
    print("  SECTION 6: EXIM TRADE DATA (6 tests)")
    print("=" * 60)
    
    data = load_json("exim_trade_data.json")
    if not data:
        test("EXIM data loaded", False, "File not found")
        return
    
    # Test 1: Data loaded
    test("EXIM data loaded", len(data) > 0, f"{len(data)} molecules")
    
    # Test 2: Import volumes present
    has_volume = all("total_import_volume_kg" in d for d in data)
    test("Import volumes present", has_volume)
    
    # Test 3: Price data present
    has_price = all("average_price_per_kg" in d for d in data)
    test("Price per kg present", has_price)
    
    # Test 4: Source countries present
    has_sources = all("major_source_countries" in d and len(d["major_source_countries"]) > 0 for d in data)
    test("Source countries present", has_sources)
    
    # Test 5: China as source
    china_count = sum(1 for d in data if "China" in d.get("major_source_countries", []))
    test("China source data exists", china_count >= 5, f"Found {china_count}")
    
    # Test 6: Sitagliptin trade data
    sita = [d for d in data if "sitagliptin" in d.get("molecule", "").lower()]
    test("Sitagliptin trade data exists", len(sita) >= 1)


# ============================================================
# SECTION 7: SOCIAL MEDIA TESTS (6 tests)
# ============================================================
def test_social_data():
    print("\n" + "=" * 60)
    print("  SECTION 7: SOCIAL MEDIA / PATIENT VOICE (6 tests)")
    print("=" * 60)
    
    data = load_json("social_media_posts.json")
    if not data:
        test("Social data loaded", False, "File not found")
        return
    
    # Test 1: Data loaded
    test("Social data loaded", len(data) > 0, f"{len(data)} posts")
    
    # Test 2: Diabetes posts
    diabetes = [d for d in data if "diabetes" in d.get("therapy_area", "").lower()]
    test("Diabetes posts exist", len(diabetes) >= 5, f"Found {len(diabetes)}")
    
    # Test 3: Sentiment data
    has_sentiment = all("sentiment" in d for d in data)
    test("Sentiment scores present", has_sentiment)
    
    # Test 4: Negative sentiment posts
    negative = [d for d in data if d.get("sentiment", 0) < 0]
    test("Negative sentiment posts exist", len(negative) >= 5, f"Found {len(negative)}")
    
    # Test 5: Complaint themes
    themes_found = set()
    for d in data:
        theme = d.get("complaint_theme", "")
        if theme:
            themes_found.add(theme)
    test("Multiple complaint themes exist", len(themes_found) >= 5, f"Found {len(themes_found)}")
    
    # Test 6: Respiratory posts
    resp = [d for d in data if "respiratory" in d.get("therapy_area", "").lower()]
    test("Respiratory posts exist", len(resp) >= 3, f"Found {len(resp)}")


# ============================================================
# SECTION 8: PYTHON SYNTAX TESTS (12 tests)
# ============================================================
def test_python_syntax():
    print("\n" + "=" * 60)
    print("  SECTION 8: PYTHON SYNTAX VALIDATION (12 tests)")
    print("=" * 60)
    
    files = [
        "app.py",
        "run.py",
        "src/tools/iqvia_tool.py",
        "src/tools/exim_tool.py",
        "src/tools/patent_tool.py",
        "src/tools/competitor_tool.py",
        "src/tools/clinical_tool.py",
        "src/tools/social_tool.py",
        "src/tools/internal_tool.py",
        "src/tools/web_tool.py",
        "src/services/report_generator.py",
        "pages/4_Admin.py",
    ]
    
    for filepath in files:
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    source = f.read()
                compile(source, filepath, "exec")
                test(f"Syntax: {filepath}", True)
            except SyntaxError as e:
                test(f"Syntax: {filepath}", False, f"Line {e.lineno}: {e.msg}")
        else:
            test(f"Syntax: {filepath}", False, "File not found")


# ============================================================
# MAIN
# ============================================================
def main():
    start = datetime.now()
    
    print("\n" + "=" * 60)
    print("  PHARMA AGENTIC AI - COMPREHENSIVE TEST SUITE")
    print(f"  {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # Run all test sections
    test_mock_data_files()    # 8 tests
    test_iqvia_data()         # 8 tests
    test_patent_data()        # 8 tests (variable)
    test_competitor_data()    # 8 tests
    test_clinical_data()      # 6 tests
    test_exim_data()          # 6 tests
    test_social_data()        # 6 tests
    test_python_syntax()      # 12 tests
    
    # Summary
    elapsed = (datetime.now() - start).total_seconds()
    passed = len(results["passed"])
    failed = len(results["failed"])
    total = passed + failed
    
    print("\n" + "=" * 60)
    print("  FINAL SUMMARY")
    print("=" * 60)
    print(f"  Total Tests: {total}")
    print(f"  Passed: {passed} ({100*passed/total:.1f}%)")
    print(f"  Failed: {failed} ({100*failed/total:.1f}%)")
    print(f"  Time: {elapsed:.2f}s")
    
    if failed > 0:
        print("\n  FAILED TESTS:")
        for name, details in results["failed"]:
            print(f"    - {name}: {details}")
    
    print("=" * 60)
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
