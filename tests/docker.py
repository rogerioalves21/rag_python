Choosing the data:

I chose the recent article from 10th April 2024 which Mistral could not have been trained on — https://arxiv.org/abs/2404.07143 — and downloaded the PDF file.

To provide your own data just add the file and change to the suitable text loader provided by langchain (currently raw text, CSV, HTML, MD and more are supported).

FROM python:3

WORKDIR /usr/src/app

# COPY requirements.txt ./
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir chromadb
RUN pip install --no-cache-dir langchain_community
RUN pip install --no-cache-dir langchain_text_splitters
RUN pip install --no-cache-dir sentence-transformers
RUN pip install --no-cache-dir openai
RUN pip install --no-cache-dir flask
RUN pip install --no-cache-dir ollama
RUN pip install --no-cache-dir pypdf

COPY . .

RUN python rag.py

CMD [ "python", "./rag_query.py" ]



import langchain_community
import langchain_text_splitters
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import CharacterTextSplitter

# load the document and split it into pages
loader = PyPDFLoader("2404.07143.pdf")
pages = loader.load_and_split()

# split it into chunks
text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
docs = text_splitter.split_documents(pages)

# create the open-source embedding function
embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")


# create the chroma client
import uuid
import chromadb
from chromadb.config import Settings

client = chromadb.HttpClient(host='host.docker.internal', port=8000,settings=Settings(allow_reset=True))
client.reset()  # resets the database
collection = client.create_collection("my_collection")
for doc in docs:
    collection.add(
        ids=[str(uuid.uuid1())], metadatas=doc.metadata, documents=doc.page_content
    )

# tell LangChain to use our client and collection name
db = Chroma(
    client=client,
    collection_name="my_collection",
    embedding_function=embedding_function,
)
query = "What training does the model have?"
docs = db.similarity_search(query)
print(docs[0].page_content)


import chromadb
from chromadb.config import Settings
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings.sentence_transformer import (
    SentenceTransformerEmbeddings,
)

def Extract_context(query):
    chroma_client = chromadb.HttpClient(host='host.docker.internal', port=8000,settings=Settings(allow_reset=True))
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    db = Chroma(
        client=chroma_client,
        collection_name="my_collection",
        embedding_function=embedding_function,
    )
    docs = db.similarity_search(query)
    fullcontent =''
    for doc in docs:
        fullcontent ='. '.join([fullcontent,doc.page_content])

    return fullcontent
    
def get_system_message_rag(content):
        return f"""You are an expert consultant helping executive advisors to get relevant information from internal documents.

        Generate your response by following the steps below:
        1. Recursively break down the question into smaller questions.
        2. For each question/directive:
            2a. Select the most relevant information from the context in light of the conversation history.
        3. Generate a draft response using selected information.
        4. Remove duplicate content from draft response.
        5. Generate your final response after adjusting it to increase accuracy and relevance.
        6. Do not try to summarise the answers, explain it properly.
        6. Only show your final response! 
        
        Constraints:
        1. DO NOT PROVIDE ANY EXPLANATION OR DETAILS OR MENTION THAT YOU WERE GIVEN CONTEXT.
        2. Don't mention that you are not able to find the answer in the provided context.
        3. Don't make up the answers by yourself.
        4. Try your best to provide answer from the given context.

        CONTENT:
        {content}
        """
        
        
        
        
def get_ques_response_prompt(question):
    return f"""
    ==============================================================
    Based on the above context, please provide the answer to the following question:
    {question}
    """
    
    
from ollama import Client

def generate_rag_response(content,question):
    client = Client(host='http://host.docker.internal:11434')
    stream = client.chat(model='mistral', messages=[
    {"role": "system", "content": get_system_message_rag(content)},            
    {"role": "user", "content": get_ques_response_prompt(question)}
    ],stream=True)
    print(get_system_message_rag(content))
    print(get_ques_response_prompt(question))
    print("####### THINKING OF ANSWER............ ")
    full_answer = ''
    for chunk in stream:
        print(chunk['message']['content'], end='', flush=True)
        full_answer =''.join([full_answer,chunk['message']['content']])

    return full_answer
    
    
from flask import Flask, request

@app.route('/query', methods=['POST'])
def respond_to_query():
    if request.method == 'POST':
        data = request.get_json()
        # Assuming the query is sent as a JSON object with a key named 'query'
        query = data.get('query')
        # Here you can process the query and generate a response
        response = f'This is the response to your query:\n {get_reponse(query)}'
        return response
    
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
    
    
    
docker build -t rag .
docker run -it -p 5000:5000 rag






curl -X POST http://192.168.0.31:5000/query -H "Content-Type: application/json" -d '{
"query":"What are the valuable results from this research?"
}'