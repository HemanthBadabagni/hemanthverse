# How to Verify Cloud Storage is Working

## Quick Verification Steps

### 1. Check Storage Status in Admin Page
1. Go to your admin dashboard: `https://your-app.streamlit.app?invite=YOUR_INVITE_ID&admin=true`
2. Look for the **"💾 Storage Status"** section at the top
3. You should see:
   - ✅ Cloud Storage: **Enabled**
   - ✅ GitHub Token: **Configured**
   - ✅ Gist ID: **Set** (or "Will be created" on first use)

### 2. Run the Storage Test
1. In the admin page, click **"🧪 Test Cloud Storage"** button
2. Wait for the test to complete
3. You should see:
   - ✅ **Cloud Storage Test: PASSED**
   - ✅ Save test: Passed
   - ✅ Load test: Passed

### 3. Verify Data Persistence
**Test 1: Create an Invitation**
1. Create a new invitation
2. Check the app logs (Streamlit Cloud → Manage app → Logs)
3. Look for: `"Saved invitation {invite_id} to cloud storage"`

**Test 2: Restart the App**
1. Go to Streamlit Cloud → Manage app → Restart app
2. Wait for the app to restart
3. Open your invitation link again
4. ✅ **If it works**: Cloud storage is working!
5. ❌ **If it says "Invitation not found"**: Cloud storage is not working

**Test 3: Check GitHub Gist**
1. Go to https://gist.github.com
2. You should see a private Gist named "Happenin Invitations Storage"
3. Click on it to see your invitations data
4. ✅ **If you see your invitation data**: Cloud storage is working!

## What to Look For

### ✅ Success Indicators:
- Storage Status shows all green checkmarks
- Test button shows "PASSED"
- Invitations persist after app restart
- You can see data in GitHub Gist
- App logs show "Saved to cloud storage" messages

### ❌ Failure Indicators:
- Storage Status shows red X marks
- Test button shows "FAILED"
- Invitations disappear after app restart
- App logs show "Cloud storage failed" warnings
- Error messages in the admin page

## Troubleshooting

### "Cloud Storage: Disabled"
- **Fix**: Add `USE_CLOUD_STORAGE = "true"` to Streamlit secrets
- **Restart**: Restart your app after adding secrets

### "GitHub Token: Not Set"
- **Fix**: Add `GITHUB_TOKEN = "your_token"` to Streamlit secrets
- **Verify**: Make sure token has `gist` scope

### "Test Failed: Failed to access Gist"
- **Check**: Verify Gist ID is correct in secrets
- **Fix**: Remove `INVITATIONS_GIST_ID` from secrets and let app create a new one

### "Invitation not found" after restart
- **Check**: Storage Status section in admin page
- **Verify**: Run the storage test
- **Fix**: Make sure all secrets are set correctly

## Monitoring

### Check App Logs
1. Go to Streamlit Cloud → Manage app → Logs
2. Look for these messages:
   - `"Saved invitation {id} to cloud storage"` ✅
   - `"Cloud storage failed, falling back to local storage"` ⚠️
   - `"Cloud storage load failed"` ❌

### Check GitHub Gist
1. Go to https://gist.github.com
2. Find your "Happenin Invitations Storage" Gist
3. Check if it has recent updates
4. Verify your invitation data is there

## Expected Behavior

### When Cloud Storage is Working:
1. ✅ Create invitation → Saved to cloud
2. ✅ Restart app → Invitation still accessible
3. ✅ Add RSVP → Saved to cloud
4. ✅ Restart app → RSVPs still there
5. ✅ All data persists across restarts

### When Cloud Storage is NOT Working:
1. ❌ Create invitation → Saved locally only
2. ❌ Restart app → Invitation lost
3. ❌ "Invitation not found" error
4. ❌ Data disappears after sleep/restart

## Quick Test Checklist

- [ ] Storage Status shows "Enabled"
- [ ] GitHub Token shows "Configured"
- [ ] Test button shows "PASSED"
- [ ] Created invitation persists after restart
- [ ] Can see data in GitHub Gist
- [ ] App logs show "cloud storage" messages

If all checkboxes are ✅, cloud storage is working correctly!

