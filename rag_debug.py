from pymongo import MongoClient
import os, re

MONGO_URL = os.getenv("MONGODB_URL", "mongodb://openedx:password@mongodb:27017")
mongo = MongoClient(MONGO_URL)
db = mongo["openedx"]

structures = list(db["modulestore.structures"].find(
    {"blocks.block_type": {"$in": ["html", "problem", "video"]}},
    {"blocks": 1}
).limit(50))
print("structures found:", len(structures))

total = 0
skipped_no_fields = 0
skipped_short = 0
processed = 0

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
        if not fields and block.get("definition"):
            definition = db["modulestore.definitions"].find_one(
                {"_id": block["definition"]},
                {"fields": 1}
            )
            if definition:
                fields = definition.get("fields", {})
            else:
                skipped_no_fields += 1
                continue

        text = ""
        if block_type == "html":
            text = re.sub(r"<[^>]+>", " ", fields.get("data", ""))
        elif block_type == "problem":
            text = re.sub(r"<[^>]+>", " ", fields.get("data", ""))
        elif block_type == "video":
            text = fields.get("display_name", "")

        text = text.strip()
        if len(text) < 50:
            skipped_short += 1
            continue

        processed += 1
        print(f"WOULD INDEX: {block_type} len={len(text)} preview={text[:80]!r}")

print(f"processed={processed} skipped_no_fields={skipped_no_fields} skipped_short={skipped_short}")
mongo.close()
