import pandas as pd
import numpy as np

def convert_used_to_available(used_map, max_per_cell=100):
    return {zone: max_per_cell - used for zone, used in used_map.items()}

def predict_best_zone(state, model):
    q_table = model["q_table"]
    state_to_index = model["state_to_index"]
    actions = model["actions"]

    state_idx = state_to_index.get(state)
    if state_idx is None:
        raise ValueError(f"Invalid state: {state}")

    action_idx = np.argmax(q_table[state_idx])
    return actions[action_idx]

def process_batch_allocations_qtable(requests, model, capacity_map):
    log = []
    cap = capacity_map.copy()

    for i, req in enumerate(requests):
        try:
            state = (
                req.get("urgency", "Medium"),
                int(req.get("fragile", 0)),
                int(req.get("temp", 0))
            )
            demand = int(req.get("capacity_required", 0))

            zone_key = predict_best_zone(state, model)

            available = cap.get(zone_key, 0)
            stored = min(available, demand)
            remaining = max(0, demand - available)

            cap[zone_key] = max(0, available - stored)

            log.append({
                "urgency": state[0],
                "fragile": state[1],
                "temp": state[2],
                "capacity_required": demand,
                "Assigned_Zone": zone_key,
                "Stored": stored,
                "Remaining_Unallocated": remaining
            })

        except Exception as e:
            print(f"❌ Allocation error at row {i}: {e}")
            log.append({
                "urgency": req.get("urgency"),
                "fragile": req.get("fragile"),
                "temp": req.get("temp"),
                "capacity_required": req.get("capacity_required"),
                "Assigned_Zone": "ERROR",
                "Stored": 0,
                "Remaining_Unallocated": req.get("capacity_required"),
                "error": str(e)
            })

    return pd.DataFrame(log), cap
