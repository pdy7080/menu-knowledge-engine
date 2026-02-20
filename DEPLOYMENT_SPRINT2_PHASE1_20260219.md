# Sprint 2 Phase 1: Database Migration Deployment Guide

**Date:** 2026-02-19
**Migration:** Sprint 2 Phase 1 - Multi-Image and Enriched Content Schema
**Risk Level:** 🟢 LOW (all columns NULLABLE, rollback ready)
**Estimated Time:** 15 minutes execution + 30 minutes monitoring

---

## Pre-Deployment Checklist

### 1. Backup Verification
- [ ] **CRITICAL:** Production database backup created
- [ ] Backup file verified (non-zero size)
- [ ] Backup location: `~/backups/menu_knowledge/`
- [ ] Backup filename: `backup_pre_sprint2_20260219.sql`

**Backup Command:**
```bash
ssh chargeap@d11475.sgp1.stableserver.net
cd ~

# Create backup directory if not exists
mkdir -p ~/backups/menu_knowledge

# Execute backup
PGPASSWORD='eromlab!1228' pg_dump -h localhost \
  -U chargeap_dcclab2022 chargeap_menu_knowledge \
  > ~/backups/menu_knowledge/backup_pre_sprint2_20260219.sql

# Verify backup
ls -lh ~/backups/menu_knowledge/backup_pre_sprint2_20260219.sql
# Expected: File size > 50 KB (current DB has 214 records)
```

### 2. Migration Files Ready
- [x] `app/backend/migrations/sprint2_phase1_images.sql` (verified)
- [x] `app/backend/migrations/rollback_sprint2_phase1.sql` (verified)
- [ ] Files uploaded to server

### 3. Team Notification
- [ ] All teammates notified of deployment window
- [ ] backend-dev on standby
- [ ] qa-devops monitoring ready

---

## Deployment Window

**Recommended:** Korea Time 02:00-04:00 (UTC+9)
**Alternative:** Korea Time 10:00-12:00 (if business requires)

**Selected Window:** _________________ (fill in before execution)

---

## Deployment Execution Steps

### Step 1: Upload Migration Files (5 minutes)

```bash
# From local machine (PowerShell/cmd)
cd C:\project\menu

# Upload migration script
scp app/backend/migrations/sprint2_phase1_images.sql \
  chargeap@d11475.sgp1.stableserver.net:~/menu-knowledge/migrations/

# Upload rollback script
scp app/backend/migrations/rollback_sprint2_phase1.sql \
  chargeap@d11475.sgp1.stableserver.net:~/menu-knowledge/migrations/
```

**Verification:**
```bash
ssh chargeap@d11475.sgp1.stableserver.net
ls -lh ~/menu-knowledge/migrations/sprint2_*.sql
# Expected: 2 files
```

### Step 2: Pre-Migration Verification (2 minutes)

```bash
ssh chargeap@d11475.sgp1.stableserver.net

# Check current schema (should NOT have new columns yet)
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT column_name FROM information_schema.columns
      WHERE table_name='canonical_menus'
      AND column_name IN ('primary_image', 'images', 'content_completeness');"

# Expected: 0 rows (columns don't exist yet)

# Check current row count
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT COUNT(*) FROM canonical_menus;"

# Expected: 214 rows (or current production count)
```

### Step 3: Execute Migration (5 minutes)

```bash
# Navigate to migrations directory
cd ~/menu-knowledge/migrations

# Execute migration
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -f sprint2_phase1_images.sql

# Monitor output for:
# - "Migration Complete" message
# - Total menus count
# - Migrated images count
# - New columns added: 11
# - New indexes added: 3
```

**Expected Output:**
```
NOTICE:  Migration Complete:
NOTICE:    - Total menus: 214
NOTICE:    - Migrated images: 80
NOTICE:    - New columns added: 11
NOTICE:    - New indexes added: 3
COMMIT
```

### Step 4: Post-Migration Verification (3 minutes)

