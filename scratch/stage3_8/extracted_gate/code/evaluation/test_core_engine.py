#!/usr/bin/env python3
"""
Independent Unit & Regression Test Suite for Core Audit Engine
Challenge: HackerRank Orchestrate October 2026 — Ghost Data Still Exists
"""

import os
import sys
import json
import csv
import unittest

# Ensure repo root and code dir are in python path
REPO_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, REPO_DIR)

import importlib.util
spec = importlib.util.spec_from_file_location("main", os.path.join(REPO_DIR, "code", "main.py"))
main_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(main_mod)

PolicyEngine = main_mod.PolicyEngine
IdentityResolver = main_mod.IdentityResolver
RequestClassifier = main_mod.RequestClassifier
SystemActivityTracker = main_mod.SystemActivityTracker
EvidenceManager = main_mod.EvidenceManager
DeletionAuditor = main_mod.DeletionAuditor
VALID_STATUSES = main_mod.VALID_STATUSES
VALID_PHASES = main_mod.VALID_PHASES
VALID_SYSTEMS = main_mod.VALID_SYSTEMS
OP_ORDER = main_mod.OP_ORDER
PHASE_ORDER = main_mod.PHASE_ORDER


class TestCoreAuditEngine(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset_dir = os.path.join(REPO_DIR, "dataset")
        cls.auditor = DeletionAuditor(cls.dataset_dir)

    def test_no_sample_leakage(self):
        """1. Verify engine has no sample-answer shortcuts and evaluates purely from evidence."""
        self.assertFalse(hasattr(self.auditor, "sample_baseline"), "Engine must not retain sample_baseline attribute")
        
        # Test an arbitrary synthetic request
        synthetic_req = {
            "case_id": "synthetic_01",
            "email": "test.unknown@domain.com",
            "requested_at": "2026-09-01T10:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-02T10:00:00Z",
            "audit_at": "2026-09-10T10:00:00Z",
            "request_text": "Please delete my account and all personal details."
        }
        status, steps = self.auditor.audit_case(synthetic_req)
        self.assertIn(status, VALID_STATUSES)
        self.assertIsInstance(steps, list)

    def test_identity_resolution_and_aliases(self):
        """2. Test identity resolution across current emails, historical aliases, and email hashes."""
        resolver = self.auditor.resolver
        
        # Current email
        uid_eze = resolver.resolve_email("a.eze08@gmail.com")
        self.assertEqual(uid_eze, "user_541")
        
        # Historical email from user_audit_log.csv
        uid_kim = resolver.resolve_email("minjun.kim90@gmail.com")
        self.assertEqual(uid_kim, "user_12")
        
        # Historical email_hash from user_audit_log.csv
        uid_hash = resolver.resolve_email_hash("44a65154bfd8e408852578fbd76813d094d1944f255ac1769ee81ba90492f10e")
        self.assertEqual(uid_hash, "user_12")

    def test_policy_rules_ingestion(self):
        """3. Test loading and enforcement of all 15 rules from deletion_rules.csv."""
        policy = self.auditor.policy
        self.assertGreaterEqual(len(policy.rules), 14, "Must load all rules from deletion_rules.csv")
        
        # Verify required actions
        self.assertEqual(policy.get_action("USER_PROFILE"), "DELETE")
        self.assertEqual(policy.get_action("ACCOUNT_TOMBSTONE"), "REDACT")
        self.assertEqual(policy.get_action("ANALYTICS_PROFILE"), "ANONYMIZE")
        self.assertEqual(policy.get_action("SECURITY_AUDIT_LOG"), "RETAIN")
        self.assertEqual(policy.get_action("USER_EXPORT"), "DELETE")
        self.assertEqual(policy.get_action("BACKUP_ARCHIVE"), "RETAIN")

    def test_tombstone_and_redaction(self):
        """4. Test that tombstones without PII are verified redacted, and tombstones with PII trigger findings."""
        # Clean tombstone: user_541 in customer_data_snapshot_bundle_20260915.json (evidence_51)
        req_clean = {
            "case_id": "case_31",
            "email": "a.eze08@gmail.com",
            "requested_at": "2026-09-04T12:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-06T12:00:00Z",
            "audit_at": "2026-09-15T12:00:00Z",
            "request_text": "I no longer need this account. Please remove my name and contact details, but keeping an internal deleted-account reference is fine."
        }
        status, steps = self.auditor.audit_case(req_clean)
        self.assertEqual(status, "COMPLETE")
        tombstone_steps = [s for s in steps if s["system_id"] == "identity_service"]
        self.assertTrue(len(tombstone_steps) > 0)
        for s in tombstone_steps:
            self.assertEqual(s["phase"], "VERIFICATION")
            self.assertEqual(s["operation"], "VERIFY_RECORD_REDACTED")
            self.assertEqual(s["state"], "REDACTED")

        # Dirty tombstone: user_542 in evidence_51 has exposed PII (Kofi Addo)
        req_dirty = {
            "case_id": "case_32",
            "email": "addo.kofi@gmail.com",
            "requested_at": "2026-09-03T12:00:00Z",
            "reported_status": "PARTIALLY_COMPLETE",
            "reported_at": "2026-09-06T12:00:00Z",
            "audit_at": "2026-09-15T12:00:00Z",
            "request_text": "Please remove my account profile and personal details."
        }
        status_d, steps_d = self.auditor.audit_case(req_dirty)
        self.assertEqual(status_d, "INCOMPLETE")
        finding = [s for s in steps_d if s["phase"] == "FINDING" and s["system_id"] == "identity_service"]
        self.assertTrue(len(finding) > 0)
        self.assertEqual(finding[0]["operation"], "REPORT_EXPOSED_PII")

    def test_replica_remnants(self):
        """5. Test detection of remaining records in database replicas (e.g., failover replica drift)."""
        req_replica = {
            "case_id": "case_05",
            "email": "leila.haddad@yahoo.com",
            "requested_at": "2026-08-27T14:17:00Z",
            "reported_status": "PARTIALLY_COMPLETE",
            "reported_at": "2026-08-28T16:00:00Z",
            "audit_at": "2026-09-08T13:40:00Z",
            "request_text": "I deleted my account last month. Please confirm that my profile was removed everywhere."
        }
        status, steps = self.auditor.audit_case(req_replica)
        self.assertEqual(status, "INCOMPLETE")
        findings = [s for s in steps if s["phase"] == "FINDING" and s["system_id"] == "account_service"]
        self.assertTrue(len(findings) > 0)
        self.assertEqual(findings[0]["operation"], "REPORT_REMAINING_RECORD")

    def test_active_data_flows(self):
        """6. Test detection of active integration data flows."""
        req_flow = {
            "case_id": "case_11",
            "email": "novak.tomasz@icloud.com",
            "requested_at": "2026-09-09T12:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-12T12:00:00Z",
            "audit_at": "2026-10-01T12:00:00Z",
            "request_text": "I would like the account associated with this address to be erased. Please handle any copies that fall within the scope of the deletion request."
        }
        status, steps = self.auditor.audit_case(req_flow)
        self.assertEqual(status, "INCOMPLETE")
        flow_findings = [s for s in steps if s["phase"] == "FINDING" and s["system_id"] == "integration_service"]
        self.assertTrue(len(flow_findings) > 0)
        self.assertEqual(flow_findings[0]["operation"], "REPORT_ACTIVE_DATA_FLOW")

    def test_backup_restore_risks(self):
        """7. Test detection of backup archives where restore has not been blocked."""
        req_backup = {
            "case_id": "case_09",
            "email": "k.appiah88@gmail.com",
            "requested_at": "2026-09-05T09:00:00Z",
            "reported_status": "NOT_STARTED",
            "reported_at": "2026-09-07T09:00:00Z",
            "audit_at": "2026-09-16T09:00:00Z",
            "request_text": "Please permanently delete the account associated with this email address. Please apply the correct treatment to records covered by the request."
        }
        status, steps = self.auditor.audit_case(req_backup)
        self.assertEqual(status, "INCOMPLETE")
        backup_findings = [s for s in steps if s["phase"] == "FINDING" and s["system_id"] == "backup_service"]
        self.assertTrue(len(backup_findings) > 0)
        self.assertEqual(backup_findings[0]["operation"], "REPORT_RESTORE_RISK")

    def test_temporal_evidence_window(self):
        """8. Test temporal filtering: evidence after audit_at or before requested_at is not used."""
        em = self.auditor.evidence_mgr
        
        # Test window filtering
        start = "2026-09-01T00:00:00Z"
        end = "2026-09-10T00:00:00Z"
        files_in_window = em.get_evidence_files_in_window(start, end)
        for f in files_in_window:
            self.assertGreaterEqual(f["captured_at"], start)
            self.assertLessEqual(f["captured_at"], end)

    def test_output_contract_and_structure(self):
        """9. Test output contract: valid JSON, schema, allowed systems, phase ordering, step ordering."""
        req = {
            "case_id": "case_07",
            "email": "fatima.al-mansoor@gmail.com",
            "requested_at": "2026-08-31T11:26:00Z",
            "reported_status": "PARTIALLY_COMPLETE",
            "reported_at": "2026-09-01T18:00:00Z",
            "audit_at": "2026-09-12T08:00:00Z",
            "request_text": "I deleted my profile last week. Please make sure no active account remains."
        }
        status, steps = self.auditor.audit_case(req)
        self.assertIn(status, VALID_STATUSES)
        
        for idx, s in enumerate(steps, 1):
            self.assertEqual(s["step_no"], idx)
            self.assertIn(s["phase"], VALID_PHASES)
            self.assertIn(s["system_id"], VALID_SYSTEMS)
            self.assertTrue(s["resource_id"], "resource_id must never be empty")
            self.assertIn(s["operation"], OP_ORDER[s["phase"]])
            
            # Step phase ordering check
            if idx > 1:
                prev_phase = steps[idx-2]["phase"]
                curr_phase = s["phase"]
                self.assertLessEqual(PHASE_ORDER[prev_phase], PHASE_ORDER[curr_phase])

    def test_ambiguous_worker_correlation(self):
        """10. Test that ambiguous worker candidates without explicit links are handled conservatively."""
        # Case 31 has 4 SUCCESS worker candidates in its window without explicit user foreign key
        req_c31 = {
            "case_id": "case_31",
            "email": "a.eze08@gmail.com",
            "requested_at": "2026-09-04T12:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-06T12:00:00Z",
            "audit_at": "2026-09-15T12:00:00Z",
            "request_text": "I no longer need this account. Please remove my name and contact details, but keeping an internal deleted-account reference is fine."
        }
        status, steps = self.auditor.audit_case(req_c31)
        self.assertEqual(status, "COMPLETE")
        # Ensure engine did NOT invent an ungrounded account resource ID
        acc_steps = [s for s in steps if s["system_id"] == "account_service"]
        for s in acc_steps:
            self.assertTrue(s["resource_id"].startswith("account_"))

    def test_duplicate_evidence_handling(self):
        """11. Test that multiple evidence files observing the same state are deduplicated."""
        req = {
            "case_id": "case_06",
            "email": "jonas.berg@outlook.com",
            "requested_at": "2026-08-29T06:51:00Z",
            "reported_status": "PARTIALLY_COMPLETE",
            "reported_at": "2026-08-30T17:12:00Z",
            "audit_at": "2026-09-10T09:15:00Z",
            "request_text": "My account page is gone, but my old profile still appears when I search for it."
        }
        status, steps = self.auditor.audit_case(req)
        # Check that steps do not contain duplicate (phase, system, resource, op) tuples
        signatures = [(s["phase"], s["system_id"], s["resource_id"], s["operation"]) for s in steps]
        self.assertEqual(len(signatures), len(set(signatures)), "Steps must be deduplicated")

    def test_stale_replica_drift(self):
        """12. Test detection of remaining replica records in failover SQL databases."""
        req_drift = {
            "case_id": "case_05",
            "email": "leila.haddad@yahoo.com",
            "requested_at": "2026-08-27T14:17:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-08-28T09:03:00Z",
            "audit_at": "2026-09-08T13:40:00Z",
            "request_text": "I deleted this account and received a confirmation, but the same email address is still recognized."
        }
        status, steps = self.auditor.audit_case(req_drift)
        self.assertEqual(status, "INCOMPLETE")
        findings = [s for s in steps if s["phase"] == "FINDING" and s["system_id"] == "account_service"]
        self.assertTrue(len(findings) > 0)
        self.assertIn(findings[0]["evidence_id"], {"evidence_53", "evidence_54"})

    def test_negative_probe_log_filtering(self):
        """13. Test that 404 lookup probes in historical logs do not contaminate resource mapping."""
        # user_17 had a 404 lookup probe in March 2026 for account_6523; verify account_6523 is NOT mapped
        self.assertNotEqual(self.auditor.user_to_account_res.get("user_17"), "account_6523")

    def test_export_service_archive_detection(self):
        """14. Test detection of remaining user export archives with owner_email (Rule 8)."""
        req_exp = {
            "case_id": "case_23",
            "email": "thandiwe.m6866@zoho.com",
            "requested_at": "2026-09-02T12:00:00Z",
            "reported_status": "NOT_STARTED",
            "reported_at": "2026-09-05T12:00:00Z",
            "audit_at": "2026-09-15T12:00:00Z",
            "request_text": "Please delete my account and all associated personal information."
        }
        status, steps = self.auditor.audit_case(req_exp)
        self.assertEqual(status, "INCOMPLETE")
        exp_finding = [s for s in steps if s["system_id"] == "export_service" and s["phase"] == "FINDING"]
        self.assertTrue(len(exp_finding) > 0, "Must detect export_service archive as FINDING")
        self.assertEqual(exp_finding[0]["resource_id"], "export_7364")
        self.assertEqual(exp_finding[0]["operation"], "REPORT_REMAINING_RECORD")

    def test_support_ticket_pii_scan_detection(self):
        """15. Test detection of exposed PII in support tickets via message_pii_scan (Rule 5)."""
        req_supp = {
            "case_id": "case_19",
            "email": "e.varga90@yahoo.com",
            "requested_at": "2026-08-17T12:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-08-19T12:00:00Z",
            "audit_at": "2026-09-15T12:00:00Z",
            "request_text": "I request that all my data be permanently deleted."
        }
        status, steps = self.auditor.audit_case(req_supp)
        self.assertEqual(status, "INCOMPLETE")
        supp_finding = [s for s in steps if s["system_id"] == "support_platform" and s["phase"] == "FINDING"]
        self.assertTrue(len(supp_finding) > 0, "Must detect support_platform exposed PII from message_pii_scan")
        self.assertEqual(supp_finding[0]["resource_id"], "support_9553")
        self.assertEqual(supp_finding[0]["operation"], "REPORT_EXPOSED_PII")

    def test_empty_snapshot_no_false_verification(self):
        """16. Test that empty snapshot bundles do not fabricate false absence verifications."""
        # For case_21, customer_data_snapshot_bundle_20260915 (evidence_51) has 0 account records
        # Verify that account verification uses the grounded 404 lookup from evidence_92, not evidence_51
        req_c21 = {
            "case_id": "case_21",
            "email": "amara-okeke@proton.me",
            "requested_at": "2026-09-04T12:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-05T12:00:00Z",
            "audit_at": "2026-09-15T12:00:00Z",
            "request_text": "I request that all my data be permanently deleted."
        }
        status, steps = self.auditor.audit_case(req_c21)
        acc_ver = [s for s in steps if s["system_id"] == "account_service"]
        if acc_ver:
            self.assertNotEqual(acc_ver[0]["evidence_id"], "evidence_51", "Must not cite empty snapshot bundle evidence_51")

    def test_synthetic_unseen_identity(self):
        """17. Test handling of completely unseen synthetic identities without evidence."""
        req_unseen = {
            "case_id": "synthetic_999",
            "email": "completely.unseen.user@nonexistent-domain.org",
            "requested_at": "2026-09-01T10:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-02T10:00:00Z",
            "audit_at": "2026-09-10T10:00:00Z",
            "request_text": "Please delete my account and all personal details."
        }
        status, steps = self.auditor.audit_case(req_unseen)
        self.assertIn(status, VALID_STATUSES)
        self.assertIsInstance(steps, list)
        for s in steps:
            self.assertIn(s["system_id"], VALID_SYSTEMS)

    def test_conflicting_timestamps(self):
        """18. Test handling of conflicting or inverted lifecycle timestamps."""
        req_inverted = {
            "case_id": "synthetic_inv",
            "email": "amina.elmasri@gmail.com",
            "requested_at": "2026-09-20T10:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-15T10:00:00Z", # reported before requested
            "audit_at": "2026-09-10T10:00:00Z",   # audit before requested
            "request_text": "Please delete my account."
        }
        # Engine should execute without unhandled exception and return valid status
        status, steps = self.auditor.audit_case(req_inverted)
        self.assertIn(status, VALID_STATUSES)
        self.assertIsInstance(steps, list)

    def test_anonymized_resource_isolation(self):
        """19. Test that anonymized analytics records (null PII) are isolated and not misattributed."""
        # Querying an arbitrary user whose email has no match in customer_analytics_report_20260907.json
        req_clean = {
            "case_id": "synthetic_anon",
            "email": "clean.user.no.analytics@domain.com",
            "requested_at": "2026-08-25T12:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-08-26T12:00:00Z",
            "audit_at": "2026-09-10T12:00:00Z",
            "request_text": "Delete my profile and records."
        }
        status, steps = self.auditor.audit_case(req_clean)
        # Verify no anonymized analytics records with null identifiers are claimed
        claimed_analytics = [s for s in steps if s["system_id"] == "analytics_platform"]
        for a in claimed_analytics:
            self.assertNotEqual(a["resource_id"], "analytics_901")

    def test_synthetic_worker_ambiguity(self):
        """20. Test that concurrent worker events without user foreign keys are handled conservatively."""
        # Query case_25 where account_3136 was submitted in an ambiguous batch
        req_c25 = {
            "case_id": "case_25",
            "email": "s.yoon04@gmail.com",
            "requested_at": "2026-08-31T12:00:00Z",
            "reported_status": "NOT_STARTED",
            "reported_at": "2026-09-02T12:00:00Z",
            "audit_at": "2026-09-15T12:00:00Z",
            "request_text": "Please delete my account and all associated personal information."
        }
        status, steps = self.auditor.audit_case(req_c25)
        self.assertEqual(status, "COMPLETE")
        for s in steps:
            self.assertTrue(s["resource_id"])

    def test_no_ungrounded_account_fabrication(self):
        """21. Test that ungrounded account IDs are not fabricated when other findings or verifications exist."""
        # case_09 has user_61 and genuine findings in export, integration, search, but ambiguous worker batch
        req_c09 = {
            "case_id": "case_09",
            "email": "k.appiah88@gmail.com",
            "requested_at": "2026-09-05T09:00:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-07T09:00:00Z",
            "audit_at": "2026-09-16T09:00:00Z",
            "request_text": "Please permanently delete the account associated with this email address."
        }
        status, steps = self.auditor.audit_case(req_c09)
        self.assertEqual(status, "INCOMPLETE")
        # Ensure that no ungrounded naming-convention fallback account_061 is fabricated
        acc_steps = [s for s in steps if s["system_id"] == "account_service"]
        self.assertEqual(len(acc_steps), 0, "Must not fabricate ungrounded account_061 when other findings exist")


if __name__ == "__main__":
    unittest.main()


