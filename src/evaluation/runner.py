"""Evaluation runner for executing agent evaluations."""

import asyncio
import time
from typing import Any, Dict, List, Optional
from datetime import datetime
import json

from ..agents.factory import create_agent
from ..agents.base import Message
from ..domains.retail.tools import RetailTools, get_retail_tools
from ..domains.retail.policies import get_retail_policy_checker
from ..domains.retail.scenarios import get_retail_scenarios
from .metrics import PassKMetric, SuccessRateMetric, PolicyComplianceMetric, ResponseQualityMetric
from .results import EvaluationResult, TaskResult
from ..utils.logging import get_logger
from ..utils.config import get_config

logger = get_logger(__name__)


class EvaluationRunner:
    """Runs agent evaluations across multiple scenarios and models."""
    
    def __init__(self):
        self.config = get_config()
        self.retail_tools = RetailTools()
        self.policy_checker = get_retail_policy_checker()
        self.scenarios = get_retail_scenarios()
        
        # Initialize metrics
        self.metrics = {
            "pass_k": PassKMetric(k_values=[1, 3, 5]),
            "success_rate": SuccessRateMetric(),
            "policy_compliance": PolicyComplianceMetric(),
            "response_quality": ResponseQualityMetric()
        }
    
    async def run_evaluation(
        self,
        model_names: List[str],
        scenario_ids: Optional[List[str]] = None,
        num_trials: int = 5,
        max_conversation_turns: int = 10
    ) -> EvaluationResult:
        """Run evaluation across multiple models and scenarios."""
        
        logger.info(f"Starting evaluation with models: {model_names}")
        logger.info(f"Number of trials per scenario: {num_trials}")
        
        # Use all retail scenarios if none specified
        if scenario_ids is None:
            scenario_ids = list(self.scenarios.scenarios.keys())
        
        start_time = datetime.now()
        all_results = []
        
        for model_name in model_names:
            logger.info(f"Evaluating model: {model_name}")
            
            try:
                agent = create_agent(model_name)
                
                for scenario_id in scenario_ids:
                    logger.info(f"Running scenario: {scenario_id}")
                    
                    # Run multiple trials for this scenario
                    scenario_results = []
                    for trial in range(num_trials):
                        logger.info(f"Trial {trial + 1}/{num_trials}")
                        
                        try:
                            result = await self._run_single_conversation(
                                agent=agent,
                                scenario_id=scenario_id,
                                trial_id=trial,
                                max_turns=max_conversation_turns
                            )
                            scenario_results.append(result)
                            
                        except Exception as e:
                            logger.error(f"Error in trial {trial}: {e}")
                            # Create failed result
                            scenario_results.append(self._create_failed_result(
                                model_name, scenario_id, trial, str(e)
                            ))
                    
                    all_results.extend(scenario_results)
                    
            except Exception as e:
                logger.error(f"Error creating agent {model_name}: {e}")
                continue
        
        # Calculate overall metrics
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Group results for metric calculation
        metric_results = {}
        for metric_name, metric in self.metrics.items():
            logger.info(f"Calculating {metric_name} metric")
            metric_result = metric.calculate(all_results)
            metric_results[metric_name] = metric_result
        
        evaluation_result = EvaluationResult(
            evaluation_id=f"eval_{int(time.time())}",
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            models_evaluated=model_names,
            scenarios_evaluated=scenario_ids,
            total_conversations=len(all_results),
            results=all_results,
            metrics=metric_results,
            configuration={
                "num_trials": num_trials,
                "max_conversation_turns": max_conversation_turns,
                "domains": ["retail"]
            }
        )
        
        logger.info(f"Evaluation completed in {duration:.2f} seconds")
        logger.info(f"Total conversations: {len(all_results)}")
        
        return evaluation_result
    
    async def _run_single_conversation(
        self,
        agent,
        scenario_id: str,
        trial_id: int,
        max_turns: int = 10
    ) -> Dict[str, Any]:
        """Run a single conversation between agent and simulated user."""
        
        scenario = self.scenarios.get_scenario(scenario_id)
        if not scenario:
            raise ValueError(f"Scenario not found: {scenario_id}")
        
        conversation_start = datetime.now()
        conversation_history = []
        tools_used = []
        policy_violations = []
        
        # Initialize conversation with scenario starter
        user_message = self.scenarios.get_conversation_starter(scenario_id)
        conversation_history.append(Message(role="user", content=user_message))
        
        success = False
        completion_reason = "max_turns_reached"
        
        for turn in range(max_turns):
            try:
                # Get agent response
                agent_response = await agent.generate_response(
                    messages=conversation_history,
                    tools=get_retail_tools()
                )
                
                conversation_history.append(agent_response.message)
                
                # Execute any tool calls
                if agent_response.tool_calls:
                    for tool_call in agent_response.tool_calls:
                        tool_result = await self._execute_tool_call(tool_call)
                        tools_used.append({
                            "tool": tool_call.function,
                            "arguments": tool_call.arguments,
                            "result": tool_result
                        })
                        
                        # Add tool result to conversation
                        conversation_history.append(Message(
                            role="tool",
                            content=json.dumps(tool_result),
                            tool_call_id=tool_call.id,
                            name=tool_call.function
                        ))
                
                # Check for policy violations
                violations = self.policy_checker.check_response(
                    agent_response.message.content,
                    {"tools_used": tools_used, "scenario": scenario}
                )
                policy_violations.extend(violations)
                
                # Check if success criteria are met
                success, completion_reason = self._evaluate_success_criteria(
                    scenario, conversation_history, tools_used
                )
                
                if success:
                    break
                
                # Simulate user follow-up (simplified for now)
                if turn < max_turns - 1:
                    followup = self._generate_user_followup(scenario, conversation_history, turn)
                    if followup:
                        conversation_history.append(Message(role="user", content=followup))
                
            except Exception as e:
                logger.error(f"Error in conversation turn {turn}: {e}")
                completion_reason = f"error: {str(e)}"
                break
        
        conversation_end = datetime.now()
        duration = (conversation_end - conversation_start).total_seconds()
        
        # Create result
        result = {
            "task_id": f"{scenario_id}_{trial_id}",
            "model_name": agent.model_name,
            "scenario_id": scenario_id,
            "trial_id": trial_id,
            "success": success,
            "completion_reason": completion_reason,
            "conversation_turns": len([msg for msg in conversation_history if msg.role in ["user", "assistant"]]),
            "tools_used": tools_used,
            "policy_violations": [
                {
                    "policy_type": v.policy_type.value,
                    "severity": v.severity,
                    "description": v.description
                }
                for v in policy_violations
            ],
            "duration_seconds": duration,
            "timestamp": conversation_start.isoformat(),
            "conversation_history": [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "tool_calls": msg.tool_calls
                }
                for msg in conversation_history
            ],
            "success_criteria_met": self._check_individual_criteria(scenario, conversation_history, tools_used),
            "quality_ratings": self._assess_response_quality(conversation_history)
        }
        
        return result
    
    async def _execute_tool_call(self, tool_call) -> Dict[str, Any]:
        """Execute a tool call and return the result."""
        tool_name = tool_call.function
        arguments = tool_call.arguments
        
        try:
            if tool_name == "search_products":
                return await self.retail_tools.search_products(**arguments)
            elif tool_name == "get_product_details":
                return await self.retail_tools.get_product_details(**arguments)
            elif tool_name == "check_inventory":
                return await self.retail_tools.check_inventory(**arguments)
            elif tool_name == "place_order":
                return await self.retail_tools.place_order(**arguments)
            elif tool_name == "get_order_status":
                return await self.retail_tools.get_order_status(**arguments)
            elif tool_name == "apply_discount":
                return await self.retail_tools.apply_discount(**arguments)
            else:
                return {"error": f"Unknown tool: {tool_name}"}
                
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}")
            return {"error": f"Tool execution failed: {str(e)}"}
    
    def _evaluate_success_criteria(self, scenario, conversation_history, tools_used) -> tuple[bool, str]:
        """Evaluate if the scenario success criteria have been met."""
        criteria_met = self._check_individual_criteria(scenario, conversation_history, tools_used)
        
        # Check if all required criteria are met
        total_criteria = len(scenario.success_criteria)
        met_count = sum(criteria_met.values())
        
        success = met_count >= (total_criteria * 0.8)  # 80% of criteria must be met
        
        if success:
            return True, f"success_criteria_met ({met_count}/{total_criteria})"
        else:
            return False, f"insufficient_criteria ({met_count}/{total_criteria})"
    
    def _check_individual_criteria(self, scenario, conversation_history, tools_used) -> Dict[str, bool]:
        """Check each individual success criterion."""
        criteria_met = {}
        tools_used_names = [tool["tool"] for tool in tools_used]
        conversation_text = " ".join([msg.content for msg in conversation_history if msg.content])
        
        for criterion in scenario.success_criteria:
            criterion_lower = criterion.lower()
            met = False
            
            # Check tool usage criteria
            for expected_tool in scenario.expected_tools:
                if expected_tool in criterion_lower and expected_tool in tools_used_names:
                    met = True
                    break
            
            # Check content criteria
            if "pricing" in criterion_lower and ("price" in conversation_text.lower() or "$" in conversation_text):
                met = True
            elif "availability" in criterion_lower and any(tool["tool"] == "check_inventory" for tool in tools_used):
                met = True
            elif "policy violations" in criterion_lower:
                # Check that no severe violations occurred
                severe_violations = [v for v in tools_used if "error" in str(v.get("result", {}))]
                met = len(severe_violations) == 0
            elif "information" in criterion_lower and len(conversation_text) > 100:
                met = True
            
            criteria_met[criterion] = met
        
        return criteria_met
    
    def _generate_user_followup(self, scenario, conversation_history, turn: int) -> Optional[str]:
        """Generate a follow-up user message based on scenario and conversation state."""
        
        # Simple follow-up generation based on scenario type
        if scenario.id == "retail_001":  # Product search
            followups = [
                "Can you tell me more about the pricing?",
                "What about the warranty on these products?",
                "Are they in stock right now?"
            ]
        elif scenario.id == "retail_002":  # Out of stock
            followups = [
                "When will it be back in stock?",
                "Do you have any similar alternatives?",
                "Can I place a backorder?"
            ]
        elif scenario.id == "retail_003":  # Multi-item order
            followups = [
                "Can you check if everything is available?",
                "What would be the total cost?",
                "How long would delivery take?"
            ]
        else:
            followups = [
                "That's helpful, anything else I should know?",
                "Can you provide more details?",
                "What would you recommend?"
            ]
        
        import random
        return random.choice(followups) if followups else None
    
    def _assess_response_quality(self, conversation_history) -> Dict[str, float]:
        """Assess the quality of agent responses in the conversation."""
        agent_messages = [msg for msg in conversation_history if msg.role == "assistant"]
        
        if not agent_messages:
            return {"relevance": 0.0, "completeness": 0.0, "clarity": 0.0, "helpfulness": 0.0}
        
        # Simple heuristic quality assessment
        total_length = sum(len(msg.content) for msg in agent_messages)
        avg_length = total_length / len(agent_messages)
        
        # Relevance: based on keyword matching and tool usage
        relevance = min(1.0, avg_length / 200)  # Longer responses generally more relevant
        
        # Completeness: based on information provided
        completeness = min(1.0, len(agent_messages) * 0.2)  # More messages = more complete
        
        # Clarity: based on response structure
        clarity = 0.8 if avg_length > 50 else 0.5  # Assume longer responses are clearer
        
        # Helpfulness: based on tool usage and response engagement
        helpfulness = 0.9 if len(agent_messages) > 1 else 0.6
        
        return {
            "relevance": relevance,
            "completeness": completeness, 
            "clarity": clarity,
            "helpfulness": helpfulness
        }
    
    def _create_failed_result(self, model_name: str, scenario_id: str, trial_id: int, error: str) -> Dict[str, Any]:
        """Create a failed result for error cases."""
        return {
            "task_id": f"{scenario_id}_{trial_id}",
            "model_name": model_name,
            "scenario_id": scenario_id,
            "trial_id": trial_id,
            "success": False,
            "completion_reason": f"error: {error}",
            "conversation_turns": 0,
            "tools_used": [],
            "policy_violations": [],
            "duration_seconds": 0.0,
            "timestamp": datetime.now().isoformat(),
            "conversation_history": [],
            "success_criteria_met": {},
            "quality_ratings": {"relevance": 0.0, "completeness": 0.0, "clarity": 0.0, "helpfulness": 0.0}
        }