#!/usr/bin/env python3
"""Demo evaluation showing GPT-5 vs Claude Opus 4.1 comparison results."""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path

from src.evaluation.results import EvaluationResult, EvaluationReport
from src.evaluation.metrics import PassKMetric, SuccessRateMetric, PolicyComplianceMetric, ResponseQualityMetric
from src.domains.retail.scenarios import get_retail_scenarios


def generate_mock_conversation(scenario_id: str, model_name: str, trial_id: int, success_rate: float) -> dict:
    """Generate a realistic mock conversation result."""
    
    scenarios_manager = get_retail_scenarios()
    scenario = scenarios_manager.get_scenario(scenario_id)
    
    # Determine success based on model's success rate
    success = random.random() < success_rate
    
    # Generate realistic metrics based on model characteristics
    model_characteristics = get_model_characteristics(model_name)
    
    # Mock conversation turns (2-6 turns)
    turns = random.randint(2, 6)
    
    # Mock tools used based on scenario
    tools_used = generate_mock_tools_used(scenario.expected_tools, model_characteristics)
    
    # Mock policy violations based on model
    violations = generate_mock_violations(model_characteristics, scenario.policy_focus)
    
    # Mock quality ratings
    quality = generate_mock_quality_ratings(model_characteristics)
    
    duration = random.uniform(15.0, 45.0)  # 15-45 seconds
    
    return {
        "task_id": f"{scenario_id}_{trial_id}",
        "model_name": model_name,
        "scenario_id": scenario_id,
        "trial_id": trial_id,
        "success": success,
        "completion_reason": "success_criteria_met" if success else "insufficient_criteria",
        "conversation_turns": turns,
        "tools_used": tools_used,
        "policy_violations": violations,
        "duration_seconds": duration,
        "timestamp": datetime.now().isoformat(),
        "conversation_history": generate_mock_conversation_history(turns, success, scenario),
        "success_criteria_met": {criterion: success for criterion in scenario.success_criteria},
        "quality_ratings": quality
    }


def get_model_characteristics(model_name: str) -> dict:
    """Get characteristics for different models to simulate realistic behavior."""
    
    characteristics = {
        "gpt5": {
            "success_rate": 0.92,  # Very high success rate
            "tool_usage_accuracy": 0.95,  # Excellent tool usage
            "policy_compliance": 0.88,  # Good compliance
            "response_quality": {
                "relevance": 0.93,
                "completeness": 0.91, 
                "clarity": 0.94,
                "helpfulness": 0.92
            },
            "common_violations": ["purchase_pressure"],  # Occasional sales pressure
            "violation_rate": 0.12
        },
        "claude_opus_4_1": {
            "success_rate": 0.89,  # High success rate
            "tool_usage_accuracy": 0.97,  # Excellent tool usage
            "policy_compliance": 0.95,  # Excellent compliance
            "response_quality": {
                "relevance": 0.91,
                "completeness": 0.93,
                "clarity": 0.96,
                "helpfulness": 0.94
            },
            "common_violations": ["inventory_misrepresentation"],  # Rare violations
            "violation_rate": 0.05
        }
    }
    
    return characteristics.get(model_name, characteristics["gpt5"])


def generate_mock_tools_used(expected_tools: list, characteristics: dict) -> list:
    """Generate realistic tool usage based on model characteristics."""
    tools_used = []
    
    # Use most expected tools based on accuracy
    accuracy = characteristics["tool_usage_accuracy"]
    
    for tool in expected_tools:
        if random.random() < accuracy:
            tools_used.append({
                "tool": tool,
                "arguments": {"mock": "arguments"},
                "result": {"success": True, "mock": "result"}
            })
    
    return tools_used


def generate_mock_violations(characteristics: dict, policy_focus: list) -> list:
    """Generate realistic policy violations."""
    violations = []
    
    if random.random() < characteristics["violation_rate"]:
        violation_type = random.choice(characteristics.get("common_violations", ["pricing_error"]))
        severity = random.uniform(0.3, 0.8)
        
        violations.append({
            "policy_type": violation_type,
            "severity": severity,
            "description": f"Mock {violation_type} violation"
        })
    
    return violations


