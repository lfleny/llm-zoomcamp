import requests 
from elasticsearch import Elasticsearch
import tiktoken


es_client = Elasticsearch('https://localhost:9200/',
                          http_auth=['elastic', 'HS-*YQL29q=WqUEk7rh_'],
                          verify_certs=False)

try:
    info = es_client.info()
    print(info)
except Exception as e:
    print(f"Error connecting to Elasticsearch: {e}")

index_settings = {
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    },
    "mappings": {
        "properties": {
            "text": {"type": "text"},
            "section": {"type": "text"},
            "question": {"type": "text"},
            "course": {"type": "keyword"} 
        }
    }
}

index_name = 'course-questions'

try:
    es_client.indices.create(index=index_name, body=index_settings)

    docs_url = 'https://github.com/DataTalksClub/llm-zoomcamp/blob/main/01-intro/documents.json?raw=1'
    docs_response = requests.get(docs_url)
    documents_raw = docs_response.json()

    documents = []

    for course in documents_raw:
        course_name = course['course']

        for doc in course['documents']:
            doc['course'] = course_name
            es_client.index(index=index_name, document=doc)
            documents.append(doc)
except:
    pass

# query = 'How do I execute a command in a running docker container?'

# search_query = {
#     "size": 5,
#     "query": {
#         "bool": {
#             "must": {
#                 "multi_match": {
#                     "query": query,
#                     "fields": ["question^4", "text"],
#                     "type": "best_fields"
#                 }
#             },
#             # "filter": {
#             #     "term": {
#             #         "course": "data-engineering-zoomcamp"
#             #     }
#             # }
#         }
#     }
# }

# result = es_client.search(index=index_name, body=search_query)

# print(result)

query = 'How do I execute a command in a running docker container?'

search_query = {
    "size": 3,
    "query": {
        "bool": {
            "must": {
                "multi_match": {
                    "query": query,
                    "fields": ["question^4", "text"],
                    "type": "best_fields"
                }
            },
            "filter": {
                "term": {
                    "course": "machine-learning-zoomcamp"
                }
            }
        }
    }
}

result = es_client.search(index=index_name, body=search_query)

print(result)

def build_prompt(query, search_results):
    prompt_template = """
You're a course teaching assistant. Answer the QUESTION based on the CONTEXT from the FAQ database.
Use only the facts from the CONTEXT when answering the QUESTION.

QUESTION: {question}

CONTEXT: 
{context}
""".strip()

    context = ""

    context_template = """
Q: {question}
A: {text}
""".strip()
    
    for doc in search_results:
        # print(f'DOC: {doc}')
        context = context + context_template.format(question=doc['_source']['question'], text=doc['_source']['text']) + '\n\n'
    
    prompt = prompt_template.format(question=query, context=context).strip()

    print(prompt)
    return prompt

prompt = build_prompt(query, result['hits']['hits'])

print(f"Prompt len: {len(prompt)}")

encoding = tiktoken.encoding_for_model("gpt-4o")

tokens = encoding.encode(prompt)
num_tokens = len(tokens)

print(f"Количество токенов: {num_tokens}")