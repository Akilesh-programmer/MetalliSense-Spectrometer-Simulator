import os
from pymongo import MongoClient
from urllib.parse import quote_plus
from dotenv import load_dotenv

load_dotenv()

MONGO_USER = os.getenv("MONGO_USER")
MONGO_PASS = os.getenv("MONGO_PASS") 
MONGO_CLUSTER = os.getenv("MONGO_CLUSTER")
DB_NAME = os.getenv("DB_NAME")

MONGO_URI = f"mongodb+srv://{MONGO_USER}:{MONGO_PASS}@{MONGO_CLUSTER}/{DB_NAME}?retryWrites=true&w=majority"

client = MongoClient(MONGO_URI)
db = client[DB_NAME]

def get_metal_grade_spec(grade):
    collection = db["metal_grade_specs"]
    doc = collection.find_one({"metal_grade": grade})
    if doc and "composition_range" in doc:
        return doc["composition_range"]
    else:
        raise ValueError(f"No composition range found for metal grade: {grade}")
