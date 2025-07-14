import json
from collections import defaultdict
from copy import deepcopy
import re
from difflib import SequenceMatcher

def load_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def exact_match(extracted, validated):
    return extracted == validated
def content_match(extracted, validated):
    def sort_items(items):
        return sorted(items, key=lambda x: str(x.get("Item Number") or ""))

    if len(extracted) != len(validated):
        return False

    for sec1, sec2 in zip(extracted, validated):
        if sec1["Section Title"].strip() != sec2["Section Title"].strip():
            return False
        if sort_items(sec1["Items"]) != sort_items(sec2["Items"]):
            return False
    return True
from difflib import SequenceMatcher

def organize_data(data):
    """Convert list of sections into dicts for fast access by titles and item numbers."""
    sections_dict = {}
    for section in data:
        section_title = section["Section Title"].strip()
        subsections_dict = {}
        for subsection in section.get("Subsections", []):
            subsection_title = subsection["Subsection Title"].strip()
            items_dict = {}
            for item in subsection.get("Items", []):
                item_number = str(item.get("Item Number") or "").strip()
                items_dict[item_number] = item
            subsections_dict[subsection_title] = items_dict
        sections_dict[section_title] = subsections_dict
    return sections_dict

def string_similarity(a, b):
    """Compute similarity between two strings (case-insensitive)."""
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()

from difflib import SequenceMatcher

def string_similarity(a, b):
    return SequenceMatcher(None, a.strip().lower(), b.strip().lower()).ratio()

import json

def flatten_items(json_data):
    """Extract all items from nested structure into a flat list."""
    flat_items = []
    for section in json_data:
        for subsection in section.get("Subsections", []):
            for item in subsection.get("Items", []):
                if item:
                    flat_items.append(item)
    for section in json_data:
            for item in section.get("Items", []):
                if item:
                    flat_items.append(item)
    return flat_items


def items_match(item1, item2):
    """Check if two items match (can adjust logic here)."""
    keys_to_check = ["Item Number", "Item Description", "Unit", "Quantity", "Rate", "Amount", "Currency"]
    for key in keys_to_check:
        v1 = str(item1.get(key, "")).strip().lower()
        v2 = str(item2.get(key, "")).strip().lower()
        if v1 != v2:
            return False
    return True


def compare_flat_items(extracted_items, validated_items):
    """Compare items regardless of order and count matches."""
    matched_Item_Number=0
    matched_Item_Description=0
    matched_Unit=0
    matched_Quantity=0
    matched_Rate=0
    matched_Amount=0
    matched_Currency=0
    matched_total =0 

    for e_item in extracted_items:
        for v_item in validated_items:
            if e_item["Item Number"] == v_item["Item Number"]:
                    matched_Item_Number=matched_Item_Number+1
            else:
                break
            if e_item["Item Description"] == v_item["Item Description"]:
                 matched_Item_Description=matched_Item_Description+1
            else:
                break
            if e_item["Unit"] == v_item["Unit"]:
                 matched_Unit=matched_Unit+1
            else:
                 break
            if e_item["Quantity"] == v_item["Quantity"]:
                 matched_Quantity=matched_Quantity+1
            else:
                 break
            if e_item["Rate"] == v_item["Rate"]:
                 matched_Rate=matched_Rate+1
            else:
                 break
            if e_item["Amount"] == v_item["Amount"]:
                 matched_Amount=matched_Amount+1
            else:
                break
            if e_item["Currency"] == v_item["Currency"]:
                 matched_Currency=matched_Currency+1
            else:
                 break

    print(f'Item Number: {matched_Item_Number}')
    print(f'Item Description: {matched_Item_Description}')
    print(f'Unit: {matched_Unit}')
    print(f'Quantity: {matched_Quantity}')
    print(f'Rate: {matched_Rate}')
    print(f'Amount: {matched_Amount}')
    print(f'Currency: {matched_Currency}')

    total = len(validated_items)
    print(total)
    match_percentages = {
        "Item Number": round((matched_Item_Number / total) * 100, 2) if total else 0.0,
        "Item Description": round((matched_Item_Description / total) * 100, 2) if total else 0.0,
        "Unit": round((matched_Unit / total) * 100, 2) if total else 0.0,
        "Quantity": round((matched_Quantity / total) * 100, 2) if total else 0.0,
        "Rate": round((matched_Rate / total) * 100, 2) if total else 0.0,
        "Amount": round((matched_Amount / total) * 100, 2) if total else 0.0,
        "Currency": round((matched_Currency / total) * 100, 2) if total else 0.0,
    }

    # Optional: total match (e.g., all fields matched)
    overall_avg = round(sum(match_percentages.values()) / len(match_percentages), 2)

    return match_percentages, total, overall_avg

path_extracted= "output/Financial/BOQ3_extracted_boq_data.json"
path_validated = "output/Financial/BOQ3_validation_boq_data.json"
extracted_data = (load_json(path_extracted))
validated_data = (load_json(path_validated))
# === Load your JSON files ===

# === Flatten the items ===
extracted_items = flatten_items(extracted_data)
validated_items = flatten_items(validated_data)
#print(extracted_items)
#print(validated_items)
# === Compare ===
match_percent, matched_count, total_validated = compare_flat_items(extracted_items, validated_items)

# === Output ===
print(f"Item Match Total: {match_percent}%")
print(f"Matched {matched_count} of {total_validated} validated items.")





