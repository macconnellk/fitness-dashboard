import os
import pandas as pd
from datetime import datetime

def fetch_lean_mass_data():
    """Fetch lean mass data from published CSV"""
    csv_url = os.environ.get('GOOGLE_SHEET_CSV_URL')
    
    if not csv_url:
        print("⚠️  No Google Sheet CSV URL configured")
        return None
    
    try:
        # Read CSV directly from URL
        df = pd.read_csv(csv_url)
        
        # Get most recent row with data
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            df = df.sort_values('Date', ascending=False)
        
        latest = df.iloc[0]
        
        data = {
            'lean_mass_kg': latest.get('Lean Mass (kg)', None),
            'body_weight_kg': latest.get('Weight (kg)', None),
            'body_fat_pct': latest.get('Body Fat %', None),
            'date': latest.get('Date', datetime.now().isoformat())
        }
        
        print(f"✅ Fetched lean mass data: {data['lean_mass_kg']} kg")
        return data
        
    except Exception as e:
        print(f"❌ Error fetching Google Sheet: {e}")
        return None

if __name__ == '__main__':
    data = fetch_lean_mass_data()
    print(f"Lean mass data: {data}")
```

4. **Commit message:** "Switch to CSV for Google Sheets"
5. **Click "Commit changes"**

---

### **Step 4: Update Requirements (Optional)**

If you want, you can remove the Google Sheets API dependencies since we don't need them:

1. **Click on `requirements.txt`**
2. **Click Edit**
3. **Remove these lines:**
```
   google-auth>=2.23.0
   google-auth-oauthlib>=1.1.0
   google-auth-httplib2>=0.1.1
   google-api-python-client>=2.100.0
