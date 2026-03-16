import streamlit as st
import os
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter 
from langchain_community.vectorstores import Chroma
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

# --- 1. HARDCODED CONFIGURATION ---
# IMPORTANT: Use a NEW key. Delete the one ending in 355d from your dashboard.
MY_API_KEY = "YOUR_API_KEY"
OPENROUTER_URL = "https://openrouter.ai/api/v1"

# --- 2. STREAMLIT UI SETUP ---
st.set_page_config(page_title="Company Support Portal", page_icon="🚗")
st.title("🚗 City 5th Gen - Staff Assistant")
st.info("System is running on the local server. Documents are confidential.")
S
# --- 3. DOCUMENT PROCESSING ---
@st.cache_resource
def initialize_system():
    # Update this path to where your PDF is located
    file_path = "/Users/krrishdeshpande/Desktop/pdfs/city 5th generation - 2022.pdf"
    
    if not os.path.exists(file_path):
        st.error(f"File not found: {file_path}")
        return None

    # Load and Split PDF
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = text_splitter.split_documents(documents)

    # FIX: Point Embeddings to OpenRouter to avoid the 401 Error
    embeddings = OpenAIEmbeddings(
        openai_api_key=MY_API_KEY,
        base_url=OPENROUTER_URL,
        check_embedding_ctx_length=False # Necessary for OpenRouter
    )

    # Use ChromaDB (it creates a local 'vector' folder in your directory)
    vectorstore = Chroma.from_documents(
        documents=docs, 
        embedding=embeddings,
        persist_directory="./chroma_db" 
    )
    return vectorstore.as_retriever()

# Initialize the internal engine
retriever = initialize_system()

# --- 4. CHAT INTERFACE ---
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# User Input Box
if user_query := st.chat_input("Ask about vehicle specs or maintenance..."):
    st.session_state.messages.append({"role": "user", "content": user_query})
    with st.chat_message("user"):
        st.markdown(user_query)

    with st.chat_message("assistant"):
        if retriever:
            # Setup the Chat Model
            llm = ChatOpenAI(
                openai_api_key=MY_API_KEY,
                base_url=OPENROUTER_URL,
                model="openrouter/hunter-alpha"
            )
            
            template = """Answer the question based strictly on the following context:
            {context}
            
            Question: {question}
            
            If the answer is not in the context, say "I don't have that information in the manual."
            """
            prompt = ChatPromptTemplate.from_template(template)
            
            # The RAG Chain
            chain = (
                {"context": retriever, "question": RunnablePassthrough()}
                | prompt
                | llm
                | StrOutputParser()
            )
            
            response = chain.invoke(user_query)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})