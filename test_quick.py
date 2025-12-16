"""
Quick Data Loading Test
Tests the JSON data loading directly without crewai dependencies.
"""
import json
import sys
from pathlib import Path

# Add src to path
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))

def test_mock_data_files():
    """Test that all mock data files exist and are valid JSON."""
    print("\n" + "=" * 60)
    print("  MOCK DATA FILE TESTS")
    print("=" * 60)
    
    mock_dir = PROJECT_ROOT / "mock_data"
    files = [
        ("iqvia_market_data.json", ["molecule", "therapy_area"]),
        ("exim_trade_data.json", ["molecule", "total_import_volume_kg"]),
        ("clinical_trials.json", ["indication", "active_trials"]),
        ("competitor_strategies.json", ["molecule", "competitor"]),
        ("social_media_posts.json", ["molecule", "sentiment"]),
        ("uspto_patents.json", ["molecule", "patents"]),
        ("web_search_results.json", ["query", "results"]),
        ("internal_docs_metadata.json", ["doc_id", "title"]),
    ]
    
    passed = 0
    failed = 0
    
    for filename, required_keys in files:
        filepath = mock_dir / filename
        if filepath.exists():
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list) and len(data) > 0:
                        first_item = data[0]
                        has_keys = all(k in first_item for k in required_keys)
                        if has_keys:
                            print(f"  [PASS] {filename}: {len(data)} entries")
                            passed += 1
                        else:
                            print(f"  [FAIL] {filename}: Missing keys {required_keys}")
                            failed += 1
                    else:
                        print(f"  [FAIL] {filename}: Empty or not a list")
                        failed += 1
            except json.JSONDecodeError as e:
                print(f"  [FAIL] {filename}: Invalid JSON - {e}")
                failed += 1
        else:
            print(f"  [FAIL] {filename}: File not found")
            failed += 1
    
    print(f"\n  Result: {passed}/{passed+failed} passed")
    return failed == 0


