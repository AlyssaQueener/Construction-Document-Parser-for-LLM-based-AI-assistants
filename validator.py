import json
from deepdiff import DeepDiff
from collections import defaultdict


def load_json_files(ground_truth_path, output_path):
    """Load both JSON files"""
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truth = json.load(f)
    
    with open(output_path, 'r', encoding='utf-8') as f:
        output = json.load(f)
    
    return ground_truth, output


def calculate_metrics(ground_truth, output):
    """
    Calculate matching metrics using DeepDiff
    
    Returns:
        dict: Detailed metrics and differences
    """
    # Use DeepDiff to find all differences
    diff = DeepDiff(
        ground_truth, 
        output, 
        ignore_order=True,  # Order in arrays doesn't matter
        verbose_level=2      # Detailed output
    )
    
    # Initialize metrics
    metrics = {
        "total_fields": 0,
        "matching_fields": 0,
        "different_fields": 0,
        "titleBlock": {
            "total": 0,
            "matching": 0,
            "different": 0,
            "differences": []
        },
        "rooms": {
            "total": 0,
            "matching": 0,
            "different": 0,
            "differences": []
        },
        "overall_match": len(diff) == 0,
        "diff_summary": diff
    }
    
    # Count titleBlock fields
    for key in ground_truth["titleBlock"]:
        metrics["titleBlock"]["total"] += 1
        metrics["total_fields"] += 1
    
    # Count room fields
    for room in ground_truth["rooms"]:
        # Each room has: roomName, area, adjacentRooms, neighboringRooms
        metrics["rooms"]["total"] += 3  # area, adjacentRooms, neighboringRooms
        metrics["total_fields"] += 3
    
    # Parse DeepDiff results
    if not diff:
        # Perfect match
        metrics["matching_fields"] = metrics["total_fields"]
        metrics["titleBlock"]["matching"] = metrics["titleBlock"]["total"]
        metrics["rooms"]["matching"] = metrics["rooms"]["total"]
    else:
        # Analyze differences
        
        # Values changed
        if "values_changed" in diff:
            for path, change in diff["values_changed"].items():
                if "titleBlock" in path:
                    metrics["titleBlock"]["different"] += 1
                    metrics["titleBlock"]["differences"].append({
                        "path": path,
                        "expected": change["old_value"],
                        "got": change["new_value"]
                    })
                elif "rooms" in path:
                    metrics["rooms"]["different"] += 1
                    metrics["rooms"]["differences"].append({
                        "path": path,
                        "expected": change["old_value"],
                        "got": change["new_value"]
                    })
                metrics["different_fields"] += 1
        
        # Items removed from arrays
        if "iterable_item_removed" in diff:
            for path, value in diff["iterable_item_removed"].items():
                if "rooms" in path:
                    metrics["rooms"]["different"] += 1
                    metrics["rooms"]["differences"].append({
                        "path": path,
                        "type": "removed",
                        "value": value
                    })
                    metrics["different_fields"] += 1
        
        # Items added to arrays
        if "iterable_item_added" in diff:
            for path, value in diff["iterable_item_added"].items():
                if "rooms" in path:
                    metrics["rooms"]["different"] += 1
                    metrics["rooms"]["differences"].append({
                        "path": path,
                        "type": "added",
                        "value": value
                    })
                    metrics["different_fields"] += 1
        
        # Calculate matching fields
        metrics["matching_fields"] = metrics["total_fields"] - metrics["different_fields"]
        metrics["titleBlock"]["matching"] = metrics["titleBlock"]["total"] - metrics["titleBlock"]["different"]
        metrics["rooms"]["matching"] = metrics["rooms"]["total"] - metrics["rooms"]["different"]
    
    return metrics


