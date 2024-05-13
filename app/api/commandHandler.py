"""
Main module in the application architecture. This is where most everything takes place.
"""
#######################################
# Author: Wolfram Donat               #
# Copyright 2024, Wolfram Donat       #
#######################################
# Version 1.0

from flask import session, redirect, url_for, current_app 
from flask import Flask, Response, request, g, flash
from flask_cors import CORS, cross_origin
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict

from . import api
import json
import datetime
import socket
import gevent
import struct
import logging
import time
import subprocess
from subprocess import Popen, PIPE
import requests
import string
import threading
# import multiprocessing
import pandas as pd
import numpy as np
import time
import os
import random
import argon2
from io import StringIO
from dotenv import load_dotenv
import openai as OA
import pypdf
from pypdf import PdfReader
import docx2txt
import chromadb
from openai import OpenAI

from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
import sqlite3 as sl

random.seed()

user_information = ''  # Stored textual information about the user, incl. resume, etc.

hasher = argon2.PasswordHasher()

load_dotenv()

OA.api_key = os.getenv('OPENAI_API_KEY')
client = OA.OpenAI()
openai_client = OpenAI()


character_splitter = RecursiveCharacterTextSplitter(separators=['\n\n', '\n', '. ', ' ', ''], chunk_size=1000, chunk_overlap=0)
token_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0, tokens_per_chunk=256)

state = {}
soft_version = '1.0'

con = sl.connect('resumes.db')
cur = con.cursor()

UPLOAD_FOLDER = '/home/wolfram/Code/ResumeChatbot/Resumes/'
ALLOWED_EXTENSIONS = {'pdf', 'txt', 'docx'}

logging.basicConfig(filename='/home/wolframdonat/chat_log.txt', format='%(asctime)s %(message)s',
                    level=logging.INFO)

print('Application started...')

def chunkSeparator(text_file):
    character_split_texts = character_splitter.split_text(text_file)
    print(character_split_texts[:-1])
    print(f'\nTotal chunks: {len(character_split_texts)}')

def rag(query, retrieved_documents, model='gpt-4-turbo-2024-04-09', temperature=0.3):
    information = "\n\n".join(retrieved_documents)
    messages = [{"role": "system", 
                 "content": "You are a helpful and friendly personal assistant. \
                 Your users are recruiters and hiring managers asking questions about information contained in a person's resume and regarding some questions that the person has answered ahead of time. \
                 You will be shown the user's question and the relevant information from the resume. \
                 Answer the user's question using only this information. \
                 If you are unable to answer the question, politely inform the user that you do not have access \
                 to that information and give the person's contact information. \
                 If you don't think you have access to the person's contact information, check again - all of the people for whom you are answering questions have contact information available to you."}, 
                 {"role": "user", "content": f"Question: {query}. \n Information: {information}"}]

    response = openai_client.chat.completions.create(model=model, messages=messages,)
    content = response.choices[0].message.content
    return content

def createLink():
    alphabet = '1234567890ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    link = ''
    for i in range(6):
        nextchar = alphabet[random.randint(0, 62)]
        link += nextchar
    return link 

def createDB():
    if not os.path.exists('resumes.db'):
        con = sl.connect('resumes.db')
        with con:
            con.execute("""
                CREATE TABLE USER (
                    id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                    name TEXT,
                    email TEXT,
                    phone TEXT,
                    salary TEXT,
                    username TEXT,
                    password TEXT,
                    link_id TEXT,
                    subscr_status INTEGER,
                    on_site BOOL,
                    hybrid BOOL,
                    remote BOOL,
                    full_time BOOL,
                    part_time BOOL,
                    contract BOOL,
                    travel BOOL,
                    relocate BOOL,
                    job_search_status INTEGER,  # 1=looking, 2=interested, 3=just browsing
                    notice_time TEXT,  # "two weeks" or "immediately"
                    curr_projects TEXT,
                    past_projects TEXT,
                    skills TEXT,
                    roles TEXT,
                    resume_text TEXT,
                    total_info TEXT
                );
            """)
    return