def test_data_loading_functions():
    """Test data loading without crewai imports."""
    print("\n" + "=" * 60)
    print("  DATA LOADING FUNCTION TESTS")
    print("=" * 60)
    
    tests = []
    
    # Test competitor data loading
    try:
        data_path = PROJECT_ROOT / "mock_data" / "competitor_strategies.json"
        with open(data_path, "r") as f:
            data = json.load(f)
        
        # Filter test
        rivaroxaban = [d for d in data if "rivaroxaban" in d.get("molecule", "").lower()]
        if len(rivaroxaban) >= 2:
            print(f"  [PASS] Competitor: Found {len(rivaroxaban)} entries for Rivaroxaban")
            tests.append(True)
        else:
            print(f"  [FAIL] Competitor: Expected 2+ Rivaroxaban entries, got {len(rivaroxaban)}")
            tests.append(False)
    except Exception as e:
        print(f"  [FAIL] Competitor: {e}")
        tests.append(False)
    
    # Test patent data loading
    try:
        data_path = PROJECT_ROOT / "mock_data" / "uspto_patents.json"
        with open(data_path, "r") as f:
            data = json.load(f)
        
        # Find Semaglutide (brand: Ozempic)
        semaglutide = [d for d in data if "semaglutide" in d.get("molecule", "").lower()]
        if len(semaglutide) >= 1:
            patents = semaglutide[0].get("patents", [])
            if len(patents) >= 2:
                print(f"  [PASS] Patent: Semaglutide has {len(patents)} patents")
                tests.append(True)
            else:
                print(f"  [FAIL] Patent: Expected 2+ patents for Semaglutide")
                tests.append(False)
        else:
            print(f"  [FAIL] Patent: Semaglutide not found")
            tests.append(False)
    except Exception as e:
        print(f"  [FAIL] Patent: {e}")
        tests.append(False)
    
    # Test IQVIA data loading
    try:
        data_path = PROJECT_ROOT / "mock_data" / "iqvia_market_data.json"
        with open(data_path, "r") as f:
            data = json.load(f)
        
        # Find respiratory therapy area
        respiratory = [d for d in data if "respiratory" in d.get("therapy_area", "").lower()]
        if len(respiratory) >= 3:
            print(f"  [PASS] IQVIA: Found {len(respiratory)} respiratory entries")
            tests.append(True)
        else:
            print(f"  [FAIL] IQVIA: Expected 3+ respiratory entries")
            tests.append(False)
    except Exception as e:
        print(f"  [FAIL] IQVIA: {e}")
        tests.append(False)
    
    # Test EXIM data loading
    try:
        data_path = PROJECT_ROOT / "mock_data" / "exim_trade_data.json"
        with open(data_path, "r") as f:
            data = json.load(f)
        
        # Find Sitagliptin
        sitagliptin = [d for d in data if "sitagliptin" in d.get("molecule", "").lower()]
        if len(sitagliptin) >= 1:
            print(f"  [PASS] EXIM: Found Sitagliptin trade data")
            tests.append(True)
        else:
            print(f"  [FAIL] EXIM: Sitagliptin not found")
            tests.append(False)
    except Exception as e:
        print(f"  [FAIL] EXIM: {e}")
        tests.append(False)
    
    # Test Clinical data loading
    try:
        data_path = PROJECT_ROOT / "mock_data" / "clinical_trials.json"
        with open(data_path, "r") as f:
            data = json.load(f)
        
        # Find COPD indication
        copd = [d for d in data if "copd" in d.get("indication", "").lower()]
        if len(copd) >= 1:
            trials = copd[0].get("active_trials", [])
            print(f"  [PASS] Clinical: COPD has {len(trials)} active trials")
            tests.append(True)
        else:
            print(f"  [FAIL] Clinical: COPD not found")
            tests.append(False)
    except Exception as e:
        print(f"  [FAIL] Clinical: {e}")
        tests.append(False)
    
    # Test Social data loading
    try:
        data_path = PROJECT_ROOT / "mock_data" / "social_media_posts.json"
        with open(data_path, "r") as f:
            data = json.load(f)
        
        # Find diabetes posts
        diabetes = [d for d in data if "diabetes" in d.get("therapy_area", "").lower()]
        if len(diabetes) >= 2:
            print(f"  [PASS] Social: Found {len(diabetes)} diabetes posts")
            tests.append(True)
        else:
            print(f"  [FAIL] Social: Expected 2+ diabetes posts")
            tests.append(False)
    except Exception as e:
        print(f"  [FAIL] Social: {e}")
        tests.append(False)
    
    passed = sum(tests)
    total = len(tests)
    print(f"\n  Result: {passed}/{total} passed")
    return all(tests)


def test_python_syntax():
    """Test that all Python files have valid syntax."""
    print("\n" + "=" * 60)
    print("  PYTHON SYNTAX TESTS")
    print("=" * 60)
    
    files_to_check = [
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
    
    passed = 0
    failed = 0
    
    for filepath in files_to_check:
        full_path = PROJECT_ROOT / filepath
        if full_path.exists():
            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    source = f.read()
                compile(source, filepath, "exec")
                print(f"  [PASS] {filepath}")
                passed += 1
            except SyntaxError as e:
                print(f"  [FAIL] {filepath}: Line {e.lineno}: {e.msg}")
                failed += 1
        else:
            print(f"  [SKIP] {filepath}: Not found")
    
    print(f"\n  Result: {passed}/{passed+failed} passed")
    return failed == 0


def main():
    print("\n" + "=" * 60)
    print("  PHARMA AI - QUICK VALIDATION TEST")
    print("  (Bypasses crewai to test core functionality)")
    print("=" * 60)
    
    results = []
    
    results.append(("Mock Data Files", test_mock_data_files()))
    results.append(("Data Loading", test_data_loading_functions()))
    results.append(("Python Syntax", test_python_syntax()))
    
    print("\n" + "=" * 60)
    print("  SUMMARY")
    print("=" * 60)
    
    for name, passed in results:
        status = "[PASS]" if passed else "[FAIL]"
        print(f"  {status} {name}")
    
    all_passed = all(r[1] for r in results)
    print(f"\n  Overall: {'ALL TESTS PASSED' if all_passed else 'SOME TESTS FAILED'}")
    print("=" * 60)
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