```bash
# 1. Verify new columns exist
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT column_name, data_type FROM information_schema.columns
      WHERE table_name='canonical_menus'
      AND column_name IN (
        'primary_image', 'images', 'description_long_ko', 'description_long_en',
        'regional_variants', 'preparation_steps', 'nutrition_detail',
        'flavor_profile', 'visitor_tips', 'similar_dishes', 'content_completeness'
      ) ORDER BY column_name;"

# Expected: 11 rows

# 2. Verify indexes created
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT indexname FROM pg_indexes
      WHERE tablename='canonical_menus'
      AND (indexname LIKE '%primary_image%'
           OR indexname LIKE '%images%'
           OR indexname LIKE '%content_completeness%');"

# Expected: 5 rows (idx_cm_primary_image_gin, idx_cm_images_gin,
#                    idx_cm_regional_variants_gin, idx_cm_content_completeness,
#                    idx_cm_content_complete)

# 3. Verify trigger exists
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT trigger_name FROM information_schema.triggers
      WHERE event_object_table='canonical_menus'
      AND trigger_name='trg_update_completeness';"

# Expected: 1 row

# 4. Verify data migration (image_url → primary_image)
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT COUNT(*) AS migrated_images
      FROM canonical_menus
      WHERE primary_image IS NOT NULL;"

# Expected: 80 rows (matches current image_url count)

# 5. Verify content_completeness calculation
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT id, name_ko, content_completeness
      FROM canonical_menus
      WHERE primary_image IS NOT NULL
      ORDER BY content_completeness DESC
      LIMIT 5;"

# Expected: Rows with completeness 10.00% (only primary_image filled)
```

### Step 5: Test API Endpoints (5 minutes)

```bash
# Test 1: Basic endpoint (existing)
curl "https://menu-knowledge.chargeapp.net/api/v1/canonical-menus?limit=1" | jq

# Expected: JSON response with existing fields + backward compatible structure

# Test 2: Enriched endpoint (new parameter)
curl "https://menu-knowledge.chargeapp.net/api/v1/canonical-menus?include_enriched=true&limit=1" | jq

# Expected: JSON response with new fields (primary_image, etc.)

# Test 3: Detail endpoint (new)
# Get menu_id from test 1, then:
curl "https://menu-knowledge.chargeapp.net/api/v1/canonical-menus/{menu_id}" | jq

# Expected: Full enriched content (even if mostly null now)

# Test 4: Images endpoint (new)
curl "https://menu-knowledge.chargeapp.net/api/v1/canonical-menus/{menu_id}/images" | jq

# Expected: Image data only
```

---

## Rollback Procedure (If Needed)

**Trigger Conditions:**
- Migration fails mid-execution
- Post-migration verification fails
- API endpoints return errors
- Performance degradation detected

**Rollback Steps:**

```bash
# 1. Execute rollback script
cd ~/menu-knowledge/migrations
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -f rollback_sprint2_phase1.sql

# 2. Verify rollback success
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT column_name FROM information_schema.columns
      WHERE table_name='canonical_menus'
      AND column_name IN ('primary_image', 'images', 'content_completeness');"

# Expected: 0 rows (columns removed)

# 3. Restart API (if needed)
pm2 restart menu-knowledge-api

# 4. Test basic endpoint
curl "https://menu-knowledge.chargeapp.net/api/v1/canonical-menus?limit=1"

# Expected: Original structure (no new fields)
```

**Alternative: Restore from Backup (Last Resort)**

```bash
# 1. Stop API
pm2 stop menu-knowledge-api

# 2. Drop and recreate database
PGPASSWORD='eromlab!1228' psql -h localhost -U chargeap_dcclab2022 -d postgres \
  -c "DROP DATABASE chargeap_menu_knowledge;"

PGPASSWORD='eromlab!1228' psql -h localhost -U chargeap_dcclab2022 -d postgres \
  -c "CREATE DATABASE chargeap_menu_knowledge OWNER chargeap_dcclab2022;"

# 3. Restore backup
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  < ~/backups/menu_knowledge/backup_pre_sprint2_20260219.sql

# 4. Restart API
pm2 restart menu-knowledge-api
```

---

## Post-Deployment Monitoring (30 minutes)

