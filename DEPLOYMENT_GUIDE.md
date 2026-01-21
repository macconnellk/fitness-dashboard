# 🚀 Deployment Guide

Complete guide to deploy your Training Dashboard to GitHub Pages with automated daily updates.

## Prerequisites

- GitHub account
- Git installed on your computer
- API credentials (see Setup Guide below)

---

## Part 1: Get Your API Credentials

### 1. Oura Ring API Token

1. Go to https://cloud.ouraring.com/personal-access-tokens
2. Click "Create New Personal Access Token"
3. Give it a name (e.g., "Training Dashboard")
4. Copy the token (save it somewhere safe)

**Note:** This token expires when your Oura subscription ends. The dashboard will automatically fall back to data exports.

### 2. Strava API

1. Go to https://www.strava.com/settings/api
2. Click "Create an App"
3. Fill in details:
   - Application Name: Training Dashboard
   - Category: Training
   - Website: http://localhost (or your GitHub Pages URL)
   - Authorization Callback Domain: localhost
4. Save and copy your **Client ID** and **Client Secret**

**Get Refresh Token:**
```bash
# Use this URL in browser (replace YOUR_CLIENT_ID):
https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&response_type=code&redirect_uri=http://localhost&approval_prompt=force&scope=activity:read_all

# After authorizing, you'll be redirected to: http://localhost/?code=AUTHORIZATION_CODE
# Copy the code from the URL

# Exchange for refresh token (replace values):
curl -X POST https://www.strava.com/oauth/token \
  -d client_id=YOUR_CLIENT_ID \
  -d client_secret=YOUR_CLIENT_SECRET \
  -d code=AUTHORIZATION_CODE \
  -d grant_type=authorization_code

# Copy the "refresh_token" from the response
```

### 3. Google Sheets

Your sheet is already published! Just need the ID:

1. Open your Google Sheet
2. Look at the URL: `https://docs.google.com/spreadsheets/d/SHEET_ID_HERE/edit`
3. Copy the `SHEET_ID_HERE` part
4. Verify it's published: File → Share → Publish to web → Check "Entire Document" and "CSV"

---

## Part 2: Deploy to GitHub

### Step 1: Create GitHub Repository

1. Go to https://github.com/new
2. Repository name: `fitness-dashboard` (or your choice)
3. **Important:** Make it **Private** (your health data!)
4. **Don't** initialize with README (we already have files)
5. Click "Create repository"

### Step 2: Push Your Code

In your terminal (in the fitness-dashboard folder):

```bash
# Initialize git (if not already done)
git init

# Add all files
git add .

# Create first commit
git commit -m "Initial commit - Training Dashboard"

# Add GitHub as remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/fitness-dashboard.git

# Push to GitHub
git branch -M main
git push -u origin main
```

### Step 3: Add Secrets to GitHub

**CRITICAL:** Never commit API keys to code. Store them as GitHub Secrets instead.

1. Go to your repository on GitHub
2. Click **Settings** (top menu)
3. Click **Secrets and variables** → **Actions** (left sidebar)
4. Click **New repository secret** for each:

Add these secrets:

| Secret Name | Value | Where to get it |
|-------------|-------|-----------------|
| `OURA_API_TOKEN` | Your Oura token | Step 1.1 above |
| `OURA_EMAIL` | Your Oura email | Your Oura login |
| `OURA_PASSWORD` | Your Oura password | Your Oura login |
| `STRAVA_CLIENT_ID` | Your Strava Client ID | Step 1.2 above |
| `STRAVA_CLIENT_SECRET` | Your Strava Secret | Step 1.2 above |
| `STRAVA_REFRESH_TOKEN` | Your refresh token | Step 1.2 above |
| `GOOGLE_SHEET_ID` | Your Sheet ID | Step 1.3 above |

**Note:** The `GITHUB_TOKEN` secret is created automatically - you don't need to add it.

### Step 4: Enable GitHub Pages

1. In your repository, go to **Settings**
2. Click **Pages** (left sidebar)
3. Under "Build and deployment":
   - Source: **Deploy from a branch**
   - Branch: **gh-pages** / **/ (root)**
   - Click **Save**

4. Wait 1-2 minutes
5. Your dashboard will be live at: `https://YOUR_USERNAME.github.io/fitness-dashboard`

### Step 5: Test the Workflow

**Option A: Wait for tomorrow 6 AM**
- The workflow will run automatically

**Option B: Trigger manually (recommended for first test)**

