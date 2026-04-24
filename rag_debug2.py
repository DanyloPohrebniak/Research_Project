from pymongo import MongoClient
import os, re

MONGO_URL = os.getenv("MONGODB_URL", "mongodb://openedx:password@mongodb:27017")
mongo = MongoClient(MONGO_URL)
db = mongo["openedx"]

structures = list(db["modulestore.structures"].find(
    {"blocks.block_type": {"$in": ["html", "problem", "video"]}},
    {"blocks": 1}
).limit(50))

for structure in structures:
    blocks = structure.get("blocks", [])
    if isinstance(blocks, dict):
        blocks_list = list(blocks.values())
    else:
        blocks_list = blocks

    for block in blocks_list:
        block_type = block.get("block_type", "")
        if block_type not in ["html", "problem", "video"]:
            continue

        fields = block.get("fields", {})
        defn = None
        if not fields and block.get("definition"):
            defn = db["modulestore.definitions"].find_one(
                {"_id": block["definition"]},
                {"fields": 1, "block_type": 1}
            )
            if defn:
                fields = defn.get("fields", {})

        data_raw = fields.get("data", "") if fields else ""
        text = re.sub(r"<[^>]+>", " ", data_raw).strip() if block_type in ["html", "problem"] else fields.get("display_name", "")

        print(f"type={block_type} raw_len={len(data_raw)} stripped_len={len(text)} text={text[:100]!r}")

mongo.close()
