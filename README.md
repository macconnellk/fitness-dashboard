# 🏋️ Training Dashboard

Automated daily fitness dashboard that pulls data from Oura Ring, Strava, and Google Sheets to provide personalized training recommendations.

## Features

- **Daily Training Recommendation**: Should you train hard or take it easy?
- **Recovery Status**: Sleep, HRV, and resting heart rate analysis
- **Training Progress**: Track runs and lifts against weekly targets
- **Lean Mass Tracking**: Monitor body composition progress
- **7-Day Trends**: Visual charts for weight, HRV, and sleep
- **Mobile-Optimized**: Add to iPhone homescreen for app-like experience

## Dashboard Preview

```
🎯 TODAY'S CALL: TRAIN AS PLANNED
Recovery: 76/100 (Good) | Trend: Stable ➡️

😴 RECOVERY              🏃 THIS WEEK
Sleep: 7.2h              Lifts: 2/2 ✓
HRV: 68 (↑)              Runs: 1/3 (35/60min)
RHR: 52 (→)              → Need 2 runs (25min)
Status: Good

📈 7-DAY TRENDS
[Charts: weight, HRV, sleep]

💪 LEAN MASS PROGRESS
Current: 168.7 lbs @ 19.4% BF
Phase: Cut to 17% (Week 1/12)
```

## Quick Start

### Option A: Full Automated Setup (Recommended)

Follow the complete **[DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)** for step-by-step instructions to deploy to GitHub Pages with daily automation.

### Option B: Local Testing Only

If you just want to test locally first:

**1. Install Dependencies**
```bash
pip install -r requirements.txt
```

**2. Configure Environment**
```bash
# Copy template
cp .env.example .env

# Edit .env with your API credentials
nano .env  # or your preferred editor
```

**3. Set Up API Access

#### Oura Ring
1. Go to https://cloud.ouraring.com/personal-access-tokens
2. Create a Personal Access Token
3. Add to `.env` as `OURA_API_TOKEN`

#### Strava
1. Go to https://www.strava.com/settings/api
2. Create an application
3. Get your Client ID and Client Secret
4. Follow OAuth flow to get Refresh Token (guide below)

#### Google Sheets
1. Go to https://console.cloud.google.com
2. Create a new project
3. Enable Google Sheets API
4. Create credentials (OAuth 2.0 Client ID)
5. Download credentials as `credentials.json`

### 5. Test Configuration

```bash
python config.py
```

Should output: `✓ Configuration validated successfully`

### 6. Run Dashboard Locally

```bash
python generate_dashboard.py
```

Opens dashboard in `output/index.html`

## Deployment to GitHub Pages

### 1. Create GitHub Repository

```bash
git init
git add .
git commit -m "Initial commit"
git branch -M main
git remote add origin https://github.com/yourusername/fitness-dashboard.git
git push -u origin main
```

### 2. Add Secrets to GitHub

Go to: Repository → Settings → Secrets and variables → Actions

Add each secret from your `.env` file:
- `OURA_API_TOKEN`
- `STRAVA_CLIENT_ID`
- `STRAVA_CLIENT_SECRET`
- `STRAVA_REFRESH_TOKEN`
- `GOOGLE_SHEET_ID`
- `GOOGLE_CREDENTIALS` (paste entire contents of credentials.json)
- All other secrets from `.env`

### 3. Enable GitHub Pages

1. Repository → Settings → Pages
2. Source: Deploy from a branch
3. Branch: `gh-pages` / `/ (root)`
4. Save

### 4. Dashboard Goes Live!

- URL: `https://yourusername.github.io/fitness-dashboard`
- Updates daily at 6 AM (configurable in workflow)
- Add to iPhone homescreen

## Adding to iPhone Homescreen

1. Open dashboard URL in Safari
2. Tap Share button (box with arrow)
3. Scroll down → "Add to Home Screen"
4. Name it "Training Dashboard"
5. Tap "Add"

Now it opens like a native app! 📱

## Project Structure

