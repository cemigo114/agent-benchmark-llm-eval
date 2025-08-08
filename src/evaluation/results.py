"""Evaluation results data structures."""

from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from pydantic import BaseModel

from ..utils.logging import get_logger

logger = get_logger(__name__)


class TaskResult(BaseModel):
    """Result for a single task/conversation."""
    task_id: str
    model_name: str
    scenario_id: str
    trial_id: int
    success: bool
    completion_reason: str
    conversation_turns: int
    tools_used: List[Dict[str, Any]]
    policy_violations: List[Dict[str, Any]]
    duration_seconds: float
    timestamp: str
    conversation_history: List[Dict[str, Any]]
    success_criteria_met: Dict[str, bool]
    quality_ratings: Dict[str, float]


class EvaluationResult(BaseModel):
    """Complete evaluation results across multiple models and scenarios."""
    evaluation_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    models_evaluated: List[str]
    scenarios_evaluated: List[str]
    total_conversations: int
    results: List[Dict[str, Any]]  # List of TaskResult-like dictionaries
    metrics: Dict[str, Any]  # MetricResult objects
    configuration: Dict[str, Any]
    
    def get_results_by_model(self, model_name: str) -> List[Dict[str, Any]]:
        """Get all results for a specific model."""
        return [r for r in self.results if r.get("model_name") == model_name]
    
    def get_results_by_scenario(self, scenario_id: str) -> List[Dict[str, Any]]:
        """Get all results for a specific scenario."""
        return [r for r in self.results if r.get("scenario_id") == scenario_id]
    
    def get_success_rate_by_model(self) -> Dict[str, float]:
        """Calculate success rate for each model."""
        model_success_rates = {}
        
        for model in self.models_evaluated:
            model_results = self.get_results_by_model(model)
            if model_results:
                success_count = sum(1 for r in model_results if r.get("success", False))
                model_success_rates[model] = success_count / len(model_results)
            else:
                model_success_rates[model] = 0.0
        
        return model_success_rates
    
    def get_success_rate_by_scenario(self) -> Dict[str, float]:
        """Calculate success rate for each scenario."""
        scenario_success_rates = {}
        
        for scenario in self.scenarios_evaluated:
            scenario_results = self.get_results_by_scenario(scenario)
            if scenario_results:
                success_count = sum(1 for r in scenario_results if r.get("success", False))
                scenario_success_rates[scenario] = success_count / len(scenario_results)
            else:
                scenario_success_rates[scenario] = 0.0
        
        return scenario_success_rates
    
    def get_policy_violations_summary(self) -> Dict[str, Any]:
        """Get summary of policy violations across all results."""
        violations_by_type = {}
        violations_by_model = {}
        total_violations = 0
        
        for result in self.results:
            model_name = result.get("model_name", "unknown")
            violations = result.get("policy_violations", [])
            
            if model_name not in violations_by_model:
                violations_by_model[model_name] = 0
            
            for violation in violations:
                policy_type = violation.get("policy_type", "unknown")
                severity = violation.get("severity", 0.0)
                
                if policy_type not in violations_by_type:
                    violations_by_type[policy_type] = {"count": 0, "total_severity": 0.0}
                
                violations_by_type[policy_type]["count"] += 1
                violations_by_type[policy_type]["total_severity"] += severity
                violations_by_model[model_name] += 1
                total_violations += 1
        
        # Calculate average severity for each violation type
        for violation_type in violations_by_type:
            count = violations_by_type[violation_type]["count"]
            if count > 0:
                violations_by_type[violation_type]["avg_severity"] = (
                    violations_by_type[violation_type]["total_severity"] / count
                )
            else:
                violations_by_type[violation_type]["avg_severity"] = 0.0
        
        return {
            "total_violations": total_violations,
            "violations_by_type": violations_by_type,
            "violations_by_model": violations_by_model,
            "violation_rate": total_violations / self.total_conversations if self.total_conversations > 0 else 0.0
        }
    
    def get_tool_usage_summary(self) -> Dict[str, Any]:
        """Get summary of tool usage across all results."""
        tool_usage_by_model = {}
        tool_usage_overall = {}
        
        for result in self.results:
            model_name = result.get("model_name", "unknown")
            tools_used = result.get("tools_used", [])
            
            if model_name not in tool_usage_by_model:
                tool_usage_by_model[model_name] = {}
            
            for tool_call in tools_used:
                tool_name = tool_call.get("tool", "unknown")
                
                # Overall usage
                if tool_name not in tool_usage_overall:
                    tool_usage_overall[tool_name] = 0
                tool_usage_overall[tool_name] += 1
                
                # Usage by model
                if tool_name not in tool_usage_by_model[model_name]:
                    tool_usage_by_model[model_name][tool_name] = 0
                tool_usage_by_model[model_name][tool_name] += 1
        
        return {
            "tool_usage_overall": tool_usage_overall,
            "tool_usage_by_model": tool_usage_by_model
        }
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary."""
        total_duration = sum(r.get("duration_seconds", 0) for r in self.results)
        avg_duration = total_duration / len(self.results) if self.results else 0
        
        avg_turns = sum(r.get("conversation_turns", 0) for r in self.results) / len(self.results) if self.results else 0
        
        return {
            "total_conversations": self.total_conversations,
            "overall_success_rate": sum(1 for r in self.results if r.get("success", False)) / len(self.results) if self.results else 0.0,
            "average_conversation_duration": avg_duration,
            "average_conversation_turns": avg_turns,
            "total_evaluation_duration": self.duration_seconds,
            "models_evaluated": len(self.models_evaluated),
            "scenarios_evaluated": len(self.scenarios_evaluated)
        }
    
    def export_to_json(self) -> str:
        """Export evaluation results to JSON format."""
        import json
        
        # Convert datetime objects to strings for JSON serialization
        export_data = {
            "evaluation_id": self.evaluation_id,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat(),
            "duration_seconds": self.duration_seconds,
            "models_evaluated": self.models_evaluated,
            "scenarios_evaluated": self.scenarios_evaluated,
            "total_conversations": self.total_conversations,
            "results": self.results,
            "metrics": {
                name: {
                    "name": metric.name,
                    "value": metric.value,
                    "details": metric.details
                }
                for name, metric in self.metrics.items()
            },
            "configuration": self.configuration,
            "summary": {
                "performance": self.get_performance_summary(),
                "success_rates": {
                    "by_model": self.get_success_rate_by_model(),
                    "by_scenario": self.get_success_rate_by_scenario()
                },
                "policy_violations": self.get_policy_violations_summary(),
                "tool_usage": self.get_tool_usage_summary()
            }
        }
        
        return json.dumps(export_data, indent=2, default=str)
    
    def save_to_file(self, filepath: str) -> None:
        """Save evaluation results to a file."""
        with open(filepath, 'w') as f:
            f.write(self.export_to_json())
        
        logger.info(f"Evaluation results saved to {filepath}")


class EvaluationReport:
    """Generates human-readable reports from evaluation results."""
    
    @staticmethod
    def generate_summary_report(results: EvaluationResult) -> str:
        """Generate a summary report of the evaluation."""
        
        performance = results.get_performance_summary()
        success_by_model = results.get_success_rate_by_model()
        policy_summary = results.get_policy_violations_summary()
        
        report_lines = [
            "# LLM Agent Evaluation Report",
            f"**Evaluation ID:** {results.evaluation_id}",
            f"**Duration:** {results.duration_seconds:.2f} seconds",
            f"**Total Conversations:** {results.total_conversations}",
            "",
            "## Overall Performance",
            f"- **Success Rate:** {performance['overall_success_rate']:.2%}",
            f"- **Average Conversation Duration:** {performance['average_conversation_duration']:.2f}s",
            f"- **Average Conversation Turns:** {performance['average_conversation_turns']:.1f}",
            "",
            "## Success Rates by Model",
        ]
        
        for model, success_rate in success_by_model.items():
            report_lines.append(f"- **{model}:** {success_rate:.2%}")
        
        report_lines.extend([
            "",
            "## Policy Compliance",
            f"- **Total Violations:** {policy_summary['total_violations']}",
            f"- **Violation Rate:** {policy_summary['violation_rate']:.2%}",
        ])
        
        if policy_summary['violations_by_type']:
            report_lines.append("- **Violations by Type:**")
            for violation_type, data in policy_summary['violations_by_type'].items():
                report_lines.append(f"  - {violation_type}: {data['count']} (avg severity: {data['avg_severity']:.2f})")
        
        report_lines.extend([
            "",
            "## Models Evaluated",
        ])
        
        for model in results.models_evaluated:
            model_results = results.get_results_by_model(model)
            successful = sum(1 for r in model_results if r.get("success", False))
            total = len(model_results)
            report_lines.append(f"- **{model}:** {successful}/{total} successful ({successful/total:.2%})")
        
        report_lines.extend([
            "",
            "## Scenarios Evaluated",
        ])
        
        scenario_success = results.get_success_rate_by_scenario()
        for scenario, success_rate in scenario_success.items():
            report_lines.append(f"- **{scenario}:** {success_rate:.2%} success rate")
        
        return "\n".join(report_lines)
    
    @staticmethod
    def generate_detailed_report(results: EvaluationResult) -> str:
        """Generate a detailed report including individual conversation results."""
        
        summary = EvaluationReport.generate_summary_report(results)
        
        detailed_lines = [
            summary,
            "",
            "## Detailed Results",
            ""
        ]
        
        # Group results by model and scenario
        for model in results.models_evaluated:
            detailed_lines.append(f"### {model}")
            model_results = results.get_results_by_model(model)
            
            for scenario in results.scenarios_evaluated:
                scenario_results = [r for r in model_results if r.get("scenario_id") == scenario]
                if not scenario_results:
                    continue
                
                detailed_lines.append(f"#### {scenario}")
                
                for result in scenario_results:
                    success_indicator = "✅" if result.get("success", False) else "❌"
                    detailed_lines.extend([
                        f"{success_indicator} **Trial {result.get('trial_id', 0)}**",
                        f"  - Duration: {result.get('duration_seconds', 0):.2f}s",
                        f"  - Turns: {result.get('conversation_turns', 0)}",
                        f"  - Tools Used: {len(result.get('tools_used', []))}",
                        f"  - Policy Violations: {len(result.get('policy_violations', []))}",
                        f"  - Completion: {result.get('completion_reason', 'unknown')}",
                        ""
                    ])
        
        return "\n".join(detailed_lines)