def print_detailed_report(metrics, ground_truth, output):
    """Print a detailed comparison report"""
    
    # Overall status
    if metrics["overall_match"]:
        print("✅ PERFECT MATCH - Files are 100% identical!")
        print()
    else:
        print("⚠️  DIFFERENCES FOUND - Detailed analysis below")
        print()
    
    # TitleBlock Analysis
    print("=" * 80)
    print("📋 TITLE BLOCK")
    print("=" * 80)
    
    tb_score = (metrics["titleBlock"]["matching"] / metrics["titleBlock"]["total"] * 100) if metrics["titleBlock"]["total"] > 0 else 0
    
    print(f"Score: {tb_score:.1f}%")
    print(f"Matching: {metrics['titleBlock']['matching']}/{metrics['titleBlock']['total']}")
    print(f"Different: {metrics['titleBlock']['different']}")
    print()
    
    if metrics["titleBlock"]["differences"]:
        print("Differences:")
        for diff in metrics["titleBlock"]["differences"]:
            field = diff["path"].split("['")[-1].rstrip("']")
            print(f"  ❌ {field}:")
            print(f"     Expected: {diff['expected']}")
            print(f"     Got:      {diff['got']}")
        print()
    else:
        print("✅ All TitleBlock fields match!")
        print()
    
    # Rooms Analysis
    print("=" * 80)
    print("🏠 ROOMS")
    print("=" * 80)
    
    rooms_score = (metrics["rooms"]["matching"] / metrics["rooms"]["total"] * 100) if metrics["rooms"]["total"] > 0 else 0
    
    print(f"Score: {rooms_score:.1f}%")
    print(f"Matching: {metrics['rooms']['matching']}/{metrics['rooms']['total']}")
    print(f"Different: {metrics['rooms']['different']}")
    print()
    
    if metrics["rooms"]["differences"]:
        print("Differences (showing field-level details):")
        print()
        
        # Analyze each room individually
        gt_rooms = {room["roomName"]: room for room in ground_truth["rooms"]}
        out_rooms = {room["roomName"]: room for room in output["rooms"]}
        
        for room_name in gt_rooms.keys():
            if room_name not in out_rooms:
                print(f"  🚪 Room: {room_name}")
                print("  " + "-" * 76)
                print(f"     ❌ Room missing in output!")
                continue
            
            gt_room = gt_rooms[room_name]
            out_room = out_rooms[room_name]
            
            room_has_diff = False
            
            # Check adjacentRooms
            gt_adj = set(gt_room.get("adjacentRooms", []))
            out_adj = set(out_room.get("adjacentRooms", []))
            
            if gt_adj != out_adj:
                if not room_has_diff:
                    print(f"  🚪 Room: {room_name}")
                    print("  " + "-" * 76)
                    room_has_diff = True
                
                missing = gt_adj - out_adj
                extra = out_adj - gt_adj
                
                print(f"     ❌ adjacentRooms:")
                print(f"        Expected: {sorted(list(gt_adj))}")
                print(f"        Got:      {sorted(list(out_adj))}")
                if missing:
                    print(f"        Missing:  {sorted(list(missing))}")
                if extra:
                    print(f"        Extra:    {sorted(list(extra))}")
            
            # Check neighboringRooms
            gt_neigh = set(gt_room.get("neighboringRooms", []))
            out_neigh = set(out_room.get("neighboringRooms", []))
            
            if gt_neigh != out_neigh:
                if not room_has_diff:
                    print(f"  🚪 Room: {room_name}")
                    print("  " + "-" * 76)
                    room_has_diff = True
                
                missing = gt_neigh - out_neigh
                extra = out_neigh - gt_neigh
                
                print(f"     ❌ neighboringRooms:")
                print(f"        Expected: {sorted(list(gt_neigh))}")
                print(f"        Got:      {sorted(list(out_neigh))}")
                if missing:
                    print(f"        Missing:  {sorted(list(missing))}")
                if extra:
                    print(f"        Extra:    {sorted(list(extra))}")
            
            # Check area
            if gt_room.get("area") != out_room.get("area"):
                if not room_has_diff:
                    print(f"  🚪 Room: {room_name}")
                    print("  " + "-" * 76)
                    room_has_diff = True
                
                print(f"     ❌ area:")
                print(f"        Expected: {gt_room.get('area')}")
                print(f"        Got:      {out_room.get('area')}")
            
            if room_has_diff:
                print()
        
        # Check for extra rooms in output
        for room_name in out_rooms.keys():
            if room_name not in gt_rooms:
                print(f"  🚪 Room: {room_name}")
                print("  " + "-" * 76)
                print(f"     ⚠️  Extra room in output (not in ground truth)")
                print()
    else:
        print("✅ All room fields match!")
        print()
    
    # Overall Summary
    print("=" * 80)
    print("📊 OVERALL SUMMARY")
    print("=" * 80)
    
    overall_score = (metrics["matching_fields"] / metrics["total_fields"] * 100) if metrics["total_fields"] > 0 else 0
    
    print(f"Total Fields: {metrics['total_fields']}")
    print(f"Matching Fields: {metrics['matching_fields']}")
    print(f"Different Fields: {metrics['different_fields']}")
    print(f"Overall Score: {overall_score:.1f}%")
    print()
    
    # Final verdict
    print("=" * 80)
    print("🎯 FINAL VERDICT")
    print("=" * 80)
    
    if overall_score == 100:
        print("🎉 PERFECT! All fields match 100%! ✅")
        verdict = "PASS"
    elif overall_score >= 95:
        print(f"✅ EXCELLENT! {overall_score:.1f}% match - Minor issues only")
        verdict = "PASS"
    elif overall_score >= 90:
        print(f"✅ GOOD! {overall_score:.1f}% match - Few errors to fix")
        verdict = "PASS"
    elif overall_score >= 80:
        print(f"⚠️  ACCEPTABLE: {overall_score:.1f}% match - Several errors")
        verdict = "WARNING"
    else:
        print(f"❌ FAILED: {overall_score:.1f}% match - Many errors")
        verdict = "FAIL"
    
    print()
    
    return verdict, overall_score


