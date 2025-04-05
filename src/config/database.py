from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

MONGO_URI = os.getenv('MONGO_URI', 'mongodb://localhost:27017')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'litscout')

client = MongoClient(MONGO_URI)
db = client[DATABASE_NAME]

# Collections
users = db.users
research_data = db.research_data