1. Go to **Actions** tab in your repository
2. Click "Daily Dashboard Update" (left sidebar)
3. Click **Run workflow** button (right side)
4. Click the green **Run workflow** button
5. Wait 2-3 minutes
6. Check if it succeeded (green checkmark) or failed (red X)

If it fails:
- Click on the failed run
- Click on "update-dashboard" job
- Expand the failed step to see error message
- Common issues: Invalid API credentials, missing secrets

If it succeeds:
- Refresh your GitHub Pages URL
- You should see your dashboard!

---

## Part 3: Add to iPhone Homescreen

1. Open your dashboard URL in Safari: `https://YOUR_USERNAME.github.io/fitness-dashboard`
2. Tap the **Share** button (box with arrow)
3. Scroll down and tap **"Add to Home Screen"**
4. Name it: "Training Dashboard" (or whatever you like)
5. Tap **Add**

**Result:** Icon appears on your homescreen like a native app! 📱

---

## Part 4: Customize Schedule

Want to change when the dashboard updates? Edit `.github/workflows/daily-run.yml`:

```yaml
schedule:
  - cron: '0 11 * * *'  # 6 AM EST (11 AM UTC)
```

**Examples:**
- `'0 10 * * *'` = 5 AM EST
- `'0 12 * * *'` = 7 AM EST
- `'0 13 * * 1-5'` = 8 AM EST, Monday-Friday only

Use https://crontab.guru to generate cron schedules.

After changing, commit and push:
```bash
git add .github/workflows/daily-run.yml
git commit -m "Update schedule"
git push
```

---

## Part 5: Monitor & Maintain

### View Dashboard Updates

- **Live URL:** `https://YOUR_USERNAME.github.io/fitness-dashboard`
- **Update history:** Check the Actions tab to see past runs
- **Email notifications:** GitHub emails you when workflows fail

### When Oura Subscription Ends

**No action needed!** The dashboard automatically:
1. Tries API first
2. Falls back to data export
3. Uses cached data if both fail

To provide manual exports after subscription ends:
1. Download from Oura: https://cloud.ouraring.com/user/settings/personal-info
2. Save to: `.cache/oura_export_YYYYMMDD.json`
3. Commit and push (or let automated export handle it)

### Updating the Dashboard Code

If you want to modify the dashboard:

1. Make changes locally
2. Test: `python generate_dashboard.py`
3. Commit and push:
   ```bash
   git add .
   git commit -m "Updated dashboard layout"
   git push
   ```
4. Next scheduled run (or manual trigger) will use new code

---

## Troubleshooting

### Dashboard shows "Oura data unavailable"
- Check that `OURA_API_TOKEN` secret is set correctly
- Verify your Oura subscription is active
- Try manual workflow trigger to see detailed error

### Dashboard shows old data
- Check Actions tab - is the workflow running?
- Verify schedule is correct (remember timezone)
- Try manual trigger to force update

### Workflow fails with "Authentication error"
- Double-check all secrets are entered correctly (no extra spaces)
- For Strava: Make sure refresh token is valid
- For Oura: Token may have expired, generate new one

### Dashboard not updating on GitHub Pages
- Check that gh-pages branch exists
- Verify GitHub Pages is enabled in settings
- Wait 2-3 minutes after workflow completes
- Hard refresh browser (Cmd+Shift+R on Mac)

### "Permission denied" errors in workflow
- Check repository permissions: Settings → Actions → General
- Verify "Workflow permissions" is set to "Read and write permissions"

---

## Privacy & Security

### Your Dashboard is Public by Default

Anyone with the URL can view it. To make it private:

**Option 1: Upgrade to GitHub Pro (Recommended)**
- Change repository to Private
- GitHub Pages will also be private
- Only you can access it

**Option 2: Use Alternative Hosting**
- AWS S3 with authentication
- Netlify with password protection
- Self-host on private server

### Keeping Credentials Safe

✅ **DO:**
- Store all credentials in GitHub Secrets
- Use `.gitignore` to exclude `.env` file
- Generate new API tokens if exposed

❌ **DON'T:**
- Commit `.env` file to Git
- Share your repository URL publicly (contains health data)
- Use same passwords across services

---

## Next Steps

Now that your dashboard is deployed:

1. ✅ Check it daily to track progress
2. ✅ Adjust training based on recommendations
3. ✅ Monitor trends over weeks
4. ✅ Celebrate hitting your lean mass goals! 💪

**Questions?** Check the main README.md or open a GitHub issue.

---

**Enjoy your automated Training Dashboard!** 🎯
