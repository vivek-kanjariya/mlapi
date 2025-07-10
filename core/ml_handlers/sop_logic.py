import os
import pandas as pd
import pickle
import json  # ✅ for pretty printing JSON
from core.ml_handlers.rl_utils import convert_used_to_available, process_batch_allocations_qtable

# ✅ Global variable to store processed result for GET
SOP_PROCESSED_RESULT = None

def process_sop_data(payload):
    global SOP_PROCESSED_RESULT

    try:
        print("📥 /sop data received")

        columns = payload.get("columns")
        data = payload.get("data")

        if not isinstance(columns, list) or not columns:
            return {"error": "'columns' must be a non-empty list."}, 400

        if not isinstance(data, list) or not data:
            return {"error": "'data' must be a non-empty list of rows."}, 400

        # ✅ Convert list of lists into list of dicts
        structured_data = []
        for i, row in enumerate(data):
            if not isinstance(row, list) or len(row) != len(columns):
                return {"error": f"Row {i} malformed"}, 400
            structured_data.append(dict(zip(columns, row)))

        print(f"🟢 SOP Data received: {len(structured_data)} rows | Columns: {columns}")

        model_path = "models/sop/warehouse_rl_policy.pkl"
        if not os.path.exists(model_path):
            return {"error": "Model file not found."}, 500

        try:
            with open(model_path, "rb") as f:
                model = pickle.load(f)
            print("✅ Pickle Q-table Model loaded.")
        except Exception as e:
            return {"error": f"Model loading failed: {e}"}, 500

        # 📦 Used Map from first row
        zone_keys = ['A1', 'B1', 'C1', 'A2', 'B2', 'C2', 'A3', 'B3', 'C3']
        used_map = {zone: int(structured_data[0].get(f"{zone}_used", 0)) for zone in zone_keys}
        print("📊 Initial Used Map from Payload:")
        for k, v in used_map.items():
            print(f"  {k}: {v}")

        available_map = convert_used_to_available(used_map)

        log_df, updated_cap = process_batch_allocations_qtable(structured_data, model, available_map)

        # ✅ Convert DataFrame to frontend-friendly format
        result_json = {
            "columns": log_df.columns.tolist(),
            "data": log_df.values.tolist()
        }

        # ✅ Print formatted JSON result preview
        # print("🧾 Formatted JSON Result Preview:")
        # print(json.dumps(result_json, indent=2))

        # ✅ Store for GET access
        SOP_PROCESSED_RESULT = result_json

        # ✅ Debug output of full allocation log
        # print("📋 Allocation Log:")
        # print(log_df.to_string(index=False))

        print("✅ Final result formatted and returned to frontend.")

        return {
            "status": "ok",
            "message": "Predictions complete",
            "rows": len(log_df),
            "result": result_json  # 👈 Final output is JSON style
        }, 200

    except Exception as e:
        print(f"❌ SOP Processing Exception: {str(e)}")
        return {"error": f"Server error: {str(e)}"}, 500
