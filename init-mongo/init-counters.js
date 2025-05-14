db = db.getSiblingDB('chat_app');

db.createCollection("counters");

db.counters.insertOne({
  _id: "user_id",
  sequence_value: 0
});