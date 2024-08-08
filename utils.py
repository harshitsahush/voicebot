from groq import Groq
from flask import Flask, request, render_template, redirect, jsonify, session
from flask_session import Session
import uuid
import os
from dotenv import load_dotenv
from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface.embeddings import HuggingFaceEmbeddings
from sentence_transformers import SentenceTransformer
from langchain_community.vectorstores import Redis
import redis
from redis.commands.search import Search
from datetime import datetime
import glob
from langchain_community.vectorstores import FAISS

load_dotenv()

#db0 will be used to store client conversation  {iser_id : [[query, response], [q, r],....]}
client0 = redis.Redis(host='localhost', port=6379, db=0)


def process_query(data):
    query = data["query_text"]  

    # get similar docs from faiss_db
    if(glob.glob(session["uid"])):
        context = sim_search(query)
    else:
        context = ""  

    #fetch last 3 messages from db, for chat history
    t = fetch_chat_history()
    
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))

    chat_completion = client.chat.completions.create(
        messages = [
            {
                "role" : "system",
                "content" : """You are a personal assistant AI designed to help users by answering their queries accurately and efficiently. You will be provided with a user query, relevant context, and chat history. Your task is to respond to the user's query by utilizing the provided context and chat history to ensure a VERY concise and relevant answer. Be clear, concise, and ensure your response aligns with the user's needs and the given information."""
            },
            {
                "role" : "user",
                "content" : f"""User Query : {query} \n Context : {context} \n Chat history : {t}"""
            }
        ],
        model = "llama3-70b-8192",
        temperature=0.1,
    )
    data = {"response" : chat_completion.choices[0].message.content}

    #save message in db
    save_in_db(query, data["response"])
    return data

def process_file(file):
    pdfReader = PdfReader(file)

    text = ""
    for page in pdfReader.pages:
        text += page.extract_text()
        
    #chunking
    chunks = create_chunks(text)
    print(str(datetime.now()))

    #create and store embeddings
    create_store_embeds(chunks)

    print("storing in db----")
    print(str(datetime.now()))

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
    for i in range(min(3, len(docs))):
        context += docs[i].page_content
    return context

def save_in_db(query, response):
    #no need for time, since message will always be added at the end
    client0.rpush(session["uid"], f"Query : {query} \n Response : {response}\n")

def fetch_chat_history():
    if(client0.exists(session["uid"])):
        t = ""
        temp = client0.lrange(session["uid"], 0, -1)
        for i in range(len(temp)-1, max(-1, len(temp)-1-6), -1):
            t += temp[i].decode("utf-8")
        return t
    else:
        print("No history yet")
        return ""