# Stage 3.6 — Final Account Resolution and Release Review

**Date & Time**: 2026-10-25T02:40:00+05:30  
**Evaluator**: Forensic Audit & Identity Verification Engine  
**Review Target**: Remaining account-resolution gap, evidence grounding, and candidate release integrity  
**Safety Protocol**: Root files (`output.csv`, `code.zip`, `log.txt`), `backup_stage1/`, and candidate files in `scratch/` remain strictly unmodified.

---

## 1. Investigation of case_06

### 1.1 Source Evidence Identification
- **Target Case**: `case_06` (`jonas.berg@outlook.com`).
- **Audit Window**: Requested at `2026-08-29T06:51:00Z`, reported at `2026-08-30T17:12:00Z` (`PARTIALLY_COMPLETE`), audited at `2026-09-10T09:15:00Z`.
- **Evidence File**: `dataset/evidence/databases/customer_search_primary_20260910.sql` (Catalog ID: `evidence_57`, Origin: `customer_search_primary_capture`, Captured: `2026-09-10T08:45:00Z`).
- **Exact Line in Evidence**:
  ```sql
  CREATE TABLE search_documents_primary (resource_id TEXT PRIMARY KEY, display_name TEXT, email TEXT, source_resource_id TEXT, indexed_at TEXT);
  INSERT INTO "search_documents_primary" VALUES('search_001','Jonas Berg','jonas.berg@outlook.com','account_006','2026-09-09T22:12:00Z');
  ```

### 1.2 Evaluation of Questions
1. **Whether the record is in scope for the requested audit**:
   - **Yes**. `evidence_57` was captured on `2026-09-10T08:45:00Z`, which falls precisely within the request audit window `[2026-08-29T06:51:00Z, 2026-09-10T09:15:00Z]`. The target email `jonas.berg@outlook.com` matches the request email exactly.
2. **Whether it is linked to the requested user through a reliable identity attribute**:
   - **Yes**. The row contains `email: 'jonas.berg@outlook.com'` and `display_name: 'Jonas Berg'`. Both match the primary identity attributes from `sample_deletion_requests.csv` without ambiguity. It directly links this identity to `source_resource_id: 'account_006'`.
3. **Whether the record establishes presence, absence, or another state at the relevant audit time**:
   - For `search_service`: It proves that search document `search_001` is **PRESENT** (un-deleted) in the primary search index on `2026-09-09T22:12:00Z`. This supports the finding `REPORT_REMAINING_RECORD` on `search_service`.
   - For `account_service`: The table is a search index snapshot (`search_documents_primary`), not the live `customer_profiles` table of `account_service`. However, `activity_3545` in `system_activity.csv` recorded `DELETE_RECORD` on `account_006` in `account_service` with result `SUCCESS` on `2026-08-30T17:08:20Z`. Moreover, `account_006` is absent from the failover replica `customer_accounts_failover_replica_20260902.sql`. Together, these establish that `account_006` was deleted from `account_service`.
4. **Why the current engine does not emit a verification step**:
   - In `code/main.py`, `_init_account_mappings()` scans SQL files exclusively for `customer_profiles` table lines (`if "customer_profiles" in line:`). It does not inspect `search_documents_primary`.
   - In `system_activity.csv`, `activity_3545` had reported result `SUCCESS`. Because `case_06` had `reported_status = "PARTIALLY_COMPLETE"`, the engine's worker heuristic filtered for `reported_result in ("PARTIAL", "FAILED")`, excluding `activity_3545`.
   - Because `findings` existed (`search_001`), the Stage 3.3 patch prevented emitting the fallback heuristic `account_006`.
5. **Proposed General Evidence-Parsing Fix**:
   - *Fix Description*: Update `_init_account_mappings()` in `code/main.py` to also parse SQL tables containing `source_resource_id` (such as `search_documents_primary`), mapping `source_resource_id` to the associated user email when present.
   - *Impact Assessment*:
     - **On 32 Sample Cases**: Emits `VERIFY_RECORD_ABSENT` for `account_006` in `case_06`. Increases Exact Sequence Accuracy from 13/32 (40.62%) to 14/32 (43.75%). Retains 100.00% Semantic Precision.
     - **On 518 Evaluation Cases**: Zero rows in `customer_search_primary_20260910.sql` match any email in `dataset/deletion_requests.csv` (the other two rows are `jonas.berglund@outlook.com` and `joana.berg@outlook.com`). The 518-case output is **100% identical**.
   - *Action*: In accordance with Stage 3.6 safety rules ("Do not apply the fix to the release candidate in this stage"), this fix is documented and ready for post-promotion incorporation if desired.