### Immediate Checks (0-5 minutes)
- [ ] API responds with 200 status
- [ ] No error logs in PM2 (`pm2 logs menu-knowledge-api --lines 50`)
- [ ] Database connection stable

### Short-term Monitoring (5-30 minutes)
- [ ] API response time < 500ms (use curl -w)
- [ ] No database errors in PostgreSQL logs
- [ ] Memory usage stable (PM2 dashboard)

**Monitoring Commands:**

```bash
# API logs
pm2 logs menu-knowledge-api --lines 50

# API status
pm2 status

# Response time test
curl -w "\nTime: %{time_total}s\n" -o /dev/null -s \
  "https://menu-knowledge.chargeapp.net/api/v1/canonical-menus"

# Expected: < 0.5s

# Database connections
PGPASSWORD='eromlab!1228' psql -h localhost \
  -U chargeap_dcclab2022 -d chargeap_menu_knowledge \
  -c "SELECT count(*) FROM pg_stat_activity
      WHERE datname='chargeap_menu_knowledge';"

# Expected: 2-5 connections (uvicorn workers)
```

---

## Success Criteria

Migration is considered **successful** when ALL of the following are met:

- [x] ✅ Backup created and verified
- [ ] ✅ Migration script executed without errors
- [ ] ✅ 11 new columns created
- [ ] ✅ 5 new indexes created
- [ ] ✅ Trigger and functions created
- [ ] ✅ 80 images migrated (image_url → primary_image)
- [ ] ✅ API endpoints respond correctly
- [ ] ✅ No error logs in 30-minute monitoring window
- [ ] ✅ Response time < 500ms (p95)

---

## Team Communication Plan

### Before Deployment
- [ ] Notify team-lead: Migration starting
- [ ] Notify backend-dev: Stand by for support
- [ ] Notify qa-devops: Monitoring ready

### During Deployment
- [ ] Update team every 5 minutes
- [ ] Report any errors immediately

### After Deployment
- [ ] Send success/failure notification
- [ ] Share verification results
- [ ] Document any issues encountered

---

## Known Issues / Edge Cases

1. **Issue:** Some menus may have empty `image_url`
   **Impact:** They won't get `primary_image` populated (expected)
   **Resolution:** Content enrichment (Task #9) will fill these later

2. **Issue:** `content_completeness` will be low (10-20%)
   **Impact:** Normal - enrichment hasn't run yet
   **Resolution:** Will increase as Tasks #9 and #10 complete

3. **Issue:** GIN indexes may take 10-15 seconds to build
   **Impact:** Migration execution time slightly longer
   **Resolution:** Wait for completion, no action needed

---

## Next Steps (After Successful Migration)

1. **Immediate (Day 1):**
   - Update deployment documentation with actual results
   - Close Task #11 (DB Schema Extension)
   - Notify content-engineer to proceed with Task #9 (scale from 3 → 100 menus)

2. **Short-term (Week 1):**
   - Complete Task #15 (S3/CloudFront setup) to unblock Task #7
   - Begin populating enriched content via Task #9

3. **Medium-term (Week 2-3):**
   - Upload images to S3 (Task #7)
   - Load enriched data (Task #10)
   - Integration testing (Task #14)

---

## Emergency Contacts

| Role | Name | Availability |
|------|------|--------------|
| Team Lead | qa-devops | Real-time during deployment |
| Backend Dev | backend-dev | On standby |
| Database Admin | FastComet Support | support@fastcomet.com (1-2 hour response) |

---

## Deployment Log

**Executed by:** _________________

**Date/Time:** _________________

**Result:** ☐ Success ☐ Rollback ☐ Backup Restore

**Notes:**
```
[Space for deployment notes, issues encountered, resolution steps]







```

**Final Verification Checklist:**
- [ ] All 11 columns present
- [ ] All 5 indexes created
- [ ] Trigger working (test with UPDATE)
- [ ] API endpoints functional
- [ ] No errors in logs
- [ ] Response time acceptable
- [ ] Team notified of completion

---

**Document Version:** 1.0
**Last Updated:** 2026-02-19
**Next Review:** After deployment completion