def getInfo(link):
    link_id = link,  # This format turns link into a tuple
    info = ''
    data = cur.execute("SELECT * FROM USER WHERE link_id =?", link_id)

    for row in data:
        info = row

    # info is a tuple: (1, 'John Smith', 'jsmith', ...)
    return info

def createUser(data):
    # Creates user in database - just email address, username, password and subscription status
    # Also create link_id
    pword = hashPassword(data['password'])
    link_id = createLink()

    sql = "INSERT INTO USER (email, username, password, link_id, subscr_status) values (?, ?, ?, ?, ?)"
    vals = [(data['email'], data['username'], pword, link_id, 1)]
    try:
        cur.executemany(sql, vals)
        con.commit()
        return 1
    except(Exception, e):
        return 0 

def hashPassword(pw:str):
    hp = hasher.hash(pw.encode())
    return hp

def updateUser(data:dict):
    """
    Inserts user info into DB, extracts info from resume_text column and updates
    total_info
    """
    personal_info = []
    ident = data['userID']

    # First, pull latest resume_text from DB
    # (It may have just been uploaded)
    user_data = cur.execute("SELECT * FROM USER WHERE id=" + str(ident))
    for row in user_data:
        info = row
    personal_info = json.loads(info[23])  # It's a list
    # personal_info.append(json.loads(info[23]))

    # Add to the list:
    personal_info.append('My full name is ' + data['fullName'] + '. ')
    personal_info.append('My email address is ' + data['emailAddress'] + '. ')
    personal_info.append('My phone number is ' + data['phoneNumber'] + '. ')

    # Salary
    if data['salaryRequirement'] == 0 or data['salaryRequirement'] == '0' or data['salaryRequirement'] == '':
        personal_info.append('I prefer not to discuss salary at this time')  # salary
    else:
        personal_info.append('My minimum salary requirement is ' + str(data['salaryRequirement']))

    # Onsite/hybrid/remote
    if data['onsite']:
        personal_info.append('I am interested in onsite work or employment')  # onsite
    else:
        personal_info.append('I am not interested in onsite work or employment')

    # Full/parttime/contract
    if data['fulltime']:
        personal_info.append('I am interested in full time work or employment')  # fulltime
    else:
        personal_info.append('I am not interested in full time work or employment')
    if data['parttime']:
        personal_info.append('I am interested in part time work or employment')
    else:
        personal_info.append('I am not interested in part time work or employment')
    if data['contract']:
        personal_info.append('I am interested in contract work or employment')
    else:
        personal_info.append('I am not interested in contract work or employment')

    # Travel
    if data['travel']:
        personal_info.append('I am willing to travel for work')
    else:
        personal_info.append('I am not willing to travel for work')

    # Relocate
    if data['relocate']:
        personal_info.append('I am willing to relocate or move for a position')
    else:
        personal_info.append('I am not willing to relocate or move for a position')

    # Search status
    if data['search'] == 'active':
        personal_info.append('I am actively looking and interviewing for positions')
    elif data['search'] == 'interested':
        personal_info.append('I am not actively looking for work, but I am interested in possibilities and would be open to a discussion.')
    else:
        personal_info.append('I am just seeing what employment opportunities are out there, and am not actively looking for work')

    # Notice time
    if data['start'] == 'immediately':
        personal_info.append('I am available to start work immediately')
    else:
        personal_info.append('I need to give at least two weeks notice to my employer')

    # Projects
    if data['currentProjects'] != '':
        personal_info.append('Some of my current projects include ' + data['currentProjects'])
    if data['pastProjects'] != '':
        personal_info.append('Some of my past projects include ' + data['pastProjects'])

    # Skills
    if data['skills'] != '':
        personal_info.append('Some of my most valuable current skills include ' + data['skills'])

    # Roles
    if data['roles'] != '':
        personal_info.append('I am interested in roles such as ' + data['roles'])

    # Now save updated info to total_info column
    sql = "UPDATE USER SET total_info='" + json.dumps(personal_info) + "' WHERE id=" + ident
    cur.execute(sql)
    con.commit()

    # Finally, update all of the other columns for the user
    name = data['fullName']
    email = data['emailAddress']
    phone = data['phoneNumber']
    salary = data['salaryRequirement']
    on_site = data['onsite']
    hybrid = data['hybrid']
    remote = data['remote']
    full_time = data['fulltime']
    part_time = data['parttime']
    contract = data['contract']
    travel = data['travel']
    relocate = data['relocate']
    search = data['search']
    start = data['start']
    curr_projects = data['currentProjects']
    past_projects = data['pastProjects']
    skills = data['skills']
    roles = data['roles']

    sql = "UPDATE USER SET name='" + name + \
          "', email='" + email + \
          "', phone='" + phone + \
          "', salary='" + salary + \
          "', on_site='" + str(int(on_site)) + \
          "', hybrid='" + str(int(hybrid)) + \
          "', remote='" + str(int(remote)) + \
          "', full_time='" + str(int(full_time)) + \
          "', part_time='" + str(int(part_time)) + \
          "', contract='" + str(int(contract)) + \
          "', travel='" + str(int(travel)) + \
          "', relocate='" + str(int(relocate)) + \
          "', job_search_status='" + search + \
          "', notice_time='" + start + \
          "', curr_projects='" + curr_projects + \
          "', past_projects='" + past_projects + \
          "', skills='" + skills + \
          "', roles='" + roles + \
          "' WHERE id=" + ident

    cur.execute(sql)
    con.commit()
    return

