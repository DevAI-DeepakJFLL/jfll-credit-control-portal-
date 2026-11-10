# Remediation of All Code Review, Security & DSA Findings Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolve all identified findings across Security (SEC-01 to SEC-07), DSA performance bottlenecks (DSA-01 to DSA-05), and UI/Quality findings (Finding 1 to Finding 4) in the technical ledger.

**Architecture:** Harden FastAPI security controls (fail-closed authentication, strict CORS, CSP/Permissions-Policy headers, rate limiting, tokenized downloads). Optimize DSA bottlenecks (server-side indexed SQLite search, `os.scandir()` I/O, linear string joins, precompiled regexes). Sync frontend state and tie history download links to unguessable tokens.

**Tech Stack:** FastAPI, Pydantic v2, SQLite WAL, python-docx, pypdf, React 18, TypeScript, Tailwind CSS, Vite.

**Spec:** [`code-review-findings.md`](file:///Users/deepak/.gemini/antigravity-cli/brain/064eda1f-b8c4-45ae-b528-9a01572ef751/code-review-findings.md)

## Global Constraints

- 100% pass rate on all automated unit and integration tests.
- Zero TypeScript compiler errors (`npm run build`).
- Maintain backward compatibility for existing appraisal records.
- Fail closed for all administrative and maintenance endpoints.

---

### Task 1: Security Hardening & Defense-in-Depth

**Files:**
- Modify: `backend/app/main.py`
- Modify: `backend/app/s3_storage.py`
- Modify: `backend/tests/test_pipeline.py`

**Interfaces:**
- Produces: Fail-closed `trigger_maintenance_cleanup` with constant-time comparison.
- Produces: CSP and Permissions-Policy response headers in middleware.
- Produces: In-memory IP rate limiting on `/api/extract` and `/api/generate`.
- Produces: Safe default CORS configuration and S3 token preservation during reconciliation.

- [ ] **Step 1: Write failing security tests**
In `backend/tests/test_pipeline.py`, add tests asserting:
1. `POST /api/maintenance/cleanup` returns HTTP 401 Unauthorized when `ADMIN_SECRET_KEY` is not set or invalid key is supplied.
2. Response headers contain `Content-Security-Policy` and `Permissions-Policy`.
3. S3 reconciliation restores `access_token` into the SQLite database.

- [ ] **Step 2: Run test to confirm it fails**
Run `python3 -m unittest backend.tests.test_pipeline.TestCreditControlPipeline.test_security_hardening`.

- [ ] **Step 3: Implement security controls**
1. In `backend/app/main.py`:
   - Enforce fail-closed admin auth using `secrets.compare_digest`.
   - Update `add_security_headers` to inject `Content-Security-Policy` and `Permissions-Policy`.
   - Default `ALLOWED_ORIGINS` to `http://localhost:3000,http://127.0.0.1:3000` when not explicitly set.
   - Implement simple token-bucket rate limiter helper for `/api/extract` and `/api/generate`.
   - Guard `/api/sample/{filename}` with `ENABLE_SAMPLE_ROUTES` check.
2. In `backend/app/s3_storage.py`:
   - Include `access_token` in `reconcile_records_from_s3` SQL insert and value tuple.

- [ ] **Step 4: Run tests to confirm passes**
Run `python3 -m unittest discover backend/tests`. Verify all tests pass.

- [ ] **Step 5: Commit changes**
Commit with: `fix(security): implement fail-closed cleanup auth, CSP headers, rate limiting, and S3 token reconciliation`.

---

### Task 2: DSA Optimizations & Schema Refactoring

**Files:**
- Modify: `backend/app/database.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/parser.py`
- Modify: `backend/app/generator.py`
- Modify: `backend/app/models.py`
- Modify: `backend/tests/test_pipeline.py`

**Interfaces:**
- Produces: Server-side search filter in `get_all_appraisals` via SQLite B-Tree index.
- Produces: $\mathcal{O}(1)$ directory scanning in `prune_storage_files()` using `os.scandir()`.
- Produces: Linear $\mathcal{O}(P)$ string joins and precompiled regular expressions in `parser.py`.
- Produces: Scaled font size in `generator.py` for long composite tenors.
- Produces: Shared `BaseAppraisalData` model in `models.py`.

- [ ] **Step 1: Write test for server-side search**
In `backend/tests/test_pipeline.py`, add a test testing `/api/appraisals?search=...` asserting that filtering by customer name or salesperson works via SQL.

- [ ] **Step 2: Implement DSA optimizations**
1. In `backend/app/database.py`:
   - Add `search: Optional[str] = None` to `get_all_appraisals`. When present, filter with `WHERE customer_name LIKE ? OR salesperson LIKE ?` with `%query%`.
   - Add `search` filter to `get_appraisals_count`.
2. In `backend/app/main.py`:
   - Accept `search: Optional[str] = None` in `GET /api/appraisals` and pass to `get_all_appraisals` and `get_appraisals_count`.
   - In `prune_storage_files`, replace `os.listdir` and `os.path.getmtime` with `os.scandir()` to avoid redundant `stat()` syscalls.
3. In `backend/app/parser.py`:
   - Precompile regular expressions at module level (`RE_EPFO`, `RE_COURT_VS`, `RE_INR`, `RE_WHITESPACE`).
   - Replace `text += ...` loops with `"\n".join(...)`.
4. In `backend/app/generator.py`:
   - In Section 2 metric card for approved credit days, dynamically set font size to `8.5pt` if `len(values[1]) > 16` to prevent awkward 3-line cell height inflation.
5. In `backend/app/models.py`:
   - Extract common fields into `BaseAppraisalData` and inherit in `RubixExtractedData` and `GenerateDocxRequest`.

- [ ] **Step 3: Run test suite**
Run `python3 -m unittest discover backend/tests`. Ensure all tests pass cleanly.

- [ ] **Step 4: Commit changes**
Commit with: `perf(dsa): add server-side search, scandir cleanup, linear string joins, and schema deduplication`.

---

### Task 3: Frontend State Sync, Secure Downloads, and Server-Side Search

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/components/MemoForm.tsx`
- Modify: `frontend/src/components/AppraisalHistory.tsx`

**Interfaces:**
- Consumes: `/api/appraisals?search=...` server-side search from Task 2.
- Produces: Synced `approved_credit_days` across `MetricCards.tsx` and `MemoForm.tsx`.
- Produces: Unguessable token download URLs in `AppraisalHistory.tsx`.

- [ ] **Step 1: Update frontend types**
In `frontend/src/types.ts`, add `access_token?: string;` to `AppraisalRecord`.

- [ ] **Step 2: Sync approved credit days in MemoForm.tsx**
In `frontend/src/components/MemoForm.tsx`, when the user changes `commercial_mode`, `iata_credit_days`, or `ocean_credit_days`, compute the composite tenor and automatically pass `approved_credit_days` to `onChange(...)` so the top Key Metric card mirrors the selection.

- [ ] **Step 3: Update AppraisalHistory.tsx for secure downloads and server search**
In `frontend/src/components/AppraisalHistory.tsx`:
1. Use `item.access_token || item.id` in the download anchor `apiUrl(\`/api/download/\${item.access_token || item.id}\`)`.
2. Connect `deferredSearch` to the fetch request (`apiUrl(\`/api/appraisals?search=\${encodeURIComponent(deferredSearch)}\`)`), enabling full-database search across all records beyond the 200-item window.

- [ ] **Step 4: Verify build and tests**
Run `npm run build` in `frontend/` and `python3 -m unittest discover backend/tests`. Ensure everything is green.

- [ ] **Step 5: Commit changes**
Commit with: `feat(frontend): sync metric card tenor, implement tokenized downloads, and connect server-side search`.
