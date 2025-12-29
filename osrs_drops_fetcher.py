#!/usr/bin/env python3

import json
from typing import List, Dict, Any
from collections import defaultdict
from osrs_bucket_api import OSRSBucketAPI


class OSRSDropsBucketAPI(OSRSBucketAPI):
    DROPS_FIELDS = [
        'page_name',
        'page_name_sub',
        'item_name',
        'drop_json',
        'rare_drop_table',
    ]

    NPC_FIELDS = [
        'page_name',
        'name',
        'slayer_level',
        'is_members_only',
        'id',
        'combat_level',
    ]

    def __init__(self):
        super().__init__(user_agent='OSRS Drops Fetcher/1.0')

    def fetch_drops(self, max_results: int = None) -> List[Dict[str, Any]]:
        data = self.fetch_bucket('dropsline', self.DROPS_FIELDS)

        if max_results is not None:
            return data[:max_results]
        return data

    def fetch_npc_info(self) -> List[Dict[str, Any]]:
        return self.fetch_bucket('infobox_monster', self.NPC_FIELDS)

    def parse_drop_json(self, drop_json_str: str) -> Dict[str, Any]:
        try:
            return json.loads(drop_json_str)
        except (json.JSONDecodeError, TypeError):
            return {}

    def merge_drops_with_npcs(self, drops: List[Dict], npc_info: List[Dict]) -> List[Dict[str, Any]]:
        print("Merging drops with NPC data...")

        npc_lookup = {}
        for npc in npc_info:
            page_name = npc.get('page_name', '')
            npc_lookup[page_name] = npc

        npc_drops_map = defaultdict(lambda: {'regular': [], 'rare_drop_table': []})

        drops_processed = 0
        drops_filtered = 0
        drops_unmatched = 0

        for drop_entry in drops:
            drop_data = self.parse_drop_json(drop_entry.get('drop_json', ''))

            if not drop_data:
                continue

            drop_type = drop_data.get('Drop type', '')
            if drop_type != 'combat':
                drops_filtered += 1
                continue

            page_name = drop_entry.get('page_name', '')

            if page_name not in npc_lookup:
                drops_unmatched += 1
                continue

            drops_processed += 1
            is_rare_drop_table = 'rare_drop_table' in drop_entry

            drop_obj = {
                'name': drop_data.get('Dropped item', ''),
                'rarity': drop_data.get('Rarity', ''),
                'quantity': drop_data.get('Drop Quantity', ''),
            }

            if is_rare_drop_table:
                npc_drops_map[page_name]['rare_drop_table'].append(drop_obj)
            else:
                npc_drops_map[page_name]['regular'].append(drop_obj)

        print(f"  Processed {drops_processed} combat drops")
        print(f"  Filtered {drops_filtered} non-combat drops")
        print(f"  Unmatched {drops_unmatched} drops (NPC not found)")

        output_npcs = []

        for npc_data in npc_info:
            page_name = npc_data.get('page_name', '')

            drops_data = npc_drops_map.get(page_name, {'regular': [], 'rare_drop_table': []})

            slayer_level = npc_data.get('slayer_level', None)
            if slayer_level is None or slayer_level == '':
                slayer_level = 1

            npc_obj = {
                'name': npc_data.get('name', page_name),
                'id': npc_data.get('id', None),
                'combat_level': npc_data.get('combat_level', None),
                'slayer_level': slayer_level,
                'is_members_only': 'is_members_only' in npc_data,
                'drops': drops_data
            }

            output_npcs.append(npc_obj)

        npcs_with_drops = sum(1 for npc in output_npcs if npc['drops']['regular'] or npc['drops']['rare_drop_table'])
        print(f"  Created {len(output_npcs)} total NPCs ({npcs_with_drops} with drops)")

        return output_npcs

    def save_to_json(self, data: Any, filename: str = "data/osrs_npc_drops.json"):
        super().save_to_json(data, filename)


def main():
    api = OSRSDropsBucketAPI()

    print("=" * 60)
    print("OSRS NPC Drops Fetcher")
    print("=" * 60)
    print()

    drops = api.fetch_drops()
    npc_info = api.fetch_npc_info()

    if drops and npc_info:
        merged_data = api.merge_drops_with_npcs(drops, npc_info)

        api.save_to_json(merged_data)

        print(f"\n--- Summary ---")
        print(f"Total drops fetched: {len(drops)}")
        print(f"Total NPCs: {len(merged_data)}")
        npcs_with_drops = sum(1 for npc in merged_data if npc['drops']['regular'] or npc['drops']['rare_drop_table'])
        print(f"Total NPCs with drops: {npcs_with_drops}")
    else:
        print("No data retrieved")


if __name__ == "__main__":
    main()
