#!/usr/bin/env python3
"""Generate simple charts for blog post."""

import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# Set style
plt.style.use('default')

def load_evaluation_data():
    """Load the comprehensive evaluation data."""
    data_path = Path("blog_materials/data/summary_statistics.json")
    with open(data_path) as f:
        return json.load(f)

def create_success_rate_chart():
    """Create success rate comparison chart."""
    data = load_evaluation_data()
    
    models = []
    success_rates = []
    
    for model_id, stats in data["by_model"].items():
        if model_id == "gpt5":
            models.append("GPT-5")
        elif model_id == "claude_opus_4_1":
            models.append("Claude Opus 4.1")
        success_rates.append(stats["success_rate"])
    
    fig, ax = plt.subplots(figsize=(10, 6))
    
    bars = ax.bar(models, success_rates, color=['#FF6B6B', '#4ECDC4'], width=0.6)
    
    # Add value labels on bars
    for bar, rate in zip(bars, success_rates):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                f'{rate:.1%}', ha='center', va='bottom', fontsize=14, fontweight='bold')
    
    ax.set_title('GPT-5 vs Claude Opus 4.1: Success Rate Comparison', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Success Rate', fontsize=12)
    ax.set_ylim(0, 1.05)
    ax.grid(axis='y', alpha=0.3)
    
    # Add sample size annotation
    total_conversations = data["overall"]["total_conversations"] // 2
    ax.text(0.02, 0.98, f'Sample size: {total_conversations} conversations per model', 
            transform=ax.transAxes, va='top', fontsize=10,
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('blog_materials/images/success_rate_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_performance_comparison_chart():
    """Create multi-metric performance comparison."""
    data = load_evaluation_data()
    
    # Prepare data
    metrics = ['Success Rate', 'Avg Duration (s)', 'Violations', 'Quality Score']
    gpt5_data = data["by_model"]["gpt5"]
    claude_data = data["by_model"]["claude_opus_4_1"]
    
    # Normalize data for comparison (0-1 scale)
    gpt5_values = [
        gpt5_data["success_rate"],
        1 - (gpt5_data["avg_duration_seconds"] - 25) / 10,  # Inverted and scaled
        1 - gpt5_data["violation_rate"],  # Inverted (lower is better)
        sum(gpt5_data["avg_quality_ratings"].values()) / 4
    ]
    
    claude_values = [
        claude_data["success_rate"],
        1 - (claude_data["avg_duration_seconds"] - 25) / 10,  # Inverted and scaled
        1 - claude_data["violation_rate"],  # Inverted (lower is better)
        sum(claude_data["avg_quality_ratings"].values()) / 4
    ]
    
    x = np.arange(len(metrics))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    bars1 = ax.bar(x - width/2, gpt5_values, width, label='GPT-5', color='#FF6B6B', alpha=0.8)
    bars2 = ax.bar(x + width/2, claude_values, width, label='Claude Opus 4.1', color='#4ECDC4', alpha=0.8)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{height:.2f}', ha='center', va='bottom', fontsize=10)
    
    ax.set_title('Performance Metrics Comparison (Normalized)', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Normalized Score (Higher is Better)', fontsize=12)
    ax.set_xlabel('Metrics', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, rotation=15, ha='right')
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 1.1)
    
    plt.tight_layout()
    plt.savefig('blog_materials/images/performance_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_quality_breakdown_chart():
    """Create quality metrics breakdown."""
    data = load_evaluation_data()
    
    dimensions = ['Relevance', 'Completeness', 'Clarity', 'Helpfulness']
    
    gpt5_quality = data["by_model"]["gpt5"]["avg_quality_ratings"]
    claude_quality = data["by_model"]["claude_opus_4_1"]["avg_quality_ratings"]
    
    gpt5_scores = [gpt5_quality[dim.lower()] for dim in dimensions]
    claude_scores = [claude_quality[dim.lower()] for dim in dimensions]
    
    x = np.arange(len(dimensions))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(12, 8))
    
    bars1 = ax.bar(x - width/2, gpt5_scores, width, label='GPT-5', color='#FF6B6B', alpha=0.8)
    bars2 = ax.bar(x + width/2, claude_scores, width, label='Claude Opus 4.1', color='#4ECDC4', alpha=0.8)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.005,
                    f'{height:.3f}', ha='center', va='bottom', fontsize=10)
    
    ax.set_title('Response Quality Breakdown', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Quality Score', fontsize=12)
    ax.set_xlabel('Quality Dimensions', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels(dimensions)
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 1.05)
    
    plt.tight_layout()
    plt.savefig('blog_materials/images/quality_breakdown.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_scenario_success_chart():
    """Create scenario-by-scenario success comparison."""
    data_path = Path("blog_materials/data/comprehensive_evaluation_data.json")
    with open(data_path) as f:
        full_data = json.load(f)
    
    scenarios = []
    scenario_names = []
    gpt5_success = []
    claude_success = []
    
    # Calculate success rates by scenario
    for scenario_id, scenario_info in full_data["scenarios"].items():
        scenarios.append(scenario_id)
        scenario_names.append(scenario_info["name"])
        
        gpt5_results = [r for r in full_data["results"] if r["model"]["id"] == "gpt5" and r["scenario"]["id"] == scenario_id]
        claude_results = [r for r in full_data["results"] if r["model"]["id"] == "claude_opus_4_1" and r["scenario"]["id"] == scenario_id]
        
        gpt5_rate = sum(1 for r in gpt5_results if r["success"]) / len(gpt5_results) if gpt5_results else 0
        claude_rate = sum(1 for r in claude_results if r["success"]) / len(claude_results) if claude_results else 0
        
        gpt5_success.append(gpt5_rate)
        claude_success.append(claude_rate)
    
    x = np.arange(len(scenario_names))
    width = 0.35
    
    fig, ax = plt.subplots(figsize=(15, 8))
    
    bars1 = ax.bar(x - width/2, gpt5_success, width, label='GPT-5', color='#FF6B6B', alpha=0.8)
    bars2 = ax.bar(x + width/2, claude_success, width, label='Claude Opus 4.1', color='#4ECDC4', alpha=0.8)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                        f'{height:.0%}', ha='center', va='bottom', fontsize=9)
    
    ax.set_title('Success Rate by Scenario', fontsize=16, fontweight='bold', pad=20)
    ax.set_ylabel('Success Rate', fontsize=12)
    ax.set_xlabel('Evaluation Scenarios', fontsize=12)
    ax.set_xticks(x)
    ax.set_xticklabels([name[:20] + "..." if len(name) > 20 else name for name in scenario_names], 
                      rotation=45, ha='right')
    ax.legend(fontsize=12)
    ax.grid(axis='y', alpha=0.3)
    ax.set_ylim(0, 1.1)
    
    plt.tight_layout()
    plt.savefig('blog_materials/images/scenario_comparison.png', dpi=300, bbox_inches='tight')
    plt.close()

def create_summary_infographic():
    """Create a summary infographic with key stats."""
    data = load_evaluation_data()
    
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('GPT-5 vs Claude Opus 4.1: Comprehensive Comparison', fontsize=20, fontweight='bold', y=0.95)
    
    # Success rates
    models = ['GPT-5', 'Claude Opus 4.1']
    success_rates = [data["by_model"]["gpt5"]["success_rate"], data["by_model"]["claude_opus_4_1"]["success_rate"]]
    
    bars1 = ax1.bar(models, success_rates, color=['#FF6B6B', '#4ECDC4'], alpha=0.8)
    ax1.set_title('Overall Success Rate', fontweight='bold', fontsize=14)
    ax1.set_ylabel('Success Rate')
    for bar, rate in zip(bars1, success_rates):
        ax1.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.005,
                f'{rate:.1%}', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    # Response times
    durations = [data["by_model"]["gpt5"]["avg_duration_seconds"], 
                data["by_model"]["claude_opus_4_1"]["avg_duration_seconds"]]
    
    bars2 = ax2.bar(models, durations, color=['#FF6B6B', '#4ECDC4'], alpha=0.8)
    ax2.set_title('Average Response Time', fontweight='bold', fontsize=14)
    ax2.set_ylabel('Duration (seconds)')
    for bar, duration in zip(bars2, durations):
        ax2.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.5,
                f'{duration:.1f}s', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    # Policy violations
    violations = [data["by_model"]["gpt5"]["total_violations"], 
                 data["by_model"]["claude_opus_4_1"]["total_violations"]]
    
    bars3 = ax3.bar(models, violations, color=['#FF6B6B', '#4ECDC4'], alpha=0.8)
    ax3.set_title('Policy Violations', fontweight='bold', fontsize=14)
    ax3.set_ylabel('Number of Violations')
    for bar, violation in zip(bars3, violations):
        ax3.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.1,
                str(violation), ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    # Overall quality scores
    gpt5_quality_avg = sum(data["by_model"]["gpt5"]["avg_quality_ratings"].values()) / 4
    claude_quality_avg = sum(data["by_model"]["claude_opus_4_1"]["avg_quality_ratings"].values()) / 4
    quality_scores = [gpt5_quality_avg, claude_quality_avg]
    
    bars4 = ax4.bar(models, quality_scores, color=['#FF6B6B', '#4ECDC4'], alpha=0.8)
    ax4.set_title('Overall Quality Score', fontweight='bold', fontsize=14)
    ax4.set_ylabel('Quality Score')
    for bar, score in zip(bars4, quality_scores):
        ax4.text(bar.get_x() + bar.get_width()/2., bar.get_height() + 0.005,
                f'{score:.3f}', ha='center', va='bottom', fontweight='bold', fontsize=12)
    
    # Add grids
    for ax in [ax1, ax2, ax3, ax4]:
        ax.grid(axis='y', alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('blog_materials/images/summary_infographic.png', dpi=300, bbox_inches='tight')
    plt.close()

def main():
    """Generate all charts."""
    print("📊 Generating Simple Charts...")
    
    # Create images directory
    images_dir = Path("blog_materials/images")
    images_dir.mkdir(exist_ok=True)
    
    print("  • Success rate comparison...")
    create_success_rate_chart()
    
    print("  • Performance comparison...")
    create_performance_comparison_chart()
    
    print("  • Quality breakdown...")
    create_quality_breakdown_chart()
    
    print("  • Scenario comparison...")
    create_scenario_success_chart()
    
    print("  • Summary infographic...")
    create_summary_infographic()
    
    print("✅ Generated charts:")
    print("  • success_rate_comparison.png")
    print("  • performance_comparison.png")
    print("  • quality_breakdown.png")
    print("  • scenario_comparison.png") 
    print("  • summary_infographic.png")

if __name__ == "__main__":
    main()