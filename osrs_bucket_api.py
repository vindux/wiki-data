#!/usr/bin/env python3

import json
import re
import time
from typing import Any, Dict, List

import requests


class OSRSBucketAPI:

    BASE_URL = "https://oldschool.runescape.wiki/api.php"

    # The wiki renames and removes bucket fields without notice, and a single
    # stale name fails the entire query: "Field foo not found in bucket bar."
    UNKNOWN_FIELD_PATTERN = re.compile(r"Field (\w+) not found in bucket")

    # When a template can't parse a parameter it renders a red "ERR" span
    # instead of omitting the value, which would otherwise be stored as data.
    ERROR_SPAN_PATTERN = re.compile(r'<span[^>]*>\s*ERR\s*</span>', re.IGNORECASE)

    MAX_ATTEMPTS = 3

    def __init__(self, user_agent: str = "OSRS Wiki Fetcher/1.0"):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent
        })

    @classmethod
    def strip_error_values(cls, value: Any) -> Any:
        if isinstance(value, str):
            return None if cls.ERROR_SPAN_PATTERN.search(value) else value
        if isinstance(value, list):
            cleaned = [cls.strip_error_values(item) for item in value]
            return [item for item in cleaned if item is not None]
        return value

    @classmethod
    def sanitize_record(cls, record: Dict[str, Any]) -> Dict[str, Any]:
        return {key: cls.strip_error_values(value) for key, value in record.items()}

    def run_query(self, query: str) -> Dict[str, Any]:
        params = {
            'action': 'bucket',
            'query': query,
            'format': 'json'
        }

        last_error = None

        for attempt in range(1, self.MAX_ATTEMPTS + 1):
            try:
                response = self.session.get(self.BASE_URL, params=params, timeout=30)
                response.raise_for_status()
                return response.json()
            except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
                last_error = e
                if attempt < self.MAX_ATTEMPTS:
                    delay = 2 ** attempt
                    print(f"\n  Request failed ({e}); retrying in {delay}s...", end=' ')
                    time.sleep(delay)

        raise RuntimeError(f"Query failed after {self.MAX_ATTEMPTS} attempts: {query}") from last_error

    def resolve_fields(self, bucket_name: str, fields: List[str]) -> List[str]:
        remaining = list(fields)

        while remaining:
            fields_str = ','.join(f"'{field}'" for field in remaining)
            data = self.run_query(f"bucket('{bucket_name}').select({fields_str}).limit(1).run()")

            error = data.get('error')
            if not error:
                return remaining

            match = self.UNKNOWN_FIELD_PATTERN.search(str(error))
            if not match or match.group(1) not in remaining:
                raise Exception(f"API Error: {error}")

            missing = match.group(1)
            print(f"  WARNING: bucket '{bucket_name}' has no field '{missing}' anymore - skipping it")
            remaining.remove(missing)

        raise Exception(f"No known fields remain for bucket '{bucket_name}'")

    def fetch_bucket(self, bucket_name: str, fields: List[str], limit: int = 500) -> List[Dict[str, Any]]:
        print(f"Fetching {bucket_name} data from OSRS Wiki...")

        fields_str = ','.join(f"'{field}'" for field in self.resolve_fields(bucket_name, fields))

        all_results = []
        offset = 0

        while True:
            query = f"bucket('{bucket_name}').select({fields_str}).limit({limit}).offset({offset}).run()"

            print(f"  Fetching batch: offset={offset}, limit={limit}...", end=' ')

            data = self.run_query(query)

            if 'error' in data:
                raise Exception(f"API Error: {data['error']}")

            if 'bucket' not in data:
                raise Exception(f"Unexpected response format for bucket '{bucket_name}': {sorted(data)}")

            results = [self.sanitize_record(record) for record in data['bucket']]
            print(f"Got {len(results)} records")

            if not results:
                break

            all_results.extend(results)
            offset += len(results)

            if len(results) < limit:
                break

        print(f"  Total fetched: {len(all_results)}\n")
        return all_results

    def save_to_json(self, data: Any, filename: str, indent: int = 2):
        import os
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)
        print(f"Data saved to {filename}")
