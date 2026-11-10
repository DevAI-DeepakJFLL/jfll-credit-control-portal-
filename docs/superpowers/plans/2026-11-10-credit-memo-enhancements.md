# Credit Memo Enhancements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement 4 user-requested enhancements: Additional Information field, Commercial Mode selector with shared 7/10-day tenors and accessible theme-styled dropdowns, customizable KYC checklist with add/remove document capability, and Mail Approval field with visual DOCX authorization marker.

**Architecture:** Extend FastAPI Pydantic request models and the python-docx generator to support the new metadata and dynamic tables. Update React state in `App.tsx` and types in `types.ts`. Polish `MemoForm.tsx` controls with custom SVG chevrons, accessible focus-visible rings, segmented mode pills, and dynamic KYC row controls adhering to Impeccable and UI/UX Pro design standards.

**Tech Stack:** FastAPI, Pydantic v2, python-docx, React 18, TypeScript, Tailwind CSS, Lucide React, Vite.

**Spec:** Ponytail Audit findings 1–7 and user requirements.

## Global Constraints

- Preserve all existing 22 automated tests and achieve 100% pass rate.
- Never use unstyled native select elements; all dropdowns must include custom chevrons, `appearance-none`, and `focus-visible:ring-2 focus-visible:ring-blue-600`.
- Maintain strict backward compatibility for existing appraisal records.
- Zero TypeScript build errors (`npm run build` must cleanly generate `dist/`).
- No AI UI slop: enforce WCAG contrast, proper touch targets, and keyboard accessibility.

---

### Task 1: Backend Models and DOCX Generator Enhancements

**Files:**
- Modify: `backend/app/models.py`
- Modify: `backend/app/generator.py`
- Modify: `backend/tests/test_pipeline.py`

**Interfaces:**
- Produces: `GenerateDocxRequest` and `RubixExtractedData` with `additional_info`, `commercial_mode`, `mail_approval`, `iata_credit_days`, `ocean_credit_days`.
- Produces: `build_crif_docx` supporting dynamic customer profile rows and email approval annotations.

- [ ] **Step 1: Write the failing test**
Add a test in `backend/tests/test_pipeline.py` asserting that `GenerateDocxRequest` validates `additional_info`, `commercial_mode`, and `mail_approval`, and that `build_crif_docx` generates a `.docx` containing "Additional Information" and "[ Approved via Email: ... ]" without IndexError.

- [ ] **Step 2: Run test to confirm it fails**
Run `python3 -m unittest backend.tests.test_pipeline.TestCreditControlPipeline.test_enhanced_fields_docx_generation`.

- [ ] **Step 3: Update models and generator**
1. In `backend/app/models.py`:
   - Add `additional_info: str = ""` to `RubixExtractedData` and `GenerateDocxRequest`.
   - Add `commercial_mode: str = "Both"` to `RubixExtractedData` and `GenerateDocxRequest`.
   - Add `mail_approval: str = ""` to `RubixExtractedData` and `GenerateDocxRequest`.
2. In `backend/app/generator.py`:
   - In Section 1 (`CUSTOMER IDENTITY & BUSINESS PROFILE`), compute `profile_rows`:
     Include `("Customer Legal Name", ...)`, `("Type of Company", ...)`, `("Date of Incorporation", ...)`, `("Registered / Business Address", ...)`. If `data.get('additional_info')`, append `("Additional Information", data['additional_info'])`.
   - Dynamically initialize `profile_table = doc.add_table(rows=len(profile_rows), cols=2)`.
   - In Section 4 / Sign-off table, if `data.get('mail_approval')`:
     In column 2 (Approver cell 1), set the run text to `f"[ Approved via Email: {data['mail_approval']} ]"` in italicized slate-600 font instead of `[ Authorized Signature ]`.

- [ ] **Step 4: Run test suite to verify passes**
Run `python3 -m unittest discover backend/tests`. Ensure all tests pass.

- [ ] **Step 5: Commit changes**
Commit with conventional commit message: `feat(backend): add additional_info, commercial_mode, mail_approval and dynamic profile table`.

---

