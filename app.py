from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import pandas as pd
from sklearn.model_selection import cross_val_score, KFold, train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score
import os
import pytz
import openpyxl
from openpyxl.workbook import Workbook
from datetime import datetime
import numpy as np
import sys
import tkinter as tk
from tkinter import ttk
import mysql.connector
from sqlalchemy import create_engine
import sqlite3
from tkinter import messagebox
import socket
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.ensemble import RandomForestRegressor
from scipy import stats
import pandas as pd
import re
import numpy as np
import os
from flask import Flask, render_template, request, jsonify, session
from passlib.hash import sha256_crypt, sha512_crypt
from passlib.hash import bcrypt
import uuid
import time
from datetime import timedelta
import json
import joblib
import random  # Import the random module
from werkzeug.security import check_password_hash
from werkzeug.security import generate_password_hash
import msoffcrypto
from msoffcrypto import OfficeFile
from werkzeug.utils import secure_filename
import win32com.client as win32
import pythoncom
import matplotlib.pyplot as plt
import matplotlib
import io
import base64
from flask import send_file
import threading
from mysql.connector import Error
from flask_sslify import SSLify  # For enforcing HTTPS


app = Flask(__name__)
app.secret_key = 'your_secret_key'



# Load clinical data from 'clinical_data.xlsx'
train_file = "C://Users//gsags//Downloads//trial(1).xlsx"

# Set up SQLite database
conn = mysql.connector.connect(
    host="localhost",
    user="moura2024",
    password="moura2024",
    database="scheduling"
)
c = conn.cursor()

UPLOAD_FOLDER = 'C:\\Users\\gsags\\Downloads\\Grad_html\\photos'  # Folder to store uploaded files
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Set Matplotlib to use the 'Agg' backend
matplotlib.use('Agg')


@app.route('/first')
def index():
    # Redirect to first.html
    return render_template('first.html')

@app.route('/file_upload')
def file_upload():
    # Redirect to file_upload.html
    return redirect(url_for('file_upload_html'))

@app.route('/already_exists')
def already_exists():
    directory = 'C:\\Users\\gsags\\Downloads\\Grad_html'  # Replace with your directory path
    events_data = {}

    # List all files in the directory
    files = os.listdir(directory)

    # Define a regex pattern to match filenames with "event" in them
    pattern = re.compile(r'^\D.*event.*\.json$', re.IGNORECASE)

    # Iterate over files and load JSON data
    for filename in files:
        if pattern.match(filename):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r') as f:
                try:
                    file_data = json.load(f)
                except json.JSONDecodeError as e:
                    print(f"Error loading JSON from {filename}: {e}")
    return render_template('receptionist_2.html')
    
    

global_decrypted_df = None
preprocessed_df = None

def unprotect_xlsx_and_return_clean_df(file_path, pw_str):
    try:
        # Load the Excel file and check if it's encrypted
        with open(file_path, 'rb') as file:
            office_file = OfficeFile(file)
            if office_file.is_encrypted():
                office_file.load_key(password=pw_str)
                decrypted_io = io.BytesIO()
                office_file.decrypt(decrypted_io)
                decrypted_io.seek(0)
            else:
                # If not encrypted, load the file directly
                decrypted_io = io.BytesIO(file.read())
                decrypted_io.seek(0)

        # Load the decrypted (or non-encrypted) Excel file with openpyxl
        wb = openpyxl.load_workbook(decrypted_io)

        # Ensure at least one visible sheet is present
        if not any(ws.sheet_state == 'visible' for ws in wb.worksheets):
            raise ValueError("At least one sheet must be visible")

        # Read the data from the first sheet into a Pandas DataFrame
        sheet = wb.active
        data = sheet.values
        columns = next(data)  # Get column names from the first row
        df = pd.DataFrame(data, columns=columns)

        # Ensure column names are unique
        if not df.columns.is_unique:
            df.columns = pd.io.parsers.ParserBase({'names': df.columns})._maybe_dedup_names(df.columns)
            
        return df

    except Exception as e:
        print(f"An error occurred: {e}")
        return None     


@app.route('/file_upload.html', methods=['GET', 'POST'])
def file_upload_html():
    if request.method == 'GET':
        return render_template('file_upload.html')
    elif request.method == 'POST':
        if 'fileUpload' not in request.files:
            return "No file uploaded", 400
        file = request.files['fileUpload']
        if file.filename == '':
            return "No file selected", 400
        if file:
            #file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            #file.save(file_path)            
            #session['file']=file_path
            try:
                wb = openpyxl.load_workbook(file)
                if wb:
                    result_train = preprocessing2(train_file, password=None)
                    result_test = preprocessing2(file, password=None)
                    process_user_input(train_file, file, password=None)
            except Exception as e:
            # Save the uploaded file using Flask-Uploads       
                password = 'moura2024'            
                global_decrypted_df = unprotect_xlsx_and_return_clean_df(file.filename, password)
                if global_decrypted_df is not None:
                    # Pass the decrypted DataFrame to the preprocessing function
                    result_train = preprocessing2(train_file, password=None)
                    result_test = preprocessing2(global_decrypted_df, password=password)
                    process_user_input(train_file, global_decrypted_df, password=password)
                
                # Introduce a delay of 500 milliseconds before redirecting
            
                else:
                    return "Error: Failed to decrypt the Excel file", 500
        time.sleep(0.5)
            
            # Redirect to the next page
        return redirect(url_for('receptionist_2'))        
    else:
        return "Error processing file", 500


       
def preprocessing2(file,password=None):
    try:
        if password:
            df=file
        else:
            df = pd.read_excel(file, engine='openpyxl')
    except Exception as e:
        # Re-raise the exception if it's not related to encryption
        raise e    

    # Replace ['nan'] with "No risk factors" in the "riskFactors" column
    df['riskFactors'].fillna('No risk factors', inplace=True)
     
    # Remove brackets, parentheses, single quotes, ampersands, question marks, plus signs, periods, double quotes, and hyphens
    df['riskFactors'] = df['riskFactors'].str.replace("[\[\]()?+.\-\"&']", "").str.replace(", ", ",")
  
    # Separate every sentence in the "riskFactors" column by commas
    df['riskFactors'] = df['riskFactors'].str.replace(".", ",")
  
  
    # Apply the function to create a new column indicating the presence of Diabetes Mellitus
    df['Diabetes'] = df['riskFactors'].apply(lambda x: bool(re.search(r'\b(?:d[iI][aA][bB][eE][tT][eE][sS]|m[eE][lL][lL][iI][tT][uU][sS]|DM|diabetic|diabetis|Type|border|line|PRE|dmii|dmi|dm2)\b', x)) if isinstance(x, str) else False)
  
    #  #Apply the function to create a new column indicating the presence of Hypertension
    df['Hypertension'] = df['riskFactors'].apply(lambda x: bool(re.search(r'\b(?:H(?:Y(?:P(?:E(?:R(?:T(?:E(?:N(?:S(?:I(?:O(?:N)?)?)?)?)?)?)?)?)?)?)?|htn|HTN|h|hy|Hy|hyt|Hyt|hyte|Hyte|hyten|Hyten|hyteni|Hyteni|hytenso|Hytenso|hytensi|Hytensi|hytensio|Hytensio|hytension|Hytension|hypertensive|hb|hyper tensive|hypertension 130/85|hypertensive under medication|hypertenion|high blood pressure|hypertemsive and asthmatic|HB|HTNHYPERTENSIVE)\b', x)) if isinstance(x, str) else False)
  
    # #Apply the function to create a new column indicating the presence of Hypertension
    df['Hypotension'] = df['riskFactors'].apply(lambda x: bool(re.search(r'\b(?:H(?:Y(?:P(?:O(?:T(?:E(?:N(?:S(?:I(?:O(?:N)?)?)?)?)?)?)?)?)?)?|hotn|HoTN|HOTN|h|hy|Hy|hyot|Hyot|hyote|Hyote|hyoten|Hyoten|hyoteni|Hyoteni|hyotenso|Hyotenso|hyotensi|Hyotensi|hyotensio|Hyotensio|hyotension|Hyotension)\b', x)) if isinstance(x, str) else False)
  
    family_history_li = ['Family history of hypertension', 'Family history of diabetes mellitus', 'Family history of mental disorders',
                            'Family history of cardiac diseases', 'Family history of thalassemia', 'Family history of sickle cell disease',
                            'Family history of epilepsy', 'Family history of asthma', 'Family history of bronchiolitis', 'Family history of hyperthyroidism',
                            'Family history of Alzheimer\'s disease', 'Family history of stroke', 'Family history of hepatitis B', 'Family history of hemophilia']
  
  
    # Initialize a list to store categorized family history for each row
    categorized_family_history_list = []
  
  # Iterate through each row in the DataFrame
    for risk_factor in df['riskFactors']:
        family_history_list = []
        risk_factors_list = [factor.strip() for factor in risk_factor.split(',')]
      # Check each risk factor against the predefined list of family history categories
        for factor in risk_factors_list:
            if factor in family_history_li:
                family_history_list.append(factor)
      # Join the categorized family history into a single string and append to the list
        categorized_family_history_list.append(', '.join(family_history_list))
  
  # Add a new column to the DataFrame with the categorized family history
    df['family_history'] = categorized_family_history_list
    # Remove rows with null values in specified columns
    columns_to_check = ['BMI', 'Weight', 'Age']
    df.dropna(subset=columns_to_check, how='all', inplace=True)
  
    # Fill null values in 'Diagnosis' column with 'no diagnosis'
    df['Diagnosis'].fillna('no diagnosis', inplace=True)
  
  
     #replace terms in the Anesthesia_type column
    df['Anesthesia_type'] = df['Anesthesia_type'].apply(lambda anesthesia_type: anesthesia_type.replace('local block', 'local').replace('GA', 'general').replace('Epidoral', 'Epidural') if isinstance(anesthesia_type, str) else anesthesia_type)
  
    # Replace boolean values with 1 for True and 0 for False
    df['Hypertension'] = df['Hypertension'].astype(int)
    df['Hypotension'] = df['Hypotension'].astype(int)
    df['Diabetes'] = df['Diabetes'].astype(int)
    # Create binary feature indicating presence of any family history
    df['Any_Family_History'] = df['family_history'].apply(lambda x: 1 if x == 1 else 0)
  
  
    df['count_previous_operations'] = df['previousOperations'].apply(lambda x: len(x.split(',')) if isinstance(x, str) else 0)
  
    # Replace null and blank values with "normal" in the "allergyLevel" column
    df['allergyLevel'].fillna('normal', inplace=True)
    df['allergyLevel'] = df['allergyLevel'].replace('', 'normal')
  
    # Create a new column for the count of allergies, excluding 'normal'
    df['allergy_count'] = df['allergyLevel'].apply(lambda x: len(x) if 'normal' not in x else 0)
  
    #remove hyphens between numbers
    df['Code_Operations'] = df['Code_Operations'].apply(lambda text: re.sub(r'(\d)-(\d)', r'\1\2', str(text))).str.replace('-', '')
  
  
    columns_to_modify = [
      'numbers_of_Scrubs',
      'numbers_of_Circulators'
    ]
  
    for column in columns_to_modify:
        conditions = df[column] == 0
        df.loc[conditions, column] = np.random.choice([1, 2, 3], size=conditions.sum())
  
  
    columns_to_sum = ['numbers_of_SURGEONs', 'numbers_of_SURGEON_ASSISTANTs', 'numbers_of_Anaesthetists',
                    'numbers_of_ansTechncians', 'numbers_of_Scrubs', 'numbers_of_Circulators']
    df['total_staff'] = df[columns_to_sum].sum(axis=1)
  
    department_mapping = {
      'UROLOGY': 'Urology',
      'GASTROENTEROLOGY': 'Gastroenterology',
      'GENERAL SURGERY': 'General Surgery',
      'ANESTHETIST': 'Anesthesiology',
      'VASCULAR': 'Vascular Surgery',
      'ENT SURGERY': 'ENT SURGERY',
      'Ophthalmology - Glaucoma': 'Ophthalmology',
      'Ophthalmology - Retina': 'Ophthalmology',
      'Bariatric Surgery': 'General Surgery',
      'DENTAL - MAXILLOFACIAL SURGERY': 'Oral and Maxillofacial Surgery',
      'OPHTHALMOLOGY - GENERAL': 'Ophthalmology',
      'NEURO SURGERY': 'Neurosurgery',
      'ORTHOPEDIC SURGERY': 'Orthopaedic Surgery',
      'CHEST SURGERY': 'Cardio-thoracic Surgery',
      'PLASTIC SURGERY': 'Plastic and Reconstructive Surgery',
      'Ophthalmology - Pediatric': 'Ophthalmology',
      'INTERVENTIONAL RADIOLOGY': 'Interventional Radiology',
      'DAY SURGERY': 'General Surgery',
      'PULMONARY': 'Pulmonology',
      'DENTAL - PEDODONTIC': 'Paediatric Dentistry',
      'EMERGENCY': 'Emergency Medicine',
      'TRAUMA SURGERY': 'Trauma Surgery',
      'DENTAL - Special Need Dentistry': 'Special Needs Dentistry',
      'RADIOLOGY': 'Radiology',
      'ICU': 'Intensive Care Unit (ICU)',
      'CARDIOLOGY': 'Cardiology',
      'General Surgery': 'General Surgery',
      'Neurosurgery': 'Neurosurgery',
      'Orthopaedic Surgery': 'Orthopaedic Surgery',
      'Otolaryngology (E.N.T)': 'ENT SURGERY',
      'Ophthalmology': 'Ophthalmology',
      'Obstetrics and Gynaecology': 'Obstetrics and Gynaecology',
      'Vascular Surgery': 'Vascular Surgery',
      'Plastic and Reconstructive Surgery': 'Plastic and Reconstructive Surgery',
      'Paediatric Surgery': 'Paediatric Surgery',
      'Paedia Gastroenterology': 'Gastroenterology',
      'Paedia Cardiology': 'Paediatric Cardiology',
      'Endocrinology': 'Endocrinology',
      'Gastroenterology and Hepatology': 'Gastroenterology',
      'Pulmonology': 'Pulmonology',
      'Interventional Radiology': 'Interventional Radiology',
      'Anesthesiology': 'Anesthesiology',
      'Paediatrics': 'Paediatrics',
      'CARDIOLOGY ': 'Cardiology',
      'Cardiology ': 'Cardiology',
      'Cardio-thoracic Surgery': 'Cardio-thoracic Surgery',
      'INTERVENTIONAL RADIOLOGY ': 'Interventional Radiology',
      'Ophthalmology - Glaucoma ': 'Ophthalmology',
      'Ophthalmology - Pediatric ': 'Ophthalmology',
      'Ophthalmology - Retina ': 'Ophthalmology',
      'Oral and Maxillofacial Surgery': 'Oral and Maxillofacial Surgery',
      'TRAUMA SURGERY ': 'Trauma Surgery',
      'Urology': 'Urology'
       }
  
  # Map specialties to departments and create a new column
    df['department'] = df['surgeon_specialty'].map(department_mapping)
    operation_types = {
      '1 Elective': "Elective",
      '2 Emergency': "Emergency",
      '5 Routine': "Routine",
      '4 Urgent': "Urgent",
      '4 Day Care': "Day Care",
      '6 Live saving': "Live saving",
      '3 ASAP': "ASAP"
     }
  
    df['operation_type'] = df['operation_type'].map(operation_types)
  
    # Assuming `existing_data` is your DataFrame
    df['surgery_type'] = df['surgery_type'].str.strip()
  
  
    df['waitingTime_beforeSurgery'] = pd.to_numeric(df['waitingTime_beforeSurgery'], errors='coerce').abs()
  
  
    column_names = ['PatientinOR_DateTime', 'SurgeryStart_DateTime', 'SurgeryEnd_DateTime', 'PatientOutofOR_DateTime', 'PatientLeaftOT_Datetime','discharge_date','requestedon','admission_date',]
  
    # Convert string to datetime format
    df[column_names] = df[column_names].applymap(lambda x: pd.to_datetime(x, errors='coerce'))
  
    # Separate date and time and create new columns for datetime columns only
    for col in column_names:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            # Extract the prefix before '_DateTime'
            prefix = col.split('_DateTime')[0]
            # Create new column names for date and time parts
            date_col_name = prefix + '_Date'
            time_col_name = prefix + '_Time'
            # Assign date and time parts to new columns
            df[date_col_name] = df[col].dt.date
            df[time_col_name] = df[col].dt.time
  
    # Create a new column based on the 'transTo_ICUorCCU' column
    df['Trans_to_ICU_or_CCU_Flag'] = df['transTo_ICUorCCU'].apply(lambda x: 0 if pd.isna(x) else 1)
    
    if password:
        return df
    
    else:
        df.to_excel(file, index=False)
    

    