def checkForUser(uname):
    # Returns username if it exists, otherwise 0 
    username = uname,
    data = cur.execute("SELECT * FROM USER WHERE username =?", username)
    try:
        for row in data:
            info = row
        return info[5]
    except:
        return 0

def checkPassword(uname, pword):
    """
    Pulls hashed password as hp from DB where user = uname, pw = submitted password 
    Returns 0 (failure) or user_id
    """
    user_info = uname,
    info = ''
    try:
        data = cur.execute("SELECT * FROM USER WHERE username =?", user_info)
        for row in data:
            info = row

        hp = info[6]
        ident = info[0]

        check = hasher.verify(hp, pword)
        if check:
            return ident
        else:
            return 0

    except:
        return 0 

def checkSubscriptionStatus(uname):
    user_info = uname,
    info = ''
    try:
        data = cur.execute("SELECT * FROM USER WHERE username =?", user_info)
        for row in data:
            info = row
        ss = info[8]
        return ss
    except:
        return 0

def getUserInfo(user):
    ident = user,
    info = ''
    try:
        data = cur.execute("SELECT * FROM USER WHERE id =?", ident)
        for row in data:
            info = row

        result = {'id': info[0],
                  'name': info[1], 
                  'email': info[2],
                  'phone': info[3],
                  'salary': info[4],
                  'link_id': 'http://resume-chat.ai/chat.html?' + info[7],
                  'on_site': info[9],
                  'hybrid': info[10],
                  'remote': info[11],
                  'full_time': info[12],
                  'part_time': info[13],
                  'contract': info[14],
                  'travel': info[15],
                  'relocate': info[16],
                  'job_search_status': info[17],
                  'notice_time': info[18],
                  'curr_projects': info[19],
                  'past_projects': info[20],
                  'skills': info[21], 
                  'roles': info[22]}

    except:
        result = 0

    return result


