import streamlit as st  
import pandas as pd   
import numpy as np
import time
import os
from io import StringIO
from dotenv import load_dotenv
import openai as OA
import pypdf 
from pypdf import PdfReader
import docx2txt
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter
import sqlite3 as sl

load_dotenv()

OA.api_key = os.getenv('OPENAI_API_KEY')
client = OA.OpenAI()

character_splitter = RecursiveCharacterTextSplitter(separators=['\n\n', '\n', '. ', ' ', ''], chunk_size=1000, chunk_overlap=0)


# To create the database 
if not os.path.exists('test.db'):
    con = sl.connect('test.db')
    with con:
        con.execute("""
            CREATE TABLE USER (
                id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
                name TEXT,
                username TEXT,
                password TEXT,
                link_id TEXT,
                subscr_status INTEGER,
                info TEXT
            );
        """)


# To insert into the database
# with open('resume_info.txt', 'r') as f:
#     x = f.readlines()
# y = ''
# for line in x:
#     y += line
# Make info one string with no newlines
# y = y.replace('\n', '')

# sql = 'INSERT INTO USER (id, name, username, password, link_id, subscr_status, info) values(?,?,?,?,?,?,?)'
# data = [(1, 'Wolfram Donat', 'wolframdonat', 'password123', 'abcdef', 1, y)]
# with con:
#     con.executemany(sql, data)

# To query the DB:
# a = ''
# with con:
#     data = con.execute("SELECT * FROM USER WHERE link_id == 'blah blah blah'")

# for row in data:
#     a = row[1]
# It's necessary to "hold" the value outside the con loop, otherwise it disappears

def getInfo(link):
    link_id = link,  # This format turns link into a tuple
    info = ''
    con = sl.connect('test.db')
    with con:
        data = con.execute("SELECT * FROM USER WHERE link_id =?", link_id)

    for row in data:
        info = row[6]
    return info


def insertIntoDB():
    with open('resume_info.txt', 'r') as f:
        x = f.readlines()
    y = ''
    for line in x:
        y += line 

    # Substitute spaces for newlines 
    y = y.replace('\n', ' ')
    sql = 'INSERT INTO USER (id, name, username, password, link_id, subscr_status, info) values(?,?,?,?,?,?,?)'

    # TODO: tweak this to reflect logged-in user's actual username/info/etc.
    data = [(2, full_name, 'wdonat', 'password234', 'bcdefg', 1, y)]
    con = sl.connect('test.db')
    with con:
        con.executemany(sql, data)


def displayInfo():
    with open('resume_info.txt', 'a') as f:
        # Remember: GPT doesn't need or want newlines!

        f.write('My full name is ' + full_name + '. ')
        f.write('My email address is ' + email_address + '. ')
        f.write('My phone number is ' + phone_number + '. ')

        if salary == 0 or salary == '0':
            f.write('I prefer not to discuss salary at this time. ')
        else:
            f.write('My minimum salary requirement is ' + str(salary) + '. ')
        st.write('Minimum Salary: $', salary)

        if onsite:
            st.write('Interested in: On-site work')
            f.write('I am interested in onsite work. ')
            f.write('I am interested in on-site work. ')
            f.write('I am interested in onsite employment. ')
            f.write('I am interested in on-site employment. ')
        else:
            f.write('I am not interested in onsite work. ')
            f.write('I am not interested in on-site work. ')
            f.write('I am not interested in onsite employment. ')
            f.write('I am not interested in on-site employment. ')
        if hybrid:
            st.write('Interested in: Hybrid work')
            f.write('I am interested in hybrid work. ')
            f.write('I am interested in hybrid employment. ')
        else:
            f.write('I am not interested in hybrid work. ')
            f.write('I am not interested in hybrid employment. ')
        if remote:
            st.write('Interested in: Remote work')
            f.write('I am interested in remote work. ')
            f.write('I am interested in remote employment. ')
        else:
            f.write('I am not interested in remote work. ')
            f.write('I am not interested in remote employment. ')

        if fulltime:
            st.write('Interested in: Full time work')
            f.write('I am interested in full time work. ')
            f.write('I am interested in full time employment. ')
        else:
            f.write('I am not interested in full time work. ')
            f.write('I am not interested in full time employment. ')

        if parttime:
            st.write('Intersted in: Part time work')
            f.write('I am interested in part time work. ')
            f.write('I am interested in part time employment. ')
        else:
            f.write('I am not interested in part time work. ')
            f.write('I am not interested in part time employment. ')

        if contract:
            st.write('Interested in: Contract work')
            f.write('I am interested in contract work. ')
            f.write('I am interested in contract employment. ')
        else:
            f.write('I am not interested in contract work. ')
            f.write('I am not interested in contract employment. ')


        if travel == 'Yes':
            st.write('You are willing to travel')
            f.write('I am willing to travel. ')
        else:
            st.write('You are not willing to travel')
            f.write('I am not willing to travel. ')

        if relocate == 'Yes':
            st.write('You are willing to relocate')
            f.write('I am willing to relocate. ')
        else:
            st.write('You are not willing to relocate')
            f.write('I am not willing to relocate. ')

        if job_search == 'Actively looking and interviewing':
            st.write('You are actively looking for work')
            f.write('I am actively looking for work. ')
        elif job_search == 'Not actively looking, but interested in possibilities':
            st.write('You are not actively looking, but you are interested in possibilities')
            f.write('I am not actively looking for work, but I am interested in possibilities. ')
        else:
            st.write('You are just seeing what is out there')
            f.write('I am just seeing what employment opportunities are out there. ')

        if availability == 'I need two weeks time':
            st.write('You need to give at least two weeks notice to your employer')
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


