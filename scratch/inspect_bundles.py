import json

for p in ['dataset/evidence/records/customer_data_snapshot_bundle_20260915.json', 'dataset/evidence/records/customer_data_snapshot_bundle_20260917.json']:
    print(f"\n==================== {p} ====================")
    with open(p, 'r', encoding='utf-8') as f:
        data = json.load(f)
        for s in data.get('snapshots', []):
            store = s.get('data_store')
            recs = s.get('records', [])
            print(f"Store: {store} ({len(recs)} records)")
            for r in recs[:3]:
                print(f"  {r}")