def insertIntoDB(data):
    """
    """
    ident = data['id']
    name = data['name']
    email = data['email']
    phone = data['phone']
    salary = data['salary']
    username = data['username']
    password = data['password']
    link_id = data['link_id']
    subscr_status = data['subscr_status']
    on_site = data['onsite']
    hybrid = data['hybrid']
    remote = data['remote']
    full_time = data['fulltime']
    part_time = data['parttime']
    contract = data['contract']
    travel = data['travel']
    relocate = data['relocate']
    job_search_status = data['search']
    notice_time = data['start']
    curr_projects = data['currentProjects']
    past_projects = data['pastProjects']
    skills = data['skills']
    roles = data['roles']
    resume_text = data['resume_text']
    total_info  = data['total_info']

    sql = 'INSERT INTO USER (id, \
        name, \
        email, \
        phone, \
        salary, \
        username, \
        password, \
        link_id, \
        subscr_status, \
        on_site, \
        hybrid, \
        remote, \
        full_time, \
        part_time, \
        contract, \
        travel, \
        relocate, \
        job_search_status, \
        notice_time, \
        curr_projects, \
        past_projects, \
        skills, \
        roles, \
        resume_text, \
        total_info) values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    data = [(ident, name, email, phone, salary, username, password, link_id, subscr_status, on_site, hybrid, remote, full_time, part_time, contract, travel, relocate, job_search_status, notice_time, curr_projects, past_projects, skills, roles, resume_text, total_info)]

    try:
        cur.executemany(sql, data)
        con.commit()
        return 1
    except(Exception, e):
        return 0

def writeDataToFile(data):
    with open('total_info.txt', 'a') as f:
        # Remember, GPT doesn't need or want newlines
        f.write('My full name is ' + data['full_name'] + '. ')
        f.write('My email address is ' + data['email_address'] + '. ')
        f.write('My phone number is ' + data['phone_number'] + '. ')

        if salary == 0 or salary == '0':
            f.write('I prefer not to discuss salary at this time. ')
        else:
            f.write('My minimum salary requirement is ' + y['salary'] + '. ')

        if data['onsite'] == 1:
            f.write('I am interested in onsite work. ')
            f.write('I am interested in on-site work. ')
            f.write('I am interested in onsite employment. ')
            f.write('I am interested in on-site employment. ')
        else:
            f.write('I am not interested in onsite work. ')
            f.write('I am not interested in on-site work. ')
            f.write('I am not interested in onsite employment. ')
            f.write('I am not interested in on-site employment. ')
        if data['hybrid'] == 1:
            f.write('I am interested in hybrid work. ')
            f.write('I am interested in hybrid employment. ')
        else:
            f.write('I am not interested in hybrid work. ')
            f.write('I am not interested in hybrid employment. ')
        if data['remote'] == 1:
            f.write('I am interested in remote work. ')
            f.write('I am interested in remote employment. ')
        else:
            f.write('I am not interested in remote work. ')
            f.write('I am not interested in remote employment. ')

        if data['fulltime'] == 1:
            f.write('I am interested in full time work. ')
            f.write('I am interested in full time employment. ')
        else:
            f.write('I am not interested in full time work. ')
            f.write('I am not interested in full time employment. ')

        if data['parttime'] == 1:
            f.write('I am interested in part time work. ')
            f.write('I am interested in part time employment. ')
        else:
            f.write('I am not interested in part time work. ')
            f.write('I am not interested in part time employment. ')

        if data['contract'] == 1:
            f.write('I am interested in contract work. ')
            f.write('I am interested in contract employment. ')
        else:
            f.write('I am not interested in contract work. ')
            f.write('I am not interested in contract employment. ')


        if data['travel'] == 'Yes':
            f.write('I am willing to travel for work. ')
        else:
            f.write('I am not willing to travel for work. ')

        if data['relocate'] == 'Yes':
            f.write('I am willing to relocate. ')
        else:
            f.write('I am not willing to relocate. ')

        if data['job_search'] == 'Actively looking and interviewing':
            f.write('I am actively looking for work. ')
        elif data['job_search'] == 'Not actively looking, but interested in possibilities':
            f.write('I am not actively looking for work, but I am interested in possibilities. ')
        else:
            f.write('I am just seeing what employment opportunities are out there, and I am not actively looking. ')

        if data['availability'] == 'I need two weeks time':
            f.write('I need to give at least two weeks notice to my employer before I could start a new job. ')
        else:
            st.write('You are available to start work immediately')
            f.write('I am available to start work immediately. ')        

        if current_projects != '':
            f.write('Some of my current projects include: ' + current_projects + '. ')

        if past_projects != '':
            f.write('Some of my past projects include: ' + past_projects + '. ')

        if skills != '':
            f.write('I am particularly skilled at: ' + skills + '. ')

        if roles != '':
            f.write('I am looking for roles such as: ' + roles + '. ')
    return

