# 📋 Deployment Checklist

Follow this checklist to deploy your Sifting Tool to Vercel.

## ✅ Pre-Deployment

- [ ] Commit all changes to your Git repository
- [ ] Push to GitHub/GitLab/Bitbucket
- [ ] Have your `OPENAI_API_KEY` ready
- [ ] Have `google_credentials.json` content ready (copy entire file as text)
- [ ] Verify `.gitignore` excludes sensitive files

## 🔧 Backend Deployment (Vercel)

### 1. Deploy Backend
- [ ] Go to [vercel.com/dashboard](https://vercel.com/dashboard)
- [ ] Click "Add New Project"
- [ ] Import your repository
- [ ] Set **Root Directory** to `backend`
- [ ] Set **Framework Preset** to "Other"

### 2. Add Environment Variables
- [ ] `OPENAI_API_KEY` = `your-openai-api-key`
- [ ] `GOOGLE_APPLICATION_CREDENTIALS_JSON` = `{paste entire google_credentials.json content}`

### 3. Deploy & Test
- [ ] Click "Deploy"
- [ ] Wait for deployment to complete
- [ ] Copy your backend URL (e.g., `https://your-backend.vercel.app`)
- [ ] Test: Visit `https://your-backend.vercel.app/health`
- [ ] Should return: `{"status": "OK"}`

## 🎨 Frontend Deployment (Vercel)

### 1. Create New Project
- [ ] Go to [vercel.com/dashboard](https://vercel.com/dashboard)
- [ ] Click "Add New Project"
- [ ] Import the **same repository**
- [ ] Set **Root Directory** to `.` (root)
- [ ] Set **Framework Preset** to "Create React App"
- [ ] Set **Build Command** to `npm run build`
- [ ] Set **Output Directory** to `build`

### 2. Add Environment Variable
- [ ] `REACT_APP_API_URL` = `https://your-backend.vercel.app` (your backend URL from step above)

### 3. Deploy & Test
- [ ] Click "Deploy"
- [ ] Wait for deployment to complete
- [ ] Visit your frontend URL
- [ ] Test all features:
  - [ ] Load clients from Google Sheets
  - [ ] Load applications from Google Sheets
  - [ ] Run analysis
  - [ ] Add new client
  - [ ] Delete client

## 🔍 Troubleshooting

### Backend Issues

**"Module not found" errors**
- Check `backend/requirements.txt` includes all dependencies
- Redeploy backend

**"Google credentials error"**
- Verify `GOOGLE_APPLICATION_CREDENTIALS_JSON` is set correctly
- Content should be valid JSON (entire file content)
- No extra spaces or newlines

**"OpenAI API error"**
- Verify `OPENAI_API_KEY` is set correctly
- Check key is active in OpenAI dashboard

### Frontend Issues

**"Cannot connect to API"**
- Verify `REACT_APP_API_URL` environment variable is set
- Should be your full backend URL
- No trailing slash

**"CORS errors"**
- Backend should have `flask-cors` installed
- Check backend logs in Vercel

### General Issues

**"Serverless function timeout"**
- Vercel free tier has 10-second timeout
- ✅ **Auto-batching enabled**: App automatically splits 10+ applications into batches
- Each batch processes separately and writes results immediately
- No timeout issues even with hundreds of applications!

**"Changes not reflecting"**
- Clear browser cache
- Hard refresh (Cmd+Shift+R / Ctrl+Shift+R)
- Check Vercel deployment logs
- Redeploy if needed

## 🎉 Post-Deployment

- [ ] Test all functionality in production
- [ ] Add custom domain (optional)
- [ ] Set up monitoring/alerts (optional)
- [ ] Document any production URLs
- [ ] Share with team!

## 📝 Environment Variables Summary

### Backend (Vercel)
```
OPENAI_API_KEY=sk-...
GOOGLE_APPLICATION_CREDENTIALS_JSON={"type":"service_account",...}
```

### Frontend (Vercel)
```
REACT_APP_API_URL=https://your-backend.vercel.app
```

## 🔗 Useful Links

- [Vercel Dashboard](https://vercel.com/dashboard)
- [Vercel Documentation](https://vercel.com/docs)
- [Your Deployment Guide](./VERCEL_DEPLOYMENT.md)

---

**Need help?** Check the full deployment guide in `VERCEL_DEPLOYMENT.md`

