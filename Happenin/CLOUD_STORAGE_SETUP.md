# Cloud Storage Setup Guide

## Problem
Streamlit Cloud uses an ephemeral filesystem - when the app restarts or goes to sleep, all local files are lost. This means invitations and RSVPs stored in the `invitations/` folder are deleted.

## Solution
The app now supports cloud storage using **GitHub Gists** (free, no setup required) or **Supabase** (PostgreSQL database).

## Quick Setup: GitHub Gists (Recommended)

### Step 1: Create a GitHub Personal Access Token
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Click "Generate new token (classic)"
3. Name it: `Happenin Storage`
4. Select scope: `gist` (check the box)
5. Click "Generate token"
6. **Copy the token** (you won't see it again!)

### Step 2: Configure Streamlit Secrets
1. Go to your Streamlit Cloud app: https://share.streamlit.io
2. Click on your app → Settings → Secrets
3. Add the following secrets:

```toml
[secrets]
USE_CLOUD_STORAGE = "true"
GITHUB_TOKEN = "your_github_token_here"
```

**Note:** The `INVITATIONS_GIST_ID` will be created automatically on first use. After the first invitation is created, check the app logs to see the Gist ID, then add it to secrets:

```toml
INVITATIONS_GIST_ID = "gist_id_from_logs"
```

### Step 3: Restart Your App
1. Go to your Streamlit Cloud app
2. Click "Manage app" → "Restart app"
3. Your app will now use cloud storage!

## Alternative: Supabase Setup (Optional)

If you prefer a database solution:

### Step 1: Create Supabase Account
1. Go to https://supabase.com
2. Sign up for free account
3. Create a new project

### Step 2: Create Table
Run this SQL in Supabase SQL Editor:

```sql
CREATE TABLE invitations (
  id TEXT PRIMARY KEY,
  data JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Step 3: Get API Credentials
1. Go to Project Settings → API
2. Copy your:
   - Project URL (SUPABASE_URL)
   - anon/public key (SUPABASE_KEY)

### Step 4: Configure Streamlit Secrets
Add to Streamlit Cloud secrets:

```toml
[secrets]
USE_CLOUD_STORAGE = "true"
SUPABASE_URL = "your_supabase_url"
SUPABASE_KEY = "your_supabase_key"
```

## How It Works

- **Cloud Storage Enabled**: Data is saved to GitHub Gists or Supabase
- **Cloud Storage Disabled**: Data is saved locally (works for development, but lost on Streamlit Cloud restarts)
- **Automatic Fallback**: If cloud storage fails, the app falls back to local storage

## Troubleshooting

### "Invitation not found" after restart
- Make sure `USE_CLOUD_STORAGE = "true"` is set in secrets
- Check that `GITHUB_TOKEN` is valid
- Verify `INVITATIONS_GIST_ID` is set (check app logs for the ID)

### App still losing data
- Check Streamlit Cloud logs for errors
- Verify secrets are correctly formatted (no quotes around values in TOML)
- Make sure the GitHub token has `gist` scope

### First invitation creates Gist
- This is normal! The app will create a Gist on first use
- Check the app logs to get the Gist ID
- Add `INVITATIONS_GIST_ID` to secrets for faster access

## Benefits

✅ **Persistent Storage**: Data survives app restarts  
✅ **Free**: GitHub Gists are free and unlimited  
✅ **Automatic**: Works seamlessly with existing code  
✅ **Backward Compatible**: Falls back to local storage if cloud is unavailable

