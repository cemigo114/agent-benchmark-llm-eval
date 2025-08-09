# Changelog - LLM Agent Benchmark Framework

## [1.1.0] - August 8, 2025 - Real API Integration

### 🎉 Major Features Added
- **Real API Integration**: Framework now supports actual OpenAI and Anthropic API calls
- **Cost Tracking**: Real-time cost calculation for API usage
- **Authentic Evaluation**: Compare simulated vs real model performance

### ✅ New Scripts
- `create_env.py`: Interactive API key setup script
- `test_api_connection.py`: API connection verification with cost estimates
- `real_benchmark.py`: Real API benchmark with actual cost tracking
- `simple_demo.py`: Simplified demo with simulated data

### 📊 Key Findings
- **Real vs Simulated Performance**: Claude-3 real performance (66.7%) significantly differs from simulated estimates (94.3%)
- **Cost Analysis**: 3 scenarios cost $0.0395 USD with Claude-3.5 Sonnet
- **Model Updates**: Updated to latest Claude-3.5 Sonnet and GPT-4o models

### 🔧 Technical Improvements
- Updated `requirements.txt` with current API library versions
- Added `.env` support for secure API key management
- Enhanced error handling and rate limiting detection
- Improved documentation with real usage examples

### 📝 Documentation Updates
- `REAL_RESULTS.md`: Detailed comparison of simulated vs real results
- Updated `BENCHMARK_README.md` with real API setup instructions
- Added disclaimers about simulated vs authentic results

### ⚠️ Important Changes
- **Breaking**: Previous GPT-5 vs Claude Opus 4.1 results were simulated, not real API calls
- **Security**: Added `.env` to `.gitignore` for API key protection
- **Model Updates**: Migrated to current model versions (Claude-3.5 Sonnet, GPT-4o)

## [1.0.0] - Previous Version - Simulated Framework

### 🏗️ Initial Framework
- Complete τ-bench methodology implementation
- Simulated GPT-5 vs Claude Opus 4.1 comparison
- Statistical analysis with confidence intervals
- Blog post materials and publication assets

### ⚠️ Limitation Discovered
- Results were based on simulated data, not actual API calls
- Performance estimates were overly optimistic
- No real cost tracking or authentic model responses

---

## Migration Guide

### From v1.0 to v1.1
1. **Set up API keys**: Run `python3 create_env.py`
2. **Test connections**: Run `python3 test_api_connection.py`
3. **Use real benchmarks**: Replace simulated demos with `python3 real_benchmark.py`
4. **Update expectations**: Real performance may differ significantly from simulated results

### Cost Considerations
- **Development**: Use `simple_demo.py` for free simulated testing
- **Validation**: Use `real_benchmark.py` for authentic results (~$0.04 per 3 scenarios)
- **Production**: Budget appropriately for comprehensive evaluations

---

**Recommendation**: Always validate simulated results with real API calls before making deployment decisions.