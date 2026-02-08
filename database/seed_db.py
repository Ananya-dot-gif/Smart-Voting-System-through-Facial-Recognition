from pymongo import MongoClient

client = MongoClient("mongodb://localhost:27017/")
db = client["smartVoting"]

# insert one voter (creates the collection if it doesn't exist)
voter_id = db.voters.insert_one({
    "name": "Alice",
    "email": "alice@example.com",
    "password_hash": "hashed_password_here",
    "face_encoding": [0.1, 0.23, 0.45, 0.67]
}).inserted_id

# insert one candidate
candidate_id = db.candidates.insert_one({
    "name": "John Doe",
    "bio": "Candidate for City Mayor"
}).inserted_id

# insert one vote
db.votes.insert_one({
    "voter_id": voter_id,
    "candidate_id": candidate_id
})

print("Seeded OK:", voter_id, candidate_id)
