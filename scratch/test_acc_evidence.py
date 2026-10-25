import csv, json, os

# Let's inspect what evidence_92 has for account_service
with open("dataset/evidence/records/service_resource_export_20260915_114455.json", "r", encoding="utf-8") as f:
    d = json.load(f)
    acc = d.get("service_exports", {}).get("account_service", {})
    lookups = acc.get("profile_lookups", [])
    print(f"evidence_92 account lookups ({len(lookups)}):")
    for item in lookups:
        print(f"  res={item.get('resource_id')} status={item.get('status_code')} prof={item.get('profile')}")

print("\n--- Let's inspect database replica evidence_54 ---")
# Does evidence_54 cover account_001, account_004?
with open("dataset/evidence/databases/customer_accounts_failover_replica_20260902.sql", "r", encoding="utf-8") as f:
    sql = f.read()
    print("account_001 in ev_54:", "account_001" in sql)
    print("account_004 in ev_54:", "account_004" in sql)
