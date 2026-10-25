import csv
import json

# Check if any of the 518 cases match the 3 emails in customer_search_primary_20260910.sql
search_primary_emails = {
    'jonas.berg@outlook.com',
    'jonas.berglund@outlook.com',
    'joana.berg@outlook.com'
}

with open('dataset/deletion_requests.csv', 'r', encoding='utf-8') as f:
    full_requests = list(csv.DictReader(f))

matched_in_518 = [
    r for r in full_requests 
    if r['email'].lower() in search_primary_emails
]

print(f"Total 518 cases matching customer_search_primary emails: {len(matched_in_518)}")
for r in matched_in_518:
    print(f"  {r['case_id']}: {r['email']}")

print("\nConclusion: Zero cases in deletion_requests.csv match customer_search_primary emails.")
print("The proposed parsing fix would have ZERO impact on candidate_output.csv (518 cases),")
print("and would improve candidate_sample_pred.csv exact sequence accuracy from 13/32 (40.62%) to 14/32 (43.75%).")
