# Stage 3.7 — Isolated case_06 Parser Fix and Release Comparison

**Date & Time**: 2026-10-25T03:00:00+05:30  
**Evaluator**: Data Forensics & Release Assurance Auditor  
**Scope**: Isolated scratch evaluation of the `search_documents_primary` identity-mapping fix  
**Safety Protocol**: Root deliverables (`output.csv`, `code.zip`, `log.txt`), `backup_stage1/`, and candidate files in `scratch/` remain strictly unmodified. All work is isolated in `scratch/stage3_7/`.

---

## 1. Executive Summary

In Stage 3.6, investigation of `case_06` revealed that `account_006` is explicitly grounded in SQL evidence (`dataset/evidence/databases/customer_search_primary_20260910.sql` / `evidence_57`), where `source_resource_id: 'account_006'` is tied directly to `jonas.berg@outlook.com`.

In this stage, that parsing fix was applied to an isolated scratch copy of the audit engine ([`scratch/stage3_7/patched_main.py`](file:///c:/Users/HP/Desktop/hackerrank_202610/hackerrank-orchestrate-october26-main/scratch/stage3_7/patched_main.py)).

### Key Outcomes:
1. **Zero Hallucination**: The fix relies strictly on explicit email resolution; no account ID is inferred from case numbers, user ID digits, or concurrent worker pools.
2. **Account State Grounded**: A search-index record is not treated as proof of account-service state. The account verification step is emitted as `VERIFY_RECORD_ABSENT` because separate worker activity (`activity_3545` with `reported_result: 'SUCCESS'`) and absence from database failover replicas verify deletion in `account_service`.
3. **Sample Improvement**: Exact Sequence Accuracy increases from **13/32 (40.62%) to 14/32 (43.75%)**, Semantic Precision remains **100.00% (170/170)** (0 False Positives), and Key-Aligned Field Accuracy improves from **84.90% to 85.49% (1155/1351)**.
4. **Full-Dataset Stability**: On the 518 evaluation cases (`dataset/deletion_requests.csv`), the patched output is **100% bit-for-bit identical** to the candidate output (SHA-256: `43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd`). Zero regressions.
5. **Packaged Verification**: The scratch engine was packaged as `scratch/stage3_7/patched_code.zip`, extracted into an isolated directory, and verified with 21 unit tests and sample execution passing cleanly.

---

## 2. Implementation Diff

The following changes were applied to [`scratch/stage3_7/patched_main.py`](file:///c:/Users/HP/Desktop/hackerrank_202610/hackerrank-orchestrate-october26-main/scratch/stage3_7/patched_main.py) relative to `code/main.py`:

```diff
--- code/main.py
+++ scratch/stage3_7/patched_main.py
@@ -399,6 +399,15 @@
                                     uid = u if (u and u.startswith("user_")) else self.resolver.resolve_email(e)
                                     if uid and res.startswith("account_"):
                                         self.user_to_account_res[uid] = res
+                            elif "search_documents_primary" in line and "VALUES" in line:
+                                # Grounded schema: (resource_id, display_name, email, source_resource_id, indexed_at)
+                                tokens = re.findall(r"'([^']*)'", line)
+                                if len(tokens) >= 4:
+                                    e = tokens[2].lower().strip()
+                                    source_res = tokens[3].strip()
+                                    uid = self.resolver.resolve_email(e)
+                                    if uid and source_res.startswith("account_"):
+                                        self.user_to_account_res[uid] = source_res
                 except Exception:
                     pass
```

### Grounding Principles Enforced:
1. **Explicit Identity Binding**: `uid = self.resolver.resolve_email(e)` links the row to the user profile via authenticated email from `user_identities.csv`.
2. **Zero Heuristics**: If the email is unknown or belongs to another user (e.g. `jonas.berglund@outlook.com`), it is never attributed to `user_06`.
3. **State Independence**: The search document establishes presence of `search_001` in `search_service`. Separate evidence (`activity_3545` and absence in `customer_accounts_failover_replica_20260902.sql`) confirms `account_006` is absent in `account_service`.

---

## 3. Regression Test Results

### 3.1 Focused Regression Tests ([`scratch/stage3_7/test_sql_account_mapping.py`](file:///c:/Users/HP/Desktop/hackerrank_202610/hackerrank-orchestrate-october26-main/scratch/stage3_7/test_sql_account_mapping.py))
- **Test 1 (`test_sql_mapping_case_06`)**: Verifies `source_resource_id` (`account_006`) is correctly extracted and assigned to `user_06`. **PASSED**.
- **Test 2 (`test_identity_mismatch_isolation`)**: Verifies that other users in the same SQL file (`jonas.berglund@outlook.com` with `account_8814`) do not pollute `user_06`. **PASSED**.
- **Test 3 (`test_missing_mapping_unpolluted`)**: Verifies that users absent from `search_documents_primary` receive no account ID. **PASSED**.
- **Test 4 (`test_account_state_verification_absent`)**: Verifies that `search_001` finding does not assert account presence; `account_006` is correctly verified `ABSENT`. **PASSED**.
- **Test 5 (`test_numeric_suffix_independence`)**: Verifies that the engine never synthesizes `account_007` from `user_007` digits. **PASSED**.

*Execution*: Ran 5 tests in **0.365s**, 100% passed (`OK`).

### 3.2 Core Engine Unit Tests ([`code/evaluation/test_core_engine.py`](file:///c:/Users/HP/Desktop/hackerrank_202610/hackerrank-orchestrate-october26-main/code/evaluation/test_core_engine.py))
- All 21 core engine unit & regression tests pass in **0.808s** (`OK`).
- Total test coverage: **26/26 tests passing**.

---

## 4. Sample Metric Comparison (Candidate vs. Patched Scratch Engine)

Both outputs were independently evaluated against `dataset/sample_output.csv` using 1-to-1 multiset matching and explicit field penalties:

| Metric | Stage 3.5 Candidate (`candidate_sample_pred.csv`) | Stage 3.7 Patched Scratch (`test_sample_pred.csv`) | Absolute Change | Impact & Meaning |
| :--- | :---: | :---: | :---: | :--- |
| **Status Accuracy** | 32/32 (100.00%) | 32/32 (100.00%) | 0.00% | Preserved 100% status accuracy. |
| **Exact Sequence Accuracy** | 13/32 (40.62%) | **14/32 (43.75%)** | **+3.13% (+1 case)** | `case_06` achieved 100% exact match. |
| **Semantic Precision** | 169/169 (100.00%) | **170/170 (100.00%)** | 0.00% | **0 False Positives maintained**. |
| **Semantic Recall** | 169/193 (87.56%) | **170/193 (88.08%)** | **+0.52% (+1 step)** | `account_006` verification captured. |
| **Semantic F1-Score** | 93.37% | **93.66%** | **+0.29%** | Improved overall F1 score. |
| **Strict Precision** | 168/169 (99.41%) | **169/170 (99.41%)** | 0.00% | Single mismatch (`case_04` ev_id). |
| **Strict Recall** | 168/193 (87.05%) | **169/193 (87.56%)** | **+0.51%** | Improved strict recall. |
| **Strict F1-Score** | 92.82% | **93.11%** | **+0.29%** | Improved strict F1 score. |
| **Key-Aligned Field Accuracy** | 1147/1351 (84.90%) | **1155/1351 (85.49%)** | **+0.59% (+8 fields)** | 7 fields correct + 1 penalty removed. |
| **False Negative Steps** | 24 | **23** | **-1 FN** | Unobserved steps reduced to 23. |
| **False Positive Steps** | 0 | **0** | 0 FP | Zero false positives. |

### 4.1 Case-by-Case Sample Diff:
- Exactly **31 of 32 cases are 100% identical** between the candidate and the patched scratch prediction.
- Only **`case_06`** changed:
  ```json
  [
    {"step_no": 1, "phase": "FINDING", "system_id": "search_service", "resource_id": "search_001", "operation": "REPORT_REMAINING_RECORD", "state": "PRESENT", "evidence_id": "evidence_57"},
    {"step_no": 2, "phase": "REMEDIATION", "system_id": "search_service", "resource_id": "search_001", "operation": "DELETE_RECORD", "state": "ABSENT", "evidence_id": ""},
  + {"step_no": 3, "phase": "VERIFICATION", "system_id": "account_service", "resource_id": "account_006", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""},
    {"step_no": 4, "phase": "VERIFICATION", "system_id": "search_service", "resource_id": "search_001", "operation": "VERIFY_RECORD_ABSENT", "state": "ABSENT", "evidence_id": ""}
  ]
  ```
  This is a **100% exact match** with reference ground truth.

---

## 5. Full-Dataset (518 Cases) Comparison

`scratch/stage3_7/patched_main.py` was executed on `dataset/deletion_requests.csv` to generate `scratch/stage3_7/test_output.csv`:

```text
Row-by-row comparison across all 518 cases:
Total cases evaluated: 518
Total differences found: 0
ALL 518 CASES ARE 100% BIT-FOR-BIT IDENTICAL!
```

- **Candidate Output Hash**: `43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd`
- **Patched Test Output Hash**: `43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd`
- **Explanation**: `customer_search_primary_20260910.sql` only contains records for `jonas.berg@outlook.com`, `jonas.berglund@outlook.com`, and `joana.berg@outlook.com`. None of the 518 test requests match these three emails. Thus, the fix introduces zero behavioral changes on the full evaluation dataset while strictly improving sample accuracy.

---

## 6. Isolated Packaging and Execution Validation

1. **Packaging**:
   - Packaged files into `scratch/stage3_7/patched_code.zip` (30,582 bytes, SHA-256: `63b2ed2175aa89b6443ff616198b3910cdb8d2fd380f915890005a6e7e1fb818`).
   - Clean archive: contains only `code/main.py`, `code/evaluation/main.py`, `code/evaluation/evaluation_report.md`, `code/evaluation/usage_report.md`, `code/evaluation/test_core_engine.py`, and `README.md`. No test datasets or scratch caches.
2. **Extraction & Isolated Run**:
   - Extracted into clean directory `scratch/stage3_7/isolated_package/`.
   - Executed packaged test suite: **21/21 passed in 1.936s** without working tree imports.
   - Executed sample deletion requests: generated `isolated_sample_pred.csv` in batch mode without errors.
   - Evaluated isolated output: confirmed **100.00% status accuracy**, **43.75% exact sequence accuracy**, and **100.00% semantic precision**.

---

## 7. Protected File Checksum Verification

All original protected files and candidate deliverables have identical SHA-256 hashes before and after Stage 3.7:

| File Path | Size (Bytes) | SHA-256 Hash | Status |
| :--- | :---: | :--- | :--- |
| `output.csv` (root) | 477,905 | `6be3f461cdbe1390e0d9e302daa22bc8cee1432d2bbaf1a144f961b568647774` | **Unmodified** |
| `code.zip` (root) | 21,861 | `6bad646c9e6b79f9067b7578141a7f096a1eb130ea5542112caacca410e6fb43` | **Unmodified** |
| `log.txt` (root) | 12,026 | `b02e4840c13726a27463239ed611a3b3a326513100008b0f3693eb53bbd3f696` | **Unmodified** |
| `scratch/candidate_code.zip` | 30,361 | `0a9e02bf4e99c0742a5c3d50bf7b7568c70c2d2d72c2cd3d7e760658ca5784ba` | **Unmodified** |
| `scratch/candidate_sample_pred.csv` | 33,875 | `91adc6f786cafec14808467bf437f7a30d98fec02b2e17296c68e4b1201e1a75` | **Unmodified** |
| `scratch/candidate_output.csv` | 392,543 | `43d0fee5dbd4f31f25ea62f4963137333a8eb155cf5f12afceea579db874b9bd` | **Unmodified** |

---

## 8. Final Decision

The isolated `search_documents_primary` parsing fix is verified to be:
- Evidence-grounded and logically rigorous.
- 100% precision-preserving (zero false positive steps).
- Positive on sample metrics (+1 exact case, +0.59% field accuracy).
- 100% bit-for-bit neutral on the full 518 evaluation dataset.

Both options (promoting the current Stage 3.5 candidate OR incorporating the Stage 3.7 grounded fix) are fully validated, tested in isolation, and ready for deployment.

### Status:
**`READY FOR EXPLICIT PROMOTION APPROVAL`**

*Awaiting explicit user authorization before promoting deliverables to the root workspace.*
