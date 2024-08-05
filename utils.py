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

load_dotenv()

conn = sqlite3.connect("convo_data", check_same_thread=False)
cursor = conn.cursor()
cursor.execute(
    """CREATE TABLE IF NOT EXISTS convo_data (uid TEXT, query TEXT, response TEXT, time TIMESTAMP)"""
)
conn.commit()


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
                "content" : """You are a very helpful personal assistant. You're given context and chat history consisting of last 3 user queries and reponses in decreasing order. Find the context from the given context and chat history and then answer the given query appropriately. Answer concisely. Do not provide sentences greater than 20 words in length. Do not assume your own context. If some context is missing, simply tell the user that the question is missing some context."""
            },
            {
                "role" : "user",
                "content" : f"""{query} \n Context : {context} \n Chat history : {t}"""
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
        """SELECT * FROM convo_data WHERE uid == (?) ORDER BY time DESC LIMIT 3""",
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