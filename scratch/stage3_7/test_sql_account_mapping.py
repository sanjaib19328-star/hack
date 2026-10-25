import unittest
import os
import sys

sys.path.insert(0, os.path.abspath("."))
import scratch.stage3_7.patched_main as patched_engine

class TestSQLAccountMapping(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dataset_dir = os.path.abspath("dataset")
        cls.auditor = patched_engine.DeletionAuditor(cls.dataset_dir)

    def test_sql_mapping_case_06(self):
        """Test 1: Confirms source_resource_id account_006 is grounded via search_documents_primary."""
        user_id = self.auditor.resolver.resolve_email("jonas.berg@outlook.com")
        self.assertEqual(user_id, "user_06")
        acc_res = self.auditor.user_to_account_res.get(user_id)
        self.assertEqual(acc_res, "account_006")

    def test_identity_mismatch_isolation(self):
        """Test 2: Confirms identity mismatch does not pollute another user's account mapping."""
        # jonas.berglund@outlook.com has account_8814 in search_documents_primary
        # Ensure user_06 does not receive account_8814
        user_id_06 = self.auditor.resolver.resolve_email("jonas.berg@outlook.com")
        acc_res_06 = self.auditor.user_to_account_res.get(user_id_06)
        self.assertNotEqual(acc_res_06, "account_8814")
        self.assertEqual(acc_res_06, "account_006")

    def test_missing_mapping_unpolluted(self):
        """Test 3: Confirms user without search_documents_primary entry does not get an account mapped."""
        # user_007 (priya.raman@gmail.com) has no entry in search_documents_primary
        user_id_007 = self.auditor.resolver.resolve_email("priya.raman@gmail.com")
        acc_res_007 = self.auditor.user_to_account_res.get(user_id_007)
        self.assertIsNone(acc_res_007)

    def test_account_state_verification_absent(self):
        """Test 4: Confirms search finding does not assert account presence; account is correctly verified ABSENT."""
        case_06_row = {
            "case_id": "case_06",
            "email": "jonas.berg@outlook.com",
            "requested_at": "2026-08-29T06:51:00Z",
            "reported_status": "PARTIALLY_COMPLETE",
            "reported_at": "2026-08-30T17:12:00Z",
            "audit_at": "2026-09-10T09:15:00Z",
            "request_text": "My account page is gone, but my old profile still appears when I search for it."
        }
        status, steps = self.auditor.audit_case(case_06_row)
        self.assertEqual(status, "INCOMPLETE")
        # Check that search finding exists
        search_f = [s for s in steps if s["phase"] == "FINDING" and s["system_id"] == "search_service"]
        self.assertEqual(len(search_f), 1)
        self.assertEqual(search_f[0]["resource_id"], "search_001")
        self.assertEqual(search_f[0]["state"], "PRESENT")

        # Check that account verification exists as ABSENT
        acc_v = [s for s in steps if s["phase"] == "VERIFICATION" and s["system_id"] == "account_service"]
        self.assertEqual(len(acc_v), 1)
        self.assertEqual(acc_v[0]["resource_id"], "account_006")
        self.assertEqual(acc_v[0]["state"], "ABSENT")

    def test_numeric_suffix_independence(self):
        """Test 5: Confirms engine does not synthesize account_007 from user_007 digits."""
        case_07_row = {
            "case_id": "case_07",
            "email": "priya.raman@gmail.com",
            "requested_at": "2026-08-31T11:26:00Z",
            "reported_status": "COMPLETE",
            "reported_at": "2026-09-01T19:30:00Z",
            "audit_at": "2026-09-12T08:00:00Z",
            "request_text": "Please delete my account and the identity document."
        }
        status, steps = self.auditor.audit_case(case_07_row)
        # Should not fabricate account_007 verification
        acc_steps = [s for s in steps if s["system_id"] == "account_service" and s["resource_id"] == "account_007"]
        self.assertEqual(len(acc_steps), 0)

if __name__ == "__main__":
    unittest.main()
