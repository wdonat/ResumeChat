import streamlit as st  
import pandas as pd   
import numpy as np
import time
import os
from io import StringIO
from dotenv import load_dotenv
import openai as OA
import PyPDF2
import docx2txt
import chromadb
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter

load_dotenv()

OA.api_key = os.getenv('OPENAI_API_KEY')
client = OA.OpenAI()

character_splitter = RecursiveCharacterTextSplitter(separators=['\n\n', '\n', '. ', ' ', ''], chunk_size=1000, chunk_overlap=0)

#client.files.create(
#    file=open('notes.txt', 'rb'),
#    purpose='assistants')

def displayInfo():
    with open('resume_info.txt', 'a') as f:

        f.write('My full name is ' + full_name + '\n')
        f.write('My email address is ' + email_address + '\n')
        f.write('My phone number is ' + phone_number + '\n')

        if salary == 0 or salary == '0':
            f.write('I prefer not to discuss salary at this time\n')
        else:
            f.write('My minimum salary requirement is ' + salary + '\n')
        st.write('Minimum Salary: $', salary)

        if onsite:
            st.write('Interested in: On-site work')
            f.write('I am interested in onsite work\n')
            f.write('I am interested in on-site work\n')
            f.write('I am interested in onsite employment\n')
            f.write('I am interested in on-site employment\n')
        else:
            f.write('I am not interested in onsite work\n')
            f.write('I am not interested in on-site work\n')
            f.write('I am not interested in onsite employment\n')
            f.write('I am not interested in on-site employment\n')
        if hybrid:
            st.write('Interested in: Hybrid work')
            f.write('I am interested in hybrid work\n')
            f.write('I am interested in hybrid employment\n')
        else:
            f.write('I am not interested in hybrid work\n')
            f.write('I am not interested in hybrid employment\n')
        if remote:
            st.write('Interested in: Remote work')
            f.write('I am interested in remote work\n')
            f.write('I am interested in remote employment\n')
        else:
            f.write('I am not interested in remote work\n')
            f.write('I am not interested in remote employment\n')

        st.write('Interested in:')
        if fulltime:
            st.write('Full time work')
            f.write('I am interested in full time work\n')
        else:
            f.write('I am not interested in full time work\n')

        if parttime:
            st.write('Part time work')
            f.write('I am interested in part time work\n')
        else:
            f.write('I am not interested in part time work\n')

        if contract:
            st.write('Contract work')
            f.write('I am interested in contract work\n')
        else:
            f.write('I am not interested in contract work\n')


        if travel == 'Yes':
            st.write('You are willing to travel')
            f.write('I am willing to travel\n')
        else:
            st.write('You are not willing to travel')
            f.write('I am not willing to travel\n')

        if relocate == 'Yes':
            st.write('You are willing to relocate')
            f.write('I am willing to relocate\n')
        else:
            st.write('You are not willing to relocate')
            f.write('I am not willing to relocate\n')

        if job_search == 'Actively looking and interviewing':
            st.write('You are actively looking for work')
            f.write('I am actively looking for work\n')
        elif job_search == 'Not actively looking, but interested in possibilities':
            st.write('You are not actively looking, but you are interested in possibilities')
            f.write('I am not actively looking, but I am interested in possibilities\n')
        else:
            st.write('You are just seeing what is out there')
            f.write('I am just seeing what is out there.\n')

        if availability == 'I need two weeks time':
            st.write('You need to give two weeks notice to your employer')
            f.write('I need to give two weeks notice to my employer before I could start a new job\n')
        else:
            st.write('You are available to start work immediately')
            f.write('I am available to start work immediately\n')        

def chunkSeparator(text_file):
    character_split_texts = character_splitter.split_text(text_file)
    print(character_split_texts[:-1])
    print(f'\nTotal chunks: {len(character_split_texts)}')


uploaded_file = st.file_uploader('Please upload your resume in PDF, DOCX, or TXT format -- (Sorry, .doc files are not supported at this time)', type=['pdf', 'docx', 'txt'])
if uploaded_file is not None:
    st.write(uploaded_file.name)
    if 'pdf' in uploaded_file.name:
        pdf_reader = PyPDF2.PdfReader(uploaded_file)
        with open('resume_info.txt', 'w') as f:
            for i in range(len(pdf_reader.pages)):
                f.write(str(pdf_reader.pages[i].extract_text()))
                f.write('\n')

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

pronouns = st.radio('How do you refer to yourself?',
    ['he/him/his', 'she/her/her', 'they/them/their'])

if st.button('Submit your info'):
    displayInfo()
    chunkSeparator('resume_info.txt')

#st.button('Submit your info', on_click=displayInfo())


# client.files.create(
#     file=open(bytes_data),
#     purpose='assistants')


# time.sleep(5)
#st.write(client.files.list())
#for f in client.files.list():
#    client.files.delete(f.id)
