from langchain.document_loaders import TextLoader
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from langchain.document_loaders import Docx2txtLoader
__import__('pysqlite3')
import sys

sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')
# Load the document, split it into chunks, embed each chunk and load it into the vector store.
loader = Docx2txtLoader("70887730_test_positive.docx")

from langchain.text_splitter import RecursiveCharacterTextSplitter

text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 0)
splits = text_splitter.split_documents(loader.load())

# Embed and store splits

from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
vectorstore = Chroma.from_documents(documents=splits,embedding=OpenAIEmbeddings())
retriever = vectorstore.as_retriever()

# Prompt 
# https://smith.langchain.com/hub/rlm/rag-prompt

from langchain import hub
rag_prompt = hub.pull("rlm/rag-prompt")

# LLM

from langchain.chat_models import ChatOpenAI
llm = ChatOpenAI(model_name="gpt-4", temperature=0)

# RAG chain 

from langchain.schema.runnable import RunnablePassthrough
rag_chain = (
    {"context": retriever, "question": RunnablePassthrough()} 
    | rag_prompt 
    | llm 
)

print(rag_chain.invoke("Мы поставляем Ксантоновая камедь, полиэфирное волокно, гуаровая камедь, диоксид титана, пальмовое масло, кокосовое масло, защищённый жир, заменитель какао масла. Проанализируй документ и найди что и в каком объеме (из того, что мы поставляем) им нужно и куда его поставить? Перечисли позиции и объем"))