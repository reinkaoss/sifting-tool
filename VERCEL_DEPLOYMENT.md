# 🚀 Deploying to Vercel

This guide will walk you through deploying your Sifting Tool to Vercel.

## 📋 Prerequisites

1. **Vercel Account**: Sign up at [vercel.com](https://vercel.com)
2. **Git Repository**: Your code should be in a GitHub, GitLab, or Bitbucket repository
3. **Environment Variables**: Have your `OPENAI_API_KEY` ready
4. **Google Service Account**: Your `google_credentials.json` file

---

## 🎯 Part 1: Backend Setup (Flask API)

### Step 1: Create `vercel.json` for Backend

Create a new file `/backend/vercel.json`:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "app.py",
      "use": "@vercel/python"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "app.py"
    }
  ]
}
```

### Step 2: Update `requirements.txt`

Make sure `/backend/requirements.txt` has all dependencies:

```txt
Flask==3.0.0
flask-cors==4.0.0
openai==1.52.0
python-dotenv==1.0.0
gspread==6.2.1
google-auth==2.41.1
google-auth-oauthlib==1.2.2
google-auth-httplib2==0.2.0
```

### Step 3: Update Flask App for Production

Modify `/backend/app.py` to handle Vercel's serverless environment:

```python
# At the bottom of app.py, replace:
if __name__ == '__main__':
    app.run(debug=True, port=5000)

# With:
if __name__ == '__main__':
    app.run(debug=False)

# Add this for Vercel
handler = app
```

### Step 4: Deploy Backend to Vercel

1. **Go to Vercel Dashboard**: [vercel.com/dashboard](https://vercel.com/dashboard)
2. **Click "Add New Project"**
3. **Import your repository**
4. **Configure project**:
   - **Root Directory**: `backend`
   - **Framework Preset**: Other
5. **Add Environment Variables**:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `GOOGLE_APPLICATION_CREDENTIALS_JSON`: Copy the entire contents of `google_credentials.json` as a string
6. **Deploy!**

### Step 5: Update Backend Code for Vercel Credentials

Modify `/backend/sheets_api.py` to handle credentials from environment:

```python
import os
import json

def get_spreadsheet(sheet_id=None):
    """Get authenticated spreadsheet connection"""
    # Try to get credentials from environment (Vercel)
    creds_json = os.getenv('GOOGLE_APPLICATION_CREDENTIALS_JSON')
    
    if creds_json:
        # Parse JSON from environment variable
        creds_dict = json.loads(creds_json)
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
    else:
        # Use local file (development)
        creds = Credentials.from_service_account_file('google_credentials.json', scopes=SCOPES)
    
    client = gspread.authorize(creds)
    spreadsheet_id = sheet_id or DEFAULT_SPREADSHEET_ID
    return client.open_by_key(spreadsheet_id)
```

---

## 🎨 Part 2: Frontend Setup (React)

### Step 1: Update API URLs

Update `/src/App.js` to use the deployed backend URL:

```javascript
// At the top of App.js, add:
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

// Then replace all fetch calls from:
fetch('http://localhost:5000/...')

// To:
fetch(`${API_URL}/...`)
```

### Step 2: Create Frontend Environment Variables

Create `/public/_redirects` for SPA routing:

```
/*    /index.html   200
```

### Step 3: Deploy Frontend to Vercel

1. **Go to Vercel Dashboard**: [vercel.com/dashboard](https://vercel.com/dashboard)
2. **Click "Add New Project"**
3. **Import your repository** (same repo, different project)
4. **Configure project**:
   - **Root Directory**: `.` (root)
   - **Framework Preset**: Create React App
   - **Build Command**: `npm run build`
   - **Output Directory**: `build`
5. **Add Environment Variable**:
   - `REACT_APP_API_URL`: Your backend URL (e.g., `https://your-backend.vercel.app`)
6. **Deploy!**

---

## 🔧 Alternative: Monorepo Deployment

If you want to deploy both frontend and backend from the same repository:

### Create Root `vercel.json`:

```json
{
  "version": 2,
  "builds": [
    {
      "src": "backend/app.py",
      "use": "@vercel/python",
      "config": { "maxLambdaSize": "15mb" }
    },
    {
      "src": "package.json",
      "use": "@vercel/static-build",
      "config": {
        "distDir": "build"
      }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "backend/app.py"
    },
    {
      "src": "/(.*)",
      "dest": "/$1"
    }
  ]
}
```

Then update frontend to use `/api/...` for backend calls.

---

## ✅ Post-Deployment Checklist

### Backend Verification:
1. Visit `https://your-backend.vercel.app/health`
2. Should return `{"status": "OK"}`

### Frontend Verification:
1. Visit `https://your-frontend.vercel.app`
2. Test loading clients
3. Test loading applications
4. Test analysis

### Common Issues:

**Issue**: Google Sheets API fails
- **Fix**: Make sure `GOOGLE_APPLICATION_CREDENTIALS_JSON` is set correctly in Vercel

**Issue**: CORS errors
- **Fix**: Ensure `flask-cors` is installed and configured in `app.py`

**Issue**: API key errors
- **Fix**: Verify `OPENAI_API_KEY` environment variable in Vercel

**Issue**: Serverless function timeout
- **Fix**: The app automatically batches 10+ applications into groups of 10 to avoid timeout
- Each batch is processed separately with results written immediately
- For very large batches (100+ applications), this may take time but won't timeout

---

## 🔒 Security Best Practices

1. **Never commit**:
   - `.env` files
   - `google_credentials.json`
   - API keys

2. **Always use environment variables** in Vercel for:
   - `OPENAI_API_KEY`
   - `GOOGLE_APPLICATION_CREDENTIALS_JSON`

3. **Update `.gitignore`**:
```
.env
*.env
google_credentials.json
backend/.env
```

---

## 📱 Custom Domain (Optional)

1. Go to your project in Vercel
2. Click **Settings** > **Domains**
3. Add your custom domain
4. Update DNS records as instructed

---

## 🔄 Continuous Deployment

Vercel automatically redeploys when you push to your repository:
- **Production**: Pushes to `main` branch
- **Preview**: Pushes to other branches

---

## 💡 Tips

1. **Environment Variables**: Test locally with `.env` before deploying
2. **Logs**: Check Vercel deployment logs for errors
3. **Caching**: Vercel caches builds, use "Redeploy" if needed
4. **Regions**: Choose a deployment region close to your users

---

## 📞 Support

- **Vercel Docs**: [vercel.com/docs](https://vercel.com/docs)
- **Vercel Community**: [github.com/vercel/vercel/discussions](https://github.com/vercel/vercel/discussions)

---

Good luck with your deployment! 🚀

