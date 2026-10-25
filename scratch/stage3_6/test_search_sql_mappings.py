import csv
import json
import os
import re

# Check all search_documents_primary lines in evidence SQL files
sql_files = []
for root, dirs, files in os.walk('dataset/evidence'):
    for f in files:
        if f.endswith('.sql'):
            sql_files.append(os.path.join(root, f))

print(f"Total SQL evidence files: {len(sql_files)}")
mappings = {}
for sf in sql_files:
    with open(sf, 'r', encoding='utf-8', errors='ignore') as f:
        for line in f:
            if 'search_documents' in line and 'VALUES' in line:
                # INSERT INTO "search_documents_primary" VALUES('search_001','Jonas Berg','jonas.berg@outlook.com','account_006','2026-09-09T22:12:00Z');
                tokens = re.findall(r"'([^']*)'", line)
                if len(tokens) >= 4:
                    search_id = tokens[0]
                    name = tokens[1]
                    email = tokens[2].lower()
                    source_res = tokens[3]
                    mappings[email] = (search_id, name, source_res)
                    print(f"  {sf}: email={email}, search_id={search_id}, source_res={source_res}")

print(f"\nTotal mappings from search_documents: {len(mappings)}")
