# Stage 3.9 — Submission Requirements and Promotion Plan

**Document Path**: `scratch/stage3_9/promotion_plan.md`  
**Date & Time**: 2026-10-25T08:30:00+05:30  
**Status**: Inspection-Only Plan — **NO FILES CHANGED**  
**Repository**: `c:\Users\HP\Desktop\hackerrank_202610\hackerrank-orchestrate-october26-main` (Remote: `https://github.com/sanjaib19328-star/hack`)

---

## 1. Challenge Submission Requirements and Source Locations

The official requirements for the HackerRank Orchestrate October 2026 challenge, **"Ghost Data Still Exists"**, were identified from the repository instructions:

| Source Document | Location | Key Requirement Excerpt |
| :--- | :--- | :--- |
| **`README.md`** | Lines 28–42, 65–77, 89–100, 118–158 | "Your final generated file for submission must be the root-level `output.csv`."<br>"Packaging `code.zip`: Runnable solution, prompts, configuration, `README.md`, and `evaluation/` reports."<br>"Upload `log.txt` directly as your `chat_transcript` submission on HackerRank." |
| **`problem_statement.md`** | Lines 129–162 | "Submission: `code.zip`, `output.csv`, `chat_transcript`, AI interview."<br>"Your `code.zip` must include `evaluation/evaluation_report.md` and `evaluation/usage_report.md`." |
| **`AGENTS.md`** | Lines 45–60, 100–120 | "The log file is named `log.txt` and lives in the repository root... Always launch your AI coding agent from the repository root... upload `log.txt` directly as your `chat_transcript` submission." |

### Deliverable Classification:
- **`output.csv`**: **Mandatory Primary Deliverable**. Required format: CSV with header `case_id,deletion_status,steps_json` covering all 518 cases (`case_33` to `case_550`), sorted numerically.
- **`code.zip`**: **Mandatory Primary Deliverable**. Required format: Clean zip archive containing `code/main.py`, `code/evaluation/main.py`, `code/evaluation/evaluation_report.md`, `code/evaluation/usage_report.md`, `code/evaluation/test_core_engine.py`, and `README.md`. No test datasets, virtual environments, build caches, or nested archives.
- **`log.txt`** (`chat_transcript`): **Mandatory Primary Deliverable**. Required format: Complete chronological coding agent transcript adhering to `AGENTS.md` format.

---

## 2. Proposed Source-to-Destination Mappings

| Submission Deliverable | Target Root Destination | Proposed Source File | Rationale |
| :--- | :--- | :--- | :--- |
| **Prediction File** | `output.csv` (repo root) | `scratch/candidate_output.csv`<br>*(identical to `scratch/stage3_7/test_output.csv`)* | Contains 518 audited cases (`case_33` to `case_550`), 0 schema errors, 0 warnings. Verified bit-for-bit identical across Stages 3.5, 3.7, and 3.8. |
| **Implementation Archive** | `code.zip` (repo root) | `scratch/stage3_7/patched_code.zip` | Fully validated package containing Stage 3.7 grounded `search_documents_primary` fix. Achieves 43.75% exact sequence match (14/32), 100.00% semantic precision (170/170), and passes 21/21 unit tests in complete isolation. |
| **Agent Transcript** | `log.txt` (repo root) | `scratch/stage3_9/candidate_final_log.txt` | Comprehensive transcript covering all turns from initial audit through Stages 3.1–3.9 with verified tool headers (`tool=antigravity-ide model=gemini-3.8-flash`). |
| **Working Tree Source Sync** | `code/main.py` | `scratch/stage3_7/patched_main.py` | Synchronizes the active working tree `code/main.py` with the packaged engine inside `code.zip` so local execution exactly mirrors packaged execution. |

---

## 3. Checksums and Byte Sizes

### 3.1 Proposed Sources (Ready for Promotion):

| Deliverable | Proposed Source Path | Size (Bytes) | SHA-256 Hash |
| :--- | :--- | :---: | :--- |
| `output.csv` | `scratch/candidate_output.csv` | 392,543 | `43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd` |
| `code.zip` | `scratch/stage3_7/patched_code.zip` | 30,582 | `63b2ed2175aa89b6443ff616198b3910cdb8d2fd380f915890005a6e7e1fb818` |
| `log.txt` | `scratch/stage3_9/candidate_final_log.txt` | 34,720 | `ce32768808fbcec57458570f5cf62dc714c11c06932307db0d6ac42bfcf3a56a` |
| `code/main.py` | `scratch/stage3_7/patched_main.py` | 76,669 | `16fa3f728e87f258111f7e52e40e31081e8781bacb436e46d5605b9b9c98edcd` |

### 3.2 Current Protected Root Files (To Be Replaced Upon Approval):

| Current Root File | Size (Bytes) | Current SHA-256 Hash | Notes |
| :--- | :---: | :--- | :--- |
| `output.csv` | 477,905 | `6be3f461cdbe1390e0d9e302daa22bc8cee1432d2bbaf1a144f961b568647774` | Contains initial buggy baseline with sample-leakage shortcuts. |
| `code.zip` | 21,861 | `6bad646c9e6b79f9067b7578141a7f096a1eb130ea5542112caacca410e6fb43` | Initial baseline zip without full evaluation reports or regression tests. |
| `log.txt` | 12,026 | `b02e4840c13726a27463239ed611a3b3a326513100008b0f3693eb53bbd3f696` | Initial transcript ending at early Stage 2. |