### Task 2: Frontend Types and State Synchronization

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/App.tsx`

**Interfaces:**
- Consumes: Backend `GenerateDocxRequest` schema from Task 1.
- Produces: Synced state in `App.tsx` passing all 4 new parameters to `/api/generate`.

- [ ] **Step 1: Update TypeScript types**
In `frontend/src/types.ts`:
- Update `KYCItem` to include optional `id?: string`.
- Update `RubixExtractedData` to include `additional_info?: string; commercial_mode?: 'Air' | 'Ocean' | 'Both'; mail_approval?: string;`.

- [ ] **Step 2: Synchronize state and payload in App.tsx**
In `frontend/src/App.tsx`:
- In `handleGenerate`, compute composite `credit_days`:
  - If `commercial_mode === 'Air'`, use `extractedData.iata_credit_days || '15 Days'`.
  - If `commercial_mode === 'Ocean'`, use `extractedData.ocean_credit_days || '30 Days'`.
  - If `commercial_mode === 'Both'` or default, use `Air: ${extractedData.iata_credit_days || '15 Days'} | Ocean: ${extractedData.ocean_credit_days || '30 Days'}`.
- Include in `payload`:
  - `additional_info: extractedData.additional_info || ''`
  - `commercial_mode: extractedData.commercial_mode || 'Both'`
  - `mail_approval: extractedData.mail_approval || ''`
  - Filter `kyc_documents` to omit items with blank document titles.

- [ ] **Step 3: Verify build**
Run `npm run build` in `frontend/` to confirm zero type errors.

- [ ] **Step 4: Commit changes**
Commit with: `feat(frontend): update types and payload synchronization for commercial terms and approval`.

---

### Task 3: Form UI/UX Polish with Impeccable and UI/UX Pro Max

**Files:**
- Modify: `frontend/src/components/MemoForm.tsx`

**Interfaces:**
- Consumes: `RubixExtractedData` from `frontend/src/types.ts`.
- Produces: Polished, theme-aligned accessible form with segmented pills, custom chevrons, dynamic KYC editor, and mail approval input.

- [ ] **Step 1: Add Additional Information field in Card 1**
In Card 1 (`1. Customer Identity & Entity Profile`), add a multi-line textarea for `Additional Information (Special Notes / Group Background)` with placeholder and accessible focus rings.

- [ ] **Step 2: Upgrade Card 3 Commercial Terms & Mode Selector**
1. Add segmented toggle pills (`Air`, `Ocean`, `Both`) with active state (`bg-blue-600 text-white font-bold shadow-xs`, inactive: `bg-slate-100 text-slate-600 hover:text-slate-900`).
2. Define unified `CREDIT_TENOR_OPTIONS`:
   `["7 Days", "10 Days", "15 Days", "21 Days", "30 Days", "45 Days", "60 Days"]`.
3. Wrap all `<select>` inputs with `appearance-none relative` and custom Lucide `ChevronDown` (`pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 w-4 h-4`).
4. Enable or disable / visually dim the Air or Ocean dropdown based on selected mode.

- [ ] **Step 3: Enhance Card 4 KYC Checklist with Add/Delete Capability**
1. Add `+ Add Custom Document` button below the table with Lucide `Plus` icon.
2. Add a delete icon button (Lucide `Trash2`) on each row with tooltip and confirmable click.
3. Use stable row key (`item.id || item.document + '-' + idx`).
4. Support editing document name, status, source, and remarks inline.

- [ ] **Step 4: Add Mail Approval field in Card 5**
In Card 5 (`5. Credit Approval & Sign-Off Matrix`), add an input field:
- Label: `Email Approval Reference / Sanction Note (e.g., Approved via email by Director on 10/11/2026)`
- Placeholder: `e.g. Email approval from Director Mr. XYZ dated 10-Nov-2026`
- Helper text: `If approved over email, this reference replaces the physical signature in the generated memorandum.`

- [ ] **Step 5: Verify build & tests**
Run `npm run build` in `frontend/` and run backend tests `python3 -m unittest discover backend/tests`. Ensure everything is green.

- [ ] **Step 6: Commit changes**
Commit with: `feat(ui): implement accessible commercial mode selector, custom KYC, and email approval controls`.
