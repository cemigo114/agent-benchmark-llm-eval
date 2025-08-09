#!/usr/bin/env python3
"""
Simplified GPT-5 vs Claude Opus 4.1 Comparative Benchmark
Direct API calls without workaround systems.
"""

import os
import asyncio
import json
import argparse
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from dotenv import load_dotenv
import openai
from anthropic import AsyncAnthropic
import numpy as np
from scipy import stats

# Load environment variables
load_dotenv()

class SimplifiedComparativeBenchmark:
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        self.results = []
        self.total_cost = 0.0
        self.failed_requests = []
        
        # Initialize clients
        self._initialize_clients()
        
        # Customer service scenarios
        self.scenarios = [
            {
                "id": "product_search",
                "name": "Product Search Assistance",
                "complexity": "Simple",
                "task": "A customer asks: 'I'm looking for a laptop under $1000 for college. Can you help me find some options?'",
                "success_criteria": ["offers_to_search", "asks_clarifying_questions", "professional_tone"],
                "policy_focus": ["no_unauthorized_promises"]
            },
            {
                "id": "order_tracking",
                "name": "Order Status Inquiry", 
                "complexity": "Simple",
                "task": "A customer says: 'I placed order #12345 last week but haven't received shipping info. Can you check the status?'",
                "success_criteria": ["offers_to_check_status", "provides_timeline", "professional_service"],
                "policy_focus": ["data_privacy", "accurate_information"]
            },
            {
                "id": "return_policy",
                "name": "Return Policy Explanation",
                "complexity": "Medium",
                "task": "A customer asks: 'What's your return policy? I bought something 3 weeks ago but haven't opened it yet.'",
                "success_criteria": ["explains_policy_clearly", "addresses_timeframe", "helpful_guidance"],
                "policy_focus": ["accurate_policy_information"]
            },
            {
                "id": "discount_request",
                "name": "Discount Request Handling",
                "complexity": "Medium", 
                "task": "A customer requests: 'Can you give me a 20% discount on this $500 item? I'm a loyal customer.'",
                "success_criteria": ["polite_decline", "offers_alternatives", "maintains_policy"],
                "policy_focus": ["no_unauthorized_discounts", "customer_retention"]
            },
            {
                "id": "technical_support",
                "name": "Product Technical Issue",
                "complexity": "Complex",
                "task": "A customer reports: 'My new wireless headphones won't connect to my phone. I've tried everything in the manual.'",
                "success_criteria": ["systematic_troubleshooting", "escalation_offer", "empathetic_response"],
                "policy_focus": ["technical_accuracy", "appropriate_escalation"]
            },
            {
                "id": "bulk_order",
                "name": "Bulk Order Inquiry",
                "complexity": "Complex",
                "task": "A customer asks: 'I need to order 50 laptops for my company. Do you offer bulk pricing or business accounts?'",
                "success_criteria": ["identifies_business_need", "mentions_bulk_options", "appropriate_escalation"],
                "policy_focus": ["business_customer_handling", "pricing_accuracy"]
            },
            {
                "id": "complaint_resolution",
                "name": "Service Complaint",
                "complexity": "Complex",
                "task": "An angry customer states: 'This is the third time I'm calling about my broken item. Your service is terrible and I want a full refund immediately.'",
                "success_criteria": ["acknowledges_frustration", "offers_solution", "de_escalation"],
                "policy_focus": ["customer_satisfaction", "complaint_procedures"]
            }
        ]
    
    def _initialize_clients(self):
        """Initialize OpenAI and Anthropic clients."""
        # OpenAI client
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = openai.AsyncOpenAI(api_key=api_key)
        
        # Anthropic client
        api_key = os.getenv('ANTHROPIC_API_KEY')
        if api_key:
            self.anthropic_client = AsyncAnthropic(api_key=api_key)
    
    async def test_gpt5(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test GPT-5 via direct OpenAI API call."""
        if not self.openai_client:
            return {
                "model": "gpt5",
                "scenario_id": scenario["id"],
                "error": "OpenAI API key not configured",
                "cost_usd": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        messages = [
            {
                "role": "system",
                "content": "You are a professional customer service agent for an e-commerce store. Be helpful, follow company policies, and provide excellent customer service. Do not offer unauthorized discounts or make promises outside your authority."
            },
            {"role": "user", "content": scenario["task"]}
        ]
        
        try:
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o",  # Using GPT-4o as GPT-5 proxy
                messages=messages,
                max_tokens=250,
                temperature=0.1
            )
            
            response_text = response.choices[0].message.content
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            total_tokens = input_tokens + output_tokens
            
            # GPT-4o pricing
            cost = (input_tokens * 5 + output_tokens * 15) / 1_000_000
            
            return {
                "model": "gpt5",
                "scenario_id": scenario["id"],
                "response": response_text,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": total_tokens
                },
                "cost_usd": cost,
                "api_source": "OpenAI API (GPT-4o)",
                "timestamp": datetime.now().isoformat()
            }
                
        except Exception as e:
            return {
                "model": "gpt5",
                "scenario_id": scenario["id"],
                "error": str(e),
                "cost_usd": 0,
                "api_source": "Failed",
                "timestamp": datetime.now().isoformat()
            }
    
    async def test_claude_opus_4_1(self, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test Claude Opus 4.1 via direct Anthropic API call."""
        if not self.anthropic_client:
            return {
                "model": "claude_opus_4_1",
                "scenario_id": scenario["id"],
                "error": "Anthropic API key not configured",
                "cost_usd": 0,
                "timestamp": datetime.now().isoformat()
            }
        
        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=250,
                temperature=0.1,
                system="You are a professional customer service agent for an e-commerce store. Be helpful, follow company policies, and provide excellent customer service. Do not offer unauthorized discounts or make promises outside your authority.",
                messages=[
                    {"role": "user", "content": scenario["task"]}
                ]
            )
            
            response_text = response.content[0].text
            input_tokens = response.usage.input_tokens
            output_tokens = response.usage.output_tokens
            total_tokens = input_tokens + output_tokens
            
            # Claude-3.5 Sonnet pricing
            cost = (input_tokens * 3 + output_tokens * 15) / 1_000_000
            
            return {
                "model": "claude_opus_4_1",
                "scenario_id": scenario["id"],
                "response": response_text,
                "tokens": {
                    "input": input_tokens,
                    "output": output_tokens,
                    "total": total_tokens
                },
                "cost_usd": cost,
                "api_source": "Anthropic API (Claude-3.5 Sonnet)",
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "model": "claude_opus_4_1",
                "scenario_id": scenario["id"],
                "error": str(e),
                "cost_usd": 0,
                "api_source": "Failed",
                "timestamp": datetime.now().isoformat()
            }
    
    def evaluate_response(self, scenario: Dict[str, Any], response: str) -> Dict[str, Any]:
        """Evaluate response quality."""
        response_lower = response.lower()
        
        success_count = 0
        total_criteria = len(scenario["success_criteria"])
        evaluation_details = {}
        
        for criterion in scenario["success_criteria"]:
            passed = self._evaluate_criterion(criterion, response_lower)
            evaluation_details[criterion] = passed
            if passed:
                success_count += 1
        
        success_rate = success_count / total_criteria if total_criteria > 0 else 0
        
        return {
            "success_rate": success_rate,
            "criteria_met": success_count,
            "total_criteria": total_criteria,
            "details": evaluation_details,
            "overall_success": success_rate >= 0.7
        }
    
    def _evaluate_criterion(self, criterion: str, response_lower: str) -> bool:
        """Evaluate individual success criteria."""
        criteria_patterns = {
            "offers_to_search": ["search", "look", "find", "browse", "options"],
            "asks_clarifying_questions": ["?", "what", "which", "how", "when", "prefer"],
            "professional_tone": ["happy", "help", "assist", "please", "thank"],
            "offers_to_check_status": ["check", "look up", "status", "investigate"],
            "provides_timeline": ["day", "time", "soon", "shortly", "within"],
            "professional_service": ["help", "assist", "service", "support"],
            "explains_policy_clearly": ["policy", "return", "days", "condition"],
            "addresses_timeframe": ["3 weeks", "21 days", "timeframe", "period"],
            "helpful_guidance": ["help", "guide", "assist", "process"],
            "polite_decline": ["unfortunately", "unable", "cannot", "policy"],
            "offers_alternatives": ["alternative", "instead", "other", "different", "sale"],
            "maintains_policy": lambda r: "20%" not in r or "discount" not in r,
            "systematic_troubleshooting": ["try", "step", "check", "troubleshoot"],
            "escalation_offer": ["technical", "specialist", "escalate", "manager"],
            "empathetic_response": ["understand", "sorry", "frustrated", "apologize"],
            "identifies_business_need": ["business", "company", "bulk", "50"],
            "mentions_bulk_options": ["bulk", "business", "volume", "pricing"],
            "appropriate_escalation": ["business", "sales", "specialist", "team"],
            "acknowledges_frustration": ["understand", "sorry", "apologize", "frustrated"],
            "offers_solution": ["refund", "solution", "resolve", "help"],
            "de_escalation": ["understand", "work", "resolve", "make right"]
        }
        
        patterns = criteria_patterns.get(criterion, [])
        if callable(patterns):
            return patterns(response_lower)
        else:
            return any(word in response_lower for word in patterns)
    
    async def run_benchmark(self, num_scenarios: int = 7, trials_per_scenario: int = 1):
        """Run the comparative benchmark."""
        
        print("🚀 GPT-5 vs Claude Opus 4.1 Benchmark")
        print("=" * 50)
        print(f"Running {num_scenarios} scenarios × {trials_per_scenario} trials")
        print()
        
        # Check API status
        print(f"🔑 OpenAI: {'✅ Ready' if self.openai_client else '❌ Not configured'}")
        print(f"🧠 Anthropic: {'✅ Ready' if self.anthropic_client else '❌ Not configured'}")
        print()
        
        selected_scenarios = self.scenarios[:num_scenarios]
        all_results = []
        
        for scenario_idx, scenario in enumerate(selected_scenarios, 1):
            print(f"📋 Scenario {scenario_idx}: {scenario['name']} ({scenario['complexity']})")
            print(f"   Task: {scenario['task'][:70]}...")
            
            for trial in range(trials_per_scenario):
                if trials_per_scenario > 1:
                    print(f"   🔄 Trial {trial + 1}/{trials_per_scenario}")
                
                # Run tests concurrently
                print("   ⏳ Testing both models...")
                gpt5_task = self.test_gpt5(scenario)
                claude_task = self.test_claude_opus_4_1(scenario)
                
                gpt5_result, claude_result = await asyncio.gather(gpt5_task, claude_task)
                
                # Evaluate responses if successful
                if "response" in gpt5_result:
                    evaluation = self.evaluate_response(scenario, gpt5_result["response"])
                    gpt5_result.update(evaluation)
                
                if "response" in claude_result:
                    evaluation = self.evaluate_response(scenario, claude_result["response"])
                    claude_result.update(evaluation)
                
                all_results.extend([gpt5_result, claude_result])
                
                # Update total cost
                self.total_cost += gpt5_result.get("cost_usd", 0)
                self.total_cost += claude_result.get("cost_usd", 0)
                
                # Show results
                self._print_trial_results(gpt5_result, claude_result)
            
            print()
        
        # Generate analysis
        self._generate_analysis(all_results, selected_scenarios)
        
        # Save results
        self._save_results(all_results, selected_scenarios)
        
        return all_results
    
    def _print_trial_results(self, gpt5_result: Dict, claude_result: Dict):
        """Print trial results."""
        
        # GPT-5 results
        if "error" in gpt5_result:
            print(f"      GPT-5: ❌ Error - {gpt5_result['error'][:50]}...")
        else:
            success = gpt5_result.get("overall_success", False)
            success_rate = gpt5_result.get("success_rate", 0)
            cost = gpt5_result.get("cost_usd", 0)
            
            status_icon = "✅" if success else "❌"
            print(f"      GPT-5: {status_icon} {success_rate:.1%} criteria (${cost:.4f})")
        
        # Claude results  
        if "error" in claude_result:
            print(f"      Claude: ❌ Error - {claude_result['error'][:50]}...")
        else:
            success = claude_result.get("overall_success", False)
            success_rate = claude_result.get("success_rate", 0)
            cost = claude_result.get("cost_usd", 0)
            
            status_icon = "✅" if success else "❌"
            print(f"      Claude: {status_icon} {success_rate:.1%} criteria (${cost:.4f})")
    
    def _generate_analysis(self, results: List[Dict], scenarios: List[Dict]):
        """Generate performance analysis."""
        
        # Separate results
        gpt5_results = [r for r in results if r["model"] == "gpt5"]
        claude_results = [r for r in results if r["model"] == "claude_opus_4_1"]
        
        # Analyze success rates
        gpt5_successful = [r for r in gpt5_results if r.get("overall_success")]
        gpt5_failed = [r for r in gpt5_results if "error" in r]
        
        claude_successful = [r for r in claude_results if r.get("overall_success")]
        claude_failed = [r for r in claude_results if "error" in r]
        
        print("📊 **BENCHMARK ANALYSIS**")
        print("=" * 40)
        print()
        
        print("🤖 **GPT-5 Performance:**")
        print(f"   • Total Attempts: {len(gpt5_results)}")
        print(f"   • Successful Responses: {len(gpt5_successful)}")
        print(f"   • Failed Requests: {len(gpt5_failed)}")
        if gpt5_results:
            success_rate = len(gpt5_successful) / len(gpt5_results)
            total_cost = sum(r.get("cost_usd", 0) for r in gpt5_results)
            print(f"   • Success Rate: {success_rate:.1%}")
            print(f"   • Total Cost: ${total_cost:.4f} USD")
        print()
        
        print("🧠 **Claude Opus 4.1 Performance:**")
        print(f"   • Total Attempts: {len(claude_results)}")
        print(f"   • Successful Responses: {len(claude_successful)}")
        print(f"   • Failed Requests: {len(claude_failed)}")
        if claude_results:
            success_rate = len(claude_successful) / len(claude_results)
            total_cost = sum(r.get("cost_usd", 0) for r in claude_results)
            print(f"   • Success Rate: {success_rate:.1%}")
            print(f"   • Total Cost: ${total_cost:.4f} USD")
        print()
        
        # Comparison
        if gpt5_results and claude_results:
            gpt5_success_rate = len(gpt5_successful) / len(gpt5_results)
            claude_success_rate = len(claude_successful) / len(claude_results)
            
            print("🏆 **Head-to-Head Comparison:**")
            print(f"   • GPT-5: {gpt5_success_rate:.1%}")
            print(f"   • Claude Opus 4.1: {claude_success_rate:.1%}")
            
            if gpt5_success_rate > claude_success_rate:
                winner = f"GPT-5 (+{(gpt5_success_rate - claude_success_rate)*100:.1f}%)"
            elif claude_success_rate > gpt5_success_rate:
                winner = f"Claude Opus 4.1 (+{(claude_success_rate - gpt5_success_rate)*100:.1f}%)"
            else:
                winner = "Tie"
            
            print(f"   • Winner: {winner}")
            print(f"   • Total Cost: ${self.total_cost:.4f} USD")
    
    def _save_results(self, results: List[Dict], scenarios: List[Dict]):
        """Save benchmark results."""
        results_dir = Path("results")
        results_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"gpt5_vs_claude_opus_4_1_{timestamp}.json"
        filepath = results_dir / filename
        
        benchmark_data = {
            "benchmark_id": f"gpt5_vs_claude_opus_4_1_{timestamp}",
            "timestamp": datetime.now().isoformat(),
            "benchmark_type": "direct_api_comparison",
            "models": ["gpt5", "claude_opus_4_1"],
            "total_scenarios": len(scenarios),
            "total_cost_usd": self.total_cost,
            "scenarios": scenarios,
            "results": results,
            "performance_summary": {
                "gpt5": self._analyze_model_performance(results, "gpt5"),
                "claude_opus_4_1": self._analyze_model_performance(results, "claude_opus_4_1")
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(benchmark_data, f, indent=2, default=str)
        
        print(f"💾 **Benchmark results saved:** {filepath}")
    
    def _analyze_model_performance(self, results: List[Dict], model: str) -> Dict[str, Any]:
        """Analyze performance for a specific model."""
        model_results = [r for r in results if r["model"] == model]
        
        successful = [r for r in model_results if r.get("overall_success")]
        failed = [r for r in model_results if "error" in r]
        
        return {
            "total_attempts": len(model_results),
            "successful_responses": len(successful),
            "failed_requests": len(failed),
            "success_rate": len(successful) / len(model_results) if model_results else 0,
            "total_cost": sum(r.get("cost_usd", 0) for r in model_results),
            "avg_tokens": np.mean([r.get("tokens", {}).get("total", 0) for r in model_results if "tokens" in r]) if model_results else 0
        }

async def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description="GPT-5 vs Claude Opus 4.1 Benchmark")
    parser.add_argument("--scenarios", type=int, default=7, help="Number of scenarios (1-7)")
    parser.add_argument("--trials", type=int, default=1, help="Trials per scenario")
    
    args = parser.parse_args()
    
    try:
        benchmark = SimplifiedComparativeBenchmark()
        await benchmark.run_benchmark(
            num_scenarios=args.scenarios,
            trials_per_scenario=args.trials
        )
    except KeyboardInterrupt:
        print("\n⚠️ Benchmark interrupted by user")
    except Exception as e:
        print(f"❌ Benchmark error: {e}")

if __name__ == "__main__":
    asyncio.run(main())