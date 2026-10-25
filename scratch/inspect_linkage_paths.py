import json, re

print("--- Inspecting case_03: analytics_9406 in resource_lookup_trace_20260926_103856.log ---")
with open("dataset/evidence/logs/resource_lookup_trace_20260926_103856.log", "r", encoding="utf-8") as f:
    for line in f:
        if "analytics_9406" in line:
            print(line.strip())

print("\n--- Inspecting case_04: analytics_901 in customer_analytics_report_20260907.json ---")
with open("dataset/evidence/records/customer_analytics_report_20260907.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    for rec in data.get("records", []):
        if rec.get("resource_id") == "analytics_901":
            print(json.dumps(rec))

print("\n--- Inspecting case_09: account_3960 and audit_record_4902 in structured_service_events_eu_west_20260918.log ---")
with open("dataset/evidence/logs/structured_service_events_eu_west_20260918.log", "r", encoding="utf-8") as f:
    for line in f:
        if "account_3960" in line or "audit_record_4902" in line:
            print(line.strip()[:140])

print("\n--- Inspecting case_19: support_9553 in service_events_ap_south_20260915.log ---")
with open("dataset/evidence/logs/service_events_ap_south_20260915.log", "r", encoding="utf-8") as f:
    for line in f:
        if "support_9553" in line:
            print(line.strip())

print("\n--- Inspecting case_23: export_7364 in customer_data_snapshot_bundle_20260917.json and service_resource_export_20260915_114455.json ---")
with open("dataset/evidence/records/customer_data_snapshot_bundle_20260917.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    for rec in data.get("records", []):
        if rec.get("resource_id") == "export_7364":
            print("bundle:", json.dumps(rec))
with open("dataset/evidence/records/service_resource_export_20260915_114455.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    for rec in data.get("records", []):
        if rec.get("resource_id") == "export_7364":
            print("service_export:", json.dumps(rec))

print("\n--- Inspecting case_25, 26, 27, 28: analytics resources in customer_data_snapshot_bundle_20260917.json ---")
with open("dataset/evidence/records/customer_data_snapshot_bundle_20260917.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    for rec in data.get("records", []):
        if rec.get("resource_id") in ["analytics_1895", "analytics_4566", "analytics_4574", "analytics_6077"]:
            print(json.dumps(rec))