def writeUploadedResumeFileToDatabase(info:list, uid):
    # Updates just the resume_text field
    # A file cannot be uploaded unless the user is logged in
    user_id = uid
    print('426: ', type(info))
    # sql = "UPDATE USER SET resume_text=info WHERE id=user_id"
    sql = "UPDATE USER SET resume_text='" + json.dumps(info) + "' WHERE id=" + user_id
    # print(sql)
    cur.execute(sql)
    con.commit()
    print('resume_text written to database')
    return

def convertUploadedFile(file, file_name, uid):
    print('434: ', uid)
    if 'pdf' in file:
        reader = PdfReader(file)
        pdf_texts = [p.extract_text().strip() for p in reader.pages]
        pdf_texts = [text for text in pdf_texts if text]
        character_split_texts = character_splitter.split_text('\n\n'.join(pdf_texts))
        
        # At this point, character_split_texts is a list
        # which can be written to the database, but it may need to be 
        # cleaned up first
        escaped_text = []
        for i in range(len(character_split_texts)):
            escaped_text.append(character_split_texts[i].replace("'", ""))

        # Save 'fixed' resume text to DB
        writeUploadedResumeFileToDatabase(escaped_text, uid)

        # Split text into tokens to be embedded
        token_split_texts = []
        for text in character_split_texts:
            token_split_texts += token_splitter.split_text(text)

        # Create string from extracted text
        personal_info = ''
        for line in token_split_texts:
            personal_info += line

        # Write string to text files
        # First, write to the file for JUST resume info
        with open('resume_text.txt', 'w') as f:
            f.write(personal_info)

        # Next, write to file that will be appended to
        with open('total_info.txt', 'w') as f:
            f.write(personal_info)

        print('PDF resume information written to file')

        # Clean up after ourselves
        os.system('rm resume_text.txt')

        ################################################################
        # Create embeddings and chroma collection
        # embedding_function = SentenceTransformerEmbeddingFunction()
        
        # chroma_client = chromadb.Client()
        # coll_list = chroma_client.list_collections()
        # coll_name = file_name.lower().split('.')[0]

        # Check for existing collection by same name
        # Delete (and replace) if it exists already
        # if coll_name in coll_list:
        #     chroma_client.delete_collection(coll_name)

        # chroma_collection = chroma_client.create_collection(
        #     coll_name, 
        #     embedding_function=embedding_function)
        # ids = [str(i) for i in range(len(token_split_texts))]
        # chroma_collection.add(ids=ids, documents=token_split_texts)

        # print('Chroma collection created')
        return 1

    elif 'docx' in file:
        resume_text = docx2txt.process(file)

        resume_text = resume_text.replace('\n', ' ')
        resume_text = resume_text.replace('\t', '')

        t_split_texts = []
        t_split_texts.append(resume_text)
        # At this point, t_split_texts is a list (of length 1, most likely)
        # which can be written to the database, but it may need to be
        # cleaned up first
        escaped_text = []
        for i in range(len(t_split_texts)):
            escaped_text.append(t_split_texts[i].replace("'", ""))

        # Save 'fixed' resume text to DB
        writeUploadedResumeFileToDatabase(escaped_text, uid)

        # Split text into tokens to be embedded
        token_split_texts = []
        for text in t_split_texts:
            token_split_texts += token_splitter.split_text(text)

        # Create string from extracted text
        personal_info = ''
        for line in token_split_texts:
            personal_info += line

        # Write string to text files
        # First, write to the file for JUST resume info
        with open('resume_text.txt', 'w') as f:
            f.write(personal_info)

        # Next, write to file that will be appended to
        with open('total_info.txt', 'w') as f:
            f.write(personal_info)


        # writeUploadedFileToDatabase(personal_info)

        ################################################################
        # Create embeddings and chroma collection
        # embedding_function = SentenceTransformerEmbeddingFunction()

        # chroma_client = chromadb.Client()
        # coll_list = chroma_client.list_collections()
        # coll_name = file_name.lower().split('.')[0]

        # Check for existing collection by same name
        # Delete (and replace) if it exists already
        # if coll_name in coll_list:
        #     chroma_client.delete_collection(coll_name)
        
        # chroma_collection = chroma_client.create_collection(
        #     coll_name, 
        #     embedding_function=embedding_function)
        # ids = [str(i) for i in range(len(token_split_texts))]
        # chroma_collection.add(ids=ids, documents=token_split_texts)

        # print('Chroma collection created')
        return 1

    else:
        return 2


