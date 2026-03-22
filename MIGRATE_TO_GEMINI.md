## 📋 Migrating from OpenAI to Google Gemini

If you previously set up the system with **OpenAI API**, follow these simple steps to switch to the **free Google Gemini API**.

---

## ✅ Why Switch to Gemini?

| Feature | OpenAI | Gemini |
|---------|--------|--------|
| Cost per image | $0.01 USD | **FREE** ✅ |
| Setup complexity | Requires credit card | **Just need Google account** ✅ |
| Speed | 3-5 seconds | **2-3 seconds** ✅ |
| Quality | Excellent | **Excellent** ✅ |
| API Key setup | Complex | **Super easy** ✅ |

**Result**: You'll save ~$1 per 100 menu items!

---

## 🔄 Migration Steps (5 minutes)

### Step 1: Remove Old OpenAI Settings
If you have an `OPENAI_API_KEY` set in your `.env` or environment variables:

**In `.env` file:**
- Delete or comment out: `OPENAI_API_KEY=sk-...`

**In System Environment Variables (Windows):**
1. Open System Properties → Environment Variables
2. Find and delete `OPENAI_API_KEY` variable
3. Restart your terminal

### Step 2: Get Your FREE Gemini API Key
1. Go to: https://ai.google.dev
2. Click "Get API Key"
3. Sign in with Google (Gmail works!)
4. Copy the API key (starts with `AIza_`)

### Step 3: Update `.env` File
In your project root, update `.env`:

```
# Remove this line:
# OPENAI_API_KEY=sk-...

# Add this line:
GEMINI_API_KEY=AIza_your_key_here
```

### Step 4: Update Dependencies
```bash
pip install -r requirements.txt
```

This installs:
- ✅ `google-generativeai` (replaces openai)
- ✅ `python-dotenv` (still needed)

### Step 5: Restart the Application
```bash
python app.py
```

---

## ✨ That's It!

Your system is now using **100% FREE Google Gemini** for all AI dish analysis!

---

## 🎯 What Changed?

| Component | Before (OpenAI) | After (Gemini) |
|-----------|-----------------|---|
| Backend Library | `openai` | `google-generativeai` |
| API Endpoint | `/api/analyze_food_image` | *(same)* |
| Frontend UI | *(no change)* | *(no change)* |
| Config File | `OPENAI_API_KEY` | `GEMINI_API_KEY` |
| Database | *(no change)* | *(no change)* |
| Menu Forms | *(no change)* | *(no change)* |

**Bottom line**: Just swap the API key and library - everything else works the same!

---

## 🆘 Troubleshooting

### Still seeing OpenAI errors?
1. Make sure you restarted the application
2. Check if old `OPENAI_API_KEY` is still in environment
3. Delete any old `__pycache__` folders: `python -c "import shutil; shutil.rmtree('__pycache__', ignore_errors=True)"`

### Getting "API key not configured" error?
- Verify `.env` file has: `GEMINI_API_KEY=AIza_xxxxx`
- Make sure there are no extra spaces: `GEMINI_API_KEY = ...` (spaces will cause issues)
- Restart the application

### API key error?
- Visit [ai.google.dev](https://ai.google.dev)
- Generate a new API key
- Update `.env` file
- Restart

---

## 📚 Documentation

- **Quick Start**: See `GEMINI_QUICKSTART.md`
- **Full Guide**: See `AI_SETUP_GEMINI.md`
- **Original Setup**: See `AI_SETUP.md` (archived)

---

## 💡 Cost Savings Example

**Before (OpenAI)**:
- 100 menu items × $0.01 per image = **$1.00 cost**
- Recurring costs for updates

**After (Gemini)**:
- 100 menu items × $0 per image = **$0 cost** ✅
- Completely FREE forever!

**Savings**: Up to **$1+ per 100 items** 🎉

---

## ✅ Verification

After migration, test it works:

1. Go to: `http://localhost:5000/admin/menu/create`
2. Upload a food image
3. Click "Analyze Image"
4. Should get results in 2-3 seconds

If it works → **Migration successful!** 🎉

---

**No more paying for AI! Enjoy your free Gemini setup!** 🚀
