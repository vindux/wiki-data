#!/usr/bin/env python3

import requests
import json
from typing import List, Dict, Any


class OSRSBucketAPI:

    BASE_URL = "https://oldschool.runescape.wiki/api.php"

    def __init__(self, user_agent: str = "OSRS Wiki Fetcher/1.0"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent
        })

    def fetch_bucket(self, bucket_name: str, fields: List[str], limit: int = 500) -> List[Dict[str, Any]]:
        all_results = []
        offset = 0

        print(f"Fetching {bucket_name} data from OSRS Wiki...")

        while True:
            fields_str = ','.join(f"'{field}'" for field in fields)
            query = f"bucket('{bucket_name}').select({fields_str}).limit({limit}).offset({offset}).run()"

            params = {
                'action': 'bucket',
                'query': query,
                'format': 'json'
            }

            print(f"  Fetching batch: offset={offset}, limit={limit}...", end=' ')

            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()

                if 'error' in data:
                    raise Exception(f"API Error: {data['error']}")

                if 'bucket' in data:
                    results = data['bucket']
                    print(f"Got {len(results)} records")

                    if not results:
                        break

                    all_results.extend(results)
                    offset += len(results)

                    if len(results) < limit:
                        break

                else:
                    print("\nUnexpected response format")
                    break

            except requests.exceptions.RequestException as e:
                print(f"\nRequest failed: {e}")
                break
            except json.JSONDecodeError as e:
                print(f"\nFailed to parse JSON response: {e}")
                break

        print(f"  Total fetched: {len(all_results)}\n")
        return all_results

    def save_to_json(self, data: Any, filename: str, indent: int = 2):
        import os
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        print(f"Data saved to {filename}")