def model(train_file, test_data, save_model_path=None):
     # Read the training data
    train_df = pd.read_excel(train_file, engine='openpyxl')

    # Extract features and target variable for training data
    X_train = train_df[['Age', 'Weight', 'BMI', 'Hypertension', 'Hypotension', 'Diabetes',
                       'PATGender', 'Anesthesia_type', 'surgery_type', 'PatientAdmissiontype',
                       'department', 'total_staff', 'Code_Operations', 'count_previous_operations',
                       'Diagnosis', 'allergy_count']]
    y_train = stats.mstats.winsorize(train_df['actual_operationTime'], limits=[0.05, 0.05])

    # Apply one-hot encoding to categorical columns for training data
    categorical_columns = ['PATGender', 'Anesthesia_type', 'surgery_type', 'PatientAdmissiontype',
                           'department', 'Diagnosis']
    X_train_encoded = pd.get_dummies(X_train, columns=categorical_columns)

    # Optionally scale the data if needed
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train_encoded)

    # Initialize the Random Forest model
    model = RandomForestRegressor()

    # Fit the model on the training data
    model.fit(X_train_scaled, y_train)
    
    # Optionally save the trained model
    if save_model_path:
        joblib.dump(model, save_model_path)    

    if isinstance(test_data, pd.DataFrame):
        
        if save_model_path is None:
            raise ValueError("save_model_path must be provided when test_data is provided")
        
                # Load the trained model from disk
        loaded_model = joblib.load(save_model_path)        
        # Ensure the order of columns is the same
        test_data_encoded = pd.get_dummies(test_data, columns=categorical_columns)
        missing_cols = list(set(X_train_encoded.columns) - set(test_data_encoded.columns))
        if missing_cols:
            # Create a DataFrame with zeros for missing columns
            zeros_df = pd.DataFrame(0, index=test_data_encoded.index, columns=missing_cols)
            # Concatenate the existing test_data_encoded with the zeros_df
            test_data_encoded = pd.concat([test_data_encoded, zeros_df], axis=1)
        test_data_encoded = test_data_encoded[X_train_encoded.columns]
        # Optionally scale the data if needed
        test_data_scaled = scaler.transform(test_data_encoded)
        # Predict on the testing data
        predicted_time = model.predict(test_data_scaled)

    return predicted_time

def calculate_priority(surgery_type, operation_type, department):
    # Map surgery type to priority level
    surgery_type_priority = {
        'SPECIAL SKILLS': 5,
        'MAJOR': 4,
        'MODERATE': 3,
        'MINOR': 2,
        'SIMPLE': 1
    }

    # Map operation type to priority level
    operation_type_priority = {
        'Elective': 1,
        'Day Care': 2,
        'Routine': 3,
        'Urgent': 4,
        'Emergency': 5,
        'Live saving': 6,
        'ASAP': 7
    }


    department_priority = {
    'Neurosurgery': 30,                           # Important surgery with high complexity
    'Cardio-thoracic Surgery': 28,                # Important surgery with high complexity
    'Interventional Radiology': 26,               # Important surgery with high complexity
    'Paediatric Cardiology': 24,                  # Specialized care for pediatric heart issues
    'Obstetrics and Gynaecology': 23,             # Important for women's health, slightly lower than pediatric cardiology
    'Vascular Surgery': 20,                       # Important surgery with moderate complexity
    'Orthopaedic Surgery': 18,                    # Important surgery with moderate complexity
    'General Surgery': 16,                        # Covers a wide range of important surgeries
    'Plastic and Reconstructive Surgery': 15,     # Important for reconstructive purposes
    'ENT SURGERY': 12,                # Important for ear, nose, and throat issues
    'Urology': 10,                                # Important for urinary tract issues
    'Anesthesiology': 8,                          # Essential for surgeries, lower weight due to supporting role
    'Ophthalmology': 6,                           # Important for eye-related issues
    'Gastroenterology': 5,                        # Important for gastrointestinal issues, slightly lower than ophthalmology
    'Pulmonology': 4,                             # Important for respiratory issues, slightly lower than gastroenterology
    'Endocrinology': 3,                           # Important for hormonal issues, slightly lower than pulmonology
    'Paediatric Surgery': 22,                     # Specialized surgery for pediatric patients
    'Oral and Maxillofacial Surgery': 14,         # Important for oral and facial issues
    'Special Needs Dentistry': 13,                # Specialized care for patients with special needs
    'Paediatric Dentistry': 12,                   # Specialized dental care for pediatric patients
    'Cardiology': 27,                             # Important specialty dealing with heart issues
    'Radiology': 25                              # Essential for diagnostics and imaging
}


    # Calculate priority based on surgery type and operation type
    # priority = surgery_type_priority.get(surgery_type, 0) + operation_type_priority.get(operation_type, 0)+surgery_type_weights.get(surgery_type_weights,0)
    priority = (
        surgery_type_priority[surgery_type] + operation_type_priority[operation_type]+department_priority[department]
    )
    return priority

department_to_room_mapping = {
       'Neurosurgery': 'OPERATION ROOM 5',
    'Cardio-thoracic Surgery': 'G23',
    'Interventional Radiology': 'G25',
    'Paediatric Cardiology': 'G27',
    'Obstetrics and Gynaecology': 'G29',
    'Vascular Surgery': 'G45',
    'Orthopaedic Surgery': 'G47',
    'General Surgery': 'G49',
    'Plastic and Reconstructive Surgery': 'G51',
    'ENT SURGERY': 'OPERATION ROOM 1',
    'Urology': 'Lithotripsy',
    'Anesthesiology': 'OPERATION ROOM 2',
    'Ophthalmology': 'OPERATION ROOM 3',
    'Gastroenterology': 'OPERATION ROOM 4',
    'Pulmonology': 'OPERATION ROOM 5',
    'Endocrinology': 'OPERATION ROOM 6',
    'Paediatric Surgery': 'OPERATION ROOM 7',
    'Oral and Maxillofacial Surgery': 'OPERATION ROOM 8',
    'Special Needs Dentistry': 'OPERATION ROOM 9',
    'Paediatric Dentistry': 'OPERATION ROOM 9',
    'Cardiology': 'G23',
    'Radiology': 'G25'
        }



