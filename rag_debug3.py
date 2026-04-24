from pymongo import MongoClient
import os

MONGO_URL = os.getenv("MONGODB_URL", "mongodb://openedx:password@mongodb:27017")
mongo = MongoClient(MONGO_URL)
db = mongo["openedx"]

structures = list(db["modulestore.structures"].find(
    {"blocks.block_type": {"$in": ["html", "problem"]}},
    {"blocks": 1}
).limit(5))

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
        print(f"block_type={block['block_type']} fields_keys={list(fields.keys())} has_definition={bool(block.get('definition'))} not_fields={not fields}")
        break
    break

mongo.close()
