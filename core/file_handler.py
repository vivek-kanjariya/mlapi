import pandas as pd
import os

MASTER_PATH = os.path.join(os.path.dirname(__file__), '..', 'assets', 'products.csv')

def update_master_file(file_obj):
    df = pd.read_csv(file_obj)
    df.to_csv(MASTER_PATH, index=False)

def process_uploaded_csv(df):
    master = pd.read_csv(MASTER_PATH)

    df = df.dropna()
    df = df.merge(master, on="Product_ID", how="left")

    df['Total_Weight'] = df['Quantity_Assigned'] * df['Unit_Weight_(kg)']
    df['Total_Volume'] = df['Quantity_Assigned'] * df['Unit_Volume_(L)']

    df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date'])
    df['Dispatch_Window'] = pd.to_datetime(df['Dispatch_Window'])

    df['Expiry_Days_Left'] = (df['Expiry_Date'] - pd.Timestamp.today()).dt.days
    df['Delivery_Window_Days'] = (pd.to_datetime(df['Delivery_Window']) - df['Dispatch_Window']).dt.days

    return df
