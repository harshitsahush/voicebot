from groq import Groq
from flask import Flask, request, render_template, redirect, jsonify, session
from flask_session import Session
import uuid
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
import glob

load_dotenv()

def process_query(data):
    data = data["query_text"]   


    # get similar docs from faiss_db
    if(glob.glob(session["uid"])):
        context = sim_search(data)
    else:
        context = ""
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    chat_completion = client.chat.completions.create(
        messages = [
            {
                "role" : "system",
                "content" : """You are a very helpful personal assistant. Respond each query ONLY from the given context. Answer concisely. Do not provide sentences greater than 20 words in length. Do not assume your own context. If some context is missing, simply tell the user that the question is missing some context."""
            },
            {
                "role" : "user",
                "content" : data + "\n\nContext: \n" + context
            }
        ],
        model = "llama3-70b-8192",
        temperature=0.1,
    )

    data = {"response" : chat_completion.choices[0].message.content}
    return data

def process_file(file):
    pdfReader = PdfReader(file)

    text = ""
    for page in pdfReader.pages:
        text += page.extract_text()
    
    #chunking
    chunks = create_chunks(text)

    #create and store embeddings
    create_store_embeds(chunks)

def create_chunks(text):
    # recursive chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 1000, chunk_overlap = 100)
    chunks = text_splitter.split_text(text)
    return chunks

def create_store_embeds(chunks):
    embeddings = HuggingFaceEmbeddings()
    db = FAISS.from_texts(chunks, embeddings)
    db.save_local(session["uid"])

def sim_search(query):
    db = FAISS.load_local(session["uid"], HuggingFaceEmbeddings(), allow_dangerous_deserialization=True)
    docs = db.similarity_search(query)

    context = ""
    for i in range(min(5, len(docs))):
        context += docs[i].page_content
    return context