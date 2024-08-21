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
from load_crew import *

load_dotenv()

#db0 will be used to store client conversation  {user_id : [[query, response], [q, r],....]}
client0 = redis.Redis(host='localhost', port=6379, db=0)


def process_query(data):    
    query = data["query_text"]

    # fetch last 3 messages from db, for chat history
    t = fetch_chat_history()
    
    user_input = {
        "query" : f"Query : {query} \n Chat History : {t}"
    }

    result = crew.kickoff(inputs=user_input)
    
    #create json to resturn to js
    data = {"response" : str(result)}

    #save message in db
    save_in_db(query, data["response"])

    return data

def process_file(file):
    print(datetime.now())
    pdfReader = PdfReader(file)

    text = ""
    for page in pdfReader.pages:
        text += page.extract_text()
    
    print("Text extraction")
    print(datetime.now())
        
    #chunking
    chunks = create_chunks(text)

    print("chunking")
    print(datetime.now())

    #create and store embeddings
    create_store_embeds(chunks)

    print("storing vectors in db----")
    print(datetime.now())

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
    docs = db.similarity_search(query, k=3)

    context = ""
    for i in range(len(docs)):
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
        return ""