import os
import face_recognition
import pandas as pd
from pymongo import MongoClient

# -----------------------------
#  MongoDB Connection
# -----------------------------
client = MongoClient("mongodb://localhost:27017/")
db = client["smartVoting"]
students_db = db["students_list"]

# -----------------------------
#  Load Excel Safely
# -----------------------------
EXCEL_FILE = "Student_List.xlsx"
df = pd.read_excel(EXCEL_FILE)

# Normalize all column names (remove spaces, lowercase them)
normalized_columns = {col: col.strip().lower() for col in df.columns}
df.rename(columns=normalized_columns, inplace=True)

# Detect the USN column automatically
usn_col = None
for col in df.columns:
    if "usn" in col.lower().replace(" ", ""):
        usn_col = col
        break

if usn_col is None:
    print("❌ ERROR: No column containing 'USN' found in the Excel file!")
    print("Columns found:", df.columns.tolist())
    exit()

print(f"✅ Detected USN column: {usn_col}")

# Collect all valid USNs
valid_usns = set(df[usn_col].astype(str).str.upper())

# -----------------------------
#  Folder containing photos
# -----------------------------
PHOTOS_FOLDER = "student_photos"

print("\n🔍 Checking student photos and inserting face encodings...\n")

for filename in os.listdir(PHOTOS_FOLDER):

    if filename.lower().endswith((".jpg", ".jpeg", ".png")):

        usn = os.path.splitext(filename)[0].upper()
        img_path = os.path.join(PHOTOS_FOLDER, filename)

        # Check if USN exists in Excel
        if usn not in valid_usns:
            print(f"❌ USN {usn} NOT found in Excel. Skipping...\n")
            continue

        print(f"📌 Processing: {usn}")

        try:
            img = face_recognition.load_image_file(img_path)
            encodings = face_recognition.face_encodings(img)

            if not encodings:
                print(f"⚠️ No face detected in {filename}. Skipping...\n")
                continue

            encoding = encodings[0].tolist()

        except Exception as e:
            print(f"❌ Error processing {filename}: {e}\n")
            continue

        # Update DB
        result = students_db.update_one(
            {"usn": usn},
            {"$set": {"face_encoding": encoding}}
        )

        if result.matched_count:
            print(f"✅ Encoding saved for {usn}\n")
        else:
            print(f"❌ DB record for {usn} not found.\n")

print("🎉 All student face encodings inserted successfully!")

