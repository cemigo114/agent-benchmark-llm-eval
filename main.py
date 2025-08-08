#!/usr/bin/env python3
"""Main CLI script for running LLM agent evaluations."""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime

from src.evaluation.runner import EvaluationRunner
from src.evaluation.results import EvaluationReport
from src.agents.factory import list_available_models
from src.domains.retail.scenarios import get_retail_scenarios
from src.utils.logging import get_logger, setup_logging
from src.utils.config import get_config

logger = get_logger(__name__)


def setup_cli_parser():
    """Set up command line argument parser."""
    parser = argparse.ArgumentParser(
        description="LLM Agent Evaluation Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --models gpt4 claude-3 --trials 3
  python main.py --models gpt4 --scenarios retail_001 retail_002
  python main.py --list-models
  python main.py --list-scenarios
        """
    )
    
    parser.add_argument(
        "--models", 
        nargs="+", 
        help="Model names to evaluate (from config.yaml)"
    )
    
    parser.add_argument(
        "--scenarios",
        nargs="+",
        help="Specific scenario IDs to run (default: all retail scenarios)"
    )
    
    parser.add_argument(
        "--trials",
        type=int,
        default=5,
        help="Number of trials per scenario (default: 5)"
    )
    
    parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="Maximum conversation turns per trial (default: 10)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="results",
        help="Directory to save results (default: results)"
    )
    
    parser.add_argument(
        "--report-format",
        choices=["summary", "detailed", "json"],
        default="summary",
        help="Report format (default: summary)"
    )
    
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models and exit"
    )
    
    parser.add_argument(
        "--list-scenarios", 
        action="store_true",
        help="List available scenarios and exit"
    )
    
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    return parser


def list_models():
    """List available models from configuration."""
    try:
        models = list_available_models()
        print("Available Models:")
        print("=" * 50)
        
        for model_name, config in models.items():
            print(f"• {model_name}")
            print(f"  Provider: {config.provider}")
            print(f"  Model: {config.model_name}")
            print(f"  Max Tokens: {config.max_tokens}")
            print(f"  Temperature: {config.temperature}")
            print()
            
    except Exception as e:
        print(f"Error listing models: {e}")
        sys.exit(1)


def list_scenarios():
    """List available evaluation scenarios."""
    try:
        scenarios_manager = get_retail_scenarios()
        scenarios = scenarios_manager.list_all_scenarios()
        
        print("Available Scenarios:")
        print("=" * 50)
        
        for scenario in scenarios:
            print(f"• {scenario['id']}: {scenario['title']}")
            print(f"  Description: {scenario['description']}")
            print(f"  Complexity: {scenario['complexity']}")
            print(f"  Policy Focus: {', '.join(scenario['policy_focus'])}")
            print(f"  Expected Tools: {', '.join(scenario['expected_tools'])}")
            print()
            
    except Exception as e:
        print(f"Error listing scenarios: {e}")
        sys.exit(1)


def validate_models(model_names):
    """Validate that requested models are available."""
    try:
        available_models = list_available_models()
        available_names = set(available_models.keys())
        requested_names = set(model_names)
        
        invalid_models = requested_names - available_names
        if invalid_models:
            print(f"Error: Unknown models: {', '.join(invalid_models)}")
            print(f"Available models: {', '.join(available_names)}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error validating models: {e}")
        return False


def validate_scenarios(scenario_ids):
    """Validate that requested scenarios exist."""
    try:
        scenarios_manager = get_retail_scenarios()
        available_scenarios = {s['id'] for s in scenarios_manager.list_all_scenarios()}
        requested_scenarios = set(scenario_ids)
        
        invalid_scenarios = requested_scenarios - available_scenarios
        if invalid_scenarios:
            print(f"Error: Unknown scenarios: {', '.join(invalid_scenarios)}")
            print(f"Available scenarios: {', '.join(available_scenarios)}")
            return False
            
        return True
        
    except Exception as e:
        print(f"Error validating scenarios: {e}")
        return False


async def run_evaluation(args):
    """Run the evaluation with given arguments."""
    
    # Validate inputs
    if not validate_models(args.models):
        sys.exit(1)
    
    if args.scenarios and not validate_scenarios(args.scenarios):
        sys.exit(1)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(exist_ok=True)
    
    print("Starting LLM Agent Evaluation")
    print("=" * 50)
    print(f"Models: {', '.join(args.models)}")
    print(f"Scenarios: {args.scenarios or 'All retail scenarios'}")
    print(f"Trials per scenario: {args.trials}")
    print(f"Max turns per trial: {args.max_turns}")
    print(f"Output directory: {output_dir}")
    print()
    
    try:
        # Initialize runner and run evaluation
        runner = EvaluationRunner()
        
        results = await runner.run_evaluation(
            model_names=args.models,
            scenario_ids=args.scenarios,
            num_trials=args.trials,
            max_conversation_turns=args.max_turns
        )
        
        # Generate timestamp for filenames
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON results
        json_file = output_dir / f"evaluation_results_{timestamp}.json"
        results.save_to_file(str(json_file))
        
        # Generate and save report
        if args.report_format in ["summary", "detailed"]:
            if args.report_format == "summary":
                report = EvaluationReport.generate_summary_report(results)
            else:
                report = EvaluationReport.generate_detailed_report(results)
            
            report_file = output_dir / f"evaluation_report_{timestamp}.md"
            with open(report_file, 'w') as f:
                f.write(report)
            
            # Also print summary to console
            print("Evaluation Complete!")
            print("=" * 50)
            print(EvaluationReport.generate_summary_report(results))
            print(f"\nDetailed results saved to: {json_file}")
            print(f"Report saved to: {report_file}")
            
        elif args.report_format == "json":
            # Just print JSON summary to console
            print("Evaluation Complete!")
            print("=" * 50)
            performance = results.get_performance_summary()
            success_rates = results.get_success_rate_by_model()
            
            print(f"Overall Success Rate: {performance['overall_success_rate']:.2%}")
            print("Success Rates by Model:")
            for model, rate in success_rates.items():
                print(f"  {model}: {rate:.2%}")
            
            print(f"\nFull results saved to: {json_file}")
        
    except KeyboardInterrupt:
        print("\nEvaluation interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Evaluation failed: {e}")
        print(f"Error: {e}")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = setup_cli_parser()
    args = parser.parse_args()
    
    # Set up logging
    log_level = "DEBUG" if args.verbose else "INFO"
    setup_logging(config_override={"level": log_level})
    
    # Handle list commands
    if args.list_models:
        list_models()
        return
    
    if args.list_scenarios:
        list_scenarios()
        return
    
    # Validate required arguments
    if not args.models:
        print("Error: --models is required")
        parser.print_help()
        sys.exit(1)
    
    # Run evaluation
    asyncio.run(run_evaluation(args))


if __name__ == "__main__":
    main()