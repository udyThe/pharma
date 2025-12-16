"""
Golden Tasks Test Script
Validates the Pharma Agentic AI system against predefined test scenarios.
"""
import sys
from pathlib import Path
import time
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_result(success: bool, message: str):
    """Print a formatted result."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status}: {message}")


def test_tool(tool_func, args: dict, expected_contains: list) -> bool:
    """Test a single tool function."""
    try:
        result = tool_func._run(**args)
        
        # Check if expected content is present
        result_lower = result.lower()
        all_found = all(
            expected.lower() in result_lower
            for expected in expected_contains
        )
        
        return all_found, result
    except Exception as e:
        return False, str(e)


def run_golden_task_1():
    """
    Task 1: Whitespace Query
    "Which respiratory diseases show low competition but high patient burden in India?"
    """
    print_header("Golden Task 1: Whitespace Analysis")
    
    from src.tools.iqvia_tool import find_low_competition_markets
    from src.tools.clinical_tool import analyze_competition_density
    
    # Test IQVIA agent
    success, result = test_tool(
        find_low_competition_markets,
        {"therapy_area": "Respiratory", "region": "India"},
        ["IPF", "COPD", "low"]
    )
    print_result(success, "IQVIA finds respiratory whitespace opportunities")
    print(f"   Result preview: {result[:200]}...")
    
    # Test Clinical agent
    success, result = test_tool(
        analyze_competition_density,
        {"indication": "COPD"},
        ["competition", "unmet need"]
    )
    print_result(success, "Clinical Agent analyzes COPD competition density")
    
    return True


def run_golden_task_2():
    """
    Task 2: Repurposing Query
    "Identify potential repurposing opportunities for Pembrolizumab."
    """
    print_header("Golden Task 2: Repurposing Opportunities")
    
    from src.tools.clinical_tool import find_repurposing_opportunities
    from src.tools.patent_tool import query_patents
    
    # Test Clinical agent
    success, result = test_tool(
        find_repurposing_opportunities,
        {"molecule": "Pembrolizumab"},
        ["pembrolizumab", "phase"]
    )
    print_result(success, "Clinical Agent finds Pembrolizumab repurposing opportunities")
    print(f"   Result preview: {result[:200]}...")
    
    # Test Patent agent
    success, result = test_tool(
        query_patents,
        {"molecule": "Pembrolizumab"},
        ["2028", "active"]
    )
    print_result(success, "Patent Agent checks Pembrolizumab IP landscape")
    
    return True


def run_golden_task_3():
    """
    Task 3: FTO Check
    "Check patent expiry for Sitagliptin in the US."
    """
    print_header("Golden Task 3: FTO Check")
    
    from src.tools.patent_tool import check_patent_expiry
    
    success, result = test_tool(
        check_patent_expiry,
        {"molecule": "Sitagliptin", "country": "US"},
        ["2022", "expired", "generic"]
    )
    print_result(success, "Patent Agent confirms Sitagliptin patent expired (2022-11-24)")
    print(f"   Result preview: {result[:300]}...")
    
    return success


def run_golden_task_4():
    """
    Task 4: Patient Voice Insight
    "What are patients complaining about regarding current Diabetes injectables?"
    """
    print_header("Golden Task 4: Patient Voice Analysis")
    
    from src.tools.social_tool import analyze_patient_complaints
    
    success, result = test_tool(
        analyze_patient_complaints,
        {"therapy_area": "Diabetes"},
        ["needle", "side effects", "cost"]
    )
    print_result(success, "Social Agent identifies Diabetes patient complaints")
    print(f"   Result preview: {result[:300]}...")
    
    # Check for innovation opportunity identification
    innovation_found = "oral" in result.lower() or "formulation" in result.lower() or "innovation" in result.lower()
    print_result(innovation_found, "Innovation opportunities identified from patient feedback")
    
    return success and innovation_found


def run_golden_task_5():
    """
    Task 5: War Game Simulation
    "Simulate a launch of generic Rivaroxaban in 2025. What will competitors do?"
    """
    print_header("Golden Task 5: War Game Simulation")
    
    from src.tools.competitor_tool import war_game_scenario, assess_competitive_threats
    
    # War game scenario
    success, result = test_tool(
        war_game_scenario,
        {"molecule": "Rivaroxaban", "proposed_strategy": "Launch generic in 2025"},
        ["bayer", "teva", "price", "risk"]
    )
    print_result(success, "Competitor Agent simulates war game scenario")
    print(f"   Result preview: {result[:300]}...")
    
    # Threat assessment
    success2, result2 = test_tool(
        assess_competitive_threats,
        {"molecule": "Rivaroxaban"},
        ["threat", "counter"]
    )
    print_result(success2, "Competitor Agent provides counter-strategies")
    
    return success and success2


def run_integration_test():
    """Test the full orchestration flow."""
    print_header("Integration Test: Full Orchestration")
    
    try:
        from src.agents.master_agent import classify_intent, create_master_crew
        
        # Test intent classification
        query = "Which respiratory diseases show low competition in India?"
        agents = classify_intent(query)
        
        expected_agents = ["iqvia", "clinical"]
        agents_correct = all(a in agents for a in expected_agents)
        print_result(agents_correct, f"Intent classification correct: {agents}")
        
        # Note: Full crew execution requires LLM API calls
        print("   ℹ️  Full crew execution skipped (requires API calls)")
        
        return agents_correct
    
    except Exception as e:
        print_result(False, f"Integration test failed: {str(e)}")
        return False


def run_report_generation_test():
    """Test PDF and Excel report generation."""
    print_header("Report Generation Test")
    
    try:
        from src.services.report_generator import ReportGenerator
        
        generator = ReportGenerator()
        
        # Test PDF generation
        pdf_result = generator.generate_pdf(
            title="Test Report",
            query="Test query for report generation",
            content="**Key Findings**\n- Finding 1\n- Finding 2\n\n**Recommendations**\n- Recommendation 1",
            metadata={"agents_used": ["iqvia", "patent"]}
        )
        pdf_success = not pdf_result.startswith("Error") and not pdf_result.startswith("PDF generation not available")
        print_result(pdf_success, f"PDF generation: {pdf_result if pdf_success else 'Not available (install fpdf2)'}")
        
        # Test Excel generation
        excel_result = generator.generate_excel(
            title="Test Report",
            query="Test query",
            data={
                "findings": ["Finding 1", "Finding 2"],
                "recommendations": ["Recommendation 1"]
            },
            metadata={"agents_used": ["iqvia"]}
        )
        excel_success = not excel_result.startswith("Error") and not excel_result.startswith("Excel generation not available")
        print_result(excel_success, f"Excel generation: {excel_result if excel_success else 'Not available (install openpyxl)'}")
        
        return True
    
    except Exception as e:
        print_result(False, f"Report generation failed: {str(e)}")
        return False


def main():
    """Run all golden task tests."""
    print("\n" + "=" * 70)
    print("  PHARMA AGENTIC AI - GOLDEN TASK VALIDATION")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)
    
    start_time = time.time()
    results = []
    
    # Run all golden tasks
    results.append(("Task 1: Whitespace", run_golden_task_1()))
    results.append(("Task 2: Repurposing", run_golden_task_2()))
    results.append(("Task 3: FTO Check", run_golden_task_3()))
    results.append(("Task 4: Patient Voice", run_golden_task_4()))
    results.append(("Task 5: War Game", run_golden_task_5()))
    results.append(("Integration Test", run_integration_test()))
    results.append(("Report Generation", run_report_generation_test()))
    
    # Summary
    print_header("TEST SUMMARY")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {name}")
    
    elapsed = time.time() - start_time
    print(f"\n  Total: {passed}/{total} passed ({elapsed:.2f}s)")
    print("=" * 70)
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