def chunkSeparator(text_file):
    character_split_texts = character_splitter.split_text(text_file)
    print(character_split_texts[:-1])
    print(f'\nTotal chunks: {len(character_split_texts)}')

def convertUploadedFile():
    if uploaded_file is not None:
        st.write(uploaded_file.name)
        if 'pdf' in uploaded_file.name:
            reader = PdfReader(uploaded_file)
            pdf_texts = [p.extract_text().strip() for p in reader.pages]
            pdf_texts = [text for text in pdf_texts if text]
            character_split_texts = character_splitter.split_text('\n\n'.join(pdf_texts))

            token_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0, tokens_per_chunk=256)
            token_split_texts = []
            for text in character_split_texts:
                token_split_texts += token_splitter.split_text(text)

            embedding_function = SentenceTransformerEmbeddingFunction()
            chroma_client = chromadb.Client()
            chroma_collection = chroma_client.create_collection(uploaded_file.name.lower().split('.')[0], embedding_function=embedding_function)
            ids = [str(i) for i in range(len(token_split_texts))]
            chroma_collection.add(ids=ids, documents=token_split_texts)

            # Create string from extracted text
            personal_info = ''
            for line in token_split_texts:
                personal_info += line

            # Write string to text file
            with open('resume_info.txt', 'w') as f:
                f.write(personal_info)

            print('Resume information written to file')


        elif 'docx' in uploaded_file.name:
            # print('It is a docx!')
            text = docx2txt.process(uploaded_file)
            with open('resume_info.txt', 'w') as f:
                f.write(text)
                f.write('\n')

        elif 'txt' in uploaded_file.name:
            print('It is a text file!')

        else:
            print('It is a doc!')    

uploaded_file = st.file_uploader('Please upload your resume in PDF, DOCX, or TXT format -- (Sorry, .doc files are not supported at this time)', type=['pdf', 'docx', 'txt'])


st.write('\n')
st.write('\n')

st.write('PERSONAL INFO')
full_name = st.text_input('What is your full name?')
email_address = st.text_input('What is your email address?')
phone_number = st.text_input('What is your phone number?')

st.write('\n')
st.write('\n')

st.write('What is your minimum salary requirement?') 
st.write('Enter "0" if you prefer not to discuss salary at this time')
salary = st.text_input('Minimum salary requirement')

st.write('\n')
st.write('\n')

st.write('What job locations are you interested in?')
onsite = st.checkbox('On-site')
hybrid = st.checkbox('Hybrid')
remote = st.checkbox('Remote')

st.write('What type of employment are you looking for?')
fulltime = st.checkbox('Full time')
parttime = st.checkbox('Part time')
contract = st.checkbox('Contract')

travel = st.radio('Are you willing to travel?',
    ['Yes', 'No'], index=None)

relocate = st.radio('Are you willing to relocate?',
    ['Yes', 'No'], index=None)

job_search = st.radio('Where are you in the job search process?',
    ['Actively looking and interviewing',
    'Not actively looking, but interested in possibilities',
    'Just seeing what is out there'],
    index=None)

availability = st.radio('When would you be available to start work?',
    ['I need two weeks time', 'Immediately'],
    index=None)

st.write('\n')
st.write('\n')

current_projects = st.text_input('What are some projects you are currently working on?')
past_projects = st.text_input('What are some past projects you are particularly proud of?')
roles = st.text_input('What are some of your preferred roles/titles?')
skills = st.text_input('What are some highlights from your skillset? What are you particularly good at doing?')

pronouns = st.radio('How do you refer to yourself?',
    ['he/him/his', 'she/her/her', 'they/them/their'],
    index=None)

if st.button('Submit your info'):
    convertUploadedFile()
    displayInfo()
    insertIntoDB()
#    chunkSeparator('resume_info.txt')

#st.button('Submit your info', on_click=displayInfo())


# client.files.create(
#     file=open(bytes_data),
#     purpose='assistants')


# time.sleep(5)
#st.write(client.files.list())
#for f in client.files.list():
#    client.files.delete(f.id)