def generate_mock_quality_ratings(characteristics: dict) -> dict:
    """Generate realistic quality ratings with some variance."""
    base_quality = characteristics["response_quality"]
    
    # Add some random variance (±0.1)
    return {
        dimension: max(0.0, min(1.0, base_score + random.uniform(-0.1, 0.1)))
        for dimension, base_score in base_quality.items()
    }


def generate_mock_conversation_history(turns: int, success: bool, scenario) -> list:
    """Generate a mock conversation history."""
    history = []
    
    # Start with user message
    starter = random.choice(scenario.conversation_starters)
    history.append({"role": "user", "content": starter, "tool_calls": None})
    
    # Add alternating assistant/user messages
    for i in range(turns - 1):
        if i % 2 == 0:  # Assistant turn
            content = f"Mock assistant response for turn {i+1}"
            tool_calls = [{"id": f"call_{i}", "type": "function", "function": {"name": "search_products", "arguments": {}}}] if i == 0 else None
            history.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
        else:  # User follow-up
            content = f"Mock user follow-up for turn {i+1}"
            history.append({"role": "user", "content": content, "tool_calls": None})
    
    return history


def create_demo_evaluation() -> EvaluationResult:
    """Create a comprehensive demo evaluation."""
    
    print("🚀 Generating Demo Evaluation: GPT-5 vs Claude Opus 4.1")
    print("=" * 60)
    
    scenarios_manager = get_retail_scenarios()
    all_scenarios = list(scenarios_manager.scenarios.keys())
    
    models = ["gpt5", "claude_opus_4_1"]
    trials = 5
    
    all_results = []
    start_time = datetime.now()
    
    # Generate results for each model and scenario
    for model in models:
        characteristics = get_model_characteristics(model)
        success_rate = characteristics["success_rate"]
        
        print(f"📊 Generating results for {model} (success rate: {success_rate:.1%})")
        
        for scenario_id in all_scenarios:
            for trial in range(trials):
                result = generate_mock_conversation(scenario_id, model, trial, success_rate)
                all_results.append(result)
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    # Calculate metrics
    metrics = {}
    
    pass_k_metric = PassKMetric(k_values=[1, 3, 5])
    success_metric = SuccessRateMetric()
    compliance_metric = PolicyComplianceMetric()
    quality_metric = ResponseQualityMetric()
    
    metrics["pass_k"] = pass_k_metric.calculate(all_results)
    metrics["success_rate"] = success_metric.calculate(all_results)
    metrics["policy_compliance"] = compliance_metric.calculate(all_results)
    metrics["response_quality"] = quality_metric.calculate(all_results)
    
    # Create evaluation result
    evaluation = EvaluationResult(
        evaluation_id=f"demo_gpt5_vs_claude_opus_4_1_{int(datetime.now().timestamp())}",
        start_time=start_time,
        end_time=end_time,
        duration_seconds=duration,
        models_evaluated=models,
        scenarios_evaluated=all_scenarios,
        total_conversations=len(all_results),
        results=all_results,
        metrics=metrics,
        configuration={
            "num_trials": trials,
            "max_conversation_turns": 8,
            "domains": ["retail"],
            "demo": True
        }
    )
    
    return evaluation


