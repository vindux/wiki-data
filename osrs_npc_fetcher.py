#!/usr/bin/env python3

import csv
import argparse
from typing import List, Dict, Any
from osrs_bucket_api import OSRSBucketAPI


class OSRSNpcBucketAPI(OSRSBucketAPI):
    FIELDS = [
        'page_name',
        'name',
        'id',
        'combat_level',
        'hitpoints',
        'attack_level',
        'strength_level',
        'defence_level',
        'magic_level',
        'ranged_level',
        'attack_bonus',
        'strength_bonus',
        'magic_attack_bonus',
        'magic_damage_bonus',
        'range_attack_bonus',
        'range_strength_bonus',
        'stab_defence_bonus',
        'slash_defence_bonus',
        'crush_defence_bonus',
        'magic_defence_bonus',
        'elemental_weakness',
        'elemental_weakness_percent',
        'light_range_defence_bonus',
        'standard_range_defence_bonus',
        'heavy_range_defence_bonus',
        'flat_armour',
        'attack_speed',
        'attribute',
        'max_hit',
        'attack_style',
        'experience_bonus',
        'is_members_only',
        'slayer_level',
        'slayer_experience',
        'size',
        'examine',
        'poison_immune',
        'venom_immune',
        'thrall_immune',
        'cannon_immune',
        'burn_immune',
    ]

    def __init__(self):
        super().__init__(user_agent='OSRS NPC Stats Fetcher/1.0')

    def fetch_all_npcs(self) -> List[Dict[str, Any]]:
        return self.fetch_bucket('infobox_monster', self.FIELDS)

    def normalize_npc_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized_data = []

        for record in data:
            normalized_record = {}

            for field in self.FIELDS:
                if field in record:
                    value = record[field]

                    if field == 'elemental_weakness':
                        if value is None or value == '':
                            normalized_record[field] = "None"
                        else:
                            normalized_record[field] = value
                    elif field == 'elemental_weakness_percent':
                        elemental_weakness = normalized_record.get('elemental_weakness',
                                                                   record.get('elemental_weakness', ''))
                        if elemental_weakness == "None" or elemental_weakness is None or elemental_weakness == '':
                            normalized_record[field] = 0
                        elif value is None or value == '':
                            normalized_record[field] = "unknown"
                        else:
                            normalized_record[field] = value
                    elif field == 'flat_armour':
                        if value is None or value == '':
                            normalized_record[field] = 0
                        else:
                            normalized_record[field] = value
                    elif field == 'attribute':
                        if value is None or value == '':
                            normalized_record[field] = []
                        else:
                            normalized_record[field] = value
                    elif field == 'slayer_level':
                        if value is None or value == '':
                            normalized_record[field] = 1
                        else:
                            normalized_record[field] = value
                    elif field == 'slayer_experience':
                        if value is None or value == '':
                            normalized_record[field] = 0
                        else:
                            normalized_record[field] = value
                    elif field == 'experience_bonus':
                        if value is None or value == '':
                            normalized_record[field] = 0
                        else:
                            normalized_record[field] = value
                    elif field == 'is_members_only':
                        normalized_record[field] = True
                    else:
                        if value is None or value == '':
                            normalized_record[field] = "unknown"
                        else:
                            normalized_record[field] = value
                else:
                    if field == 'elemental_weakness':
                        normalized_record[field] = "None"
                    elif field == 'elemental_weakness_percent':
                        elemental_weakness = normalized_record.get('elemental_weakness', "None")
                        if elemental_weakness == "None":
                            normalized_record[field] = 0
                        else:
                            normalized_record[field] = "unknown"
                    elif field == 'flat_armour':
                        normalized_record[field] = 0
                    elif field == 'attribute':
                        normalized_record[field] = []
                    elif field == 'slayer_level':
                        normalized_record[field] = 1
                    elif field == 'slayer_experience':
                        normalized_record[field] = 0
                    elif field == 'experience_bonus':
                        normalized_record[field] = 0
                    elif field == 'is_members_only':
                        normalized_record[field] = False
                    else:
                        normalized_record[field] = "unknown"

            for key, value in record.items():
                if key not in normalized_record:
                    normalized_record[key] = value

            normalized_data.append(normalized_record)

        return normalized_data

    def save_to_json(self, data: List[Dict[str, Any]], filename: str = "data/osrs_npcs.json"):
        normalized_data = self.normalize_npc_data(data)

        super().save_to_json(normalized_data, filename)

    def save_to_csv(self, data: List[Dict[str, Any]], filename: str = "data/osrs_npcs.csv"):
        if not data:
            print("No data to save")
            return

        normalized_data = self.normalize_npc_data(data)

        fieldnames = self.FIELDS

        import os
        os.makedirs(os.path.dirname(filename) if os.path.dirname(filename) else '.', exist_ok=True)

        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(normalized_data)

        print(f"Data saved to {filename}")


def main():
    parser = argparse.ArgumentParser(description='Fetch OSRS NPC data from the Wiki')
    parser.add_argument('--json', type=lambda x: x.lower() == 'true', default=True,
                        help='Save data as JSON (default: true)')
    parser.add_argument('--csv', type=lambda x: x.lower() == 'true', default=True,
                        help='Save data as CSV (default: true)')

    args = parser.parse_args()

    api = OSRSNpcBucketAPI()

    npcs = api.fetch_all_npcs()

    if npcs:
        if not args.json and not args.csv:
            print("\nWarning: No output format selected. Use --json=true or --csv=true")
        if args.json:
            api.save_to_json(npcs)
        if args.csv:
            api.save_to_csv(npcs)
    else:
        print("No data retrieved")


if __name__ == "__main__":
    main()
