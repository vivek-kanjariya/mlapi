from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import pandas as pd
import traceback
import datetime
import os
from .ml_utils import load_priority_model_and_encoder, predict_priority


# Optional if using ML later
# from .ml_utils import load_model, predict_dispatch
from .file_handler import process_uploaded_csv, update_master_file


# ✅ Serve HTML frontend
def index(request):
    return render(request, 'index.html')

class PredictView(APIView):
    def post(self, request):
        ...


# ✅ Unified handler for data sent from React (JSON or CSV)

PRODUCTS_CSV_PATH = os.path.join(os.path.dirname(__file__), '..\\assets\\products.csv')

class TestJSONView(APIView):
    def post(self, request):
        try:
            print("\n[INFO] 🔥 Incoming /api/data/ POST Request")

            df = None

            # ✅ CASE 1: React format
            if isinstance(request.data, dict) and "columns" in request.data and "data" in request.data:
                df = pd.DataFrame(data=request.data["data"], columns=request.data["columns"])
                print("[OK] ✅ DataFrame created from columns + data")

            # ✅ CASE 2: Direct JSON array
            elif isinstance(request.data, list):
                df = pd.DataFrame(request.data)
                print("[OK] ✅ DataFrame created from list of dicts")

            # ✅ CASE 3: File upload
            elif 'file' in request.FILES:
                file = request.FILES['file']
                df = pd.read_csv(file)
                print("[OK] ✅ DataFrame created from uploaded CSV")

            else:
                print("[ERR] ❌ No valid data format found in request")
                return Response({"error": "No valid data provided"}, status=400)

            # 🔍 Show original uploaded columns
            uploaded_columns = df.columns.tolist()
            print(f"\n📥 Uploaded Columns: {uploaded_columns}")

            # ✅ REQUIRED Columns Check
            REQUIRED_COLUMNS = [
                'Assignment_ID',
                'Product_ID',
                'Quantity_Assigned',
                'Unit_Weight_(kg)',
                'Unit_Volume_(L)',
                'Urgent_Flag',
                'Dispatch_Window',
                'Delivery_Window',
                'Fragile_Flag',
                'Temp_Sensitive_Flag',
                'Zone', 'Rack', 'UID', 'Vehicle_No'
            ]

            missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
            if missing_cols:
                return Response({
                    "error": f"❌ Missing required columns: {missing_cols}",
                    "uploaded_columns": uploaded_columns
                }, status=400)

            # ✅ Load product master
            product_df = pd.read_csv(PRODUCTS_CSV_PATH)
            product_df.columns = [col.strip().replace(" ", "_").replace("(", "").replace(")", "") for col in product_df.columns]
            product_map = product_df.set_index("Product_ID").to_dict(orient="index")

            # ✅ Enrichment
            def enrich(row):
                
                # ✅ Generate Handle tag
                
                fragile = int(row.get('Fragile_Flag', 0))
                temp_sens = int(row.get('Temp_Sensitive_Flag', 0))

                if fragile and temp_sens:
                    row['Handle'] = 'TF'
                elif fragile:
                    row['Handle'] = 'F'
                elif temp_sens:
                    row['Handle'] = 'T'
                else:
                    row['Handle'] = 'N'

                pid = row['Product_ID']
                if pid not in product_map:
                    raise ValueError(f"❌ Expiry_Date not found for Product_ID: {pid}")

                product = product_map[pid]
                today = datetime.datetime.today()

                dispatch = pd.to_datetime(row['Dispatch_Window'], errors='coerce')
                delivery = pd.to_datetime(row['Delivery_Window'], errors='coerce')
                expiry = pd.to_datetime(product['Expiry_Date'], errors='coerce')

                qty = float(row['Quantity_Assigned'])
                wt = float(row['Unit_Weight_(kg)'])
                vol = float(row['Unit_Volume_(L)'])

                row['Total_Weight'] = qty * wt
                row['Total_Volume'] = qty * vol
                row['Delivery_Window_Days'] = (delivery - dispatch).days if pd.notna(dispatch) and pd.notna(delivery) else None
                mfg_date = pd.to_datetime(product['Manufacture_Date'], errors='coerce')
                row['Expiry_Days_Left'] = (expiry - mfg_date).days if pd.notna(expiry) and pd.notna(mfg_date) else None
                row['Expiry_Date'] = expiry.strftime("%Y-%m-%d") if pd.notna(expiry) else None

                # Construct Assignment_ID & Product_ID
                row['Assignment_ID'] = f"{row['Zone']}::{row['Rack']}::{row['UID']}::{row['Vehicle_No']}"
                row['Product_ID'] = f"{product['Product_Name'].split()[0]}-{product['SKU_Code']}-{product['Batch_Number']}-{row['UID']}"

                return row

            df = df.apply(enrich, axis=1)
            
            df['Urgent_Flag'] = df['Urgent_Flag'].astype(int)
            df['Temp_Sensitive_Flag'] = df['Temp_Sensitive_Flag'].astype(int)
            df['Fragile_Flag'] = df['Fragile_Flag'].astype(int)

            
            column_mapping = {
                'Fragile_Flag': 'Fragility',
                'Temp_Sensitive_Flag': 'Temp_Sensitive',
                'Urgent_Flag': 'Urgent_Order_Flag'
            }

            df.rename(columns=column_mapping, inplace=True)


            # 🔍 Show final cleaned & enriched columns
            final_columns = df.columns.tolist()
            print(f"\n✅ Final DataFrame Columns After Enrichment: {final_columns}")

            print("\n✅ Final Cleaned & Enriched DataFrame Preview:")
            print(df.head())
            
            
            print("\n[INFO] 🚀 Loading ML model and encoder...")
            model, label_encoder = load_priority_model_and_encoder()

            print("[INFO] 🧠 Running prediction...")
            df = predict_priority(df, model, label_encoder)

            
            print(df.columns.tolist())

            return Response({
                "message": "Data cleaned and enriched successfully",
                "uploaded_columns": uploaded_columns,
                "final_columns": final_columns,
                "preview": df.head(5).to_dict(orient="records")  # optional
            }, status=200)

        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)

class UploadMasterView(APIView):
    def post(self, request):
        try:
            if 'file' not in request.FILES:
                return Response({"error": "No master file uploaded"}, status=400)

            update_master_file(request.FILES['file'])
            return Response({"message": "Master file updated"}, status=200)
        except Exception as e:
            traceback.print_exc()
            return Response({"error": str(e)}, status=500)
