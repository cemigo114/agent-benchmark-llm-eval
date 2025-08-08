"""Evaluation metrics for agent performance."""

import math
from abc import ABC, abstractmethod
from typing import Any, Dict, List

from pydantic import BaseModel

from ..utils.logging import get_logger

logger = get_logger(__name__)


class MetricResult(BaseModel):
    """Result of a metric evaluation."""
    name: str
    value: float
    details: Dict[str, Any] = {}


class BaseMetric(ABC):
    """Abstract base class for evaluation metrics."""
    
    @abstractmethod
    def calculate(self, results: List[Dict[str, Any]]) -> MetricResult:
        """Calculate the metric value from evaluation results."""
        pass


class SuccessRateMetric(BaseMetric):
    """Basic success rate metric."""
    
    def calculate(self, results: List[Dict[str, Any]]) -> MetricResult:
        """Calculate success rate as percentage of successful completions."""
        if not results:
            return MetricResult(name="success_rate", value=0.0)
        
        successful = sum(1 for r in results if r.get("success", False))
        rate = successful / len(results)
        
        return MetricResult(
            name="success_rate",
            value=rate,
            details={
                "successful": successful,
                "total": len(results),
                "percentage": rate * 100
            }
        )


class PassKMetric(BaseMetric):
    """Pass@K metric measuring reliability across multiple trials."""
    
    def __init__(self, k_values: List[int] = None):
        self.k_values = k_values or [1, 3, 5, 8, 10]
    
    def calculate(self, results: List[Dict[str, Any]]) -> MetricResult:
        """Calculate Pass@K for different values of K."""
        if not results:
            return MetricResult(name="pass_k", value=0.0)
        
        # Group results by task_id to get multiple trials per task
        task_groups = {}
        for result in results:
            task_id = result.get("task_id", "default")
            if task_id not in task_groups:
                task_groups[task_id] = []
            task_groups[task_id].append(result.get("success", False))
        
        pass_k_values = {}
        
        for k in self.k_values:
            if not task_groups:
                pass_k_values[f"pass@{k}"] = 0.0
                continue
                
            task_pass_rates = []
            
            for task_id, trials in task_groups.items():
                # Only consider tasks with at least k trials
                if len(trials) < k:
                    continue
                    
                # Calculate pass@k for this task
                n_success = sum(trials[:k])  # Take first k trials
                n_total = k
                
                # pass@k = probability of at least one success in k trials
                # = 1 - P(all k trials fail)
                if n_success == 0:
                    task_pass_k = 0.0
                elif n_success == k:
                    task_pass_k = 1.0
                else:
                    # Use binomial coefficient calculation
                    task_pass_k = 1.0 - self._binomial_prob_all_fail(n_success, n_total, k)
                
                task_pass_rates.append(task_pass_k)
            
            if task_pass_rates:
                pass_k_values[f"pass@{k}"] = sum(task_pass_rates) / len(task_pass_rates)
            else:
                pass_k_values[f"pass@{k}"] = 0.0
        
        # Use the maximum k value as the primary metric
        primary_k = max(self.k_values)
        primary_value = pass_k_values.get(f"pass@{primary_k}", 0.0)
        
        return MetricResult(
            name="pass_k",
            value=primary_value,
            details={
                "pass_k_values": pass_k_values,
                "tasks_evaluated": len(task_groups),
                "k_values": self.k_values
            }
        )
    
    def _binomial_prob_all_fail(self, n_success: int, n_total: int, k: int) -> float:
        """Calculate probability that all k samples fail."""
        if n_success >= k:
            return 0.0
        if n_success == 0:
            return 1.0
            
        # P(all k fail) = C(n_total-n_success, k) / C(n_total, k)
        try:
            prob_all_fail = (
                math.comb(n_total - n_success, k) / 
                math.comb(n_total, k)
            )
            return min(1.0, prob_all_fail)
        except (ValueError, ZeroDivisionError):
            return 1.0 if n_success == 0 else 0.0


class PolicyComplianceMetric(BaseMetric):
    """Metric for measuring adherence to domain policies."""
    
    def __init__(self, policy_weights: Dict[str, float] = None):
        self.policy_weights = policy_weights or {}
    
    def calculate(self, results: List[Dict[str, Any]]) -> MetricResult:
        """Calculate policy compliance rate."""
        if not results:
            return MetricResult(name="policy_compliance", value=0.0)
        
        compliance_scores = []
        policy_violations = {}
        
        for result in results:
            violations = result.get("policy_violations", [])
            conversation_score = 1.0
            
            for violation in violations:
                policy_type = violation.get("policy_type", "unknown")
                severity = violation.get("severity", 1.0)
                
                # Apply weight if specified
                weight = self.policy_weights.get(policy_type, 1.0)
                penalty = severity * weight
                conversation_score = max(0.0, conversation_score - penalty)
                
                # Track violation counts
                if policy_type not in policy_violations:
                    policy_violations[policy_type] = 0
                policy_violations[policy_type] += 1
            
            compliance_scores.append(conversation_score)
        
        average_compliance = sum(compliance_scores) / len(compliance_scores)
        
        return MetricResult(
            name="policy_compliance",
            value=average_compliance,
            details={
                "compliance_scores": compliance_scores,
                "policy_violations": policy_violations,
                "total_conversations": len(results),
                "perfect_compliance_count": sum(1 for s in compliance_scores if s == 1.0)
            }
        )


class ResponseQualityMetric(BaseMetric):
    """Metric for measuring response quality and appropriateness."""
    
    def calculate(self, results: List[Dict[str, Any]]) -> MetricResult:
        """Calculate response quality score."""
        if not results:
            return MetricResult(name="response_quality", value=0.0)
        
        quality_scores = []
        quality_dimensions = {
            "relevance": [],
            "completeness": [],
            "clarity": [],
            "helpfulness": []
        }
        
        for result in results:
            # Extract quality ratings from result
            quality = result.get("quality_ratings", {})
            
            # Calculate overall quality score
            dimension_scores = []
            for dimension in quality_dimensions.keys():
                score = quality.get(dimension, 0.5)  # Default to middle score
                quality_dimensions[dimension].append(score)
                dimension_scores.append(score)
            
            if dimension_scores:
                overall_score = sum(dimension_scores) / len(dimension_scores)
            else:
                overall_score = 0.5
                
            quality_scores.append(overall_score)
        
        average_quality = sum(quality_scores) / len(quality_scores)
        
        # Calculate dimension averages
        dimension_averages = {
            dim: sum(scores) / len(scores) if scores else 0.0
            for dim, scores in quality_dimensions.items()
        }
        
        return MetricResult(
            name="response_quality",
            value=average_quality,
            details={
                "quality_scores": quality_scores,
                "dimension_averages": dimension_averages,
                "total_responses": len(results)
            }
        )