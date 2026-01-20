# Release Notes - v0.3.0

**Release Date**: 2025
**Status**: Intelligence & Localization Release

---

## Overview

LLM-Quality-Observer v0.3.0 introduces LLM-as-a-Judge evaluation capabilities, enabling AI-powered quality assessment alongside rule-based evaluation. This release also adds comprehensive multi-language support for the dashboard and expands evaluation metrics with detailed scoring dimensions.

---

## 🎯 What's New

### LLM-as-a-Judge Evaluation (NEW)
- **AI-Powered Assessment**: Use GPT-4 or similar models to evaluate response quality
- **Dual Evaluation System**: Choose between rule-based or LLM-as-a-judge evaluation
- **Structured Prompting**: Carefully designed evaluation prompts for consistent scoring
- **Judge Model Configuration**: Configurable judge model selection
- **Raw Response Storage**: Store complete judge reasoning for transparency

### Enhanced Evaluation Metrics (NEW)
- **Multi-Dimensional Scoring**:
  - `score_overall`: Overall response quality (1-5)
  - `score_instruction_following`: How well the response follows the prompt (1-5)
  - `score_truthfulness`: Factual accuracy and reliability (1-5)
- **Judge Type Tracking**: Distinguish between rule-based and LLM judge evaluations
- **Detailed Comments**: Comprehensive feedback on evaluation decisions
- **Raw Judge Response**: Complete LLM judge output for audit trail

### Multi-Language Dashboard Support (NEW)
- **Localization Framework**: Complete i18n implementation
- **Supported Languages**:
  - 🇺🇸 English (en)
  - 🇰🇷 Korean (ko)
  - 🇯🇵 Japanese (ja)
  - 🇨🇳 Chinese (zh)
- **Language Switcher**: Easy language selection in dashboard UI
- **Localized UI Elements**: All dashboard text and labels translated
- **Persistent Language Selection**: Language preference saved in session

### Time Series Analytics (NEW)
- **Trend Analysis**: Track quality metrics over time
- **Time-Based Aggregation**: Hourly, daily, weekly views
- **Performance Metrics**: Monitor latency and success rate trends
- **Historical Comparison**: Compare current vs. past performance

---

## 🏗️ Architecture Updates

The architecture remains the same as v0.2.0, with enhanced evaluation logic:

```
Client/Browser → Dashboard (port 8501) [Multi-language UI]
                      ↓
                 Gateway API (port 18000) → OpenAI GPT
                      ↓
                 PostgreSQL (port 5432)
                      ↑
                 Evaluator (port 18001) → OpenAI GPT (Judge Model)
```

---

## 🗄️ Database Schema Changes

### Updated llm_evaluations Table

```sql
ALTER TABLE llm_evaluations
ADD COLUMN score_instruction_following FLOAT,
ADD COLUMN score_truthfulness FLOAT,
ADD COLUMN judge_type VARCHAR,           -- 'rule' or 'llm'
ADD COLUMN raw_judge_response TEXT;      -- Complete LLM judge output
```

**Migration**: These columns are nullable, so existing data remains compatible.

---

## 🆕 New Features in Detail

### LLM-as-a-Judge Implementation

**Evaluation Prompt Structure**:
```python
"""
You are an expert AI assistant evaluator. Evaluate the following LLM response.

Prompt: {prompt}
Response: {response}

Provide scores (1-5) for:
1. Overall Quality
2. Instruction Following
3. Truthfulness

Return JSON:
{
  "score_overall": float,
  "score_instruction_following": float,
  "score_truthfulness": float,
  "comments": "detailed explanation"
}
"""
```

**Usage**:
```python
# services/evaluator/app/llm_judge.py
from .llm_judge import evaluate_with_llm

result = evaluate_with_llm(
    prompt="What is Python?",
    response="Python is a programming language...",
    judge_model="gpt-4"
)

# Returns structured evaluation with scores and comments
```

### Multi-Dimensional Scoring

Each evaluation now includes three distinct scores:

1. **Overall Quality (score_overall)**:
   - Comprehensive quality assessment
   - Considers all aspects of the response
   - Range: 1 (poor) to 5 (excellent)

2. **Instruction Following (score_instruction_following)**:
   - How well the response addresses the prompt
   - Relevance and completeness
   - Range: 1 (off-topic) to 5 (perfect match)

3. **Truthfulness (score_truthfulness)**:
   - Factual accuracy
   - Absence of hallucinations
   - Reliability of information
   - Range: 1 (false) to 5 (accurate)

### Localization System

**Language Configuration**:
```python
# Dashboard language files
locales/
├── en.json    # English
├── ko.json    # Korean
├── ja.json    # Japanese
└── zh.json    # Chinese
```

**Example Translation**:
```json
{
  "dashboard.title": "LLM Quality Observer",
  "dashboard.overview": "Overview",
  "dashboard.quality_metrics": "Quality Metrics",
  "dashboard.select_language": "Select Language",
  "metrics.total_requests": "Total Requests",
  "metrics.average_score": "Average Score"
}
```

