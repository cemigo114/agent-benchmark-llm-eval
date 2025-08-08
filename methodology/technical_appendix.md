# Technical Appendix: Implementation Details

## System Architecture

### Framework Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Agent Factory │    │ Scenario Manager │    │ Policy Checker  │
│                 │    │                  │    │                 │
│ • OpenAI Agent  │    │ • 7 Scenarios    │    │ • Real-time     │
│ • Anthropic     │    │ • Tool Mapping   │    │ • Severity      │
│   Agent         │    │ • Success        │    │ • Context       │
│                 │    │   Criteria       │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌──────────────────┐
                    │ Evaluation       │
                    │ Runner           │
                    │                  │
                    │ • Async Executor │
                    │ • Conversation   │
                    │   Management     │
                    │ • Metrics        │
                    │   Calculation    │
                    └──────────────────┘
                                 │
                    ┌──────────────────┐
                    │ Results &        │
                    │ Reporting        │
                    │                  │
                    │ • JSON Export    │
                    │ • Statistical    │
                    │   Analysis       │
                    │ • Visualization  │
                    └──────────────────┘
```

## Configuration Management

### Model Configuration

```yaml
models:
  gpt5:
    provider: "openai"
    model_name: "gpt-5"
    max_tokens: 8192
    temperature: 0.1
    timeout: 90
    
  claude_opus_4_1:
    provider: "anthropic" 
    model_name: "claude-4.1-opus"
    max_tokens: 8192
    temperature: 0.1
    timeout: 90
```

### API Integration

#### OpenAI Agent Implementation

```python
class OpenAIAgent(BaseAgent):
    async def generate_response(self, messages, tools=None, **kwargs):
        request_params = {
            "model": self.model_name,
            "messages": self._convert_messages(messages),
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "tools": self._convert_tools(tools) if tools else None
        }
        
        response = await self.client.chat.completions.create(**request_params)
        return self._parse_response(response)
```

#### Anthropic Agent Implementation

```python
class AnthropicAgent(BaseAgent):
    async def generate_response(self, messages, tools=None, **kwargs):
        system_message, claude_messages = self._convert_messages(messages)
        
        request_params = {
            "model": self.model_name,
            "messages": claude_messages,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "system": system_message,
            "tools": self._convert_tools(tools) if tools else None
        }
        
        response = await self.client.messages.create(**request_params)
        return self._parse_response(response)
```

## Retail Domain Implementation

### API Tools

#### Product Search Tool

```python
async def search_products(query: str, category: Optional[str] = None) -> Dict[str, Any]:
    """Search for products in the catalog."""
    results = product_db.search_products(query, category)
    return {
        "success": True,
        "results": results,
        "count": len(results)
    }
```

#### Inventory Check Tool

```python
async def check_inventory(product_id: str) -> Dict[str, Any]:
    """Check product inventory levels."""
    stock_info = product_db.check_stock(product_id)
    return {
        "success": True,
        "stock": stock_info
    }
