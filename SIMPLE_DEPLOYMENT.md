# 🚀 Simple Deployment Guide (Monorepo)

Deploy both frontend and backend together in **one Vercel project**!

---

## ✅ Prerequisites

1. **Vercel Account**: [vercel.com](https://vercel.com)
2. **Git Repository**: Push your code to GitHub/GitLab/Bitbucket
3. **Google Credentials**: Copy contents of `google_credentials.json`
4. **OpenAI API Key**: Your OpenAI API key

---

## 📦 Step 1: Prepare Your Repository

Make sure all changes are committed and pushed:

```bash
git add .
git commit -m "Ready for deployment"
git push origin main
```

---

## 🎯 Step 2: Deploy to Vercel (5 minutes)

### A. Import Project

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click **"Add New Project"**
3. **Import** your Git repository
4. Vercel will auto-detect the configuration

### B. Configure Project

**Project Settings:**
- **Framework Preset**: Create React App ✅ (auto-detected)
- **Root Directory**: `.` (leave as root) ✅
- **Build Command**: `npm run build` ✅ (auto-detected)
- **Output Directory**: `build` ✅ (auto-detected)

### C. Add Environment Variables

Click **"Environment Variables"** and add these **3 variables**:

| Key | Value |
|-----|-------|
| `OPENAI_API_KEY` | Your OpenAI API key |
| `GOOGLE_APPLICATION_CREDENTIALS_JSON` | Paste **entire** contents of `google_credentials.json` |
| `REACT_APP_API_URL` | `/api` |

**Important**: 
- For `GOOGLE_APPLICATION_CREDENTIALS_JSON`: Open your `google_credentials.json`, copy **everything** (the entire JSON object), and paste it
- Make sure it's valid JSON (starts with `{` and ends with `}`)

### D. Deploy!

1. Click **"Deploy"**
2. Wait 2-3 minutes
3. Get your URL: `https://your-app.vercel.app` 🎉

---

## ✅ Step 3: Test Your Deployment

1. Visit your Vercel URL
2. Test backend health: `https://your-app.vercel.app/api/health`
   - Should return: `{"status": "OK"}`
3. Test the full app:
   - Enter spreadsheet URL
   - Load applications
   - Load clients
   - Run analysis

---

## 🔧 How It Works

### **Single Deployment = Frontend + Backend**

```
your-app.vercel.app/              → React frontend
your-app.vercel.app/api/health    → Flask backend
your-app.vercel.app/api/clients   → Flask backend
your-app.vercel.app/api/sheets/*  → Flask backend
```

### **Routing Magic** (vercel.json)
- All `/api/*` requests → Python backend
- All other requests → React frontend
- No CORS issues!
- Single domain!

---

## 🐛 Troubleshooting

### Issue: "Module not found" error
**Fix**: Make sure `backend/requirements.txt` exists with all dependencies

### Issue: "Google credentials error"  
**Fix**: 
1. Verify `GOOGLE_APPLICATION_CREDENTIALS_JSON` is set
2. Check it's valid JSON (copy the **entire file contents**)
3. No extra quotes or formatting

### Issue: "OpenAI API error"
**Fix**: Verify `OPENAI_API_KEY` is correct in environment variables

### Issue: Frontend shows "Cannot connect to API"
**Fix**: 
1. Check `REACT_APP_API_URL` is set to `/api`
2. Redeploy the project
3. Clear browser cache

### Issue: Still not working?
1. Check Vercel **deployment logs** for errors
2. Check Vercel **function logs** for runtime errors
3. Try redeploying: Click "Redeploy" in Vercel dashboard

---

## 🔄 Continuous Deployment

Once deployed, Vercel **automatically redeploys** when you push to your repository:

```bash
# Make changes
git add .
git commit -m "Update feature"
git push

# Vercel automatically deploys! ✨
```

- **Production**: Pushes to `main` branch
- **Preview**: Pushes to other branches

---

## 📊 Monitor Your Deployment

### Vercel Dashboard:
- **Deployments**: See all deployment history
- **Logs**: View runtime logs
- **Analytics**: Monitor usage (optional)
- **Settings**: Update environment variables

---

## 🎨 Optional: Custom Domain

1. Go to your project in Vercel
2. Click **Settings** > **Domains**
3. Add your domain (e.g., `sifting.yourdomain.com`)
4. Follow DNS instructions
5. SSL certificate auto-generated! 🔒

---

## 📋 Environment Variables Summary

```bash
# Required for deployment:
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
REACT_APP_API_URL=/api
```

---

## 🎉 You're Done!

Your app is now live with:
- ✅ **Frontend** (React)
- ✅ **Backend** (Flask/Python)  
- ✅ **Google Sheets Integration**
- ✅ **OpenAI Analysis**
- ✅ **Automatic Batching** (no timeouts!)
- ✅ **Auto-deployment** on git push

---

## 🔗 Quick Links

- [Vercel Dashboard](https://vercel.com/dashboard)
- [Vercel Docs](https://vercel.com/docs)
- [Project Repository](https://github.com/your-repo)

---

**Total deployment time: ~5 minutes** ⚡

Need the detailed guide? See `VERCEL_DEPLOYMENT.md`