**Usage in Dashboard**:
```python
from utils.localization import get_text

st.title(get_text("dashboard.title"))
st.metric(get_text("metrics.total_requests"), total_count)
```

---

## 📖 Updated API Endpoints

### Evaluator Service

#### POST /evaluate-once
**Enhanced**: Now supports judge type selection

**Query Parameters**:
- `limit` (optional): Number of logs to evaluate
- `judge_type` (optional): "rule" or "llm" (default: "rule")

**Request Example**:
```bash
# Use LLM-as-a-judge
curl -X POST "http://localhost:18001/evaluate-once?limit=10&judge_type=llm"

# Use rule-based evaluation
curl -X POST "http://localhost:18001/evaluate-once?limit=10&judge_type=rule"
```

**Response**:
```json
{
  "message": "Evaluation completed",
  "evaluated_count": 10,
  "judge_type": "llm",
  "average_score_overall": 4.2,
  "average_score_instruction_following": 4.5,
  "average_score_truthfulness": 4.0
}
```

### Gateway API

#### GET /api/time-series
**New**: Time series data for trend analysis

**Query Parameters**:
- `metric`: "score", "latency", or "count"
- `interval`: "hour", "day", or "week"
- `start_date` (optional): Start date (ISO 8601)
- `end_date` (optional): End date (ISO 8601)

**Request Example**:
```bash
curl "http://localhost:18000/api/time-series?metric=score&interval=day"
```

**Response**:
```json
{
  "metric": "score",
  "interval": "day",
  "data": [
    {
      "timestamp": "2024-01-01T00:00:00Z",
      "value": 4.2,
      "count": 150
    },
    {
      "timestamp": "2024-01-02T00:00:00Z",
      "value": 4.5,
      "count": 200
    }
  ]
}
```

#### GET /api/evaluations
**Enhanced**: Now returns additional score dimensions

**Response**:
```json
{
  "evaluations": [
    {
      "id": 1,
      "log_id": 1,
      "score_overall": 4.5,
      "score_instruction_following": 5.0,
      "score_truthfulness": 4.0,
      "judge_type": "llm",
      "comments": "Excellent response with minor factual nuance",
      "judge_model": "gpt-4",
      "raw_judge_response": "{...}"
    }
  ]
}
```

---

## 🔧 Configuration Updates

### New Environment Variables

```bash
# LLM Judge Configuration
OPENAI_MODEL_JUDGE=gpt-4          # Model used for LLM-as-a-judge
EVALUATION_JUDGE_TYPE=rule         # Default: 'rule' or 'llm'

# Dashboard Localization
DEFAULT_LANGUAGE=en                # Default UI language
SUPPORTED_LANGUAGES=en,ko,ja,zh    # Available languages
```

### Updated .env.local.example

```bash
# Existing variables...

# LLM Judge Settings (v0.3.0+)
OPENAI_MODEL_JUDGE=gpt-4
EVALUATION_JUDGE_TYPE=rule

# Dashboard Localization (v0.3.0+)
DEFAULT_LANGUAGE=en
```

---

## 📁 Updated Project Structure

```
LLM-Quality-Observer/
├── services/
│   ├── evaluator/
│   │   └── app/
│   │       ├── llm_judge.py     # NEW: LLM-as-a-judge implementation
│   │       ├── rules.py         # Enhanced rule-based evaluation
│   │       ├── schemas.py       # Updated with new score fields
│   │       └── models.py        # Updated evaluation model
│   └── dashboard/
│       ├── app/
│       │   ├── locales/         # NEW: Translation files
│       │   │   ├── en.json
│       │   │   ├── ko.json
│       │   │   ├── ja.json
│       │   │   └── zh.json
│       │   └── utils/
│       │       └── localization.py  # NEW: i18n utilities
└── docs/
    └── README.md                # Updated with v0.3.0 features
```

---

## 🔄 Migration from v0.2.0

### Database Migration

**Option 1: Automatic (on startup)**
The services will automatically add new columns if they don't exist.

**Option 2: Manual SQL**
```sql
-- Add new columns to llm_evaluations table
ALTER TABLE llm_evaluations
ADD COLUMN IF NOT EXISTS score_instruction_following FLOAT,
ADD COLUMN IF NOT EXISTS score_truthfulness FLOAT,
ADD COLUMN IF NOT EXISTS judge_type VARCHAR,
ADD COLUMN IF NOT EXISTS raw_judge_response TEXT;
```

### Configuration Updates

1. **Update .env.local**:
```bash
# Add new variables
OPENAI_MODEL_JUDGE=gpt-4
EVALUATION_JUDGE_TYPE=rule
DEFAULT_LANGUAGE=en
```

2. **Restart services**:
```bash
cd infra/docker
docker compose -f docker-compose.local.yml down
docker compose -f docker-compose.local.yml up --build
```

### Re-evaluate Existing Logs

Existing evaluations only have `score_overall`. To populate new metrics:

```bash
# Re-evaluate with LLM judge
curl -X POST "http://localhost:18001/evaluate-once?limit=100&judge_type=llm"
```

---

## 🚀 Using LLM-as-a-Judge