### 3.3 Preserved Original Backup (`backup_stage1/`):
- `backup_stage1/output.csv` (477,905 bytes, SHA-256: `6be3f461cdbe1390e0d9e302daa22bc8cee1432d2bbaf1a144f961b568647774`)
- `backup_stage1/code.zip` (21,861 bytes, SHA-256: `6bad646c9e6b79f9067b7578141a7f096a1eb130ea5542112caacca410e6fb43`)
- `backup_stage1/log.txt` (12,026 bytes, SHA-256: `b02e4840c13726a27463239ed611a3b3a326513100008b0f3693eb53bbd3f696`)
*`backup_stage1/` will NEVER be overwritten, modified, or deleted.*

---

## 4. Risk Analysis and Uncertainty Evaluation

1. **Risk: Loss of Initial Baseline Artifacts**:
   - *Assessment*: Negligible risk. `backup_stage1/` already holds the initial baseline artifacts, but an additional safety snapshot `backup_pre_promotion/` will be created immediately before overwriting any root files.
2. **Risk: Working Tree and Packaged ZIP Divergence**:
   - *Assessment*: If `scratch/stage3_7/patched_code.zip` is promoted to root `code.zip` without updating `code/main.py`, a reviewer inspecting `code/main.py` directly would see the Stage 3.3 code instead of the Stage 3.7 code.
   - *Mitigation*: The promotion plan explicitly synchronizes `code/main.py` from `scratch/stage3_7/patched_main.py` so the working tree and the zip archive are 100% identical.
3. **Risk: 518-Case Regression**:
   - *Assessment*: Zero risk. As verified in Stage 3.7 and Stage 3.8, `scratch/candidate_output.csv` and `gate_full_output.csv` have the exact same SHA-256 hash (`43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd`). The 518 cases are completely unaffected by the `case_06` grounded parser fix.

---

## 5. Promotion Execution Procedure (Step-by-Step)

Upon receiving explicit user authorization, the promotion will proceed in the following strict sequence:

### Step 1: Pre-Promotion Safety Snapshot
```powershell
New-Item -ItemType Directory -Force -Path backup_pre_promotion
Copy-Item output.csv backup_pre_promotion/output.csv -Force
Copy-Item code.zip backup_pre_promotion/code.zip -Force
Copy-Item log.txt backup_pre_promotion/log.txt -Force
```

### Step 2: Deliverables Promotion
```powershell
Copy-Item scratch/candidate_output.csv output.csv -Force
Copy-Item scratch/stage3_7/patched_code.zip code.zip -Force
Copy-Item scratch/stage3_9/candidate_final_log.txt log.txt -Force
Copy-Item scratch/stage3_7/patched_main.py code/main.py -Force
```

### Step 3: Rollback Procedure (In Case Any Post-Promotion Check Fails)
If any post-promotion check fails, execute immediately:
```powershell
Copy-Item backup_pre_promotion/output.csv output.csv -Force
Copy-Item backup_pre_promotion/code.zip code.zip -Force
Copy-Item backup_pre_promotion/log.txt log.txt -Force
git checkout -- code/main.py
```

---

## 6. Post-Promotion Verification Checklist

Immediately after promotion, the following automated checks will be executed to confirm release readiness:

1. **Checksum Verification**:
   - Verify `output.csv` SHA-256 equals `43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd`.
   - Verify `code.zip` SHA-256 equals `63b2ed2175aa89b6443ff616198b3910cdb8d2fd380f915890005a6e7e1fb818`.
   - Verify `log.txt` SHA-256 equals `ce32768808fbcec57458570f5cf62dc714c11c06932307db0d6ac42bfcf3a56a`.
2. **Schema & Count Validation**:
   - Run official evaluator schema check: `python code/evaluation/main.py --pred output.csv --expected-count 518`.
   - Run full 518 audit script: `python scratch/audit_518_candidate.py` against root `output.csv`.
3. **Test Suite Verification**:
   - Run working tree test suite: `python code/evaluation/test_core_engine.py` (21 tests).
4. **ZIP Archive Inspection**:
   - Inspect root `code.zip` file list and confirm exactly 6 files with zero caches or datasets.
5. **Git Status Review**:
   - Run `git status --short` to review modified files without staging or committing.

---

## 7. Questions for User Confirmation

Prior to authorization, the user may review and confirm:
1. **Approval of Source Deliverables**: Confirm selection of `scratch/candidate_output.csv` (518 cases), `scratch/stage3_7/patched_code.zip` (Stage 3.7 package), and `scratch/stage3_9/candidate_final_log.txt` (full audit log).
2. **Working Tree Synchronization**: Confirm that active `code/main.py` should be updated to match the packaged `code/main.py` in `code.zip`.
3. **Git Staging/Commit**: Confirm whether Git staging or committing is desired, or whether files should remain unstaged in the working tree for user review.

---

## 8. Status

**`READY FOR USER REVIEW — NO FILES CHANGED`**

*All original files remain 100% untouched. Awaiting explicit user authorization.*
