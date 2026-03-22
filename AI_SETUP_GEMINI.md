# 🤖 AI Food Analysis Setup Guide (Google Gemini)

## Overview
The restaurant management system now includes an **AI Dish Assistant** that automatically generates dish names and descriptions from food images using **Google Gemini Vision API**.

---

## 📋 Prerequisites

1. **Python 3.8+** (already installed)
2. **Google Gemini API Key** (FREE - unlimited usage)

---

## 🔑 Getting a Google Gemini API Key

### ✅ Important: Gemini API is 100% FREE!
- No credit card required
- Unlimited free usage (generous limits)
- Perfect for restaurant menus
- Much faster than paid APIs

### Step 1: Get Your Free API Key
1. Go to [ai.google.dev](https://ai.google.dev)
2. Click **"Get API Key"** button (in top right, or in "Get started" section)
3. Sign in with your Google account (Gmail, Google Workspace, etc.)
4. Click **"Create API key in new project"** or select existing project
5. Copy your API key (it starts with `AIza...`)
6. **IMPORTANT**: Keep this key private - don't share it!

### Visual Guide:
```
1. Visit: https://ai.google.dev
   ↓
2. Click "Get API Key" button
   ↓
3. Select "Create API key in new project"
   ↓
4. Copy the provided API key
   ↓
5. Paste into .env file (see Step 3 below)
```

---

## 📦 Install Required Dependencies

Run the following command to install the AI packages:

```bash
pip install -r requirements.txt
```

This will install:
- `google-generativeai==0.3.0` - Google Gemini API client
- `python-dotenv==1.0.0` - Environment variable loader

---

## 🔧 Configure Your API Key

### Option A: Using `.env` File (Recommended)
1. In the project root directory, create a file named `.env`
2. Add your API key:
   ```
   GEMINI_API_KEY=AIza_your_api_key_here
   ```
3. Save the file
4. **DO NOT commit this file to Git**

### Option B: Using Environment Variable (Windows)
1. Open **System Properties** → **Environment Variables**
2. Click **New** under User variables
3. Variable name: `GEMINI_API_KEY`
4. Variable value: `AIza_your_api_key_here`
5. Click **OK** and restart your terminal/IDE

---

## 🚀 Using the AI Dish Assistant

### Admin Creates a New Menu Item:
1. Navigate to **Admin → Create Menu** (`/admin/menu/create`)
2. In the **"AI Dish Assistant"** section:
   - Click **"Choose File"** to select a food image
   - Click **"Analyze Image"** button
3. The AI will automatically:
   - Generate a professional **dish name** (in English)
   - Create an **appetizing description** (50-100 words)
   - Fill these fields automatically in the form
4. Review and edit the AI-generated content if needed
5. Fill in other fields (Price, Category, Rating)
6. Click **"Save Menu"** to create the dish

### Admin Edits an Existing Menu Item:
1. Navigate to the menu item edit page
2. In the **"AI Dish Assistant"** section:
   - Upload a new image
   - Click **"Analyze"** to regenerate the name and description
3. Edit the auto-filled content as needed
4. Click **"Save Changes"**

---

## 🎯 Why Google Gemini?

| Feature | Gemini | OpenAI |
|---------|--------|--------|
| **Cost** | ✅ FREE | ❌ ~$0.01/image |
| **API Key** | ✅ Easy (no credit card) | ❌ Requires credit card |
| **Vision Quality** | ✅ Excellent | ✅ Excellent |
| **Speed** | ✅ Very fast (2-3s) | ⚠️ Slower (3-5s) |
| **Limits** | ✅ Very generous | ⚠️ Rate limits |

---

## 🎯 Features

- **Automatic Dish Recognition**: AI identifies the food in the image
- **English Descriptions**: Professional, appetizing descriptions in English
- **Quick & Accurate**: 2-3 seconds per analysis
- **100% Free**: No cost to use
- **Editable**: Admin can modify AI-generated content
- **Error Handling**: Clear error messages if something goes wrong

---

## ⚠️ Troubleshooting

### Error: "API key not configured"
**Solution:** 
1. Make sure your `.env` file exists with `GEMINI_API_KEY` set
2. Or set the environment variable and restart the application
3. Verify the key format starts with `AIza`

### Error: "Invalid or missing API key"
**Solution:**
1. Your API key might be incorrect or expired
2. Get a new key from [ai.google.dev](https://ai.google.dev)
3. Update your `.env` file or environment variable
4. Restart the application

### Error: "Failed to parse AI response"
**Solution:**
1. The image might be too small, blurry, or not a food image
2. Try a higher-quality, clearer food image
3. Ensure the file is in JPG, PNG, GIF, or WebP format
4. Make sure the image is clearly a food/dish

### No response after clicking "Analyze"
**Solution:**
1. Check your internet connection
2. Verify your Gemini API key is valid at [ai.google.dev](https://ai.google.dev)
3. Check if the image file is uploaded properly
4. Try again with a different image

---

## 🔒 Security Tips

1. **Never commit `.env` file to Git**
   - Add `.env` to `.gitignore`: `echo ".env" >> .gitignore`
2. **Keep your API key private**
   - Don't share your `GEMINI_API_KEY` with anyone
3. **Monitor API usage**
   - Check your usage at [ai.google.dev](https://ai.google.dev/dashboard)

---

## 📚 Supported Image Formats

- ✅ JPEG (.jpg, .jpeg)
- ✅ PNG (.png)
- ✅ GIF (.gif)
- ✅ WebP (.webp)

**Image Requirements:**
- Minimum: 32x32 pixels
- Maximum: 20MB
- **Best results**: Clear, well-lit, close-up food photos

---

## 📞 Getting Help

### Documentation
- Google Gemini API Docs: https://ai.google.dev/docs
- Vision Guide: https://ai.google.dev/tutorials/vision

### Common Issues
1. API key not working? 
   - Get a new one from [ai.google.dev](https://ai.google.dev)
2. Images not recognized?
   - Try clearer, higher-res images
3. Application errors?
   - Check the console output for detailed error messages

---

## 🎉 Quick Start

1. **Get your FREE API key** at [ai.google.dev](https://ai.google.dev)
2. **Install packages**: `pip install -r requirements.txt`
3. **Set up `.env` file** with your `GEMINI_API_KEY`
4. **Restart the application**
5. **Start using the AI Dish Assistant!**

---

## 💡 Tips for Best Results

### Image Quality Tips:
1. **Use clear, high-quality images** - Avoid blurry or dark photos
2. **Show the entire dish** - Make sure the main food is visible
3. **Good lighting** - Natural light works best
4. **Close-up shots** - Better than distant views

### Example Flow:
```
1. Admin goes to "/admin/menu/create"
2. Uploads a photo of grilled salmon
3. Clicks "Analyze Image"
4. AI generates:
   - Name: "Pan-Seared Salmon with Lemon Herb Butter"
   - Description: "Succulent Atlantic salmon fillet pan-seared to perfection..."
5. Admin enters price, category, rating
6. Clicks "Save Menu" - Done!
```

---

## ✨ Enjoy Your AI-Powered Menu Creation!

With Gemini's powerful vision capabilities and 100% free pricing, you can instantly create professional menu items with just an image. No more manual typing! 🍽️✨

Happy analyzing! 🚀
