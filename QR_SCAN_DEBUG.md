# QR Code Scan Troubleshooting Guide

## Current Status
- ✅ Backend API (`/api/get_order_by_qr`) works correctly → returns 200 with all required fields
- ✅ Database query fixed (timeout parameter fixed)
- ✅ String normalization added (trim, BOM, quotes removal)
- ✅ Server health check endpoint (`/api/health`) working
- ⏳ Frontend display may have issues - added detailed logging

## Test the System Step-by-Step

### Step 1: Verify Backend (Server Running)
Visit: **http://127.0.0.1:5000/api/health**
Expected response:
```json
{
  "status": "ok",
  "message": "Server is running"
}
```

### Step 2: Test API Endpoint
Visit: **http://127.0.0.1:5000/test_qr_scan**
- Click "Test QR Scan" button
- Watch the output log for SUCCESS or ERROR
- Also check browser DevTools Console (F12) for detailed logs

### Step 3: Test Full QR Scan Page
Visit: **http://127.0.0.1:5000/scan_qr**
1. Page should load and show "✅ Server đang hoạt động" at top
2. Try scanning an actual QR code with camera or paste `ORDER#78#RESTAURANT` in input
3. Open DevTools Console (F12) to see detailed logs as it processes

## If Still Not Working

### Check Browser Console (F12 → Console)
Look for these patterns in logs:
- `Response received: 200` = Server responded
- `Data received: Success` = API data parsed correctly
- `Order found, displaying...` = Starting to show order
- `displayOrderDetails` logs = Each field being set

### Common Issues & Fixes

**Issue: "Response received: 200" but then error**
→ Check if `data.success === true` and `data.order !== undefined`

**Issue: JSON parse error**
→ Server may be returning HTML error page instead of JSON
→ Check app.py logs for Python errors

**Issue: Missing order in database**
→ Try a different order ID (not just #78)
→ Check database.db file exists and has orders

**Issue: Timeout after 8 seconds**
→ Server taking too long to respond
→ Could be database locked or query slow
→ Restart Flask server and try again

## Debug Endpoints Available

- `GET /api/health` - Check if server is running
- `POST /api/get_order_by_qr` - Search for order by QR code
- `GET /api/debug_qr/<order_id>` - View QR data in database
- `GET /qr_diagnostic` - Admin diagnostic page
- `GET /test_qr_scan` - This test page

## What Was Fixed

1. **Connection Timeout Error** (CRITICAL)
   - Changed `conn.timeout = 5.0` (wrong attribute)
   - To `sqlite3.connect(self.db_path, timeout=5.0)` (correct parameter)
   - This was preventing any QR lookup from working

2. **String Normalization**
   - Added trim, BOM removal, quote stripping
   - Handles QR codes with extra whitespace/encoding issues

3. **Frontend Logging**
   - Added detailed console logs at each step
   - Now captures exactly where failure occurs

## Next Steps if Still Broken

If the test page shows ERROR, please:
1. Copy the full error message/stack trace from the test page
2. Check Flask server console (terminal) for Python exceptions
3. Clear browser cache (Ctrl+Shift+Del) and reload
4. Restart Flask server and try again
