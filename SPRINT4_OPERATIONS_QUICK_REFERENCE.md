# Sprint 4 Operations Quick Reference

**Last Updated**: 2026-02-19
**Status**: 🟢 LIVE on FastComet

---

## 🚀 Quick Commands

### SSH Access
```bash
ssh chargeap@d11475.sgp1.stableserver.net
```

### View Logs (Real-time)
```bash
tail -f ~/menu-api.log

# Filter OCR logs only
tail -f ~/menu-api.log | grep -E "OCR|Tier|fallback|metrics"
```

### Check Service Status
```bash
ps aux | grep uvicorn
```

### Restart Service
```bash
pkill -f "python -m uvicorn"
sleep 2
cd ~/menu-knowledge/app/backend
source venv/bin/activate
nohup python -m uvicorn main:app --host 127.0.0.1 --port 8001 --workers 2 > ~/menu-api.log 2>&1 &
```

---

## 📊 Health Checks

### Health Endpoint
```bash
curl http://localhost:8001/health | jq .
# Expected: {"status": "ok", "service": "Menu Knowledge Engine", ...}
```

### Metrics Endpoint
```bash
curl http://localhost:8001/api/v1/admin/ocr/metrics | jq .
# Shows: tier_1_count, tier_2_count, success_rates, processing_time
```

### Admin Stats
```bash
curl http://localhost:8001/api/v1/admin/stats | jq .
# Shows: canonical_count, modifier_count, db_hit_rate_7d, ai_cost_7d
```

---

## ⚠️ Troubleshooting

### Service Won't Start
```bash
# 1. Check if port 8001 is in use
lsof -i :8001

# 2. Verify Python environment
cd ~/menu-knowledge/app/backend
source venv/bin/activate
python --version

# 3. Test imports
python -c "from services.ocr_orchestrator import ocr_orchestrator; print('OK')"

# 4. Check logs
tail -50 ~/menu-api.log
```

### High Processing Time (> 5s)
```bash
# Check if Tier 1 (GPT) is responding
curl -s http://localhost:8001/api/v1/admin/ocr/metrics | jq '.tier_1_count'

# If Tier 1 is slow, check if Tier 2 fallback is working
curl -s http://localhost:8001/api/v1/admin/ocr/metrics | jq '.tier_2_count'

# Monitor real-time: grep for "fallback_triggered" in logs
tail -f ~/menu-api.log | grep fallback
```

### Redis Connection Failed
```bash
# This is normal - service works without Redis (cache disabled)
# To enable Redis: check if Redis service is running
redis-cli ping

# If needed, restart Redis or continue without caching
```

---

## 📈 Monitoring Dashboard URLs

After deployment, these endpoints are available:

```
Base URL: https://menu.chargeapp.net (or http://localhost:8001 on FastComet)

Health Check:
  GET /health

OCR Metrics:
  GET /api/v1/admin/ocr/metrics

Admin Stats:
  GET /api/v1/admin/stats

B2B Menu Upload:
  POST /api/v1/b2b/restaurants/{restaurant_id}/menus/upload-images
```

---

## 🔍 Key Metrics to Monitor

### Critical (Alert if not met)
- **Service Uptime**: Should be 99%+
- **Error Rate**: Should be < 1%
- **Health Check**: Should return 200 OK

### Important (Track for optimization)
- **Tier 1 Success Rate**: Target 85%+
- **Tier 2 Fallback Rate**: Target 10-15% (handwritten images)
- **Avg Processing Time**: Target < 4 seconds
- **Price Error Rate**: Target < 5%

### Nice to Have (For cost analysis)
- **Cache Hit Rate**: Target > 30%
- **AI Cost per Scan**: Target < 50₩
- **Handwriting Detection**: Track percentage

---

## 🎯 Daily Checklist

### Morning (Start of Day)
- [ ] Check health endpoint responds 200 OK
- [ ] Verify no critical errors in logs from overnight
- [ ] Note any Tier 2 fallback spikes

### During Business Hours
- [ ] Monitor metrics endpoint for data collection
- [ ] Check for any unusual error patterns
- [ ] Track Tier 1 vs Tier 2 ratio

### Evening (End of Day)
- [ ] Export metrics for daily report
- [ ] Check if any scaling issues occurred
- [ ] Verify cache is working (non-zero cache_hit_rate_7d)

### Weekly
- [ ] Review AI cost trends
- [ ] Analyze image preprocessing effectiveness
- [ ] Check database growth
- [ ] Validate 7-day KPIs

---

## 🚨 Alert Thresholds

```
CRITICAL (Immediate Action):
  - Error Rate > 2%
  - Health Check fails
  - Tier 1 Success Rate < 70%

WARNING (Within 1 hour):
  - Avg Processing Time > 5s
  - Tier 2 Fallback Rate > 20%
  - Price Error Rate > 10%

INFO (Daily Report):
  - Cache hit rate changes
  - Daily AI cost accumulation
  - Handwriting detection patterns
```

---

## 📋 Common Tasks

### Test Tier 1 → Tier 2 Fallback
```bash
# Upload clear menu image (should use Tier 1/GPT)
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/test/menus/upload-images \
  -F "files=@clear_menu.jpg"

# Expected: provider = "gpt_vision", fallback_triggered = false

# Upload handwritten menu image (should fallback to Tier 2/CLOVA)
curl -X POST http://localhost:8001/api/v1/b2b/restaurants/test/menus/upload-images \
  -F "files=@handwritten_menu.jpg"

# Expected: provider = "clova", fallback_triggered = true
```

### Check Cache Hit Ratio
```bash
# Get current metrics
curl http://localhost:8001/api/v1/admin/stats | jq '.db_hit_rate_7d'

# Should show 0.0-1.0 (0% to 100%)
# Target: > 0.30 (30%+)
```

### Monitor Cost Accumulation
```bash
# Check 7-day AI cost
curl http://localhost:8001/api/v1/admin/stats | jq '.ai_cost_7d'

# Expected: reasonable amount for number of scans
# Calculate: (scans_7d × tier_2_fallback_rate) × $0.00009 × 1300
```

---

## 🔧 Configuration Files

### Environment Variables (.env)
```bash
Location: ~/menu-knowledge/app/backend/.env
Critical:
  - OPENAI_API_KEY (for Tier 1)
  - DATABASE_URL (for canonical menus)
  - REDIS_HOST (for caching)
```

### Service Configuration
```bash
Service Name: menu-api
User: chargeap
Port: 8001 (internal), exposed via Nginx
Workers: 2 (for concurrency)
```

---

## 📞 Support Contacts

### If Service Fails
1. Check logs: `tail -50 ~/menu-api.log`
2. Restart: See "Restart Service" above
3. Contact: FastComet support@ncloud.com (for server issues)

### If API Endpoints Return Errors
1. Verify service is running: `ps aux | grep uvicorn`
2. Check health: `curl http://localhost:8001/health`
3. Review error message in response JSON

### If Tier 1 (GPT) Fails
1. Verify OPENAI_API_KEY is set: `grep OPENAI ~/.env`
2. Check GPT API status (may be rate limited)
3. Service will automatically fallback to Tier 2 (CLOVA)

---

**Quick Status**: 🟢 All systems operational as of 2026-02-19
**Last Restart**: 2026-02-19 00:50 UTC
**Uptime**: Stable
**Next Review**: 2026-02-26 (Weekly)