---

## 2. Investigation of case_07, case_08, and case_10

A comprehensive, multi-parser audit was conducted across all 94 evidence files, `system_activity.csv`, `user_audit_log.csv`, and `user_identities.csv`:

### 2.1 case_07 (`priya.raman@gmail.com`)
- **Direct User/Account Mappings**: None. `user_identities.csv` has `user_007` with `priya.raman@gmail.com`, but contains no `account_id` column.
- **Database Rows**: `customer_accounts_failover_replica_20260902.sql` contains an account row for `Priya Ramanathan` (`p.ramanathan@gmail.com`, `account_7204`). This is a different person with a different email and phone number; it is not the target user.
- **Service Exports**: `delivery_correction_attachment.pdf` (`evidence_58`) confirms support ticket `support_001` belongs to `Priya Raman`, but mentions no account ID.
- **Worker Events**: `activity_3590` reports `account_007` deletion, but details are generic (`"Deletion worker reported the requested operation as completed. Target resource: account_007."`). During the case's window, 8 concurrent deletion workers ran in parallel, 5 of which were `SUCCESS`.
- **Conclusion**: There is no evidence associating `account_007` with `priya.raman@gmail.com` other than the shared suffix digits. Retaining the grounded behavior (refusing to emit ungrounded account verification) is correct.

### 2.2 case_08 (`gabriel.costa@proton.me`)
- **Direct User/Account Mappings**: None in any catalog or database table.
- **Service Exports**: `customer_export_jobs_20260914.json` (`evidence_59`) contains export job `export_001` owned by `gabriel.costa@proton.me`. It contains no account ID.
- **Worker Events**: `activity_3554` reports `account_008` deletion with generic details. During the case's window, 4 concurrent workers ran in parallel (`account_5482`, `account_7012`, `account_3866`, `account_008`).
- **Conclusion**: `account_008` is not grounded in evidence. Retaining grounded behavior is correct.

### 2.3 case_10 (`nadia.ionescu@yahoo.com`)
- **Direct User/Account Mappings**: None.
- **Log Traces**: `support_replica.log` (`evidence_61`) traces `nadia.ionescu@yahoo.com` to historical alias `nadia.popescu@yahoo.com` and ticket `support_5914`. It contains no account ID.
- **Worker Events**: `activity_3595` reports `account_010` deletion with generic details. During the window, 7 concurrent workers executed simultaneously.
- **Conclusion**: `account_010` is not grounded in evidence. Retaining grounded behavior is correct.

---

## 3. Verification of the Ten Previously Ambiguous Cases

We verified that the grounding patch did not inadvertently remove valid findings or verifications across the ten previously ambiguous cases: `case_09`, `case_18`, `case_20`, `case_22`, `case_23`, `case_25`, `case_28`, `case_29`, `case_31`, `case_32`.

### 3.1 Categorization of Evidence States

