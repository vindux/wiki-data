#!/usr/bin/env python3

import html
import re
from collections import defaultdict
from typing import List, Dict, Any

from osrs_bucket_api import OSRSBucketAPI


class OSRSItemBucketAPI(OSRSBucketAPI):
    FIELD_ORDER = [
        'item_name',
        'item_name_variant',
        'item_id',
        'equipment_slot',
        'stab_attack_bonus',
        'slash_attack_bonus',
        'crush_attack_bonus',
        'range_attack_bonus',
        'magic_attack_bonus',
        'stab_defence_bonus',
        'slash_defence_bonus',
        'crush_defence_bonus',
        'range_defence_bonus',
        'magic_defence_bonus',
        'strength_bonus',
        'ranged_strength_bonus',
        'magic_damage_bonus',
        'prayer_bonus',
        'weapon_attack_speed',
        'weapon_attack_range',
        'combat_style',
        'weight',
        'value',
        'high_alchemy_value',
        'buy_limit',
        'is_members_only',
    ]

    ALL_ITEMS_FIELD_ORDER = [
        'item_name',
        'item_name_variant',
        'item_id',
        'weight',
        'value',
        'high_alchemy_value',
        'buy_limit',
        'examine',
        'is_members_only',
    ]

    def __init__(self):
        super().__init__(user_agent='OSRS Item Stats Fetcher/1.0')

    @staticmethod
    def clean_examine_text(text: str) -> str:
        if not text:
            return text
        text = re.sub(r'<[^>]+>', '', text)
        text = html.unescape(text)
        text = text.replace('[sic]', '')
        return text

    def fetch_item_bonuses(self) -> List[Dict[str, Any]]:
        fields = [
            'page_name',
            'page_name_sub',
            'equipment_slot',
            'stab_attack_bonus',
            'slash_attack_bonus',
            'crush_attack_bonus',
            'range_attack_bonus',
            'magic_attack_bonus',
            'stab_defence_bonus',
            'slash_defence_bonus',
            'crush_defence_bonus',
            'range_defence_bonus',
            'magic_defence_bonus',
            'strength_bonus',
            'ranged_strength_bonus',
            'prayer_bonus',
            'magic_damage_bonus',
            'weapon_attack_speed',
            'weapon_attack_range',
            'combat_style',
        ]
        return self.fetch_bucket('infobox_bonuses', fields)

    def fetch_item_info(self) -> List[Dict[str, Any]]:
        fields = [
            'page_name',
            'page_name_sub',
            'item_id',
            'weight',
            'value',
            'high_alchemy_value',
            'buy_limit',
            'examine',
            'is_members_only',
        ]
        return self.fetch_bucket('infobox_item', fields)

    def merge_data(self, bonuses: List[Dict], item_info: List[Dict]) -> Dict[str, List[Dict]]:
        print("Merging data...")

        info_lookup = {}
        for item in item_info:
            page_name = item.get('page_name', '')
            page_name_sub = item.get('page_name_sub', '')
            key = (page_name, page_name_sub)
            info_lookup[key] = item

        grouped_by_slot = defaultdict(list)

        for bonus_item in bonuses:
            page_name = bonus_item.get('page_name', '')
            page_name_sub = bonus_item.get('page_name_sub', '')
            equipment_slot = bonus_item.get('equipment_slot', 'unknown')

            key = (page_name, page_name_sub)
            info_data = info_lookup.get(key, {})

            temp_data = {
                'item_name': page_name,
                'item_name_variant': page_name_sub or None,
                'item_id': info_data.get('item_id', None),
            }

            for key, value in bonus_item.items():
                if key not in ['page_name', 'page_name_sub']:
                    if value is None or value == '':
                        if key != 'equipment_slot':
                            value = 0
                    temp_data[key] = value

            if info_data:
                for field in ['weight', 'value', 'high_alchemy_value', 'buy_limit']:
                    value = info_data.get(field)
                    if value is None or value == '':
                        value = 0
                    temp_data[field] = value

                temp_data['is_members_only'] = 'is_members_only' in info_data
            else:
                temp_data['weight'] = 0
                temp_data['value'] = 0
                temp_data['high_alchemy_value'] = 0
                temp_data['buy_limit'] = 0
                temp_data['is_members_only'] = False

            merged_item = {}
            for field in self.FIELD_ORDER:
                if field in temp_data:
                    merged_item[field] = temp_data[field]

            for key, value in temp_data.items():
                if key not in merged_item:
                    merged_item[key] = value

            grouped_by_slot[equipment_slot].append(merged_item)

        print(f"Merged into {len(grouped_by_slot)} equipment slots")

        return dict(grouped_by_slot)

    def save_grouped_json(self, data: Dict, filename: str = "data/osrs_equipment.json"):
        super().save_to_json(data, filename)

    def save_flat_json(self, data: Dict, filename: str = "data/osrs_equipment_flat.json"):
        flat_list = []
        for slot, items in data.items():
            flat_list.extend(items)
        super().save_to_json(flat_list, filename)

    def save_all_items_json(self, item_info: List[Dict[str, Any]], filename: str = "data/osrs_items.json"):
        normalized_items = []

        for item in item_info:
            page_name = item.get('page_name', '')
            page_name_sub = item.get('page_name_sub', '')

            temp_data = {
                'item_name': page_name,
                'item_name_variant': page_name_sub or None,
                'item_id': item.get('item_id', None),
            }

            for field in ['weight', 'value', 'high_alchemy_value', 'buy_limit']:
                value = item.get(field)
                if value is None or value == '':
                    value = 0
                temp_data[field] = value

            examine_text = item.get('examine', None)
            if examine_text:
                examine_text = self.clean_examine_text(examine_text)
            temp_data['examine'] = examine_text

            temp_data['is_members_only'] = 'is_members_only' in item

            ordered_item = {}
            for field in self.ALL_ITEMS_FIELD_ORDER:
                if field in temp_data:
                    ordered_item[field] = temp_data[field]

            for key, value in temp_data.items():
                if key not in ordered_item and key not in ['page_name', 'page_name_sub']:
                    ordered_item[key] = value

            normalized_items.append(ordered_item)

        super().save_to_json(normalized_items, filename)


def main():
    api = OSRSItemBucketAPI()

    print("=" * 60)
    print("OSRS Item & Bonuses Fetcher")
    print("=" * 60)
    print()

    bonuses = api.fetch_item_bonuses()
    item_info = api.fetch_item_info()

    if bonuses and item_info:
        api.save_all_items_json(item_info)

        merged_data = api.merge_data(bonuses, item_info)

        api.save_grouped_json(merged_data)
        api.save_flat_json(merged_data)

        print("\n--- Summary ---")
        print(f"Total items (all): {len(item_info)}")
        total_equipment = sum(len(items) for items in merged_data.values())
        print(f"Total equipment items: {total_equipment}")
        print(f"Equipment slots: {len(merged_data)}")
        print("\nItems per slot:")
        for slot, items in sorted(merged_data.items(), key=lambda x: len(x[1]), reverse=True):
            print(f"  {slot}: {len(items)} items")
    else:
        print("No data retrieved")


if __name__ == "__main__":
    main()
