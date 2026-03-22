# 🤖 AI Food Analysis Setup Guide

## Overview
The restaurant management system now includes an **AI Dish Assistant** that automatically generates dish names and descriptions from food images using OpenAI's Vision API.

---

## 📋 Prerequisites

1. **Python 3.8+** (already installed)
2. **OpenAI API Key** (free trial available)

---

## 🔑 Getting an OpenAI API Key

### Step 1: Create an OpenAI Account
1. Go to [platform.openai.com](https://platform.openai.com)
2. Click **Sign up** and create an account
3. Verify your email address

### Step 2: Generate API Key
1. After login, navigate to **API keys** section
2. Click **+ Create new secret key**
3. Copy your API key (it starts with `sk-`)
4. **IMPORTANT**: Save this key in a secure place - you won't be able to see it again!

### Step 3: Set Your API Key
There are two ways to configure your API key:

#### Option A: Using `.env` File (Recommended)
1. In the project root directory, create a file named `.env` (or copy from `.env.example`)
2. Add your API key:
   ```
   OPENAI_API_KEY=sk-your-api-key-here
   ```
3. Save the file
4. **DO NOT commit this file to Git** - it contains sensitive information

#### Option B: Using Environment Variable (Windows)
1. Open **System Properties** → **Environment Variables**
2. Click **New** under User variables
3. Variable name: `OPENAI_API_KEY`
4. Variable value: `sk-your-api-key-here`
5. Click **OK** and restart your terminal/IDE

---

## 📦 Install Required Dependencies

Run the following command to install the AI packages:

```bash
pip install -r requirements.txt
```

This will install:
- `openai==1.3.0` - OpenAI API client
- `python-dotenv==1.0.0` - Environment variable loader

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

## 🎯 Features

- **Automatic Dish Recognition**: AI identifies the food in the image
- **English Descriptions**: Professional, appetizing descriptions in English
- **Quick & Accurate**: 3-5 seconds per analysis
- **Editable**: Admin can modify AI-generated content
- **Error Handling**: Clear error messages if something goes wrong

---

## 💰 Pricing

OpenAI Vision API pricing:
- **GPT-4 Vision**: $0.01 USD per image (approximately)
- **Free Trial**: $5 credit for first 3 months
- Average cost per menu item: **less than 1 cent**

For a restaurant with 100 menu items:
- ~$1 total cost for one-time analysis
- Negligible ongoing costs

---

## ⚠️ Troubleshooting

### Error: "API key not configured"
- Solution: Make sure your `.env` file exists with `OPENAI_API_KEY` set
- Or set the environment variable and restart the application

### Error: "Failed to analyze image"
- The image might be too small or unclear
- Try a higher-quality food image
- Ensure the file is in JPG, PNG, GIF, or WebP format

### Error: "Invalid API key"
- Your API key may have expired or been revoked
- Generate a new key from the OpenAI dashboard
- Update your `.env` file

### No response after clicking "Analyze"
- Check your internet connection
- Verify your OpenAI API key is valid
- Check OpenAI status at [status.openai.com](https://status.openai.com)

---

## 🔒 Security Tips

1. **Never commit `.env` file to Git**
   - Add `.env` to `.gitignore`: `echo ".env" >> .gitignore`
2. **Rotate API keys regularly**
   - Delete old keys from the OpenAI dashboard
3. **Use environment variables in production**
   - Don't hardcode API keys in source code
4. **Monitor API usage**
   - Check your usage dashboard at [platform.openai.com/usage](https://platform.openai.com/usage)

---

## 📚 Example Results

**Image**: Grilled salmon with lemon butter

**AI Generated:**
- **Name**: Grilled Salmon with Lemon Butter
- **Description**: A perfectly grilled Atlantic salmon fillet topped with a rich lemon butter sauce, garnished with fresh dill and served with roasted vegetables. This elegant dish combines classic French techniques with fresh, quality ingredients.

---

## 🎓 Supported Image Formats

- JPEG (.jpg, .jpeg)
- PNG (.png)
- GIF (.gif)
- WebP (.webp)

**Image Requirements:**
- Minimum: 32x32 pixels
- Maximum: 20MB
- Clear, well-lit food photos work best

---

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Review OpenAI documentation: [Cooking with AI](https://platform.openai.com/docs/guides/vision)
3. Contact OpenAI support: [support.openai.com](https://support.openai.com)

---

## 🎉 Next Steps

1. Install the packages: `pip install -r requirements.txt`
2. Set up your API key in `.env`
3. Restart the application
4. Start using the AI Dish Assistant!

Happy analyzing! 🍽️✨
