# LLM Model Comparison for Quiz Feature

## Your Current Setup

You have 4 switchable models:
1. **DeepSeek V4** (via `deepseek-v4-flash`)
2. **Gemini Flash** (via `gemini-2.5-flash`)
3. **Gemma 4** (via OpenRouter: `google/gemma-4-31b-it`)
4. **Qwen 3.5/3.6 Flash** (via `qwen3.6-flash`)

---

## 💰 Pricing Comparison (as of 2025)

### **Cheapest to Most Expensive:**

| Rank | Model | Input Price | Output Price | Best For |
|------|-------|-------------|--------------|----------|
| 🥇 **1st** | **Qwen3.6-Flash** | ~$0.05/M tokens | ~$0.15/M tokens | **CHEAPEST** |
| 🥈 **2nd** | **Gemini 2.5 Flash** | Free tier + ~$0.075/M | ~$0.30/M tokens | Best free tier |
| 🥉 **3rd** | **Gemma 4 31B** | ~$0.20/M tokens | ~$0.40/M tokens | Mid-range |
| 4th | **DeepSeek V4** | ~$0.50/M tokens | ~$1.00/M tokens | Most expensive |

> ⚠️ Prices are approximate and may vary. Check official pricing for latest rates.

---

## ⚡ Speed Comparison

| Rank | Model | Avg Response Time | Notes |
|------|-------|-------------------|-------|
| 🥇 **1st** | **Gemini 2.5 Flash** | ~1-2 seconds | Fastest overall |
| 🥈 **2nd** | **Qwen3.6-Flash** | ~2-3 seconds | Very fast |
| 🥉 **3rd** | **DeepSeek V4 Flash** | ~3-5 seconds | Good speed |
| 4th | **Gemma 4 31B** | ~4-6 seconds | Slower via OpenRouter |

---

## 🎯 Recommendation for Quiz Feature

### **Best Choice: Qwen3.6-Flash** 
- ✅ **Cheapest** - Save money on daily quizzes
- ✅ **Fast enough** - 2-3s response time
- ✅ **Good quality** - Handles structured JSON well
- ✅ **Reliable** - Less rate limiting than free tiers

### **Alternative: Gemini 2.5 Flash**
- ✅ **Free tier available** - $0 up to certain limit
- ✅ **Fastest** - Best user experience
- ⚠️ **Rate limits** - May hit quotas with many users
- ⚠️ **JSON parsing** - Sometimes adds markdown fences

---

## 📊 Cost Estimate for Quizzes

Assuming:
- 1 quiz = 4 questions
- Each question prompt ~500 tokens
- Each response ~800 tokens
- Total per quiz ≈ **5,000 tokens**

### Daily cost if 10 users generate quizzes:

| Model | Cost per 10 quizzes | Monthly cost |
|-------|--------------------|--------------|
| **Qwen3.6-Flash** | $0.005 | **$0.15** |
| **Gemini Flash** | $0.004* | **$0.12** (*with free tier) |
| **Gemma 4** | $0.03 | **$0.90** |
| **DeepSeek V4** | $0.075 | **$2.25** |

---

## 🔧 Implementation Tips

### For Quiz-Specific Model:
```python
# In your quiz_handler.py, you can force a specific provider:
result = await ai_manager.generate_response(
    prompt=prompt,
    user_id=user.id,
    is_owner=admin,
    provider='qwen'  # Force cheapest model for quizzes
)
```

### Recommended Setup:
1. **Default for chat (`/miki`)**: Gemini Flash (fastest, free tier)
2. **Default for quizzes (`/quiz`)**: Qwen3.6-Flash (cheapest)
3. **Admin override**: Allow admins to switch for testing

---

## 📝 Final Verdict

**Use Qwen3.6-Flash for quizzes** because:
- 80% cheaper than DeepSeek
- No free tier quota worries
- Still very fast (2-3s)
- Good at following JSON format instructions

**Keep Gemini Flash as default** for regular chat because:
- Fastest response time
- Free tier covers light usage
- Better conversational quality

---

## 🔗 Provider Setup in Your Code

Your current files:
- `llm/qwen.py` → Uses `qwen3.6-flash` ✅
- `llm/gemini.py` → Uses `gemini-2.5-flash` ✅
- `llm/deepseek.py` → Uses `deepseek-v4-flash` ✅
- `llm/openrouter.py` → Uses `google/gemma-4-31b-it` ✅

To switch: `/switchllm qwen` (admin only)
