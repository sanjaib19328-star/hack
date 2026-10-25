# Stage 3.8 — Final Release Artifact Gate Report

**Date & Time**: 2026-10-25T08:25:00+05:30  
**Evaluator**: Release Packaging & Artifact Assurance Gate  
**Target Archive**: `scratch/stage3_7/patched_code.zip` (30,582 bytes, SHA-256: `63b2ed2175aa89b6443ff616198b3910cdb8d2fd380f915890005a6e7e1fb818`)  
**Safety Protocol**: Root files (`output.csv`, `code.zip`, `log.txt`), `backup_stage1/`, and previous candidate files in `scratch/` remain strictly unmodified.

---

## 1. Patched ZIP Integrity and Checksum Verification

Every file inside `scratch/stage3_7/patched_code.zip` was extracted and compared against its intended source file in size (bytes) and SHA-256 hash:

| Archive Path | Source Path | File Size (Bytes) | SHA-256 Hash | Integrity Status |
| :--- | :--- | :---: | :--- | :---: |
| `code/main.py` | `scratch/stage3_7/patched_main.py` | 76,669 | `16fa3f728e87f258111f7e52e40e31081e8781bacb436e46d5605b9b9c98edcd` | **MATCH** |
| `code/evaluation/main.py` | `code/evaluation/main.py` | 12,324 | `9968ff8e1e6c1ffadff059d2551bd727cdfafd2f9f0719bdf0dc875a63f215ae` | **MATCH** |
| `code/evaluation/evaluation_report.md` | `code/evaluation/evaluation_report.md` | 13,701 | `6803f04ad8f4122d451f5145bbe899e8e2852f66ae9af1e27d98893f388dcb58` | **MATCH** |
| `code/evaluation/usage_report.md` | `code/evaluation/usage_report.md` | 3,690 | `abfc206e433cb60d8c7ffd1be5d7912396e3356d60a4ee17704d098fe78736cd` | **MATCH** |
| `code/evaluation/test_core_engine.py` | `code/evaluation/test_core_engine.py` | 20,981 | `3501118deb72e55572e686b8027a08e8af5593da3874e71c235a2274f0f26581` | **MATCH** |
| `README.md` | `README.md` | 8,386 | `9f88c1c852a2ec94461775bf7a4f1ab6d6cfebd98e4031d961ef8b8146389c20` | **MATCH** |

- **Extra Files in ZIP**: **0**. Exactly the 6 required release files are present.
- **Missing Files**: **0**.
- **Byte-for-byte / Hash Consistency**: **100% Verified**.

---

## 2. Isolated Execution and Code Logic Verification

The archive was extracted into a fresh, isolated directory (`scratch/stage3_8/extracted_gate/`). Working tree imports were blocked by configuring `PYTHONPATH` exclusively to the extracted package directory.

### 2.1 Code Logic Verification:
- **`search_documents_primary` Mapping**: Confirmed present in `code/main.py`.
- **Strict Account Fallback Policy**: Confirmed present (`elif not (findings or verifications) and fallback_acc:`).
- **Zero Sample Leakage**: Confirmed that `sample_output` and `sample_baseline` are completely absent.

### 2.2 Packaged Unit Tests Execution:
- Executed: `python code/evaluation/test_core_engine.py`
- Exit Code: **0**
- Test Results: **21/21 tests passed in 1.836s** (`OK`).

---

## 3. Output Consistency & Independent Sample Metrics

The extracted package was executed on `dataset/sample_deletion_requests.csv` to generate `gate_sample_pred.csv`, which was independently evaluated against `dataset/sample_output.csv`:

| Metric | Numerator | Denominator | Value | Assessment |
| :--- | :---: | :---: | :---: | :--- |
| **Status Accuracy** | 32 | 32 | **100.00%** | All 32 request statuses identified correctly. |
| **Exact Ordered Sequence** | 14 | 32 | **43.75%** | 14 cases match truth 100% exactly (including `case_06`). |
| **Semantic Step Precision** | 170 | 170 | **100.00%** | **0 False Positives**. Zero speculative hallucinations. |
| **Semantic Step Recall** | 170 | 193 | **88.08%** | 23 unobserved reference steps remaining. |
| **Semantic Step F1-Score** | — | — | **93.66%** | High harmonic mean. |
| **Strict Step Precision** | 169 | 170 | **99.41%** | 1 evidence ID difference (`case_04` anomaly). |
| **Strict Step Recall** | 169 | 193 | **87.56%** | High strict recall. |
| **Strict Step F1-Score** | — | — | **93.11%** | High strict F1. |
| **Key-Aligned Field Accuracy** | 1155 | 1351 | **85.49%** | Evaluated with full penalty for missing/extra steps. |

### 3.1 Verification of `case_06` and Ambiguous Cases:
- **`case_06`**: Verified as a **100% exact match** with reference truth. Contains evidence-supported step:
  `{"phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_006", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": "", "step_no": 3}`.
- **Ambiguous Cases**: All 13 other ambiguous cases (`case_07`, `case_08`, `case_09`, `case_10`, `case_18`, `case_20`, `case_22`, `case_23`, `case_25`, `case_28`, `case_29`, `case_31`, `case_32`) remain **100% free of speculative account IDs**.

---

## 4. Full-Dataset (518 Cases) Comparison

The extracted package was executed on `dataset/deletion_requests.csv` to generate `gate_full_output.csv`:

- **Execution Exit Code**: **0** (Batch execution completed successfully).
- **Total Rows**: Exactly 519 rows (1 header + 518 cases).
- **Candidate Output Hash (`scratch/candidate_output.csv`)**: `43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd`
- **Gate Output Hash (`gate_full_output.csv`)**: `43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd`
- **Hash Match**: **True**.
- **Row-by-Row Content Match**: **True** (100% bit-for-bit identical).

---

## 5. Protected File Checksum Verification

All original protected files and candidate deliverables have identical SHA-256 hashes:

| File Path | Size (Bytes) | SHA-256 Hash | Status |
| :--- | :---: | :--- | :---: |
| `output.csv` (root) | 477,905 | `6be3f461cdbe1390e0d9e302daa22bc8cee1432d2bbaf1a144f961b568647774` | **Unmodified** |
| `code.zip` (root) | 21,861 | `6bad646c9e6b79f9067b7578141a7f096a1eb130ea5542112caacca410e6fb43` | **Unmodified** |
| `log.txt` (root) | 12,026 | `b02e4840c13726a27463239ed611a3b3a326513100008b0f3693eb53bbd3f696` | **Unmodified** |
| `scratch/candidate_code.zip` | 30,361 | `0a9e02bf4e99c0742a5c3d50bf7b7568c70c2d2d72c2cd3d7e760658ca5784ba` | **Unmodified** |
| `scratch/candidate_sample_pred.csv` | 33,875 | `91adc6f786cafec14808467bf437f7a30d98fec02b2e17296c68e4b1201e1a75` | **Unmodified** |
| `scratch/candidate_output.csv` | 392,543 | `43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd` | **Unmodified** |

### Git Working Tree Status:
```text
 M code/evaluation/evaluation_report.md
 M code/evaluation/usage_report.md
 M code/main.py
?? backup_stage1/
?? code/__pycache__/
?? code/evaluation/__pycache__/
?? code/evaluation/test_core_engine.py
?? scratch/
```
No unauthorized staging, commits, or root file modifications exist.

---

## 6. Final Decision

All release gate criteria are satisfied:
1. Exact package file integrity: 100% hash match on all 6 files.
2. Isolated testing: 21/21 tests pass without working tree pollution.
3. Metric excellence: 100.00% precision, 43.75% exact sequence accuracy, 85.49% field accuracy.
4. Full dataset stability: 100% bit-for-bit identical on all 518 evaluation cases.

### Status:
**`READY FOR EXPLICIT PROMOTION APPROVAL`**

*Awaiting explicit user authorization before promoting deliverables to the root workspace.*
