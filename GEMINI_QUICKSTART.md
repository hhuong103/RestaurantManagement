## 🚀 Quick Setup for Google Gemini API

### Step 1: Get Your FREE Gemini API Key (2 minutes)

1. **Visit**: https://ai.google.dev
2. **Click**: "Get API Key" button (top right)
3. **Sign in** with your Google account (Gmail works)
4. **Accept** the terms
5. **Copy** your API key (looks like: `AIza_xxxxxxxxxxxxx`)

✅ **That's it! No credit card needed!**

---

### Step 2: Install Dependencies

> ⚠️ **Python compatibility**: The latest Gemini client may require Python 3.9 or newer. On Python 3.8 (the version bundled in this workspace), `pip install -r requirements.txt` will pull in `google-generativeai==0.1.0rc1`, which is compatible but may emit a warning about future support. If possible upgrade to Python 3.10+ to use the newest release.

```bash
pip install -r requirements.txt
```

Or if you only want to update Gemini packages:
```bash
pip install google-generativeai==0.3.0 python-dotenv==1.0.0
```

---

### Step 3: Configure Your API Key

**Create a file named `.env` in the project root** (same folder as `app.py`):

```
GEMINI_API_KEY=AIza_your_api_key_here
FLASK_ENV=development
```

Replace `AIza_your_api_key_here` with your actual API key from Step 1.

⚠️ **Important**: 
- `.env` is in `.gitignore` (not committed to Git)
- Never share your API key

---

### Step 4: Restart Your Application

```bash
python app.py
```

Or if using a different command:
```bash
flask run
```

---

### Step 5: Start Using AI!

✅ Go to: `http://localhost:5000/admin/menu/create`

✅ Use the **"AI Dish Assistant"** section to analyze food images

> 💡 **Tip:** If your Python version is too old, the AI assistant will still work but you'll see a notice like "AI unavailable" in the result box. You can type the name/description manually. Upgrading to Python 3.10+ and reinstalling dependencies will restore full functionality.

---

## 🎯 How to Use

1. **Upload an image** of your dish (JPG, PNG, GIF, or WebP)
2. **Click "Analyze Image"**
3. Wait 2-3 seconds
4. **AI automatically fills**:
   - Dish name (in English)
   - Description (appetizing, 50-100 words)
5. **Edit if needed**, then save

---

## ✨ Features

✅ **100% FREE** - No cost  
✅ **Super Fast** - 2-3 seconds per image  
✅ **High Quality** - Professional descriptions  
✅ **Easy Setup** - 5 minutes total  
✅ **Works Offline** - Just needs initial API call  

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| "API key not configured" | Check `.env` file has `GEMINI_API_KEY=AIza_...` |
| "Invalid API key" | Get new key from [ai.google.dev](https://ai.google.dev) |
| "No response from AI" | Check internet connection, try different image |
| "Can't find .env file" | Create `.env` in same folder as `app.py` |

---

## 📚 Full Documentation

See `AI_SETUP_GEMINI.md` for detailed instructions.

---

**Questions?** Check the AI_SETUP_GEMINI.md file for complete guide!
