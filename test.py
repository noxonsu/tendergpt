from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter

from langchain.document_loaders import UnstructuredWordDocumentLoader
from langchain.document_loaders import DirectoryLoader
from langchain.document_loaders.pdf import PyMuPDFLoader
from langchain.document_loaders.xml import UnstructuredXMLLoader
from langchain.document_loaders.csv_loader import CSVLoader
from langchain.document_loaders.unstructured import UnstructuredFileLoader
from langchain.document_loaders import Docx2txtLoader

import os
import requests


__import__('pysqlite3')
import sys
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')


import chromadb
chroma_client = chromadb.Client()
# Define a dictionary to map file extensions to their respective loaders
loaders = {
    '.pdf': PyMuPDFLoader,
    '.xml': UnstructuredXMLLoader,
    '.csv': CSVLoader,
    '.doc': UnstructuredFileLoader,
    '.DOC': UnstructuredFileLoader,
    '.xlsx': UnstructuredFileLoader,
    '.xls': UnstructuredFileLoader,
    '.docx': Docx2txtLoader
}

# LLM and RAG setup (moved up to avoid re-initializing for every tender)
from langchain import hub
rag_prompt = hub.pull("rlm/rag-prompt")
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.runnable import RunnablePassthrough
tender=[]
documentationfilepath = "71044343_Извещение.doc"

file_extension = os.path.splitext(documentationfilepath)[1]
loader_cls = loaders.get(file_extension, None)

if not loader_cls:
    print(f"No loader found for file type: {file_extension} for the tender at index {idx}.")
            #os.remove(tender['documentationfilepath'])
            #continue

loader = loader_cls(documentationfilepath)

        
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        
        #try splits catch and continue if error
try:
    splits = text_splitter.split_documents(loader.load())
except:
    print("split error")


        
import chromadb
chroma_client = chromadb.Client()
collection = chroma_client.create_collection(name="my_collection")