```
fitness-dashboard/
├── config.py                   # Configuration management
├── oura_manager.py            # Oura data (API + export fallback)
├── fetch_strava.py            # Strava activities
├── fetch_sheets.py            # Google Sheets lean mass data
├── calculate_baselines.py     # HRV/RHR baseline calculation
├── scoring.py                 # Custom sleep/readiness scoring
├── analyzer.py                # Training recommendations
├── generate_dashboard.py      # HTML generation
├── dashboard_template.html    # Dashboard layout
├── requirements.txt           # Python dependencies
├── .env                       # Your secrets (not committed!)
├── .env.example              # Template for .env
└── .github/
    └── workflows/
        └── daily-run.yml      # Automated daily updates
```

## How It Works

### Daily Automation (GitHub Actions)

1. **6:00 AM EST**: GitHub Actions triggers
2. **Data Collection**: 
   - Oura: Sleep, HRV, RHR (API or export)
   - Strava: Recent activities
   - Google Sheets: Lean mass tracking
3. **Analysis**:
   - Calculate custom sleep/readiness scores
   - Determine training recommendation
   - Generate trends
4. **Dashboard Update**:
   - Generate HTML from template
   - Push to `gh-pages` branch
   - Live at GitHub Pages URL

### Workflow Features

- ✅ **Automatic fallback**: API → Export → Cache
- ✅ **Error handling**: Graceful degradation if data unavailable  
- ✅ **Email notifications**: GitHub emails you if workflow fails
- ✅ **Manual trigger**: Run anytime from Actions tab
- ✅ **Secure**: All credentials stored in GitHub Secrets

### Daily Automation (GitHub Actions)

1. **6:00 AM**: GitHub Actions triggers
2. **Data Collection**: 
   - Oura: Sleep, HRV, RHR (API or export)
   - Strava: Recent activities
   - Google Sheets: Lean mass tracking
3. **Analysis**:
   - Calculate custom sleep/readiness scores
   - Determine training recommendation
   - Generate trends
4. **Dashboard Update**:
   - Generate HTML from template
   - Push to `gh-pages` branch
   - Live at GitHub Pages URL

### Scoring System

**Sleep Score (0-100)**
- Duration: 40 points
- Efficiency: 30 points
- Deep Sleep: 15 points
- REM Sleep: 15 points

**Readiness Score (0-100)**
- HRV Trend: 35 points
- Resting HR: 25 points
- Sleep Score: 25 points
- Training Load: 15 points

**Recovery Status**
- 85-100: ✅ GREEN - Train as planned
- 70-84: 🟢 YELLOW - Proceed with awareness
- 55-69: 🟡 ORANGE - Modify workout
- <55: 🔴 RED - Back off

## Troubleshooting

### "Oura data unavailable"
- Check your API token is valid
- If subscription ended, ensure export automation is working
- Check cache: Should have data from last 3 days

### "GitHub Actions failing"
- Check secrets are configured correctly
- Review Actions logs for specific errors
- Test locally first: `python generate_dashboard.py`

### "Google Sheets not loading"
- Verify `GOOGLE_SHEET_ID` is correct
- Check credentials.json is valid
- Ensure sheet is published or accessible

## Customization

### Change Training Targets
Edit in `.env`:
```
WEEKLY_LIFT_TARGET=2
WEEKLY_RUN_TARGET=3
WEEKLY_RUN_MINUTES_TARGET=60
```

### Adjust Scoring Weights
Edit `config.py` → `SLEEP_SCORE_WEIGHTS` and `READINESS_SCORE_WEIGHTS`

### Change Update Time
Edit `.github/workflows/daily-run.yml`:
```yaml
schedule:
  - cron: '0 11 * * *'  # 6 AM EST (11 AM UTC)
```

## Privacy & Security

- ✅ All API keys stored in GitHub Secrets (encrypted)
- ✅ Dashboard is static HTML (no backend to hack)
- ⚠️ Dashboard is public by default (contains your health data)

### To Make Dashboard Private:
1. Upgrade to GitHub Pro
2. Repository → Settings → Change visibility to Private
3. GitHub Pages will be private to you

Or deploy to private hosting (AWS S3, Netlify, etc.)

## License

MIT License - Use freely!

## Support

Questions? Issues? Open a GitHub issue or email [your email]

---

Built with ❤️ for evidence-based training