# Function to preprocess user input, make predictions, and append to file
def process_user_input(train_file, test_file,password=None):
    global preprocessed_df
    
    try:
        if password:
            existing_data = test_file  # Assuming test_file is the decrypted DataFrame
        else:
            existing_data = pd.read_excel(test_file, engine='openpyxl')
    except Exception as e:
        # Re-raise the exception if it's not related to encryption
        raise e    
    # Get the column headers from the original DataFrame
    categorical_columns = existing_data[['Age', 'Weight', 'BMI', 'Hypertension', 'Hypotension', 'Diabetes',
                       'PATGender', 'Anesthesia_type', 'surgery_type', 'PatientAdmissiontype',
                       'department', 'total_staff', 'Code_Operations', 'count_previous_operations',
                       'Diagnosis', 'allergy_count']].columns.tolist()
    # Create new columns with default values
    existing_data['predicted_time'] = None
    existing_data['start_time'] = None
    existing_data['end_time'] = None
    existing_data['Assigned_Room'] = None
    existing_data['priority'] = None
    existing_data['actual_start_time'] = None
    existing_data['actual_end_time'] = None
    existing_data['start_time_only'] = None
    existing_data['end_time_only'] = None    
    existing_data['modified_surgeon_1'] = existing_data['surgeon_id']
    existing_data['modified_surgeon_2'] = existing_data['surgeon_2']    
    existing_data['modified_date'] = existing_data['PatientinOR_Date'].apply(lambda x: x.strftime('%Y-%m-%d'))
    existing_data['modified_room'] = None
    existing_data['status'] = "on time"
    existing_data['reason'] = "no reason"
    try:
        if (existing_data['operation_type'] == 'Emergency').all():
            #print("ok")
        # Get the current time in Cairo time zone
            cairo_tz = pytz.timezone('Africa/Cairo')
            current_time = datetime.now(cairo_tz)
            
            # Set the same start time for all rows
            existing_data['start_time'] = current_time.strftime('%Y-%m-%d %H:%M:%S')
            #print(existing_data['start_time'])
            # Predicted time calculation (assuming you have a function/model to predict time)
            predicted_time = model(train_file, existing_data, save_model_path="random_forest_model.pkl")
            #print("done")
            for index, row in existing_data.iterrows():
                new_start_time = current_time
                predicted_time = model(train_file, existing_data.iloc[[index]], save_model_path="random_forest_model.pkl")
                if isinstance(predicted_time, np.ndarray) and predicted_time.size == 1:
                    predicted_time = predicted_time.item()
                    print(predicted_time)
                new_end_time = new_start_time + timedelta(minutes=predicted_time + 15)
                existing_data.at[index, 'start_time'] = new_start_time.strftime('%Y-%m-%d %H:%M:%S')
                existing_data.at[index, 'end_time'] = new_end_time.strftime('%Y-%m-%d %H:%M:%S')
                existing_data.at[index, 'start_time_only'] = new_start_time.strftime('%H:%M')
                existing_data.at[index, 'end_time_only'] = new_end_time.strftime('%H:%M')
                existing_data.at[index, 'actual_start_time'] = new_start_time.strftime('%H:%M')
                existing_data.at[index, 'actual_end_time'] = new_end_time.strftime('%H:%M')
            
            # Apply priority function and assign rooms accordingly
            existing_data['priority'] = existing_data.apply(lambda row: calculate_priority(row['surgery_type'], row['operation_type'], row['department']), axis=1)
            existing_data = existing_data.sort_values(by='priority', ascending=False)
            #print("done_3")
            
            # Assign rooms based on priority and department
            existing_data['Assigned_Room'] = ''
            for index, row in existing_data.iterrows():
                if row['priority'] == existing_data.iloc[0]['priority']:
                    existing_data.at[index, 'Assigned_Room'] = 'A207'
                    #print(row['priority'],existing_data.iloc[0]['priority'])
                else:
                    existing_data.at[index, 'Assigned_Room'] = department_to_room_mapping.get(row['department'], 'Unknown Room')
            #print(existing_data)
            preprocessed_df=existing_data
            existing_data.to_excel(test_file, index=False)
            create_events_json(test_file,password=password)        
            return
    except Exception as e:
        print("errrooorr",e)
            
    for index, row in existing_data.iterrows():
        depart= row['department']
        surgery_ty=row['surgery_type']
        operation_ty = row['operation_type']
        if 'Elective' in row['operation_type']:
            roo = department_to_room_mapping.get(depart, 'unknown')

        if 'Emergency' in row['operation_type']:
            roo = 'A207'
        
                
# Include only specified columns
        row_data = pd.DataFrame([row], columns=categorical_columns)
        predicted_time = model(train_file,row_data, save_model_path="random_forest_model.pkl")
      # print("Predicted time:", predicted_time)
        priority = calculate_priority(surgery_ty, operation_ty,depart)
    # print(priority)
  # Append the calculated values for this row to existing_data DataFrame
    # Dictionary-like assignment to create new columns
        existing_data.at[index, 'predicted_time'] = predicted_time.item() if isinstance(predicted_time, np.ndarray) else predicted_time
        existing_data.at[index, 'Assigned_Room'] = roo
        existing_data.at[index, 'modified_room'] = roo
        
        existing_data.at[index, 'priority'] = priority
    
            

    existing_data = existing_data.sort_values(by='priority', ascending=False)
    # turnover= process_turnover()
    previous_end_time = None
            #next_day_file_created = False  # Flag to track if next day file is created
    current_time = datetime.strptime('06:00:00', '%H:%M:%S')
    end_of_day = datetime.strptime('23:59:00', '%H:%M:%S')
    end_of_day_str = end_of_day.strftime('%H:%M:%S')
            #print(end_of_day_str)
    if isinstance(predicted_time, np.ndarray) and predicted_time.size == 1:
        predicted_time = predicted_time.item()
    existing_data= existing_data.sort_values(by=['PatientinOR_Date', 'Assigned_Room'])    
    for index, row in existing_data.iterrows():
        date = row['PatientinOR_Date']  # Assuming 'PatientinOR_Date' is the datetime column
        room = row['Assigned_Room']
        if previous_end_time is None or (date != previous_date or room != previous_room):
            new_start_time = datetime.combine(date, current_time.time())
        else:
            new_start_time = datetime.combine(date, previous_end_time.time()) + timedelta(minutes=30)
        predicted_time = row['predicted_time']
        new_end_time = new_start_time + timedelta(minutes=predicted_time + 15)
        existing_data.at[index, 'start_time'] = new_start_time.strftime('%Y-%m-%d %H:%M:%S')
        existing_data.at[index, 'end_time'] = new_end_time.strftime('%Y-%m-%d %H:%M:%S')
        existing_data.at[index, 'start_time_only'] = new_start_time.strftime('%H:%M')
        existing_data.at[index, 'end_time_only'] = new_end_time.strftime('%H:%M')
        existing_data.at[index, 'actual_start_time'] = new_start_time.strftime('%H:%M')
        existing_data.at[index, 'actual_end_time'] = new_end_time.strftime('%H:%M')        
        previous_end_time = new_end_time
        previous_date = date
        previous_room = room
        
    
    
    if password:
        create_events_json(existing_data,password=password)
    else:
        preprocessed_df=existing_data
        existing_data.to_excel(test_file, index=False)
        create_events_json(test_file,password=password)
        

@app.route('/surgery_count_data')
def surgery_count_data():
    with open('surgery_count_by_day_room.json', 'r') as f:
        surgery_count_data = json.load(f)
    return jsonify(surgery_count_data)

@app.route('/weekly_doc_count_data')
def weekly_doc_count_data():
    doctor_id = session.get('doctor_id')
    counts_file = f'{doctor_id}_event_counts.json'
    with open(counts_file, 'r') as f:
        count_data = json.load(f)
    return jsonify(count_data)    

def get_names(surgeon_id):
    # Execute SQL query to fetch surgeon name based on unique_id
    c.execute("SELECT full_name FROM credentials WHERE unique_id = %s", (surgeon_id,))
    result = c.fetchone()
    if result:
        return result[0]  # Return the name
    else:
        return "unknown"
@app.route('/get_surgeon_names', methods=['GET'])
def get_surgeon_names():
    try:
         
        # Execute SQL query to fetch names from MySQL
        c.execute("SELECT full_name FROM credentials")
        names = c.fetchall()

        # Close cursor and connection
        conn.commit()
        surgeons_list = [{"name": name[0]} for name in names]
        #print(surgeons_list)  # Debug print
        
        return jsonify(surgeons_list)
    except Exception as e:
        return jsonify({'error': str(e)})    
def create_events_json(test_file,password=None):
    # Read the Excel file
    try:
        if password:
            df = test_file
        else:
            df = pd.read_excel(test_file, engine='openpyxl')
    except Exception as e:
        # Re-raise the exception if it's not related to encryption
        raise e    
    
    events = []
    surgery_count_by_day_room = {}  # Initialize dictionary to store surgery count by day and room    
    try:
            # Fetch all unique_ids from credentials table
            c.execute("SELECT unique_id FROM credentials")
            unique_ids = [int(row[0]) for row in c.fetchall() if row[0].isdigit()] 
            #print(unique_ids)
    except mysql.connector.Error as err:
            print(f"Error: {err}")    
    # Iterate over each row in the DataFrame
    events_by_room = {}
    events_by_doc = {}
    columns_to_check = [
        'PATIENT_ID', 'PATGender', 'Age', 'Weight', 'BMI', 'allergy', 'allergyLevel', 
        'Diagnosis', 'previousOperations', 'additonalOperation', 'Diabetes', 'Hypertension', 
        'Hypotension', 'family_history', 'Anesthesia_type', 'Need_for_ICU'
    ]    
    for index, row in df.iterrows():
        extended_props = {}
        
        start_time_str = row['start_time']
        end_time_str = row['end_time']
        room = row['Assigned_Room']
        doc_1 = row['surgeon_id']
        doc_2 = row['surgeon_2']
        doc_1_name= get_names(doc_1) 
        doc_2_name=get_names(doc_2)    
        
        #print(doc_1_name,doc_2_name)
        start_time = datetime.strptime(start_time_str, "%Y-%m-%d %H:%M:%S")
        end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S")
        
        formatted_start_time = start_time.strftime("%Y-%m-%dT%H:%M:%S")
        formatted_end_time = end_time.strftime("%Y-%m-%dT%H:%M:%S")        
        date = start_time.strftime("%Y-%m-%d")
        extended_props = {
        'patient_id': row['PATIENT_ID'],
        'pat_gend': row['PATGender'],
        'pat_age': row['Age'],
        'patient_weight': row['Weight'],
        'patient_BMI': row['BMI'],
        'patient_allergy': row['allergy'],
        'patient_allergyLevel': row['allergyLevel'],
        'patient_diagnosis': row['Diagnosis'],
        'previousOperations': row['previousOperations'],
        'additonalOperation': row['additonalOperation'],
        'patient_diabetes': row['Diabetes'],
        'patient_hyper': row['Hypertension'],
        'patient_hypo': row['Hypotension'],
        'patient_family': row['family_history'],
        'patient_ana': row['Anesthesia_type']
            }

    # Replace NaN values with 'no'
        for key, value in extended_props.items():
            if pd.isna(value):
                extended_props[key] = 'no'
            if value == 0:
                extended_props[key] = 'no'
            if value==1:
                extended_props[key] = 'yes'
        extended_props.update({
                'surgery_type': row['surgery_type'],
                'operation_type': row['operation_type'],
                'department': row['department'],
                'operation_description': row['Operation_Description'],
                'surgeon_1': doc_1,
                'surgeon_2': doc_2,
                'surgeon_1_name': doc_1_name,
                'surgeon_2_name': doc_2_name,
                'Need_for_ICU': "Yes",
                'statuses': 'ontime',
                'reason': 'no reasons'
            })        

        # Create an event object
        event = {
            'title': room,
            'start': formatted_start_time,
            'end': formatted_end_time,
            'extendedProps': extended_props        
        }
        
        events.append(event)
        
        
        # Append the event to the list of events for the room
        if room not in events_by_room:
            events_by_room[room] = []
        events_by_room[room].append(event)
        
        # If date not in surgery_count_by_day_room, initialize it
        if date not in surgery_count_by_day_room:
            surgery_count_by_day_room[date] = {}
        
        # If room not in surgery_count_by_day_room[date], initialize it
        if room not in surgery_count_by_day_room[date]:
            surgery_count_by_day_room[date][room] = 0
        
        # Increment surgery count for the room on that day
        surgery_count_by_day_room[date][room] += 1        
        #event['extendedProps']['surgeryCount'] = surgery_count_by_day_room[date][room]
        
    # Write events for each room to separate JSON files
    for room, room_events in events_by_room.items():
        room_events_file = f'{room}_events.json'
        if os.path.exists(room_events_file):
            with open(room_events_file, 'r') as f:
                existing_events = json.load(f)
                existing_events.extend(room_events)
        else:
            existing_events = room_events

        with open(room_events_file, 'w') as f:
            json.dump(existing_events, f)       
        
    # Write surgery count by day and room to a JSON file
    surgery_count_file = 'surgery_count_by_day_room.json'
    if os.path.exists(surgery_count_file):
        with open(surgery_count_file, 'r') as f:
            existing_surgery_count = json.load(f)
            for date, rooms in surgery_count_by_day_room.items():
                if date not in existing_surgery_count:
                    existing_surgery_count[date] = rooms
                else:
                    for room, count in rooms.items():
                        if room in existing_surgery_count[date]:
                            existing_surgery_count[date][room] += count
                        else:
                            existing_surgery_count[date][room] = count
    else:
        existing_surgery_count = surgery_count_by_day_room

    with open(surgery_count_file, 'w') as f:
        json.dump(existing_surgery_count, f)    

    # Convert the list of events to JSON format
    events_json = json.dumps(events)

    # Check if events.json file exists and append events if it does
    events_file = 'events.json'
    if os.path.exists(events_file):
        with open(events_file, 'r') as f:
            existing_events = json.load(f)
            existing_events.extend(events)
    else:
        existing_events = events

    # Write the JSON to the file
    with open(events_file, 'w') as f:
        json.dump(existing_events, f)

     
