import csv

# 1. Inspect case_07 match in customer_accounts_failover_replica_20260902.sql
print("=" * 80)
print("1. case_07 in customer_accounts_failover_replica_20260902.sql:")
with open('dataset/evidence/databases/customer_accounts_failover_replica_20260902.sql', 'r', encoding='utf-8', errors='ignore') as f:
    for line in f:
        if 'priya' in line.lower() or 'raman' in line.lower() or 'account_007' in line.lower():
            print("  ", line.strip())

# 2. Inspect case_07 in system_activity.csv
print("\n2. case_07 in system_activity.csv:")
with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if 'priya' in str(r).lower() or 'account_007' in str(r).lower():
            print("  ", r)

# 3. Inspect case_08 in system_activity.csv and customer_export_jobs_20260914.json
print("\n3. case_08 in customer_export_jobs_20260914.json:")
with open('dataset/evidence/records/customer_export_jobs_20260914.json', 'r', encoding='utf-8') as f:
    for line in f:
        if 'gabriel' in line.lower() or 'account_008' in line.lower():
            print("  ", line.strip())

print("\n4. case_08 in system_activity.csv:")
with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if 'gabriel' in str(r).lower() or 'account_008' in str(r).lower():
            print("  ", r)

# 5. Inspect case_10 in support_replica.log and system_activity.csv
print("\n5. case_10 in support_replica.log:")
with open('dataset/evidence/logs/support_replica.log', 'r', encoding='utf-8') as f:
    for line in f:
        if 'nadia' in line.lower() or 'account_010' in line.lower():
            print("  ", line.strip())

print("\n6. case_10 in system_activity.csv:")
with open('dataset/system_activity.csv', 'r', encoding='utf-8') as f:
    for r in csv.DictReader(f):
        if 'nadia' in str(r).lower() or 'account_010' in str(r).lower():
            print("  ", r)