# def sendChatMessage(msg: str):
#     results = chroma_collection.query(query_texts=[query], n_results=5)
#     retrieved_documents = results['documents'][0]
#     output = rag(query=query, retrieved_documents=retrieved_documents)
#     return output

def sendChatMessage(msg: str):
    global chroma_collection
    # print(chroma_collection.name)
    results = chroma_collection.query(query_texts=[msg], n_results=5)
    # print(results)

    documents = results['documents'][0]
    # print(documents)
    output = rag(msg, documents)
    # print(output)
    # chat_completion = client.chat.completions.create(
    #     messages=[
    #         {
    #             'role': 'user',
    #             'content': msg,
    #         }
    #     ],
    #     model='gpt-3.5-turbo',
    #     )
    # print(chat_completion)

    # return chat_completion.choices[0].message.content
    return output

def getChatWindowUserInfo(ident):
    # ident is the link_id
    # Search DB for link_id, return 
    global chroma_collection
    link_id = ident,
    info = ''
    try:
        data = cur.execute("SELECT * FROM USER WHERE link_id =?", link_id)
        for row in data:
            info = row
        name = info[1]
        user_information = json.loads(info[24])  # Convert saved JSON back into list

        embedding_function = SentenceTransformerEmbeddingFunction()
        chroma_client = chromadb.Client()
        coll_name = name.replace(' ', '').lower()
        print('736: ', coll_name)
        chroma_collection = chroma_client.create_collection(coll_name, embedding_function=embedding_function)
        ids = [str(i) for i in range(len(user_information))]
        chroma_collection.add(ids=ids, documents=user_information)
        c_list = chromadb.Client().list_collections()
        print(c_list)

        # chroma_collection is now ready for queries
        # Need to delete it upon closing chat window

    except:
        name = ''
    return name

def deleteChatInfo():
    global chroma_collection
    coll_list = chromadb.Client().list_collections()
    for c in coll_list:
        chromadb.Client().delete_collection(c.name)
    return



@api.route('/commandHandler', methods=['POST'])
@cross_origin()

