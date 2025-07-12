import pandas as pd
import joblib
import traceback
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

# === Model Paths ===
PRIORITY_MODEL_PATH = "models/Dispatch/priority_score_model.pkl"
SCALER_PATH = "models/Dispatch/scaler.pkl"
KNN_MODEL_PATH = "models/Dispatch/knn_model.pkl"

# === Vehicle Configuration ===
base_vehicles = [
    {"Vehicle_Type": "Small", "Capacity_kg": 500, "Capacity_L": 1500, "Vehicle_Property": "General"},
    {"Vehicle_Type": "Medium", "Capacity_kg": 1000, "Capacity_L": 3000, "Vehicle_Property": "General"},
    {"Vehicle_Type": "Large", "Capacity_kg": 2000, "Capacity_L": 6000, "Vehicle_Property": "General"},
    {"Vehicle_Type": "Special_Small", "Capacity_kg": 500, "Capacity_L": 1500, "Vehicle_Property": "Specialised"},
    {"Vehicle_Type": "Special_Medium", "Capacity_kg": 1000, "Capacity_L": 3000, "Vehicle_Property": "Specialised"},
    {"Vehicle_Type": "Special_Large", "Capacity_kg": 2000, "Capacity_L": 6000, "Vehicle_Property": "Specialised"},
]

class DispatchPlannerView(APIView):
    parser_classes = [JSONParser]

    def post(self, request):
        try:
            # === Parse JSON ===
            columns = request.data.get("columns", [])
            data = request.data.get("data", [])
            print("📥 [DispatchPlanner] Payload received.")

            if not columns or not data:
                return Response({"error": "Missing 'columns' or 'data' in request"}, status=400)

            df = pd.DataFrame(data, columns=columns)
            print(f"✅ DataFrame created. Shape: {df.shape}")
            print("🧾 Columns:", df.columns.tolist())

            # === Required Columns Check ===
            required = [
                "Fragility_Tag", "Temp_Tag", "Total_Weight", "Total_Volume",
                "Expiry_Duration_Months", "Dispatch_Duration_Days"
            ]
            missing_cols = [col for col in required if col not in df.columns]
            if missing_cols:
                return Response({"error": f"Missing columns: {missing_cols}"}, status=400)

            # === Convert to Numeric ===
            for col in required:
                df[col] = pd.to_numeric(df[col], errors="coerce")

            if df[required].isnull().any().any():
                return Response({"error": "Invalid or null numeric fields"}, status=400)

            # === ML Priority Score ===
            priority_model = joblib.load(PRIORITY_MODEL_PATH)
            priority_features = list(priority_model.feature_names_in_)
            df["ML_Priority_Score"] = priority_model.predict(df[priority_features])
            print("✅ ML_Priority_Score computed.")

            # === Clustering ===
            scaler = joblib.load(SCALER_PATH)
            knn = joblib.load(KNN_MODEL_PATH)
            cluster_features = ["Total_Weight", "Total_Volume", "ML_Priority_Score", "Fragility_Tag", "Temp_Tag"]
            df["Cluster"] = knn.predict(scaler.transform(df[cluster_features]))
            print("✅ Cluster labels assigned.")

            # === Load Classification ===
            df["Fragile_Flag"] = df["Fragility_Tag"].astype(bool).astype(int)
            df["Temp_Flag"] = df["Temp_Tag"].astype(bool).astype(int)
            df["Load_Type"] = df.apply(
                lambda r: "TF" if r.Fragile_Flag and r.Temp_Flag else ("F" if r.Fragile_Flag else ("T" if r.Temp_Flag else "N")),
                axis=1
            )
            df["Sensitive_Flag"] = df["Load_Type"].isin(["TF", "F", "T"])
            df["Assignment_Status"] = "Not_Assigned"
            df["Assigned_Vehicle_ID"] = None
            print("✅ Load type logic applied.")

            # === Vehicle Pool Initialization ===
            vehicle_pool = []
            counter = 1
            for v in base_vehicles:
                for _ in range(2):
                    vehicle_pool.append({
                        "Vehicle_ID": f"{v['Vehicle_Type'].upper()}_{counter:03d}",
                        "Vehicle_Type": v["Vehicle_Type"],
                        "Vehicle_Property": v["Vehicle_Property"],
                        "Capacity_kg": v["Capacity_kg"],
                        "Capacity_L": v["Capacity_L"],
                        "Remaining_kg": v["Capacity_kg"],
                        "Remaining_L": v["Capacity_L"],
                        "Used": 0
                    })
                    counter += 1
            vehicle_df = pd.DataFrame(vehicle_pool)
            print(f"🚚 Vehicle pool initialized with {len(vehicle_df)} vehicles.")

            # === Assignment ===
            df_sorted = df.sort_values(["Cluster", "ML_Priority_Score"], ascending=[True, False])

            for i, order in df_sorted.iterrows():
                load_type = order["Load_Type"]
                weight = order["Total_Weight"]
                volume = order["Total_Volume"]

                if load_type == "TF":
                    candidates = vehicle_df[vehicle_df["Vehicle_Property"] == "Specialised"]
                elif load_type in ["F", "T"]:
                    candidates = vehicle_df.sort_values(by="Vehicle_Property", ascending=True)
                else:
                    candidates = vehicle_df.copy()

                for j, vehicle in candidates.iterrows():
                    if vehicle["Remaining_kg"] >= weight and vehicle["Remaining_L"] >= volume:
                        df.at[i, "Assigned_Vehicle_ID"] = vehicle["Vehicle_ID"]
                        df.at[i, "Assignment_Status"] = "Assigned"
                        vehicle_df.at[j, "Remaining_kg"] -= weight
                        vehicle_df.at[j, "Remaining_L"] -= volume
                        vehicle_df.at[j, "Used"] = 1
                        break

            print("✅ Vehicle assignment done.")

            # === Final Columns To Return ===
            final_columns = [
                "Product_ID",
                "Product_Name",
                "Product_Category",
                "Quantity_Dispatched",
                "Total_Weight",
                "Total_Volume",
                "ML_Priority_Score",
                "Cluster",
                "Load_Type",
                "Assignment_Status",
                "Assigned_Vehicle_ID"
            ]
            output_data = df[final_columns].values.tolist()

            return Response({
                "columns": final_columns,
                "data": output_data
            })

        except Exception as e:
            print("❌ Exception in DispatchPlannerView:")
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