@app.route('/get_events')
def get_events():
    # Read the contents of the events.json file
    with open('events.json', 'r') as f:
        events_data = json.load(f)
    return jsonify(events_data)

@app.route('/submit_event', methods=['POST'])
def submit_event():
    try:
        event_data = request.get_json()
        
        extended_props = event_data.get('extendedProps', {})
        doctor_1 = extended_props.get('surgeon_1')
        doctor_2 = extended_props.get('surgeon_2')
        extended_props['submitted'] = 'yes'
        room=event_data.get('title')
        event_data['extendedProps'] = extended_props
        if not doctor_1 or not doctor_2:
            return jsonify({'error': 'Doctor ID missing'}), 400

        doctor1_events_file = f'{doctor_1}_submitted_events.json'
        doctor2_events_file = f'{doctor_2}_submitted_events.json'
        doctor1_event_counts_file = f'{doctor_1}_event_counts.json'
        doctor2_event_counts_file = f'{doctor_2}_event_counts.json'        
        events_file= 'events.json'
        room_file= f'{room}_events.json'
        with open(events_file, 'r') as f3:
            events_data_3 = json.load(f3)
        with open(room_file, 'r') as f4:
            events_data_4 = json.load(f4)        
        # Check if the JSON file for the doctor exists
        if os.path.exists(doctor1_events_file) and os.path.exists(doctor2_events_file):
            with open(doctor1_events_file, 'r') as f:
                events_data = json.load(f)
            with open(doctor2_events_file, 'r') as f2:
                events_data_2 = json.load(f2)
            
        else:
            events_data = []
            events_data_2=[]
        # Append the new event to the doctor's events
        events_data.append(event_data)
        events_data_2.append(event_data)
        # Save the updated events to the JSON file
        with open(doctor1_events_file, 'w') as f:
            json.dump(events_data, f)
        with open(doctor2_events_file, 'w') as f2:
            json.dump(events_data_2, f2)
                
        for existing_event in events_data_3:
            extended_props = existing_event.get('extendedProps', {})            
            if (existing_event['title'] == event_data['title'] and
                existing_event['start'] == event_data['start'] and
                existing_event['end'] == event_data['end'] and existing_event['extendedProps']['surgeon_1']==doctor_1 and existing_event['extendedProps']['surgeon_2']==doctor_2):
        # Check if 'submitted' already exists
                if 'submitted' not in extended_props:
                    extended_props['submitted'] = 'yes'
                    existing_event['extendedProps'] = extended_props
                    with open('events.json', 'w') as f3:
                        json.dump(events_data_3, f3, indent=4)
                    break
                elif 'submitted' in extended_props:
                    break
        for existing_event in events_data_4:
            extended_props = existing_event.get('extendedProps', {})            
            if (existing_event['title'] == event_data['title'] and
                existing_event['start'] == event_data['start'] and
                existing_event['end'] == event_data['end'] and existing_event['extendedProps']['surgeon_1']==doctor_1 and existing_event['extendedProps']['surgeon_2']==doctor_2):
        # Check if 'submitted' already exists
                if 'submitted' not in extended_props:
                    extended_props['submitted'] = 'yes'
                    existing_event['extendedProps'] = extended_props
                    with open(room_file, 'w') as f4:
                        json.dump(events_data_4, f4, indent=4)
                    break
                elif 'submitted' in extended_props:
                    break  
        def update_event_count(file, date, room):
            if os.path.exists(file):
                with open(file, 'r') as f:
                    event_counts = json.load(f)
            else:
                event_counts = {}

            if date not in event_counts:
                event_counts[date] = {}

            if room not in event_counts[date]:
                event_counts[date][room] = 0

            event_counts[date][room] += 1

            with open(file, 'w') as f:
                json.dump(event_counts, f, indent=4)

        event_date = event_data['start'].split('T')[0]  # Extract date part from the start datetime
        update_event_count(doctor1_event_counts_file, event_date, room)
        update_event_count(doctor2_event_counts_file, event_date, room)
        
        
        return jsonify({'status': 'success'}), 200
    except Exception as e:
        #print(e)
        return jsonify({'error': str(e)}), 500

