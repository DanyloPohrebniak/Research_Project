from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGODB_URL", "mongodb://openedx:password@mongodb:27017")
mongo = MongoClient(MONGO_URL)
db = mongo["openedx"]

structures = list(db["modulestore.structures"].find(
    {"blocks.block_type": {"$in": ["html", "problem"]}},
    {"blocks": 1}
).limit(50))

print("Checking all html/problem blocks across first 50 structures:")
found_data = 0
no_data = 0

for structure in structures:
    blocks = structure.get("blocks", {})
    if isinstance(blocks, dict):
        blocks_list = list(blocks.values())
    else:
        blocks_list = blocks

    for block in blocks_list:
        if block.get("block_type") not in ["html", "problem"]:
            continue

        fields = block.get("fields", {})
        definition_id = block.get("definition")
        if not fields and definition_id:
            defn = db["modulestore.definitions"].find_one(
                {"_id": definition_id},
                {"fields": 1, "block_type": 1}
            )
            if defn:
                fields = defn.get("fields", {})
                has_data = bool(fields.get("data", ""))
                if has_data:
                    found_data += 1
                    print(f"  HAS DATA: def_id={definition_id} data_len={len(fields['data'])} preview={fields['data'][:60]!r}")
                else:
                    no_data += 1
            else:
                print(f"  DEF NOT FOUND: {definition_id}")

print(f"\nSummary: found_data={found_data}, no_data={no_data}")
mongo.close()
