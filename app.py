import streamlit as st
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_text_splitters import NLTKTextSplitter
import os

with open("key/apikey.txt", "r") as f:
    YOUR_API_KEY = f.read().strip()

chat_template = ChatPromptTemplate.from_messages([
    # System Message Prompt Template
    SystemMessagePromptTemplate.from_template("You are a Helpful AI Data Science Tutor. Your name is {name}"),
    # Human Message
    HumanMessagePromptTemplate.from_template("""Answer the following question: {question}
    Answer: """)
])

chat_model = ChatGoogleGenerativeAI(google_api_key=YOUR_API_KEY,
                                    model="gemini-1.5-pro-latest")

output_parser = StrOutputParser()

chain = chat_template | chat_model | output_parser

# Load the PDF document
loader = PyPDFLoader(R"C:\Users\hp\Desktop\RAG\paper.pdf")
pages = loader.load_and_split()

# Split the document into chunks
text_splitter = NLTKTextSplitter(chunk_size=500, chunk_overlap=100)
chunks = text_splitter.split_documents(pages)

# Create the vector store
embedding_model = GoogleGenerativeAIEmbeddings(google_api_key=YOUR_API_KEY,
                                               model="models/embedding-001")
db = Chroma.from_documents(chunks, embedding_model, persist_directory="./chroma_db_")
db.persist()
db_connection = Chroma(persist_directory="./chroma_db_", embedding_function=embedding_model)
retriever = db_connection.as_retriever(search_kwargs={"k": 5})

# Streamlit app
st.set_page_config(page_title="RAG System on Leave No Context Behind Paper", layout="wide")



st.title("RAG System on Leave No Context Behind Paper 📚")

# Setting background color
st.markdown(
    """
    <style>
    body {
        background-color: #f0f2f6;
    }
    </style>
    """,
    unsafe_allow_html=True
)

user_input = st.text_area("Ask a question about the paper:", height=100)

if st.button("Submit"):
    retrieved_docs = retriever.invoke(user_input)

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chat_template = ChatPromptTemplate.from_messages([
        # system message prompt template
        SystemMessagePromptTemplate.from_template("""You are a Helpful AI Bot,
        You take the context and question from user. Your answer should be based on the specific context."""),
        # Human Message prompt template
        HumanMessagePromptTemplate.from_template("""Answer the question based on the given context.
        Context:
        {context}

        Question:
        {question}
                                                 
        Answer: """)
    ])

    rag_chain = chat_template | chat_model | output_parser

    response = rag_chain.invoke({"context": format_docs(retrieved_docs), "question": user_input})
    st.markdown(response)