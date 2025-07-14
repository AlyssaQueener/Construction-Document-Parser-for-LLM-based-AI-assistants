import json
from collections import defaultdict
from copy import deepcopy
import re

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



def partial_word_similarity(desc1, desc2):
    """Return a float similarity score between 0 and 1."""
    if not desc1 or not desc2:
        return 0.0

    words1 = set(re.findall(r"\w+", str(desc1).lower()))
    words2 = set(re.findall(r"\w+", str(desc2).lower()))

    if not words1 or not words2:
        return 0.0

    intersection = words1 & words2
    union = words1 | words2
    similarity = len(intersection) / len(union)

    return similarity
def compute_item_similarity(item1, item2):
    keys = set(item1.keys()).union(item2.keys())
    scores = []
    for key in keys:
        score = fuzzy_match_score(item1.get(key), item2.get(key), field=key)
        scores.append(score)
    return sum(scores) / len(scores) if scores else 0.0

def fuzzy_match(extracted, validated, threshold=0.75):
    if len(extracted) != len(validated):
        return False

    for sec1, sec2 in zip(extracted, validated):
        if not fuzzy_match_score(sec1.get("Section Title"), sec2.get("Section Title"), field="Section Title") >= threshold:
            return False

        items1 = sec1.get("Items", [])
        items2 = sec2.get("Items", [])

        unmatched = set(range(len(items2)))
        for item1 in items1:
            matched = False
            for idx in unmatched:
                item2 = items2[idx]
                similarity = compute_item_similarity(item1, item2)
                if similarity >= threshold:
                    unmatched.remove(idx)
                    matched = True
                    break
            if not matched:
                return False  # this item didn't match any in the other list

    return True


def fuzzy_match_score(val1, val2, field=None):
    if val1 is None and val2 in ["", None]:
        return 1.0
    if val2 is None and val1 in ["", None]:
        return 1.0

    if field == "Item Description":
        return partial_word_similarity(val1, val2)

    try:
        # Compare numerics
        num1 = float(str(val1).replace(",", ""))
        num2 = float(str(val2).replace(",", ""))
        return 1.0 if abs(num1 - num2) < 1e-2 else 0.0
    except:
        # Case-insensitive exact match
        return 1.0 if str(val1 or "").strip().lower() == str(val2 or "").strip().lower() else 0.0

def flatten_sections(sections, parent_title=""):
    """Recursively extract all sections with items from nested structure."""
    flat_sections = []

    for sec in sections:
        # Combine titles for full context
        title_keys = ["Section Title", "Subsection Title"]
        current_title = next((sec.get(k) for k in title_keys if k in sec), "")
        full_title = f"{parent_title} > {current_title}".strip(" >")

        # If 'Items' exist, add a flat entry
        if "Items" in sec:
            flat_sections.append({
                "Section Title": full_title,
                "Items": sec["Items"]
            })

        # Recursively handle nested 'Subsections'
        if "Subsections" in sec:
            flat_sections.extend(flatten_sections(sec["Subsections"], full_title))

    return flat_sections

def per_field_accuracy(extracted, validated):
    stats = defaultdict(lambda: {"score_sum": 0.0, "total": 0})

    for sec1, sec2 in zip(extracted, validated):
        items1 = sec1["Items"]
        items2 = sec2["Items"]

        for item1, item2 in zip(items1, items2):
            keys = set(item1.keys()).union(item2.keys())
            for key in keys:
                val1 = item1.get(key)
                val2 = item2.get(key)
                score = fuzzy_match_score(val1, val2, field=key)
                stats[key]["score_sum"] += score
                stats[key]["total"] += 1

    return {
        field: round(counts["score_sum"] / counts["total"], 3)
        for field, counts in stats.items()
    }


def main():
    path_extracted= "output/Financial/BOQ3_extracted_boq_data.json"
    path_validated = "output/Financial/BOQ3_validation_boq_data.json"
    extracted = flatten_sections(load_json(path_extracted))
    validated = flatten_sections(load_json(path_validated))

    print("== COMPARISON RESULTS ==")
    print(f"Exact Match: {exact_match(deepcopy(extracted), deepcopy(validated))}")
    print(f"Content Match (order-insensitive): {content_match(deepcopy(extracted), deepcopy(validated))}")
    print(f"Fuzzy Match (tolerant): {fuzzy_match_score(deepcopy(extracted), deepcopy(validated))}")

    print("\n== PER-FIELD ACCURACY REPORT ==")
    accuracy = per_field_accuracy(deepcopy(extracted), deepcopy(validated))
    for field, acc in accuracy.items():
        print(f"{field}: {acc*100:.1f}%")

if __name__ == "__main__":
    main()