def export_results(metrics, output_file='deepdiff_results.json'):
    """Export results to JSON file"""
    
    # Convert DeepDiff object to serializable format
    export_data = {
        "total_fields": metrics["total_fields"],
        "matching_fields": metrics["matching_fields"],
        "different_fields": metrics["different_fields"],
        "overall_match": metrics["overall_match"],
        "overall_score": (metrics["matching_fields"] / metrics["total_fields"] * 100) if metrics["total_fields"] > 0 else 0,
        "titleBlock": {
            "total": metrics["titleBlock"]["total"],
            "matching": metrics["titleBlock"]["matching"],
            "different": metrics["titleBlock"]["different"],
            "score": (metrics["titleBlock"]["matching"] / metrics["titleBlock"]["total"] * 100) if metrics["titleBlock"]["total"] > 0 else 0,
            "differences": metrics["titleBlock"]["differences"]
        },
        "rooms": {
            "total": metrics["rooms"]["total"],
            "matching": metrics["rooms"]["matching"],
            "different": metrics["rooms"]["different"],
            "score": (metrics["rooms"]["matching"] / metrics["rooms"]["total"] * 100) if metrics["rooms"]["total"] > 0 else 0,
            "differences": metrics["rooms"]["differences"]
        },
        "diff_summary": str(metrics["diff_summary"])  # Convert DeepDiff to string
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    print(f"📄 Results exported to {output_file}")


def main():
    """Main function"""
    
    print("\n" + "=" * 80)
    print("DEEPDIFF JSON VALIDATOR")
    print("Comparing field values using DeepDiff")
    print("=" * 80)
    print()
    
    # Load files
    print("📂 Loading files...")
    ground_truth_path = 'Ground_truth_input5.json'
    output_path = 'output5.json'
    
    ground_truth, output = load_json_files(ground_truth_path, output_path)
    print("✅ Files loaded successfully!")
    print()
    
    # Calculate metrics
    print("🔍 Analyzing differences...")
    metrics = calculate_metrics(ground_truth, output)
    print("✅ Analysis complete!")
    print()
    
    # Print report
    verdict, score = print_detailed_report(metrics, ground_truth, output)
    
    # Export results
    export_results(metrics)
    
    print()
    print("=" * 80)
    
    # Return exit code
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)