def commandHandler():
    """
    Actual API function responding to GUI. y['command'] is the function call,
    y['data'] is necessary associated data.
    :return: response code, response message, necessary data
    :rtype: dict
    """
    global state
    global chroma_collection
    print('commandHandler activated...')

    upload = request.files
    try:
        y = request.get_json(force=True)  # If this works, it's NOT a file upload

    except:
        # Can't convert to JSON, must be a file upload
        # print(type(upload))
        if isinstance(upload, ImmutableMultiDict):
            #upload.getlist('resume')[0] is a FileStorage object that can be saved or converted
            print('file upload')
            # print('638: ', upload.keys())
            # print('639: ', list(upload.keys()))
            # print('640: ', list(upload.keys())[0])
            uid = list(upload.keys())[0]
            # print(upload.getlist('resume')[0].filename)
            # print(type(upload.getlist('resume')[0].filename))

            # f_name = str(upload.getlist('resume')[0].filename)
            f_name = str(upload.getlist(uid)[0].filename)
            
            # saved_resume = upload.getlist('resume')[0]
            saved_resume = upload.getlist(uid)[0]
            saved_resume.save(f_name)
            y = convertUploadedFile(f_name, f_name, uid)
            if y == 1:
                response_message = 'Resume uploaded successfully'
            elif y == 0:
                response_message = 'Process failed. Please try again or contact support'
            elif y == 2:
                response_message = 'Please upload only PDF or DOCX files'

            x = {'responseCode': y, 'responseMessage': response_message}
            return json.dumps(x)

    print('804: ',  y['command'])
    if y['command'] == 'createDB':
        createDB()
        x = {'responseCode': '1',
             'responseMessage': 'Success'}
        return json.dumps(x)

    elif y['command'] == 'insertIntoDB':
        result = insertIntoDB(y['data'])
        responseMessage = 'Failure' if result == 0 else 'Success'
        x = {'responseCode': str(result), 
             'responseMessage': responseMessage}
        return json.dumps(x)

    elif y['command'] == 'writeDataToFile':
        result = writeDataToFile(y['data'])
        responseMessage = 'Failure' if result == 0 else 'Success'
        x = {'responseCode': str(result), 
             'responseMessage': responseMessage}
        return json.dumps(x)

    elif y['command'] == 'getUserInfo':
        result = getUserInfo(y['data'])
        responseCode = 0 if result == 0 else 1
        responseMessage = 'Failure' if result == 0 else 'Success'
        x = {'responseCode': responseCode,
             'responseMessage': responseMessage,
             'data': result}
        return json.dumps(x)

    elif y['command'] == 'login':
        print('835: ',  'login')
        username = checkForUser(y['data']['username'])
        if username == 0:  # User does not exist
            responseCode = 0
            responseMessage = 'No user exists with that username.'
            x = {'responseCode': responseCode,
                 'responseMessage': responseMessage}
            return json.dumps(x)
        else:
            user = checkPassword(username, y['data']['password'])
            if user == 0:  # Wrong password  
                responseCode = 0
                responseMessage = 'Password incorrect.'
                x = {'responseCode': responseCode,
                     'responseMessage': responseMessage}
                return json.dumps(x)
            else:
                # make sure subscr_status == 1
                user = checkSubscriptionStatus(username)
                if user == 0:
                    responseCode = 0
                    responseMessage = 'Your subscription has expired. Please renew to continue'
                    x = {'responseCode': responseCode,
                         'responseMessage': responseMessage}
                    return json.dumps(x)

                else:
                    responseCode = 1
                    responseMessage = 'Success'
                    session['user_id'] = user
                    session['logged_in'] = 1 
                    session.modified = True
                    x = {'responseCode': responseCode,
                         'responseMessage': responseMessage,
                         'data': user}
                    return json.dumps(x)

    elif y['command'] == 'submitInfo':
        updateUser(y['data'])
        x = {'responseCode': 1,
             'responseMessage': 'Success'}
        return json.dumps(x)

    elif y['command'] == 'sendChatMessage':
        response = sendChatMessage(y['data'])
        x = {'responseCode': 1,
             'responseMessage': response}
        return json.dumps(x)

    elif y['command'] == 'getChatWindowUserInfo':
        response = getChatWindowUserInfo(y['data'])
        print(response)
        if response != '':
            response_code = 1
        else:
            response_code = 0

        x = {'responseCode': response_code,
             'responseMessage': response}
        return json.dumps(x)

    elif y['command'] == 'deleteChatInfo':
        print('Deleting chat info')
        deleteChatInfo()
        x = {'responseCode': 1,
             'responseMessage': 'Success'}
        return json.dumps(x)

    elif y['command'] == 'createLogin':
        result = createUser()
        if result == 1:
            response_message = 'Success'
        else:
            response_message = 'Unable to create user login'

        x = {'responseCode': result,
             'responseMessage': response_message}
        return json.dumps(x)

    elif y['command'] == 'logout':
        session['user_id'] = ''
        session['logged_in'] = 0

        x = {'responseCode': 1,
             'responseMessage': 'Success'}
        return json.dumps(x)

    elif y['command'] == 'resetPassword':
        print(y['data'])
        x = {'responseCode': 1,
             'responseMessage': 'Success'}
        return json.dumps(x)

    return
