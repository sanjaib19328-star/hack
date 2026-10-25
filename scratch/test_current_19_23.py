import importlib.util

spec = importlib.util.spec_from_file_location("engine", "code/main.py")
engine = importlib.util.module_from_spec(spec)
spec.loader.exec_module(engine)

audit = engine.DeletionAuditor("dataset")

print("--- Testing case_19 with current engine ---")
req_19 = {
    'case_id': 'case_19',
    'email': 'e.varga90@yahoo.com',
    'requested_at': '2026-08-17T12:00:00Z',
    'reported_at': '2026-08-19T12:00:00Z',
    'audit_at': '2026-09-15T12:00:00Z',
    'request_text': 'I request that all my data be permanently deleted.'
}
status, steps = audit.audit_case(req_19)
print(f"case_19 status: {status}, steps count: {len(steps)}")
for s in steps:
    print(f"  [{s['phase']}] sys={s['system_id']} res={s['resource_id']} op={s['operation']} ev={s['evidence_id']}")

print("\n--- Testing case_23 with current engine ---")
req_23 = {
    'case_id': 'case_23',
    'email': 'thandiwe.m6866@zoho.com',
    'requested_at': '2026-09-02T12:00:00Z',
    'reported_at': '2026-09-05T12:00:00Z',
    'audit_at': '2026-09-15T12:00:00Z',
    'request_text': 'Please delete my account and all associated personal information.'
}
status, steps = audit.audit_case(req_23)
print(f"case_23 status: {status}, steps count: {len(steps)}")
for s in steps:
    print(f"  [{s['phase']}] sys={s['system_id']} res={s['resource_id']} op={s['operation']} ev={s['evidence_id']}")
