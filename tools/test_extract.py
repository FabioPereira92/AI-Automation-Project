from llm import LLMClient
import json
from pathlib import Path

p = Path(r"C:\Users\fabio\PycharmProjects\AI Automation Project\output_real\raw_responses\sample1.txt.raw.txt")
print('RAW FILE PATH:', p)
text = p.read_text(encoding='utf-8')
print('---RAW CONTENT START---')
print(text)
print('---RAW CONTENT END---')

cleaned = LLMClient._strip_code_fences(text)
print('---CLEANED---')
print(cleaned)
print('---CLEANED END---')

extracted = LLMClient.try_extract_json(text)
print('EXTRACTED:', extracted)
if extracted:
    parsed = json.loads(extracted)
    print('PARSED:', parsed)
else:
    print('No JSON extracted')

