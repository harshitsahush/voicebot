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
import sqlite3
import datetime
from langchain_community.vectorstores import Redis
import redis

load_dotenv()

conn = sqlite3.connect("convo_data", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """CREATE TABLE IF NOT EXISTS convo_data (uid TEXT, query TEXT, response TEXT, time TIMESTAMP)"""
)
conn.commit()


def process_query(data):
    query = data["query_text"]   


    # get similar docs from redis
    client = redis.Redis(host='localhost', port=6379, db=0)
    key = session["uid"]
    if client.exists(key):
        context = ""
    else:
        context = sim_search(query)
    

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

    #create and store embeddings
    create_store_embeds(chunks)

def create_chunks(text):
    # recursive chunking
    text_splitter = RecursiveCharacterTextSplitter(chunk_size = 500, chunk_overlap = 100)
    chunks = text_splitter.split_text(text)
    return chunks

def create_store_embeds(chunks):
    embeddings = HuggingFaceEmbeddings()
    rdb = Redis.from_texts(
        chunks,
        embeddings,
        redis_url = os.getenv("REDIS_DB_URL"),
        index_name = session["uid"]
    )
    rdb.write_schema("redis_schema.yaml")

def sim_search(query):
    new_rds = Redis.from_existing_index(
        HuggingFaceEmbeddings(),
        index_name=session["uid"],
        redis_url = os.getenv("REDIS_DB_URL"),
        schema="redis_schema.yaml"
    )

    docs = new_rds.similarity_search(query)

    context = ""
    for i in range(min(5, len(docs))):
        context += docs[i].page_content
    return context

def save_in_db(query, response):
    currentDateTime = datetime.datetime.now()
    cursor = conn.cursor()
    
    cursor.execute(
        """INSERT INTO convo_data (uid, query, response, time) VALUES (?,?,?,?)""",
        (session["uid"], query, response, currentDateTime)
    )
    conn.commit()
    print("message saved")

def fetch_chat_history():
    cursor = conn.cursor()
    cursor.execute(
        """SELECT * FROM convo_data WHERE uid == (?) ORDER BY time DESC LIMIT 5""",
        (session["uid"],)               #in case of single element, comma is necessary
    )
    temp = cursor.fetchall()
    conn.commit()
    
    t = """"""
    for ele in temp:
        ele = list(ele)
        t += f"Query : {ele[1]} \n Response : {ele[2]} \n\n"
    
    print(t)
    return t