def main():
    """Run the demo evaluation."""
    
    print("\n🎯 LLM Agent Evaluation Framework - GPT-5 vs Claude Opus 4.1 Demo")
    print("=" * 70)
    print("Note: This is a demonstration using simulated data based on expected")
    print("model performance characteristics. Real evaluation requires API keys.")
    print()
    
    # Create demo evaluation
    evaluation = create_demo_evaluation()
    
    # Generate reports
    print("\n📈 Evaluation Results")
    print("=" * 50)
    
    summary_report = EvaluationReport.generate_summary_report(evaluation)
    print(summary_report)
    
    # Show detailed model comparison
    print("\n🔍 Detailed Model Comparison")
    print("=" * 50)
    
    success_by_model = evaluation.get_success_rate_by_model()
    performance = evaluation.get_performance_summary()
    violations = evaluation.get_policy_violations_summary()
    tool_usage = evaluation.get_tool_usage_summary()
    
    print(f"**Overall Results:**")
    print(f"• Total Conversations: {evaluation.total_conversations}")
    print(f"• Evaluation Duration: {evaluation.duration_seconds:.1f}s")
    print(f"• Average Conversation Duration: {performance['average_conversation_duration']:.1f}s")
    print(f"• Average Conversation Turns: {performance['average_conversation_turns']:.1f}")
    print()
    
    print("**Success Rates by Model:**")
    for model, rate in success_by_model.items():
        model_display = "GPT-5" if model == "gpt5" else "Claude Opus 4.1"
        print(f"• {model_display}: {rate:.1%}")
    
    print(f"\n**Policy Compliance:**")
    print(f"• Total Violations: {violations['total_violations']}")
    print(f"• Violation Rate: {violations['violation_rate']:.1%}")
    
    violations_by_model = violations['violations_by_model']
    for model, count in violations_by_model.items():
        model_display = "GPT-5" if model == "gpt5" else "Claude Opus 4.1"
        model_results = evaluation.get_results_by_model(model)
        model_rate = count / len(model_results) if model_results else 0
        print(f"  - {model_display}: {count} violations ({model_rate:.1%} rate)")
    
    print(f"\n**Quality Metrics (from τ-bench methodology):**")
    for metric_name, metric_result in evaluation.metrics.items():
        print(f"• {metric_name.replace('_', ' ').title()}: {metric_result.value:.3f}")
        
        # Show model breakdown for key metrics
        if metric_name in ["pass_k", "success_rate"]:
            details = metric_result.details
            if "pass_k_values" in details:
                for k, value in details["pass_k_values"].items():
                    print(f"  - {k}: {value:.3f}")
    
    print(f"\n**Key Insights:**")
    gpt5_success = success_by_model.get("gpt5", 0)
    claude_success = success_by_model.get("claude_opus_4_1", 0)
    
    if gpt5_success > claude_success:
        winner = "GPT-5"
        margin = (gpt5_success - claude_success) * 100
    else:
        winner = "Claude Opus 4.1" 
        margin = (claude_success - gpt5_success) * 100
    
    print(f"• **Overall Winner**: {winner} (by {margin:.1f}% success rate)")
    
    gpt5_violations = violations_by_model.get("gpt5", 0)
    claude_violations = violations_by_model.get("claude_opus_4_1", 0)
    
    if claude_violations < gpt5_violations:
        print(f"• **Best Policy Compliance**: Claude Opus 4.1 ({claude_violations} vs {gpt5_violations} violations)")
    else:
        print(f"• **Best Policy Compliance**: GPT-5 ({gpt5_violations} vs {claude_violations} violations)")
    
    # Save results
    results_dir = Path("results")
    results_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    json_file = results_dir / f"demo_evaluation_{timestamp}.json"
    report_file = results_dir / f"demo_report_{timestamp}.md"
    
    evaluation.save_to_file(str(json_file))
    
    with open(report_file, 'w') as f:
        f.write(f"# GPT-5 vs Claude Opus 4.1 - Demo Evaluation Report\n\n")
        f.write(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n\n")
        f.write(summary_report)
    
    print(f"\n💾 **Results Saved:**")
    print(f"• JSON Data: {json_file}")
    print(f"• Report: {report_file}")
    
    print(f"\n✅ **Demo Complete!**")
    print("To run real evaluations with actual API calls:")
    print("1. Set OPENAI_API_KEY and ANTHROPIC_API_KEY environment variables")
    print("2. Run: python3 main.py --models gpt5 claude_opus_4_1 --trials 5")


if __name__ == "__main__":
    main()