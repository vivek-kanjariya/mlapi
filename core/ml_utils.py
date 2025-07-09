import pandas as pd
import os
import traceback
import pickle
from sklearn.base import BaseEstimator
from sklearn.preprocessing import LabelEncoder

# 📍 Model and Encoder Paths
MODEL_DIR = os.path.join(os.path.dirname(__file__), '..', 'models', 'priority')
MODEL_PATH = os.path.join(MODEL_DIR, 'priority_model.pkl')
ENCODER_PATH = os.path.join(MODEL_DIR, 'priority_label_encoder.pkl')

# 📊 Required Feature Columns
# FEATURE_COLUMNS = [
#     'Expiry_Days_Left',
#     'Delivery_Window_Days',
#     'Urgent_Flag',
#     'Temp_Sensitive_Flag',
#     'Fragile_Flag'
# ]

FEATURE_COLUMNS = [
    'Expiry_Days_Left',
    'Delivery_Window_Days',
    'Urgent_Order_Flag',
    'Temp_Sensitive',
    'Fragility'
]


# 📈 Output Column
PREDICTION_COLUMN = 'Predicted_Priority'


def load_priority_model_and_encoder():
    try:
        print(f"\n[INFO] 🔍 Loading model from: {MODEL_PATH}")
        print(f"[INFO] 🔍 Loading encoder from: {ENCODER_PATH}")

        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        if not os.path.exists(ENCODER_PATH):
            raise FileNotFoundError(f"Label encoder file not found: {ENCODER_PATH}")

        with open(MODEL_PATH, 'rb') as f_model:
            model = pickle.load(f_model)

        with open(ENCODER_PATH, 'rb') as f_encoder:
            label_encoder = pickle.load(f_encoder)

        if not hasattr(model, 'predict'):
            raise AttributeError("Loaded model does not have 'predict' method.")

        print("[OK] ✅ Model and encoder loaded successfully.")
        return model, label_encoder

    except Exception as e:
        print("[ERR] ❌ Failed to load model or encoder:")
        traceback.print_exc()
        raise e


def predict_priority(df: pd.DataFrame, model: BaseEstimator, label_encoder: LabelEncoder) -> pd.DataFrame:
    try:
        if not isinstance(df, pd.DataFrame):
            raise TypeError("Input is not a DataFrame.")
        if df.empty:
            raise ValueError("Input DataFrame is empty.")

        print("\n[INFO] 🔎 Validating input features...")

        missing_cols = [col for col in FEATURE_COLUMNS if col not in df.columns]
        if missing_cols:
            raise KeyError(f"Missing required columns: {missing_cols}")

        X = df[FEATURE_COLUMNS]

        print(f"[DEBUG] 📊 Input shape: {X.shape}")
        print(f"[DEBUG] 📊 Preview of input:\n{X.head()}")

        # 🔐 Ensure all features are numeric
        for col in FEATURE_COLUMNS:
            if not pd.api.types.is_numeric_dtype(X[col]):
                raise TypeError(f"Feature '{col}' must be numeric.")

        # 🔮 Predict encoded labels
        encoded_preds = model.predict(X)

        # 🔠 Decode predictions
        decoded_preds = label_encoder.inverse_transform(encoded_preds)

        # 📝 Attach result
        df[PREDICTION_COLUMN] = decoded_preds

        print(f"\n[OK] ✅ Prediction column '{PREDICTION_COLUMN}' added to DataFrame.")

        # 📋 Show final column names
        print(f"[INFO] ✅ Final DataFrame Columns: {df.columns.tolist()}")

        # 📈 Show prediction counts by class
        prediction_counts = df[PREDICTION_COLUMN].value_counts()
        print(f"[INFO] 🧮 Prediction Summary:\n{prediction_counts.to_string()}")

        # 🔍 Preview predicted results
        print(f"[INFO] Preview with Predictions:\n{df[[PREDICTION_COLUMN]].head()}")

        return df

    except Exception as e:
        print("[ERR] ❌ Prediction failed:")
        traceback.print_exc()
        raise e