| Case ID | User Email | Account Identity State | Other Systems Identity & State | Grounding Patch Action |
| :--- | :--- | :--- | :--- | :--- |
| **case_09** | `k.appiah88@gmail.com` | **No identity available** (Worker pool ambiguous) | **Established**: `backup_4978` (RESTORE RISK) in `evidence_60` | Removed wrong `account_061`. Retained backup finding & verification. |
| **case_18** | `mori.ren@gmail.com` | **No identity available** (Worker pool ambiguous) | **Established**: `search_4013`, `analytics_037`, `support_5569`, `data_flow_4890` | Removed wrong `account_050`. Retained 4 findings, 4 remediations, 4 verifications. |
| **case_20** | `akosua.gyasi@gmail.com` | **No identity available** (Worker pool ambiguous) | **Established**: `search_4262`, `data_flow_1770` | Removed wrong `account_048`. Retained 2 findings, 2 remediations, 2 verifications. |
| **case_22** | `seoyeon-han@gmail.com` | **No identity available** (Worker pool ambiguous) | **Established**: `search_8911`, `analytics_4440`, `audit_record_3482` | Removed wrong `account_051`. Retained 2 findings, 2 remediations, 3 verifications. |
| **case_23** | `thandiwe.m6866@zoho.com`| **No identity available** (Worker pool ambiguous) | **Established**: `export_7364`, `search_898`, `audit_record_4128` | Removed wrong `account_023`. Retained 2 findings, 2 remediations, 3 verifications. |
| **case_25** | `s.yoon04@gmail.com` | **No identity available** (Worker pool ambiguous) | **Established**: `audit_record_451` in `user_audit_log.csv` | Removed wrong `account_025`. Retained security verification. |
| **case_28** | `smartinez6461@gmail.com` | **No identity available** (Worker pool ambiguous) | **Established**: `audit_record_9265`, `support_2351`, `data_flow_2337`, `backup_838` | Removed wrong `account_028`. Retained all 4 system verifications. |
| **case_29** | `noah.f438085@outlook.com`| **No identity available** (Worker pool ambiguous) | **Established**: `search_1993`, `support_5281`, `analytics_5208`, `data_flow_3827`, `audit_record_3954` | Removed wrong `account_029`. Retained 4 findings, 4 remediations, 5 verifications. |
| **case_31** | `a.eze08@gmail.com` | **No identity available** (Worker pool ambiguous) | **Established**: `audit_record_6909`, `tombstone_440` | Removed wrong `account_541`. Retained security & identity verifications. |
| **case_32** | `addo.kofi@gmail.com` | **No identity available** (Worker pool ambiguous) | **Established**: `tombstone_9178`, `audit_record_7068` | Removed wrong `account_542`. Retained tombstone finding, remediation, and verifications. |

**Confirmation**: In all 10 cases, the grounding patch removed **only** the speculative account ID. Zero evidence-supported findings or verifications across other systems were affected.

---

## 4. Rechecked Metrics and Evaluation Standards

The independent evaluator was re-run against `scratch/candidate_sample_pred.csv` and `dataset/sample_output.csv`:

- **Status Accuracy**: **100.00% (32/32)**
- **Exact Ordered Sequence Accuracy**: **40.62% (13/32)**
- **Semantic Step Precision**: **100.00% (169/169)** (0 False Positives)
- **Semantic Step Recall**: **87.56% (169/193)** (24 Unobserved Ref Steps)
- **Semantic Step F1-Score**: **93.37%**
- **Strict Step Precision**: **99.41% (168/169)**
- **Strict Step Recall**: **87.05% (168/193)**
- **Strict Step F1-Score**: **92.82%**
- **Key-Aligned Field Accuracy (with penalties)**: **84.90% (1147/1351)**
- **Positional Field Accuracy**: **90.04% (1094/1215)**

### 4.1 Separation of Benchmark Reference Agreement vs. Evidence Grounding
- **Reference Agreement**: Compares engine output against `sample_output.csv`. The reference answers contain documented anomalies, including hallucinated resources not present in the dataset (`account_004`, `audit_record_6645`, `audit_record_5569`) and speculative account assignments from ambiguous worker batches.
- **Evidence Grounding**: Measures whether every emitted finding, remediation, and verification is directly traceable to verified records in the supplied dataset. Under this standard, the candidate engine achieves **100.00% precision**.

---

## 5. Final Decision

The release candidate achieves:
1. Complete elimination of sample-output lookup shortcuts and hardcoded case logic.
2. 100.00% semantic precision with zero speculative hallucinations.
3. 100.00% status accuracy on sample requests and 0 errors / 0 warnings across all 518 candidate cases.
4. Clean isolation and verification of all packaged deliverables.

### Status:
**`READY FOR EXPLICIT PROMOTION APPROVAL`**

*No files have been promoted. Awaiting explicit user authorization before promoting candidate deliverables to the root workspace.*
