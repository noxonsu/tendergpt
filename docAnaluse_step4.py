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

from langchain.vectorstores import Chroma

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

import json 
import os

with open('tenders.json', 'r', encoding='utf-8') as f:
    tenders = json.load(f)

# LLM and RAG setup (moved up to avoid re-initializing for every tender)
from langchain import hub
rag_prompt = hub.pull("rlm/rag-prompt")
from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema.runnable import RunnablePassthrough
any_tender_to_process = False
for idx, tender in enumerate(tenders):
    if 'gptresult' not in tender:
        tenders[idx]['gptresult'] = "processing"
        any_tender_to_process = True 
        # Save the updated tenders list back to the tenders.json file
        with open('tenders.json', 'w', encoding='utf-8') as f:
            json.dump(tenders, f, ensure_ascii=False, indent=4)
        keyword = tender.get('keyword', None)
        if not keyword:
            print(f"Keyword not found in the tender at index {idx}.")
            continue

        file_extension = os.path.splitext(tender['documentationfilepath'])[1]
        loader_cls = loaders.get(file_extension, None)
        if not loader_cls:
            print(f"No loader found for file type: {file_extension} for the tender at index {idx}.")
            os.remove(tender['documentationfilepath'])
            continue

        loader = loader_cls(tender['documentationfilepath'])

        
        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        splits = text_splitter.split_documents(loader.load())

        vectorstore = Chroma.from_documents(documents=splits, embedding=OpenAIEmbeddings())
        retriever = vectorstore.as_retriever()

        rag_chain = (
            {"context": retriever, "question": RunnablePassthrough()}
            | rag_prompt
            | llm
        )
        
        gptresult = rag_chain.invoke("Есть ли упоминание " + keyword + "? Если да, то нужно ли им поставлять это вещество и в каком объеме? Так же если документе есть адрес (куда поставить) выведи его. Если не упоминается, то выведи 'Нет упоминания'")
        print(str(idx)+' '+keyword+' '+gptresult.content)


        os.remove(tender['documentationfilepath'])
        
        tenders[idx]['gptresult'] = gptresult.content
        tenders[idx]['url'] = 'https://rostender.info/tender/' + tender['tenderId']
        tenders[idx]['documentationurl'] = 'https://github.com/noxonsu/tendergpt/raw/main/'+tender['tenderId']+'.md'
        if "Нет упоминания" not in gptresult.content:
            # Construct the webhook URL with the tender data
            tender_data_json = json.dumps(tender, ensure_ascii=False)
            webhook_url = f"https://noxon.wpmix.net/counter.php?totenders=1&msg={tender_data_json}"
            
            # Send a POST request to the webhook URL
            response = requests.post(webhook_url)
            if response.status_code != 200:
                print(f"Failed to send webhook for tender at index {idx}. Status code: {response.status_code}")


# If there's no tender to process, print a message
if not any_tender_to_process:
    print("All tenders have been queried. Nothing to analyze.")

# Save the updated tenders list back to the tenders.json file
with open('tenders.json', 'w', encoding='utf-8') as f:
    json.dump(tenders, f, ensure_ascii=False, indent=4)