```

#### Order Placement Tool

```python
async def place_order(customer_id: str, items: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Place an order for multiple items."""
    order = product_db.create_order(customer_id, items)
    if "error" in order:
        return {"success": False, "error": order["error"]}
    return {"success": True, "order": order}
```

### Policy Checking System

#### Policy Categories

```python
class PolicyType(Enum):
    PRICING_ERROR = "pricing_error"
    INVENTORY_MISREPRESENTATION = "inventory_misrepresentation"
    UNAUTHORIZED_DISCOUNT = "unauthorized_discount"
    PERSONAL_INFO_EXPOSURE = "personal_info_exposure"
    PURCHASE_PRESSURE = "purchase_pressure"
    FALSE_ADVERTISING = "false_advertising"
```

#### Violation Detection

```python
def check_response(self, agent_response: str, context: Dict[str, Any]) -> List[PolicyViolation]:
    """Check agent response for policy violations."""
    violations = []
    
    # Check pricing policy
    if self._has_pricing_issues(agent_response):
        violations.append(PolicyViolation(
            policy_type=PolicyType.PRICING_ERROR,
            severity=0.8,
            description="Potential pricing inconsistency detected"
        ))
    
    # Check sales pressure
    pressure_indicators = ["buy now or", "limited time", "act fast"]
    if any(indicator in agent_response.lower() for indicator in pressure_indicators):
        violations.append(PolicyViolation(
            policy_type=PolicyType.PURCHASE_PRESSURE,
            severity=0.6,
            description="High-pressure sales language detected"
        ))
    
    return violations
```

## Statistical Analysis Implementation

### Statistical Test Calculations

#### Two-Proportion Z-Test

```python
import numpy as np
from scipy import stats

def two_proportion_z_test(x1, n1, x2, n2, alpha=0.05):
    """
    Perform two-proportion z-test for comparing success rates.
    
    Args:
        x1: number of successes in group 1 (GPT-5)
        n1: total trials in group 1
        x2: number of successes in group 2 (Claude)
        n2: total trials in group 2
        alpha: significance level
    
    Returns:
        Dictionary with test statistics and results
    """
    # Calculate proportions
    p1 = x1 / n1  # GPT-5 success rate
    p2 = x2 / n2  # Claude success rate
    
    # Pooled proportion
    p_pool = (x1 + x2) / (n1 + n2)
    
    # Standard error
    se = np.sqrt(p_pool * (1 - p_pool) * (1/n1 + 1/n2))
    
    # Z-statistic
    z = (p1 - p2) / se
    
    # P-value (two-tailed)
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    
    # Confidence interval for difference
    se_diff = np.sqrt(p1*(1-p1)/n1 + p2*(1-p2)/n2)
    margin_error = stats.norm.ppf(1 - alpha/2) * se_diff
    ci_lower = (p1 - p2) - margin_error
    ci_upper = (p1 - p2) + margin_error
    
    # Effect size (Cohen's h)
    cohens_h = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
    
    return {
        'p1': p1,
        'p2': p2,
        'difference': p1 - p2,
        'z_statistic': z,
        'p_value': p_value,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'cohens_h': cohens_h,
        'significant': p_value < alpha
    }

# Actual calculation for our data
gpt5_successes = 34  # 97.1% of 35
claude_successes = 33  # 94.3% of 35
total_conversations = 35

results = two_proportion_z_test(
    x1=gpt5_successes, n1=total_conversations,
    x2=claude_successes, n2=total_conversations
)

print(f"GPT-5 Success Rate: {results['p1']:.1%}")
print(f"Claude Success Rate: {results['p2']:.1%}")
print(f"Difference: {results['difference']:.1%}")
print(f"95% CI: [{results['ci_lower']:.1%}, {results['ci_upper']:.1%}]")
print(f"Z-statistic: {results['z_statistic']:.2f}")
print(f"P-value: {results['p_value']:.3f}")
print(f"Cohen's h: {results['cohens_h']:.2f}")
```

#### Power Analysis

```python
def power_analysis_two_proportions(p1, p2, n, alpha=0.05):
    """Calculate statistical power for two-proportion test."""
    from scipy import stats
    
    # Effect size
    effect_size = 2 * (np.arcsin(np.sqrt(p1)) - np.arcsin(np.sqrt(p2)))
    
    # Critical z-value
    z_alpha = stats.norm.ppf(1 - alpha/2)
    
    # Non-centrality parameter
    lambda_nc = effect_size * np.sqrt(n/2)
    
    # Power calculation
    power = 1 - stats.norm.cdf(z_alpha - lambda_nc) + stats.norm.cdf(-z_alpha - lambda_nc)
    
    return power

# Power for our observed effect
observed_power = power_analysis_two_proportions(0.971, 0.943, 35)
print(f"Observed Power: {observed_power:.1%}")
```

#### Confidence Interval Calculations

```python
def wilson_score_interval(x, n, alpha=0.05):
    """
    Calculate Wilson score confidence interval for proportion.
    More accurate than normal approximation for small samples.
    """
    z = stats.norm.ppf(1 - alpha/2)
    p_hat = x / n
    
    denominator = 1 + z**2/n
    center = (p_hat + z**2/(2*n)) / denominator
    margin = z * np.sqrt(p_hat*(1-p_hat)/n + z**2/(4*n**2)) / denominator
    
    return center - margin, center + margin

# Calculate exact confidence intervals
gpt5_ci = wilson_score_interval(34, 35)
claude_ci = wilson_score_interval(33, 35)

print(f"GPT-5 95% CI: [{gpt5_ci[0]:.1%}, {gpt5_ci[1]:.1%}]")
print(f"Claude 95% CI: [{claude_ci[0]:.1%}, {claude_ci[1]:.1%}]")
```

## Evaluation Metrics Implementation

### Pass@K Metric

```python
class PassKMetric(BaseMetric):
    def calculate(self, results: List[Dict[str, Any]]) -> MetricResult:
        """Calculate Pass@K for different values of K."""
        
        # Group results by task_id
        task_groups = {}
        for result in results:
            task_id = result.get("task_id")
            if task_id not in task_groups:
                task_groups[task_id] = []
            task_groups[task_id].append(result.get("success", False))
        
        pass_k_values = {}
        for k in self.k_values:
            task_pass_rates = []
            
            for task_id, trials in task_groups.items():
                if len(trials) >= k:
                    n_success = sum(trials[:k])
                    # Pass@k = 1 - P(all k trials fail)
                    if n_success == 0:
                        task_pass_k = 0.0
                    elif n_success == k:
                        task_pass_k = 1.0
                    else:
                        # Binomial probability calculation
                        task_pass_k = 1.0 - self._binomial_prob_all_fail(n_success, k, k)
                    
                    task_pass_rates.append(task_pass_k)
            
            pass_k_values[f"pass@{k}"] = sum(task_pass_rates) / len(task_pass_rates)
        
        return MetricResult(name="pass_k", value=max(pass_k_values.values()), 
                           details={"pass_k_values": pass_k_values})
```

### Policy Compliance Metric

```python
class PolicyComplianceMetric(BaseMetric):
    def calculate(self, results: List[Dict[str, Any]]) -> MetricResult:
        """Calculate policy compliance rate."""
        compliance_scores = []
        policy_violations = {}
        
        for result in results:
            violations = result.get("policy_violations", [])
            conversation_score = 1.0
            
            for violation in violations:
                policy_type = violation.get("policy_type", "unknown")
                severity = violation.get("severity", 1.0)
                
                conversation_score = max(0.0, conversation_score - severity)
                
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
                "policy_violations": policy_violations
            }
        )
```

## Data Structures

### Message Format

```python
class Message(BaseModel):
    role: str  # "user", "assistant", "system", "tool"
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_call_id: Optional[str] = None
    name: Optional[str] = None
```

### Agent Response Format

```python
class AgentResponse(BaseModel):
    message: Message
    tool_calls: List[ToolCall] = []
    finish_reason: str
    usage: Optional[Dict[str, int]] = None
```

### Evaluation Result Format

```python
class EvaluationResult(BaseModel):
    evaluation_id: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    models_evaluated: List[str]
    scenarios_evaluated: List[str]
    total_conversations: int
    results: List[Dict[str, Any]]
    metrics: Dict[str, Any]
    configuration: Dict[str, Any]
```

## Database Schema

### Conversation Storage

```sql
CREATE TABLE conversations (
    id TEXT PRIMARY KEY,
    model_name TEXT,
    scenario_id TEXT,
    trial_id INTEGER,
    success BOOLEAN,
    conversation_turns INTEGER,
    duration_seconds REAL,
    timestamp TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    role TEXT,
    content TEXT,
    tool_calls JSON,
    message_index INTEGER,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

CREATE TABLE policy_violations (
    id TEXT PRIMARY KEY,
    conversation_id TEXT,
    policy_type TEXT,
    severity REAL,
    description TEXT,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

## Performance Optimizations

### Async Execution

```python
async def run_evaluation(self, model_names: List[str], scenario_ids: List[str]):
    """Run evaluation with concurrent execution."""
    
    tasks = []
    for model_name in model_names:
        agent = create_agent(model_name)
        
        for scenario_id in scenario_ids:
            for trial in range(self.num_trials):
                task = self._run_single_conversation(agent, scenario_id, trial)
                tasks.append(task)
    
    # Execute all conversations concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out exceptions and process results
    valid_results = [r for r in results if not isinstance(r, Exception)]
    
    return valid_results
```

### Connection Pooling

```python
class AgentFactory:
    def __init__(self):
        self.openai_client = AsyncOpenAI(
            api_key=config.api_keys.openai,
            max_retries=3,
            timeout=60.0
        )
        
        self.anthropic_client = AsyncAnthropic(
            api_key=config.api_keys.anthropic,
            max_retries=3,
            timeout=60.0
        )
```

## Error Handling and Resilience

### Retry Logic

```python
async def generate_response_with_retry(self, messages, tools=None, max_retries=3):
    """Generate response with exponential backoff retry."""
    
    for attempt in range(max_retries):
        try:
            return await self.generate_response(messages, tools)
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            
            wait_time = 2 ** attempt
            await asyncio.sleep(wait_time)
            logger.warning(f"Retry attempt {attempt + 1} after {wait_time}s delay: {e}")
```

### Graceful Degradation

```python
async def _run_single_conversation(self, agent, scenario_id, trial_id):
    """Run conversation with graceful error handling."""
    
    try:
        # Normal conversation flow
        result = await self._execute_conversation(agent, scenario_id, trial_id)
        return result
        
    except APIError as e:
        # Handle API-specific errors
        logger.error(f"API error in conversation {scenario_id}_{trial_id}: {e}")
        return self._create_failed_result(scenario_id, trial_id, f"API error: {e}")
        
    except Exception as e:
        # Handle unexpected errors
        logger.error(f"Unexpected error in conversation {scenario_id}_{trial_id}: {e}")
        return self._create_failed_result(scenario_id, trial_id, f"System error: {e}")
```

## Testing and Validation

### Unit Tests

```python
class TestPolicyChecker:
    def test_pricing_violation_detection(self):
        policy_checker = PolicyChecker()
        response = "This product costs $50, but I can offer it for $30!"
        violations = policy_checker.check_response(response, {})
        
        assert len(violations) > 0
        assert violations[0].policy_type == PolicyType.PRICING_ERROR
    
    def test_pressure_sales_detection(self):
        policy_checker = PolicyChecker()
        response = "Buy now or miss out on this limited time offer!"
        violations = policy_checker.check_response(response, {})
        
        assert any(v.policy_type == PolicyType.PURCHASE_PRESSURE for v in violations)
```

### Integration Tests

```python
class TestEvaluationRunner:
    async def test_full_evaluation_flow(self):
        runner = EvaluationRunner()
        results = await runner.run_evaluation(
            model_names=["test_model"],
            scenario_ids=["retail_001"],
            num_trials=1
        )
        
        assert len(results) == 1
        assert "task_id" in results[0]
        assert "success" in results[0]
        assert "quality_ratings" in results[0]
```

## Deployment Configuration

### Docker Configuration

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/

CMD ["python", "-m", "src.main"]
```

### Environment Variables

```bash
# API Configuration
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=ant-...

# Evaluation Configuration
EVALUATION_ENVIRONMENT=production
CONCURRENT_EVALUATIONS=5
RESULTS_DATABASE_URL=sqlite:///results.db

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

---

*This technical appendix provides comprehensive implementation details for reproducing and extending the evaluation framework.*