# Set env var OPENAI_API_KEY or load from a .env file:
# import dotenv
# dotenv.load_dotenv()

from langchain.document_loaders import AsyncChromiumLoader
from langchain.document_transformers import BeautifulSoupTransformer
import re
import json

# Load HTML
loader = AsyncChromiumLoader(["https://rostender.info/extsearch/advanced?query=835681f1eba5f4f6503ca23680c3c35b"])
html = loader.load()

# Transform
bs_transformer = BeautifulSoupTransformer()
docs_transformed = bs_transformer.transform_documents(html,tags_to_extract=["a","span"])


result = docs_transformed[0].page_content[0:2000000]

# Patterns to capture the tender details: Link and Region
pattern = re.compile(r'\((/tender/\d+)\)\s*([\w\s\-]+)')
matches = pattern.findall(result)

# Using a set to track processed tenderIds
seen_tender_ids = set()
tenders = []

for match in matches:
    tender_id = match[0].split("/")[-1]
    if tender_id not in seen_tender_ids:
        seen_tender_ids.add(tender_id)

        tenders.append({
            "tenderId": tender_id,
            "region": match[1].strip(),
            "link": "https://rostender.info" + match[0]
        })

# Save to JSON
with open("tenders.json", "w", encoding='utf-8') as f:
    json.dump(tenders, f, ensure_ascii=False, indent=4)