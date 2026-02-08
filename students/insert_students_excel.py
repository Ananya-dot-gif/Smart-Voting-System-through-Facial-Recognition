import pandas as pd
from pymongo import MongoClient

# MongoDB Connection
client = MongoClient("mongodb://localhost:27017/")  # or your Atlas URI
db = client["smartVoting"]
collection = db["students_list"]

# Load Excel file
file_path = "Student_List.xlsx"
df = pd.read_excel(file_path)

# Clean column names (since Excel has colons)
df.columns = [col.strip().replace(":", "").replace(" ", "_").lower() for col in df.columns]

# Prepare student data
students = []
for _, row in df.iterrows():
    student = {
        "usn": str(row["usn"]),
        "name": str(row["name"]),
        "phone": str(row["contact_numb"]),
        "email": str(row["email_id"]),
        "is_registered": False
    }
    students.append(student)

# Insert into MongoDB
if students:
    collection.insert_many(students)
    print(f"{len(students)} students added successfully!")
else:
    print("No student records found in Excel file.")