### Cost Considerations

LLM-as-a-judge uses OpenAI API calls:
- **GPT-4**: ~$0.03 per evaluation (input + output tokens)
- **GPT-3.5-turbo**: ~$0.002 per evaluation

**Recommendation**: Start with rule-based evaluation, use LLM judge for:
- Quality assurance sampling
- Disputed evaluations
- Production monitoring of critical flows

### Evaluation Comparison

```bash
# Evaluate same logs with both methods
curl -X POST "http://localhost:18001/evaluate-once?limit=10&judge_type=rule"
curl -X POST "http://localhost:18001/evaluate-once?limit=10&judge_type=llm"

# Compare results in dashboard
# Navigate to: Quality Metrics → Score by Judge Type
```

### Best Practices

1. **Judge Model Selection**:
   - GPT-4: Higher accuracy, slower, more expensive
   - GPT-3.5-turbo: Faster, cheaper, good for high-volume

2. **Hybrid Approach**:
   - Use rule-based for all evaluations
   - Use LLM judge for random 10% sampling
   - Use LLM judge when rule-based score is borderline (2.5-3.5)

3. **Prompt Engineering**:
   - Customize evaluation prompts in `services/evaluator/app/llm_judge.py`
   - Include domain-specific criteria
   - Provide examples for consistency

---

## 🧪 Testing

### Test LLM-as-a-Judge

```bash
# Send a test request
curl -X POST "http://localhost:18000/chat" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing", "user_id": "test"}'

# Evaluate with LLM judge
curl -X POST "http://localhost:18001/evaluate-once?limit=1&judge_type=llm"

# Check evaluation result
curl "http://localhost:18000/api/evaluations?limit=1" | jq
```

### Test Multi-Language Dashboard

1. Open dashboard: http://localhost:8501
2. Click language selector in sidebar
3. Switch between English, Korean, Japanese, Chinese
4. Verify all UI elements are translated

### Test Time Series API

```bash
# Get daily score trends
curl "http://localhost:18000/api/time-series?metric=score&interval=day" | jq

# Get hourly latency trends
curl "http://localhost:18000/api/time-series?metric=latency&interval=hour" | jq
```

---

## 💡 Improvements

- **Evaluation Quality**: Multi-dimensional scoring provides deeper insights
- **Judge Transparency**: Raw LLM judge responses enable audit and debugging
- **User Experience**: Multi-language support expands global accessibility
- **Analytics**: Time series data enables trend analysis and forecasting
- **Flexibility**: Choose evaluation method based on cost/quality tradeoff

---

## 🐛 Bug Fixes

- Fixed evaluation schema to properly handle null values
- Improved error handling for LLM API failures
- Enhanced database connection retry logic
- Fixed dashboard rendering issues with large datasets

---

## ⚠️ Known Limitations

- **LLM Judge Cost**: Can be expensive for high-volume evaluation
- **LLM Judge Latency**: Slower than rule-based (2-5 seconds per evaluation)
- **Language Detection**: Dashboard doesn't auto-detect browser language
- **Limited Translation Coverage**: Some error messages remain in English
- **Time Series Caching**: No caching, queries can be slow for large datasets

---

## 🛣️ Roadmap to v0.4.0

- [ ] Automated evaluation scheduler
- [ ] Slack/Discord notification system
- [ ] CI/CD pipeline with automated tests
- [ ] Batch evaluation optimization
- [ ] Prometheus metrics integration

---

## 📝 Technical Notes

### LLM Judge Implementation

The judge uses structured output to ensure consistent scoring:

```python
# services/evaluator/app/llm_judge.py
import json
from openai import OpenAI

def evaluate_with_llm(prompt: str, response: str, judge_model: str) -> dict:
    client = OpenAI(api_key=settings.llm_api_key)

    evaluation_prompt = f"""
    Evaluate this LLM response:

    Prompt: {prompt}
    Response: {response}

    Provide JSON with scores (1-5) and comments.
    """

    result = client.chat.completions.create(
        model=judge_model,
        messages=[{"role": "user", "content": evaluation_prompt}],
        response_format={"type": "json_object"}
    )

    return json.loads(result.choices[0].message.content)
```

### Localization System

Uses a simple key-based translation system:

```python
# services/dashboard/app/utils/localization.py
import json

def load_translations(language: str) -> dict:
    with open(f"locales/{language}.json") as f:
        return json.load(f)

def get_text(key: str, language: str = "en") -> str:
    translations = load_translations(language)
    return translations.get(key, key)
```

---

## 📚 Documentation Updates

- Updated README with LLM-as-a-judge setup
- Added localization guide
- Documented new scoring dimensions
- Added cost estimation guide for LLM judge
- Updated API documentation with new endpoints

---

## 🙏 Acknowledgments

- OpenAI for GPT-4 API enabling intelligent evaluation
- Community contributors for translation support
- Users providing feedback on evaluation criteria

---

**Previous Release**: [v0.2.0](./RELEASE_NOTES_v0.2.0.md)
**Next Release**: v0.4.0 will introduce automated scheduling and notifications