@app.route('/remove_event', methods=['POST'])
def remove_event():
    try:
        event_data = request.get_json()

        extended_props = event_data.get('extendedProps', {})
        doctor_1 = extended_props.get('surgeon_1')
        doctor_2 = extended_props.get('surgeon_2')
        room = event_data.get('title')

        if not doctor_1 or not doctor_2:
            return jsonify({'error': 'Doctor ID missing'}), 400

        doctor1_events_file = f'{doctor_1}_submitted_events.json'
        doctor2_events_file = f'{doctor_2}_submitted_events.json'
        doctor1_event_counts_file = f'{doctor_1}_event_counts.json'
        doctor2_event_counts_file = f'{doctor_2}_event_counts.json'        
        events_file = 'events.json'
        room_file = f'{room}_events.json'

        def load_json(file):
            if os.path.exists(file):
                with open(file, 'r') as f:
                    return json.load(f)
            return []

        events_data = load_json(doctor1_events_file)
        events_data_2 = load_json(doctor2_events_file)
        events_data_3 = load_json(events_file)
        events_data_4 = load_json(room_file)

        def remove_event(events_list):
            return [existing_event for existing_event in events_list
                    if not (existing_event['title'] == event_data['title'] and
                            existing_event['start'] == event_data['start'] and
                            existing_event['end'] == event_data['end'] and
                            existing_event.get('extendedProps', {}).get('surgeon_1') == doctor_1 and
                            existing_event.get('extendedProps', {}).get('surgeon_2') == doctor_2)]

        def remove_submitted(events_list):
            for existing_event in events_list:
                extended_props = existing_event.get('extendedProps', {})
                if (existing_event['title'] == event_data['title'] and
                    existing_event['start'] == event_data['start'] and
                    existing_event['end'] == event_data['end'] and
                    extended_props.get('surgeon_1') == doctor_1 and
                    extended_props.get('surgeon_2') == doctor_2):
                    if 'submitted' in extended_props:
                        del extended_props['submitted']
                        existing_event['extendedProps'] = extended_props
            return events_list
        
        def update_event_count(file, date, room):
            if os.path.exists(file):
                with open(file, 'r') as f:
                    event_counts = json.load(f)
                
                if date in event_counts and room in event_counts[date]:
                    event_counts[date][room] -= 1
                    if event_counts[date][room] <= 0:
                        del event_counts[date][room]
                    if not event_counts[date]:
                        del event_counts[date]

                with open(file, 'w') as f:
                    json.dump(event_counts, f, indent=4)

        events_data = remove_event(events_data)
        events_data_2 = remove_event(events_data_2)
        events_data_3 = remove_submitted(events_data_3)
        events_data_4 = remove_submitted(events_data_4)
        event_date = event_data['start'].split('T')[0]  # Extract date part from the start datetime
        
        update_event_count(doctor1_event_counts_file, event_date, room)
        update_event_count(doctor2_event_counts_file, event_date, room)

        def save_json(file, data):
            with open(file, 'w') as f:
                json.dump(data, f, indent=4)

        save_json(doctor1_events_file, events_data)
        save_json(doctor2_events_file, events_data_2)
        save_json(events_file, events_data_3)
        save_json(room_file, events_data_4)

        return jsonify({'status': 'success'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500





@app.route('/save_form_data', methods=['POST'])
def save_form_data():
    global preprocessed_df

    # Get JSON data from request
    data = request.get_json()

    # Extract data from JSON
    date = data.get('date')
    actual_start = data.get('actualStartTime')
    actual_end = data.get('actualEndTime')
    surgeon_id = data.get('surgeonId')
    room_id = data.get('roomId')
    reason = data.get('reason')
    op_name= data.get('operationDescription')
    op_type = data.get('operationType')
    original_date=data.get('originalDate')
    original_start=data.get('originalStartTime')
    original_end=data.get('originalEndTime')
    original_room=data.get('title')
    choice_1= data.get('choice1')
    #choice_2= data.get('choice2')
    originalSurgeon1= data.get('originalSurgeon1')
    originalSurgeon2 = data.get('originalSurgeon2')
    originalID1 = data.get('originalID1')
    originalID2 = data.get('originalID2')
    operationDepartment= data.get('operationDepartment')
        
        
    try:
        
        if choice_1!="" and surgeon_id != "":
            c.execute("SELECT unique_id FROM credentials WHERE full_name = %s", (surgeon_id,))
            result = c.fetchone()
            new_id= result[0]            
            update_json_file(original_date, original_start, original_end,reason, originalSurgeon1,originalSurgeon2, original_room, actual_start, actual_end, choice_1,new_id, room_id, date, op_name,op_type)
        if choice_1=="" and surgeon_id == "":
            update_json_file(original_date, original_start, original_end,reason,originalSurgeon1,originalSurgeon2, original_room, actual_start, actual_end,None, None , room_id, date, op_name,op_type)

        return jsonify({'success': True})

    except Exception as e:
        error_msg = f"Error processing data: {str(e)}"
        print(error_msg)
        return jsonify({'success': False, 'error': error_msg}), 500
        
def update_json_file(original_date, original_start, original_end, reason,originalSurgeon1,originalSurgeon2, original_room, actual_start, actual_end,choice_1, new_id, room_id, date,op_name,op_type):
    file_path = 'events.json'
    room_events_file = f'{room_id}_events.json'
    count_events_file = 'surgery_count_by_day_room.json'
    originalSurgeon1_events_file = f'{originalSurgeon1}_submitted_events.json'
    originalSurgeon2_events_file = f'{originalSurgeon2}_submitted_events.json'
    new_events_file = f'{new_id}_submitted_events.json'
    count_doc1 =f'{originalSurgeon1}_event_counts.json'
    count_doc2 =f'{originalSurgeon2}_event_counts.json'
    if new_id:
        count_new =f'{new_id}_event_counts.json'
        c.execute("SELECT full_name FROM credentials WHERE unique_id = %s", (new_id,))
        result = c.fetchone()
        new_name=result[0]  
    
    statuses=[]
        
    global preprocessed_df
    if os.path.exists(file_path) and os.path.exists(room_events_file):
        # Load existing data from JSON file
        with open(file_path, 'r') as file:
            events = json.load(file)
        with open(room_events_file, 'r') as room_file:
            room_events = json.load(room_file)
        if  os.path.exists(count_events_file) :
            with open(count_events_file, 'r') as count_file:
                count_events = json.load(count_file)
        else:
            count_events = {}            
        

        # Find the matching event and update its details
        for event in events:
            event_start = datetime.strptime(event['start'], '%Y-%m-%dT%H:%M:%S')
            event_end = datetime.strptime(event['end'], '%Y-%m-%dT%H:%M:%S')
            
            
            if (event_start.strftime('%Y-%m-%d') == original_date and 
                event_start.strftime('%H:%M') == original_start and
                event_end.strftime('%H:%M') == original_end and
                event['extendedProps']['operation_description'] == op_name and
                event['extendedProps']['operation_type'] == op_type):
                if(event_start.strftime('%Y-%m-%d') ==date):
                    #print(event)
                    event['start'] = f"{date}T{actual_start}:00"
                    event['end'] = f"{date}T{actual_end}:00"
                    event['title'] = room_id
                    if (event['start'] != f"{date}T{original_start}" or event['end'] != f"{date}T{original_end}"):
                        status="shift in time"
                        statuses.append(status)
                        
                    if (event['title'] != room_id):
                        status="change in room"
                        statuses.append(status)
                        
                    if choice_1=="surgeon_1":
                        event['extendedProps']['surgeon_1'] = new_id
                        event['extendedProps']['surgeon_1_name'] = new_name
                        
                        status="change in surgeon 1"
                        statuses.append(status)
                        
                        
                    if choice_1=="surgeon_2":
                        event['extendedProps']['surgeon_2'] = new_id
                        event['extendedProps']['surgeon_2_name'] = new_name
                        
                        status="change in surgeon 2"
                        statuses.append(status)
                        
                        
                    if date not in count_events:
                        count_events[date] = {}
                    if room_id not in count_events[date]:
                        count_events[date][room_id] = 0
                    if(event['title'] != room_id):
                        count_events[date][original_room] -= 1                    
                    count_events[date][room_id] += 1
                    
                else:
                    if (event['title'] == room_id):
                        event['start'] = f"{date}T{actual_start}:00"
                        event['end'] = f"{date}T{actual_end}:00"
                        if (event['start'] != f"{date}T{original_start}" or event['end'] != f"{date}T{original_end}"):
                            status="shift in time"
                            statuses.append(status)
                            
                        if choice_1=="surgeon_1":
                            event['extendedProps']['surgeon_1'] = new_id
                            event['extendedProps']['surgeon_1_name'] = new_name
                            
                            status="change in surgeon 1"
                            statuses.append(status)
                            
                        if choice_1=="surgeon_2":
                            event['extendedProps']['surgeon_2'] = new_id
                            event['extendedProps']['surgeon_2_name'] = new_name
                            
                            status="change in surgeon 2"
                            statuses.append(status)
                            
                        if date not in count_events:
                            count_events[date] = {}
                        if room_id not in count_events[date]:
                            count_events[date][room_id] = 0
                        if (event_start.strftime('%Y-%m-%d') !=date):
                            count_events[original_date][room_id] -= 1                            
                        count_events[date][room_id] += 1
                        
                    else:
                        
                        event['start'] = f"{date}T{actual_start}:00"
                        event['end'] = f"{date}T{actual_end}:00"
                        event['title'] = room_id
                        if (event['start'] != f"{date}T{original_start}" or event['end'] != f"{date}T{original_end}"):
                            status="shift in time"
                            statuses.append(status)
                            
                        if (event['title'] != room_id):
                            status="change in room"
                            statuses.append(status)
                            
                        if choice_1=="surgeon_1":
                            event['extendedProps']['surgeon_1'] = new_id
                            event['extendedProps']['surgeon_1_name'] = new_name
                            
                            status="change in surgeon 1"
                            statuses.append(status)                            
                        if choice_1=="surgeon_2":
                            event['extendedProps']['surgeon_2'] = new_id
                            event['extendedProps']['surgeon_2_name'] = new_name
                            
                            status="change in surgeon 2"
                            statuses.append(status)                            
                        if date not in count_events:
                            count_events[date] = {}
                        if room_id not in count_events[date]:
                            count_events[date][room_id] = 0
                        if (event_start.strftime('%Y-%m-%d') !=date and event['title'] != room_id):
                            count_events[original_date][original_room] -= 1                            
                        count_events[date][room_id] += 1
                extended_props = event.get('extendedProps', {})            
                extended_props['statuses'] = statuses
                extended_props['reason'] = reason
                #preprocessed['status'] = "on time"
                #existing_data['reason'] = "no reason"                
                event['extendedProps'] = extended_props                
                #print(event['extendedProps']['statuses'] )
                      
        for room_event in room_events:
            event_start = datetime.strptime(room_event['start'], '%Y-%m-%dT%H:%M:%S')
            event_end = datetime.strptime(room_event['end'], '%Y-%m-%dT%H:%M:%S')
            
            if (event_start.strftime('%Y-%m-%d') == original_date and 
                event_start.strftime('%H:%M') == original_start and
                event_end.strftime('%H:%M') == original_end and
                room_event['extendedProps']['operation_description'] == op_name and
                room_event['extendedProps']['operation_type'] == op_type):
                if(event_start.strftime('%Y-%m-%d') ==date):
                    #print(room_event)
                    room_event['start'] = f"{date}T{actual_start}:00"
                    room_event['end'] = f"{date}T{actual_end}:00"
                    room_event['title'] = room_id
                    if (room_event['start'] != f"{date}T{original_start}" or room_event['end'] != f"{date}T{original_end}"):
                        status="shift in time"
                        statuses.append(status)
                    if (room_event['title'] != room_id):
                        status="change in room"
                        statuses.append(status)                    
                        
                    if choice_1=="surgeon_1":
                        room_event['extendedProps']['surgeon_1'] = new_id
                        room_event['extendedProps']['surgeon_1_name'] = new_name
                        
                        status="change in surgeon 1"
                        statuses.append(status)                        
                    if choice_1=="surgeon_2":
                        room_event['extendedProps']['surgeon_2'] = new_id
                        room_event['extendedProps']['surgeon_2_name'] = new_name
                        
                        status="change in surgeon 2"
                        statuses.append(status)                        
                
                else:
                    if (room_event['title'] == room_id):
                        room_event['start'] = f"{date}T{actual_start}:00"
                        room_event['end'] = f"{date}T{actual_end}:00"
                        room_event['title'] = room_id
                        if (room_event['start'] != f"{date}T{original_start}" or room_event['end'] != f"{date}T{original_end}"):
                            status="shift in time"
                            statuses.append(status)
                            
                        if choice_1=="surgeon_1":
                            room_event['extendedProps']['surgeon_1'] = new_id
                            room_event['extendedProps']['surgeon_1_name'] = new_name
                            
                            status="change in surgeon 1"
                            statuses.append(status)
                            
                        if choice_1=="surgeon_2":
                            room_event['extendedProps']['surgeon_2'] = new_id
                            room_event['extendedProps']['surgeon_2_name'] = new_name
                            
                            status="change in surgeon 2"
                            statuses.append(status)                            
                    else:
                        room_event['start'] = f"{date}T{actual_start}:00"
                        room_event['end'] = f"{date}T{actual_end}:00"
                        room_event['title'] = room_id
                        if (room_event['start'] != f"{date}T{original_start}" or room_event['end'] != f"{date}T{original_end}"):
                            status="shift in time"
                            statuses.append(status)
                        if (room_event['title'] != room_id):
                            status="change in room"
                            statuses.append(status)                        
                        if choice_1=="surgeon_1":
                            room_event['extendedProps']['surgeon_1'] = new_id
                            room_event['extendedProps']['surgeon_1_name'] = new_name
                            
                            status="change in surgeon 1"
                            statuses.append(status)                            
                        if choice_1=="surgeon_2":
                            room_event['extendedProps']['surgeon_2'] = new_id
                            room_event['extendedProps']['surgeon_2_name'] = new_name
                            
                            status="change in surgeon 2"
                            statuses.append(status)
                extended_props = room_event.get('extendedProps', {})            
                extended_props['statuses'] = statuses
                extended_props['reason'] = reason
                room_event['extendedProps'] = extended_props
                        
        if choice_1==None and new_id==None:
            if os.path.exists(originalSurgeon1_events_file) and os.path.exists(originalSurgeon2_events_file):
                with open(originalSurgeon1_events_file, 'r') as originalSurgeon1_file:
                    originalSurgeon1_events = json.load(originalSurgeon1_file)
                with open(originalSurgeon2_events_file, 'r') as originalSurgeon2_file:
                    originalSurgeon2_events = json.load(originalSurgeon2_file)            
                if os.path.exists(count_doc1) and os.path.exists(count_doc2):
                    with open(count_doc1, 'r') as count_doc1_file:
                        count_doc1_events = json.load(count_doc1_file)
                    with open(count_doc2, 'r') as count_doc2_file:
                        count_doc2_events = json.load(count_doc2_file)                
                else:
                    count_doc1_events = {}
                    count_doc2_events = {}            
                    
                for originalSurgeon1_event in originalSurgeon1_events:
                    event_start = datetime.strptime(originalSurgeon1_event['start'], '%Y-%m-%dT%H:%M:%S')
                    event_end = datetime.strptime(originalSurgeon1_event['end'], '%Y-%m-%dT%H:%M:%S')
                    
                    if (event_start.strftime('%Y-%m-%d') == original_date and 
                        event_start.strftime('%H:%M') == original_start and
                        event_end.strftime('%H:%M') == original_end and
                        originalSurgeon1_event['extendedProps']['operation_description'] == op_name and
                        originalSurgeon1_event['extendedProps']['operation_type'] == op_type):
                        if(event_start.strftime('%Y-%m-%d') ==date):
                        
                            originalSurgeon1_event['start'] = f"{date}T{actual_start}:00"
                            originalSurgeon1_event['end'] = f"{date}T{actual_end}:00"
                            originalSurgeon1['title'] = room_id
                            if (originalSurgeon1_event['start'] != f"{date}T{original_start}" or originalSurgeon1_event['end'] != f"{date}T{original_end}"):
                                status="shift in time"
                                statuses.append(status)
                                
                            if (originalSurgeon1_event['title'] != room_id):
                                status="change in room"
                                statuses.append(status)                            
                            if date not in count_doc1_events:
                                count_doc1_events[date] = {}
                            if room_id not in count_doc1_events[date]:
                                count_doc1_events[date][room_id] = 0
                            count_doc1_events[date][room_id] += 1                        
                            count_doc1_events[date][original_room] -= 1 
                            
                        else:
                            if (originalSurgeon1_event['title'] == room_id):
                                originalSurgeon1_event['start'] = f"{date}T{actual_start}:00"
                                originalSurgeon1_event['end'] = f"{date}T{actual_end}:00"
                                originalSurgeon1_event['title'] = room_id
                                if (originalSurgeon1_event['start'] != f"{date}T{original_start}" or originalSurgeon1_event['end'] != f"{date}T{original_end}"):
                                    status="shift in time"
                                    statuses.append(status)                                
                                if date not in count_doc1_events:
                                    count_doc1_events[date] = {}
                                if room_id not in count_doc1_events[date]:
                                    count_doc1_events[date][room_id] = 0
                                count_doc1_events[date][room_id] += 1  
                                count_doc1_events[original_date][room_id] -= 1                        
                                
                                
                            else:
                                originalSurgeon1_event['start'] = f"{date}T{actual_start}:00"
                                originalSurgeon1_event['end'] = f"{date}T{actual_end}:00"
                                originalSurgeon1_event['title'] = room_id
                                if (originalSurgeon1_event['start'] != f"{date}T{original_start}" or originalSurgeon1_event['end'] != f"{date}T{original_end}"):
                                    status="shift in time"
                                    statuses.append(status)
                                if (originalSurgeon1_event['title'] != room_id):
                                    status="change in room"
                                    statuses.append(status)                                
                                if date not in count_doc1_events:
                                    count_doc1_events[date] = {}
                                if room_id not in count_doc1_events[date]:
                                    count_doc1_events[date][room_id] = 0
                                count_doc1_events[date][room_id] += 1
                                count_doc1_events[original_date][original_room] -= 1 
                        extended_props = originalSurgeon1_event.get('extendedProps', {})            
                        extended_props['statuses'] = statuses
                        extended_props['reason'] = reason
                        originalSurgeon1_event['extendedProps'] = extended_props
                        #print("done in doc1")
                                
                for originalSurgeon2_event in originalSurgeon2_events:
                    event_start = datetime.strptime(originalSurgeon2_event['start'], '%Y-%m-%dT%H:%M:%S')
                    event_end = datetime.strptime(originalSurgeon2_event['end'], '%Y-%m-%dT%H:%M:%S')
                    
                    if (event_start.strftime('%Y-%m-%d') == original_date and 
                        event_start.strftime('%H:%M') == original_start and
                        event_end.strftime('%H:%M') == original_end and
                        originalSurgeon2_event['extendedProps']['operation_description'] == op_name and
                        originalSurgeon2_event['extendedProps']['operation_type'] == op_type):
                        if(event_start.strftime('%Y-%m-%d') ==date):
                        
                            originalSurgeon2_event['start'] = f"{date}T{actual_start}:00"
                            originalSurgeon2_event['end'] = f"{date}T{actual_end}:00"
                            originalSurgeon2_event['title'] = room_id
                            if (originalSurgeon2_event['start'] != f"{date}T{original_start}" or originalSurgeon2_event['end'] != f"{date}T{original_end}"):
                                status="shift in time"
                                statuses.append(status)
                                
                            if (originalSurgeon2_event['title'] != room_id):
                                status="change in room"
                                statuses.append(status)                            
                            if date not in count_doc1_events:
                                count_doc2_events[date] = {}
                            if room_id not in count_doc1_events[date]:
                                count_doc2_events[date][room_id] = 0
                            count_doc2_events[date][room_id] += 1                        
                            count_doc2_events[date][original_room] -= 1 
                            
                        else:
                            if (originalSurgeon2_event['title'] == room_id):
                                originalSurgeon2_event['start'] = f"{date}T{actual_start}:00"
                                originalSurgeon2_event['end'] = f"{date}T{actual_end}:00"
                                originalSurgeon2_event['title'] = room_id
                                if (originalSurgeon2_event['start'] != f"{date}T{original_start}" or originalSurgeon2_event['end'] != f"{date}T{original_end}"):
                                    status="shift in time"
                                    statuses.append(status)                                 
                                if date not in count_doc2_events:
                                    count_doc2_events[date] = {}
                                if room_id not in count_doc2_events[date]:
                                    count_doc2_events[date][room_id] = 0
                                count_doc2_events[date][room_id] += 1  
                                count_doc2_events[original_date][room_id] -= 1                        
                                
                                
                            else:
                                originalSurgeon2_event['start'] = f"{date}T{actual_start}:00"
                                originalSurgeon2_event['end'] = f"{date}T{actual_end}:00"
                                originalSurgeon2_event['title'] = room_id
                                if (originalSurgeon2_event['start'] != f"{date}T{original_start}" or originalSurgeon2_event['end'] != f"{date}T{original_end}"):
                                    status="shift in time"
                                    statuses.append(status)
                                if (originalSurgeon2_event['title'] != room_id):
                                    status="change in room"
                                    statuses.append(status)                                 
                                if date not in count_doc2_events:
                                    count_doc2_events[date] = {}
                                if room_id not in count_doc2_events[date]:
                                    count_doc2_events[date][room_id] = 0
                                count_doc2_events[date][room_id] += 1
                                count_doc2_events[original_date][original_room] -= 1
                        extended_props = originalSurgeon1_event.get('extendedProps', {})            
                        extended_props['statuses'] = statuses
                        extended_props['reason'] = reason
                        originalSurgeon1_event['extendedProps'] = extended_props
                        #print("done in doc2")
                
                
                
                with open(originalSurgeon1_events_file, 'w') as originalSurgeon1_file:
                    json.dump(originalSurgeon1_events,originalSurgeon1_file, indent=2)
                with open(originalSurgeon2_events_file, 'w') as originalSurgeon2_file:
                    json.dump(originalSurgeon2_events,originalSurgeon2_file, indent=2)            
                with open(count_doc1, 'w') as count_doc1_file:
                    json.dump(count_doc1_events,count_doc1_file, indent=2)
                with open(count_doc2, 'w') as count_doc2_file:
                    json.dump(count_doc2_events,count_doc2_file, indent=2)               
                #shift_subsequent_events(originalSurgeon1_events, date, actual_start, actual_end,room_id)
                #shift_subsequent_events(originalSurgeon2_events, date, actual_start, actual_end,room_id)                
                
                #check_and_resolve_conflicts(surgeon_events, room_id, date)
                
            

        # Save the updated data back to the JSON file
        with open(file_path, 'w') as file:
            json.dump(events, file, indent=2)
            
            
        with open(room_events_file, 'w') as room_file:
            json.dump(room_events, room_file, indent=2)
            
        with open(count_events_file, 'w') as count_file:
            json.dump(count_events, count_file, indent=2)        
            
        #shift_subsequent_events(room_events, date, actual_start, actual_end,room_id)                
        shift_and_save_events(file_path, date, actual_start, actual_end,room_id)                
        shift_and_save_events(room_events_file, date, actual_start, actual_end,room_id)                

        ## Shift subsequent events if necessary
        #check_and_resolve_conflicts(events, room_id, date)
        #check_and_resolve_conflicts(room_events, room_id, date)
        
    else:
        raise FileNotFoundError(f"JSON file not found: {file_path}")


@app.route('/suggest_alternative_surgeon', methods=['POST'])
def suggest_alternative_surgeon():
    data = request.get_json()
    department = data.get('operationDepartment')
    choice2 = data.get('choice2')
    operation_type = data.get('operationType')
    original_date = data.get('originalDate')
    original_start = data.get('originalStartTime')
    original_end = data.get('originalEndTime')

    if not department:
        return jsonify({'error': 'Department not provided'}), 400

    try:
        

        # Get the highest weight surgeon in the specified department
        c.execute(f"SELECT full_name, unique_id FROM credentials WHERE department = %s ORDER BY total_weight DESC", (department,))
        surgeons = c.fetchall()
        #print(surgeons)
        
        # Convert original_date to day of the week
        original_day_of_week = datetime.strptime(original_date, '%Y-%m-%d').strftime('%A').lower()
        print(original_day_of_week)
        # Function to check surgeon availability
        original_start_time = datetime.strptime(original_start, '%H:%M').time()
        original_end_time = datetime.strptime(original_end, '%H:%M').time()

        # Function to check surgeon availability
        def timedelta_to_time(td):
            return (datetime.min + td).time()

        # Function to check surgeon availability
        def is_surgeon_available(surgeon_id, original_day_of_week, original_start_time, original_end_time):
            c.execute(f"SELECT selected_day, slot_from, slot_to FROM {surgeon_id}_slots")
            slots = c.fetchall()
            for slot in slots:
                selected_day, slot_from_td, slot_to_td = slot
                slot_from = timedelta_to_time(slot_from_td)
                slot_to = timedelta_to_time(slot_to_td)
                #print(slot_from,original_start_time,slot_to, original_end_time)
                if selected_day == original_day_of_week and slot_from <= original_start_time and slot_to >= original_end_time:
                    return True
            return False


        for surgeon in surgeons:
            full_name, unique_id = surgeon
            if operation_type.lower() == 'emergency' or is_surgeon_available(unique_id, original_day_of_week, original_start_time, original_end_time):
                return jsonify({'surgeon_name': full_name})
        return jsonify({'surgeon_name': "no surgeons available"})
                

        # If no surgeons are available and it's not an emergency, return an error
        

    except Exception as e:
        print(f"Error querying MySQL database: {e}")
        return jsonify({'error': 'Internal server error'}), 500
    


def check_and_resolve_conflicts(events, room_id, date):
    # Filter events by room and date
    room_events = [event for event in events if event['title'] == room_id and event['start'].startswith(date)]
    global preprocessed_df
    # Check for conflicting times
    time_slots = {}
    conflicts = False
    
    for event in room_events:
        start_time = event['start'].split('T')[1]
        if start_time not in time_slots:
            time_slots[start_time] = [event]
        else:
            time_slots[start_time].append(event)
            conflicts = True

    if conflicts:
        for start_time, events in time_slots.items():
            if len(events) > 1:
                # Sort events by priority from preprocessed_df
                sorted_events = sorted(events, key=lambda x: get_priority(x, preprocessed_df))
                
                # Update times based on sorted order
                new_start_dt = datetime.strptime(f"{date}T{start_time}", '%Y-%m-%dT%H:%M:%S')
                for i, event in enumerate(sorted_events):
                    event_duration = datetime.strptime(event['end'], '%Y-%m-%dT%H:%M:%S') - datetime.strptime(event['start'], '%Y-%m-%dT%H:%M:%S')
                    event['start'] = new_start_dt.strftime('%Y-%m-%dT%H:%M:%S')
                    new_end_dt = new_start_dt + event_duration
                    event['end'] = new_end_dt.strftime('%Y-%m-%dT%H:%M:%S')
                    new_start_dt = new_end_dt + timedelta(minutes=30)  # Assuming a 30-minute gap between surgeries

        # Save the updated events back to the JSON file
        with open('events.json', 'w') as file:
            json.dump(events, file, indent=2)
        
        print("Conflicts resolved and events updated.")

def get_priority(event, preprocessed_df):
    # Assuming preprocessed_df has columns 'start_time_only', 'end_time_only', and 'priority'
    start_time = event['start'].split('T')[1]
    end_time = event['end'].split('T')[1]
    
    # Fetch priority based on start_time, end_time, room, and date from preprocessed_df
    priority = preprocessed_df[
        (preprocessed_df['start_time_only'] == start_time) &
        (preprocessed_df['end_time_only'] == end_time) &
        (preprocessed_df['Assigned_Room'] == event['title'])  # Assuming 'title' in JSON is room ID
    ]['priority'].values[0]  # Assuming there's only one priority for a specific start and end time
    
    return priority

def shift_and_save_events(file_path, new_date, new_start, new_end, room_id):
    """Load events, shift subsequent events, and save the result to the file."""

    # Load events from the JSON file
    with open(file_path, 'r') as file:
        all_events = json.load(file)
    
    # Convert new times to datetime objects
    new_end_dt = datetime.strptime(f"{new_date}T{new_end}:00", '%Y-%m-%dT%H:%M:%S')
    shifted = False
    
    # Separate events that need to be processed from those that don't
    events_to_process = [event for event in all_events if event['title'] == room_id]
    other_events = [event for event in all_events if event['title'] != room_id]
    
    # Check if there are any events on the new_date in the same room
    events_on_new_date = [event for event in events_to_process if event['start'].startswith(new_date)]

    # Exclude the updated event
    if len(events_on_new_date) == 1 and (
            datetime.strptime(events_on_new_date[0]['start'], '%Y-%m-%dT%H:%M:%S').strftime('%H:%M') == new_start and 
            datetime.strptime(events_on_new_date[0]['end'], '%Y-%m-%dT%H:%M:%S').strftime('%H:%M') == new_end):
        print(f"No other events on {new_date} in room {room_id}. No shifts needed.")
        return

    for event in events_to_process:
        # Ensure the event is in the same room
        if event['title'] == room_id:
            event_start_dt = datetime.strptime(event['start'], '%Y-%m-%dT%H:%M:%S')
            
            if event_start_dt > new_end_dt:
                event_duration = datetime.strptime(event['end'], '%Y-%m-%dT%H:%M:%S') - event_start_dt
                new_event_start_dt = new_end_dt + timedelta(minutes=30)  # Assuming a 30-minute gap
                new_event_end_dt = new_event_start_dt + event_duration

                event['start'] = new_event_start_dt.strftime('%Y-%m-%dT%H:%M:%S')
                event['end'] = new_event_end_dt.strftime('%Y-%m-%dT%H:%M:%S')
                new_end_dt = new_event_end_dt  # Update new_end_dt to the end of the current event
                
                # Add status and reason to the extendedProps of the event
                if 'extendedProps' not in event:
                    event['extendedProps'] = {}
                event['extendedProps']['statuses'] = "shifted in time"
                event['extendedProps']['reason'] = "Previous Surgery Overrun"
                shifted = True

    if shifted:
        # Combine the updated events with the unmodified events
        updated_events = other_events + events_to_process
        # Save the updated list of all events back to the file
        with open(file_path, 'w') as file:
            json.dump(updated_events, file, indent=2)
                
        print("Events successfully shifted and saved.")
    else:
        print("No events to shift.")



@app.route('/get_events_by_room')
def get_events_by_room():
    try:
        room = request.args.get('room')
        date = request.args.get('date')  # Get the date parameter from the request
        
        if room and date:
            # Construct the path to the JSON file for the specified room
            room_events_file = f'{room}_events.json'
            
            # Check if the JSON file for the room exists
            if os.path.exists(room_events_file):
                # Read the contents of the JSON file
                with open(room_events_file, 'r') as f:
                    events_data = json.load(f)
                #print("Events Data:", events_data)  # Debug print
                
                # Filter events for the specified date
                events_for_date = [event for event in events_data if event.get('start', '').split('T')[0] == date]
                #print("Events for Date:", events_for_date)  # Debug print
                
                return jsonify(events_for_date)
            else:
                return jsonify({'error': 'Events file not found for the specified room'})
        else:
            return jsonify({'error': 'Room or date parameter missing'})
    except Exception as e:
        return jsonify({'error': str(e)})
    
    
@app.route('/get_events_by_doc')
def get_events_by_doc():
    doctor_id = session.get('doctor_id')
    date = request.args.get('date')

    if doctor_id and date:
        try:
            doctor_events_file = f'{doctor_id}_submitted_events.json'
            counts_file = f'{doctor_id}_event_counts.json'
            if os.path.exists(doctor_events_file):
                with open(doctor_events_file, 'r') as f:
                    events_data = json.load(f)
                    counts = {}
                    for event in events_data:
                        event_date = event.get('start', '').split('T')[0]
                        room = event.get('title', '')
                        counts.setdefault(event_date, {}).setdefault(room, 0)
                        counts[event_date][room] += 1  
                    with open(counts_file, 'w') as f:
                        json.dump(counts, f)                    
                # Filter events for the specified date
                events_for_date = [event for event in events_data if event.get('start', '').split('T')[0] == date]
                
                return jsonify(events_for_date)
            else:
                return jsonify({'error': 'No events found for the specified doctor'})
        except Exception as e:
            return jsonify({'error': str(e)})
    else:
        return jsonify({'error': 'Doctor ID or date parameter missing'})

# Generate report based on selected date
def generate_report(selected_date):
    with open('events.json', 'r') as file:
        data = json.load(file)
    
    # Filter surgeries for the selected date
    selected_date_obj = datetime.strptime(selected_date, '%Y-%m-%d').date()
    surgeries = [event for event in data if datetime.strptime(event['start'], '%Y-%m-%dT%H:%M:%S').date() == selected_date_obj]
    
    # Calculate percentage of surgeries with different statuses
    total_surgeries = len(surgeries)
    if total_surgeries == 0:
        percentages = [0, 0, 0]
        counts = [0, 0, 0]
    else:
        ontime_count = sum(1 for event in surgeries if event.get('extendedProps', {}).get('statuses') == 'ontime')
        #cancelled_count = sum(1 for event in surgeries if event.get('extendedProps', {}).get('statuses') == 'cancelled')
        shifted_count = sum(1 for event in surgeries if 'shift' in event.get('extendedProps', {}).get('statuses', ''))
        
        percentages = [
            ontime_count / total_surgeries * 100,
            shifted_count / total_surgeries * 100
        ]
        counts = [ontime_count, shifted_count]
    
    # Generate plot for surgery statuses
    fig, axs = plt.subplots(2, 1, figsize=(8, 12))

    categories = ['Ontime', 'Shifted']
    axs[0].bar(categories, percentages, color=['green', 'red'])
    axs[0].set_title('Surgeries Status on ' + selected_date)
    axs[0].set_xlabel('Status')
    axs[0].set_ylabel('Percentage')
    axs[0].set_ylim(0, 100)
    axs[0].set_yticks(range(0, 101, 10))  # Set y-axis ticks at intervals of 10%
    
    for i, (cat, perc, count) in enumerate(zip(categories, percentages, counts)):
        text_y_position = perc + 2 if perc < 100 else perc +1  # Adjust label position for 100%
        axs[0].text(i, text_y_position, f"{perc:.2f}% ({count})", ha='center', color='black')    
    # Extract reasons and calculate their frequency
    shifted_events = [event for event in surgeries if 'shift' in event.get('extendedProps', {}).get('statuses', '')]
    total_shifted = len(shifted_events)
    reasons = [event.get('extendedProps', {}).get('reason', 'Unknown') for event in shifted_events]
    reason_counts = {}
    for reason in reasons:
        if reason in reason_counts:
            reason_counts[reason] += 1
        else:
            reason_counts[reason] = 1
    
    reason_labels = list(reason_counts.keys())
    reason_values = list(reason_counts.values())
    reason_percentages = [count / total_shifted * 100 for count in reason_values]
    
    # Generate plot for reasons
    axs[1].bar(reason_labels, reason_percentages, color='blue')
    axs[1].set_title('Reasons for Shifted Surgeries on ' + selected_date)
    axs[1].set_xlabel('Reason')
    axs[1].set_ylabel('Percentage')
    axs[1].set_ylim(0, 105)  # Increase the y-limit to 105 to provide space for labels
    axs[1].set_yticks(range(0, 101, 10))  # Set y-axis ticks at intervals of 10%

    for i, (label, perc, count) in enumerate(zip(reason_labels, reason_percentages, reason_values)):
        text_y_position = perc + 2 if perc < 100 else perc+1  # Adjust label position for 100%
        axs[1].text(i, text_y_position, f"{perc:.2f}% ({count})", ha='center', color='black')
    
    plt.tight_layout()
    
    # Convert plot to base64 encoded string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return plot_data

def generate_multi(from_date,to_date):
    with open('events.json', 'r') as file:
        data = json.load(file)
    if from_date and to_date:
            start_date_obj = datetime.strptime(from_date, '%Y-%m-%d').date()
            end_date_obj = datetime.strptime(to_date, '%Y-%m-%d').date() + timedelta(days=1)  # Include end date
            surgeries = [event for event in data if start_date_obj <= datetime.strptime(event['start'], '%Y-%m-%dT%H:%M:%S').date() < end_date_obj]
            title_suffix = f'from {from_date} to {to_date}'
    else:
        return jsonify({'error': 'Invalid request parameters'}), 400
    
    total_surgeries = len(surgeries)
    
    if total_surgeries == 0:
        percentages = [0, 0, 0]
        counts = [0, 0, 0]
        reasons_data = []
    else:
        ontime_count = sum(1 for event in surgeries if event.get('extendedProps', {}).get('statuses') == 'ontime')
        shifted_count = sum(1 for event in surgeries if 'shift' in event.get('extendedProps', {}).get('statuses', ''))
        
        percentages = [
            ontime_count / total_surgeries * 100,
            shifted_count / total_surgeries * 100
        ]
        counts = [ontime_count, shifted_count]
        
        shifted_events = [event for event in surgeries if 'shift' in event.get('extendedProps', {}).get('statuses', '')]
        reasons_data = []
        for event in shifted_events:
            reasons = event.get('extendedProps', {}).get('reason', [])
            if isinstance(reasons, list):
                reasons_data.extend(reasons)
                
            elif isinstance(reasons, str):
                reasons_data.append(reasons)            

            else:
                reasons_data.append('Unknown')
                
    
    # Generate plots
    fig, axs = plt.subplots(2, 1, figsize=(10, 12))

    # Plot for statuses
    categories = ['Ontime', 'Shifted']
    axs[0].bar(categories, percentages, color=['green', 'red'])
    axs[0].set_title(f'Surgeries Status {title_suffix}')
    axs[0].set_xlabel('Status')
    axs[0].set_ylabel('Percentage')
    axs[0].set_ylim(0, 105)  # Increase the y-limit to provide space for labels
    axs[0].set_yticks(range(0, 101, 10))  # Set y-axis ticks at intervals of 10%

    for i, (cat, perc, count) in enumerate(zip(categories, percentages, counts)):
        text_y_position = perc + 2 if perc < 100 else perc +1  # Adjust label position for 100%
        axs[0].text(i, text_y_position, f"{perc:.2f}% ({count})", ha='center', color='black')
        

    # Plot for reasons
    if reasons_data:
        reason_counts = {reason: reasons_data.count(reason) for reason in set(reasons_data)}
        reason_percentages = {reason: count / len(shifted_events) * 100 for reason, count in reason_counts.items()}
        sorted_reasons = sorted(reason_counts.keys(), key=lambda x: reason_counts[x], reverse=True)
        
        axs[1].bar(sorted_reasons, [reason_percentages[r] for r in sorted_reasons], color='blue')
        axs[1].set_title(f'Reasons for Shifted Surgeries {title_suffix}')
        axs[1].set_xlabel('Reason')
        axs[1].set_ylabel('Percentage')
        axs[1].set_ylim(0, 105)  # Increase the y-limit to provide space for labels
        axs[1].set_yticks(range(0, 101, 10))  # Set y-axis ticks at intervals of 10%

        for i, reason in enumerate(sorted_reasons):
            text_y_position = reason_percentages[reason] + 2 if reason_percentages[reason] < 100 else reason_percentages[reason] +1
            axs[1].text(i, text_y_position, f"{reason_percentages[reason]:.2f}% ({reason_counts[reason]})", ha='center', color='black')

    #plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, hspace=0.5)  # Adjust margins and spacing
    plt.tight_layout()
    # Convert plot to base64 encoded string
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)
    plot_data = base64.b64encode(buffer.getvalue()).decode('utf-8')
    
    return plot_data    
    
@app.route('/generate-report', methods=['POST'])
def generate_report_route():
    selected_date = request.json['date']
    plot_data=generate_report(selected_date)
    return plot_data, 200, {'Content-Type': 'image/png'}

@app.route('/generate-multi', methods=['POST'])
def generate_multi_route():
    from_date = request.json['from']
    to_date = request.json['to']
    
    plot_data=generate_multi(from_date,to_date)
    return plot_data, 200, {'Content-Type': 'image/png'}

    
@app.route('/Credentialing_Application')
def application():
    return render_template('Credentialing Application.html')

@app.route('/recep_sign')
def recep_sign():
    return render_template('recep_sign.html')

surgeon_ids = ['2074721941','2453973931','1012539852','1016431437','1007897885']
used_surgeon_ids = set()

def get_unique_surgeon_id():
    c.execute('SELECT unique_id FROM credentials')
    results = c.fetchall()
    for row in results:
        used_surgeon_ids.add(row[0])    
    for surgeon_id in surgeon_ids:
        if surgeon_id not in used_surgeon_ids:
            used_surgeon_ids.add(surgeon_id)
            return surgeon_id
def get_unique_recep_id():
    random_number = random.randint(100000, 999999)
        # Create the unique ID with the prefix 'REC'
    unique_id = f'REC{random_number}'
    return unique_id    
# Initialize the database connection
def initialize_database():
    # Create the credentials table if it doesn't exist
    create_table_query = """
        CREATE TABLE IF NOT EXISTS scheduling.credentials (
            full_name VARCHAR(255),
            phone VARCHAR(20) UNIQUE,
            email VARCHAR(255) UNIQUE,
            password VARCHAR(255) UNIQUE,
            unique_id VARCHAR(255) UNIQUE,
            country_location VARCHAR(100),
            address VARCHAR(255),
            national_id VARCHAR(50) UNIQUE,
            age INT,
            gender VARCHAR(10),
            marital_status VARCHAR(10),
            department VARCHAR(50),
            emergency_name VARCHAR(255),
            relationship VARCHAR(20),
            emergency_phone VARCHAR(20) UNIQUE,
            highest_degree VARCHAR(50),
            edu_location VARCHAR(100),
            institution VARCHAR(255),
            major VARCHAR(255),
            graduation_year INT,
            graduation_photo VARCHAR(255),
            specialized_training VARCHAR(255),
            certification_name VARCHAR(255),
            issuing_organization VARCHAR(255),
            year_obtained INT,
            training_location VARCHAR(100),
            training_photo VARCHAR(255),
            professional_license VARCHAR(255),
            license_number VARCHAR(50) UNIQUE,
            issuing_location VARCHAR(100),
            expiration_date DATE,
            employer_name VARCHAR(255),
            previous_position VARCHAR(255),
            work_location VARCHAR(100),
            previous_start_date DATE,
            previous_end_date DATE,
            reference1_name VARCHAR(255),
            reference1_position VARCHAR(255),
            reference1_phone VARCHAR(20) UNIQUE,
            reference1_email VARCHAR(255) UNIQUE,
            total_weight INT
        )"""
        
    
    create_recep_query = """
        CREATE TABLE IF NOT EXISTS scheduling.receptionists (
        full_name VARCHAR(255),
            phone VARCHAR(20) UNIQUE,
            email VARCHAR(255) UNIQUE,
            password VARCHAR(255) UNIQUE,
            unique_id VARCHAR(255) UNIQUE,
            country_location VARCHAR(100),
            address VARCHAR(255),
            national_id VARCHAR(50) UNIQUE,
            age INT,
            gender VARCHAR(10),
            marital_status VARCHAR(10))"""
    c.execute(create_table_query)
    conn.commit()
    c.execute(create_recep_query)
    conn.commit()    

@app.route('/submit_recep', methods=['POST'])
def submit_recep():
    if request.method == 'POST':
        # Extract form data
        full_name = request.form['full-name']
        phone=request.form['phone-drop']
        email=request.form['email']
        password=request.form['password']
        country_location=request.form['country-location']
        address=request.form['address']
        national_id=request.form['national-id']
        age=request.form['age']    
        gender = request.form.get('gender')
        marital_status = request.form.get('marital-status')
        try:
            #hashed_password = bcrypt.hash(password)
            hashed_password = generate_password_hash(password)
            
        except AttributeError:
            pass
        c.execute('SELECT unique_id FROM receptionists WHERE national_id = %s', (national_id,))
        result = c.fetchone()
        
        if result:
            unique_id = result[0]
        else:
            unique_id = get_unique_recep_id()
            if not unique_id:
                return jsonify({'error': 'Failed to generate unique ID'})
        insert_query = """
        INSERT INTO receptionists (
            full_name, phone, email, password, unique_id, country_location, address, national_id, age, gender,
            marital_status) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"""
        try:
            c.execute(insert_query, (
                full_name, phone, email, hashed_password, unique_id, country_location, address, national_id,
                int(age), gender, marital_status))
            conn.commit()
            #print("Insertion successful.")
        except Exception as e:
            conn.rollback()  # Rollback the transaction if an error occurs
            print("Error during insertion:", e)  
            return jsonify({'error': 'Failed to save data to the database'})
        time.sleep(30 * 60)  # Sleep for 30 minutes
        return ''        

@app.route('/submit', methods=['POST'])
def submit():
    if request.method == 'POST':
        # Extract form data
        full_name = request.form['full-name']
        phone=request.form['phone-drop']
        email=request.form['email']
        password=request.form['password']
        country_location=request.form['country-location']
        address=request.form['address']
        national_id=request.form['national-id']
        age=request.form['age']    
        gender = request.form.get('gender')
        marital_status = request.form.get('marital-status')
        department = request.form.get('surgery-type')
        emergency_name = request.form['emergency-name']
        relationship = request.form.get('relationship')
        emergency_phone = request.form['emp-drop']
        highest_degree = request.form.get('highest-degree')
        edu_location = request.form['edu-location']
        institution = request.form['institution']
        major = request.form['major']
        graduation_year = request.form['graduation-year']
        graduation_photo = request.files['graduation-photo']
        specialized_training = request.form['specialized-training']
        certification_name = request.form['certification-name']
        issuing_organization = request.form['issuing-organization']
        year_obtained = request.form['date-obtained']
        training_location = request.form['training-location']
        training_photo = request.files['training-photo']
        professional_license = request.form['professional-license']
        license_number = request.form['license-number']
        issuing_location = request.form['issuing-location']
        expiration_date = request.form['expiration-date']
        employer_name = request.form['employer-name']
        previous_position = request.form['previous-position']
        work_location = request.form['work-location']
        training_weight = request.form.get('weight-display')
        graduation_weight = request.form.get('graduation-weight')
        work_weight = request.form.get('work-weight')        
        
        previous_start_date = request.form['previous-start-date']
        previous_end_date = request.form['previous-end-date']
        reference1_name = request.form['reference1-name']
        reference1_position = request.form['reference1-position']
        reference1_phone = request.form['ref-drop']
        reference1_email = request.form['reference1-email']
        
        
        total_weight= int(training_weight)+int(graduation_weight)+int(work_weight)
        
        previous_start_date_obj = datetime.strptime(previous_start_date, "%Y-%m-%d")
        previous_start_date_formatted = previous_start_date_obj.strftime("%Y-%m-%d")
        
        previous_end_date_obj = datetime.strptime(previous_end_date, "%Y-%m-%d")
        previous_end_date_formatted = previous_end_date_obj.strftime("%Y-%m-%d")        
        
        expiration_date_obj = datetime.strptime(expiration_date, "%Y-%m-%d")
        expiration_date_formatted = expiration_date_obj.strftime("%Y-%m-%d")
        
        
        
        try:
            #hashed_password = bcrypt.hash(password)
            hashed_password = generate_password_hash(password)
            
        except AttributeError:
            pass        
            
        graduation_file_path = 'C:\\Users\\gsags\\Downloads\\Grad_html\\photos\\' + graduation_photo.filename
        graduation_photo.save(graduation_file_path)
            

        training_file_path = 'C:\\Users\\gsags\\Downloads\\Grad_html\\photos\\' + training_photo.filename
        training_photo.save(training_file_path)      
        
        
        # Check if the national ID already has a unique ID
        c.execute('SELECT unique_id FROM credentials WHERE national_id = %s', (national_id,))
        result = c.fetchone()
        
        if result:
            unique_id = result[0]
        else:
            unique_id = get_unique_surgeon_id()
            if not unique_id:
                return jsonify({'error': 'Failed to generate unique ID'})
        
        create_slot_query= f"""CREATE TABLE IF NOT EXISTS {unique_id}_slots(
        SlotID INT AUTO_INCREMENT PRIMARY KEY,
        selected_day VARCHAR(10),
        slot_from TIME,
        slot_to TIME)"""
        c.execute(create_slot_query)
        conn.commit()
        
        slots = []
        slot_count = 1
        while f'day-dropdown-{slot_count}' in request.form:
            day = request.form[f'day-dropdown-{slot_count}']
            slot_from = request.form[f'slot{slot_count}-from']
            slot_to = request.form[f'slot{slot_count}-to']
            
            from_obj = datetime.strptime(slot_from, "%H:%M")
            from_formatted = from_obj.strftime("%H:%M") 
            
            to_obj = datetime.strptime(slot_to, "%H:%M")
            to_formatted = to_obj.strftime("%H:%M")    
            
            slots.append((day, from_formatted, to_formatted))
            slot_count += 1        
        
        insert_slot_query= f"""INSERT INTO {unique_id}_slots( selected_day, slot_from, slot_to) VALUES (
            %s, %s, %s)"""
        try:
            c.executemany(insert_slot_query, slots)
            conn.commit()
            #print("Insertion successful.")
        except Exception as e:
            conn.rollback()  # Rollback the transaction if an error occurs
            print("Error during insertion:", e)  
            return jsonify({'error': 'Failed to save data to the database'})     
        
        
        insert_query = """
        INSERT INTO credentials (
            full_name, phone, email, password, unique_id, country_location, address, national_id, age, gender,
            marital_status, department, emergency_name, relationship, emergency_phone, highest_degree,
            edu_location, institution, major, graduation_year, graduation_photo, specialized_training,
            certification_name, issuing_organization, year_obtained, training_location, training_photo,
            professional_license, license_number, issuing_location, expiration_date, employer_name,
            previous_position, work_location, previous_start_date, previous_end_date, reference1_name,
            reference1_position, reference1_phone, reference1_email,total_weight
        ) VALUES (
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
        )
        """       
        try:
            c.execute(insert_query, (
                full_name, phone, email, hashed_password, unique_id, country_location, address, national_id,
                int(age), gender, marital_status, department, emergency_name, relationship, emergency_phone, highest_degree, edu_location, institution, major, int(graduation_year),
                graduation_file_path, specialized_training, certification_name, issuing_organization,
                int(year_obtained), training_location, training_file_path, professional_license, license_number,
                issuing_location, expiration_date_formatted, employer_name, previous_position, work_location,
                previous_start_date_formatted, previous_end_date_formatted, reference1_name, reference1_position,
                reference1_phone, reference1_email, int(total_weight)
            ))
            conn.commit()
            #print("Insertion successful.")
        except Exception as e:
            conn.rollback()  # Rollback the transaction if an error occurs
            print("Error during insertion:", e)  
            return jsonify({'error': 'Failed to save data to the database'})
            
        # Redirect to another page after form submission
        if relationship == 'other':
            other_relationship = request.form['other-relationship']
        else:
            other_relationship = None 
        
        if highest_degree == 'Other':
            other_degree = request.form['other-degree']
        else:
            other_degree = None
        time.sleep(30 * 60)  # Sleep for 30 minutes
        return ''


@app.route('/get_unique_id', methods=['GET'])
def get_unique_id():
    national_id = request.args.get('national-id')

    c.execute('SELECT unique_id FROM credentials WHERE national_id = %s', (national_id,))
    result = c.fetchone()

    if result:
        unique_id = result[0]
        return jsonify({'uniqueId': unique_id})
    else:
        return jsonify({'error': 'Unique ID not found'})

@app.route('/get_recep_id', methods=['GET'])
def get_recep_id():
    national_id = request.args.get('national-id')

    c.execute('SELECT unique_id FROM receptionists WHERE national_id = %s', (national_id,))
    result = c.fetchone()

    if result:
        unique_id = result[0]
        return jsonify({'uniqueId': unique_id})
    else:
        return jsonify({'error': 'Unique ID not found'})    



@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        # Handle GET request (e.g., render the login form)
        return render_template('login.html')
    elif request.method == 'POST':
        entered_id = request.form['ID']
        entered_password = request.form['password']
        if entered_id.startswith('REC'):
            c = conn.cursor(dictionary=True)  # Ensure the cursor returns dictionaries        
            query = 'SELECT unique_id, password FROM receptionists WHERE unique_id = %s'
            c.execute(query, (entered_id,))
            user = c.fetchone()            
            if user and check_password_hash(user['password'], entered_password):
                        # Redirect to receptionist view page
                return redirect(url_for('file_upload_html'))
            else:
                    # Handle authentication failure
                return render_template('login.html', error='Invalid ID or password')            
        else:
            c = conn.cursor(dictionary=True)  # Ensure the cursor returns dictionaries        
            query = 'SELECT unique_id, password FROM credentials WHERE unique_id = %s'
            c.execute(query, (entered_id,))
            user = c.fetchone()            
            if user and check_password_hash(user['password'], entered_password):            
                session['doctor_id'] = entered_id                
                return redirect(url_for('doc', doctor_id=entered_id))                
            else:
                    # Handle authentication failure
                return render_template('login.html', error='Invalid ID or password')     
        
@app.route('/doc')                
@app.route('/doc/<doctor_id>')
def doc(doctor_id=None):
    if doctor_id:
        return render_template('doc.html', doctor_id=doctor_id)
    else:
        pass

@app.route('/receptionist_2')
def receptionist_2():
    return render_template('receptionist_2.html')

def get_local_ip():
    # Get the local IP address of the machine
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))
    local_ip = s.getsockname()[0]
    s.close()
    return local_ip

if __name__ == '__main__':
    initialize_database()    
    local_ip = get_local_ip()
    local_url = f'http://{local_ip}:5000'
    localhost_url = 'http://127.0.0.1:5000'
    custom_url = 'http://ai-surgekit:5000'  # Custom URL

    print(f'Local URL: {local_url}')
    print(f'Localhost URL: {localhost_url}')
    print(f'Custom URL: {custom_url}')

    app.run(host='0.0.0.0', port=5000)