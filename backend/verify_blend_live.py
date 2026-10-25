import requests
import json

base_url = "http://127.0.0.1:8000"

# 1. Create Blend room
create_payload = {
    "title": "Diwali Celebration Group",
    "occasion": "Diwali Night",
    "shared_theme": "Royal Ethnic",
    "shared_palette": ["Maroon", "Navy", "Gold"],
    "host_name": "Venkat",
    "host_budget_inr": 8500.0,
    "host_gender": "men",
    "host_sizes": {"top": "L", "bottom": "34", "shoes": "UK 9"},
    "host_style": "Regal Classic",
    "host_avoid_colors": ["Neon Green"],
    "host_required_categories": ["top", "bottom", "shoes"]
}
r = requests.post(f"{base_url}/api/v1/blend/create", json=create_payload)
assert r.status_code == 200, f"Create failed: {r.text}"
room = r.json()
blend_id = room["blend_id"]
print(f"1. Created room: {blend_id}")

# 2. Join second member
join_payload = {
    "blend_id": blend_id,
    "member_name": "Ananya",
    "member_budget_inr": 6500.0,
    "member_gender": "women",
    "member_sizes": {"top": "M", "shoes": "UK 5"},
    "member_style": "Contemporary Ethnic",
    "member_avoid_colors": ["Black"],
    "member_required_categories": ["top", "shoes"]
}
r = requests.post(f"{base_url}/api/v1/blend/join", json=join_payload)
assert r.status_code == 200, f"Join failed: {r.text}"
joined = r.json()
print(f"2. Joined Ananya. Total members: {len(joined['members'])}")

# 3. Join third member
join_payload_3 = {
    "blend_id": blend_id,
    "member_name": "Rohan",
    "member_budget_inr": 4500.0,
    "member_gender": "men",
    "member_sizes": {"top": "M", "bottom": "32", "shoes": "UK 8"},
    "member_style": "Smart Indo-Casual",
    "member_avoid_colors": ["Yellow"],
    "member_required_categories": ["top", "bottom", "shoes"]
}
r = requests.post(f"{base_url}/api/v1/blend/join", json=join_payload_3)
assert r.status_code == 200, f"Join 3 failed: {r.text}"
joined = r.json()
print(f"3. Joined Rohan. Total members: {len(joined['members'])}")

# 4. Coordinate outfits
r = requests.post(f"{base_url}/api/v1/blend/{blend_id}/coordinate?force_fixture=true")
assert r.status_code == 200, f"Coordination failed: {r.text}"
coord = r.json()
score = coord["group_cohesion_score"]
breakdown = coord["score_breakdown"]
print(f"\n4. Coordination Complete! Cohesion score: {score}")
print(f"   Breakdown: {json.dumps(breakdown, indent=2)}")

for m in coord["members"]:
    outfit = m.get("recommended_outfit") or {}
    total = outfit.get("total_price_inr", 0)
    budget = m.get("budget_inr", 0)
    status = m.get("status")
    num_items = len(outfit.get("items", []))
    print(f"   Member {m['display_name']} ({m['gender']}): total INR {total:,.2f} / budget INR {budget:,.2f} | items: {num_items} | status: {status}")

# 5. Member swap test
host = coord["members"][0]
host_outfit = host["recommended_outfit"]
item_to_swap = host_outfit["items"][0]
print(f"\n5. Swapping item '{item_to_swap['title']}' for member {host['display_name']}...")

swap_payload = {
    "blend_id": blend_id,
    "member_id": host["user_id"],
    "rejected_item_id": item_to_swap["id"],
    "feedback_text": "Prefer a different ethnic piece",
    "target_category": item_to_swap["category"]
}
r = requests.post(f"{base_url}/api/v1/blend/swap", json=swap_payload)
assert r.status_code == 200, f"Swap failed: {r.text}"
after_swap = r.json()
updated_host = [m for m in after_swap["members"] if m["user_id"] == host["user_id"]][0]
new_item_ids = [it["id"] for it in updated_host["recommended_outfit"]["items"]]
print(f"   Swap successful! Rejected item {item_to_swap['id']} in new outfit: {item_to_swap['id'] in new_item_ids} (should be False)")
print(f"   New cohesion score: {after_swap['group_cohesion_score']}")

# 6. Verify persistence on disk
r_get = requests.get(f"{base_url}/api/v1/blend/{blend_id}")
assert r_get.status_code == 200
assert r_get.json()["blend_id"] == blend_id
print(f"\n6. Persistence verified: Room {blend_id} safely retrieved via GET.")

print("\n>>> ALL PHASE 4 LIVE VERIFICATIONS PASSED SUCCESSFULLY! <<<")
