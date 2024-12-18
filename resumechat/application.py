from flask import Blueprint, flash, g, redirect, jsonify
from flask import render_template, request, session, url_for
from . import create_app

from werkzeug.exceptions import abort
from werkzeug.utils import secure_filename
from werkzeug.datastructures import ImmutableMultiDict

from resumechat.auth import login_required
from resumechat.db import get_db

import datetime, socket, gevent, struct, logging, time
import subprocess, requests, string, threading
from subprocess import Popen, PIPE

import pandas as pd
import numpy as np
import os, random, json
from io import StringIO
from dotenv import load_dotenv
import openai as OA
from pypdf import PdfReader
import docx2txt
import chromadb
from openai import OpenAI

import stripe
endpoint_secret = 'xxxxx'
stripe_endpoint_secret = 'xxxxx'
stripe.api_key = 'xxxxx'

from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from langchain.text_splitter import RecursiveCharacterTextSplitter, SentenceTransformersTokenTextSplitter

character_splitter = RecursiveCharacterTextSplitter(separators=['\n\n', '\n', '. ', ' ', ''], chunk_size=1000, chunk_overlap=0)
token_splitter = SentenceTransformersTokenTextSplitter(chunk_overlap=0, tokens_per_chunk=256)

logging.basicConfig(filename='/home/wolframdonat/chat_log.txt', level=logging.INFO)

load_dotenv()

OA.api_key = os.getenv('OPENAI_API_KEY')
client = OA.OpenAI()
openai_client = OpenAI()

UPLOAD_FOLDER = 'resumes'
ALLOWED_EXTENSIONS = {'pdf', 'docx'}

bp = Blueprint('application', __name__)

def getChatWindowUserInfo(ident):
    global chroma_collection
    link_id = ident
    info = ''
    try:
        db = get_db()
        user = db.execute('SELECT * FROM USER WHERE link_id = ?', (link_id,)).fetchone()
        name = user['name']
        user_info = user['total_info']
        user_info = json.loads(user_info)  # Convert saved JSON back into list

        embedding_function = SentenceTransformerEmbeddingFunction()
        chroma_client = chromadb.Client()
        coll_name = name.replace(' ', '').lower()
        chroma_collection = chroma_client.create_collection(coll_name, embedding_function=embedding_function)
        ids = [str(i) for i in range(len(user_info))]
        chroma_collection.add(ids=ids, documents=user_info)
        c_list = chromadb.Client().list_collections()
    except:
        name = ''

    return name

def sendChatMessage(msg: str):
    global chroma_collection
    results = chroma_collection.query(query_texts=[msg], n_results=5)
    documents = results['documents'][0]
    output = rag(msg, documents)
    return output

def deleteChatInfo():
    global chroma_collection
    coll_list = chromadb.Client().list_collections()
    for c in coll_list:
        chromadb.Client().delete_collection(c.name)
    return

def createCustomer(cust):
    # cust['email']
    # cust['name']
    print(cust)
    print('creating customer')

    db = get_db()
    cursor = db.cursor()
    cursor.execute('INSERT INTO USER (customer_id, email, name, subscr_status) VALUES (?, ?, ?, ?)',
               (cust['id'], cust['email'], cust['name'], 1),  
               )
    db.commit()
    session['user_id'] = cursor.lastrowid
    print(f'Customer created with local ID: {session["user_id"]}')
    print(f'Session contents: {session}')
    return

def deleteCustomer(cust):
    print(f'deleting customer: {cust["id"]}')
    db = get_db()
    user = db.execute('SELECT * FROM USER WHERE customer_id = ?', (cust['id'],)).fetchone()
    if user:
        print(f'Found user: {user["name"]}')
        db.execute('DELETE FROM USER WHERE id = ?', (user['id'],))
        db.commit()
        print('User deleted')
    else:
        print('User not found')
    return

def disableCustomer(subscr):
    db = get_db()
    user = db.execute('SELECT * FROM USER WHERE customer_id = ?', (subscr['customer'],)).fetchone()
    db.execute('UPDATE USER SET subscr_status = ? WHERE id = ?', (0, user_id))
    db.commit()
    return

def chunkSeparator(text_file):
    character_split_texts = character_splitter.split_text(text_file)
    print(character_split_texts[:-1])
    print(f'\nTotal chunks: {len(character_split_texts)}')

def rag(query, retrieved_documents, model='gpt-4-turbo-2024-04-09', temperature=0.3):
    information = "\n\n".join(retrieved_documents)
    messages = [{"role": "system",
                 "content": "You are a helpful and friendly personal assistant. \
                 Your users are recruiters and hiring managers asking questions about information contained in a person's resume and regarding some questions that the person has answered ahead of time.\
                 You will be shown the user's question and the relevant information from the resume and answered questions.\
                 Answer the user's question using only this information. \
                 If you are unable to answer the question, politely inform the user that you do not have access to that information and give the person's contact information. \
                 If you don't think you have access to the person's contact information, check again - all of the people for whom you are answering questions have contact information available to you."},
                {"role": "user", "content": f"Question: {query}. \n Information: {information}"}]
    response = openai_client.chat.completions.create(model=model, messages=messages,)
    content = response.choices[0].message.content
    return content

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def writeDataToFile(data):
    with open('total_info.txt', 'a') as f:
        # Remember, GPT doesn't need or want newlines
        f.write('My full name is ' + data['full_name'] + '. ')
        if data['email_address'] != '':
            f.write('My email address is ' + data['email_address'] + '. ')
        if data['phone_number'] != '':
            f.write('My phone number is ' + data['phone_number'] + '. ')

        if data['salary'] == 0 or data['salary'] == '0' or data['salary'] == '':
            f.write('I prefer not to discuss salary at this time. ')
        else:
            f.write('My minimum salary requirement is ' + data['salary'] + '. ')

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

        if data['fulltime'] == 'on':
            f.write('I am interested in full time work. ')
            f.write('I am interested in full time employment. ')
        else:
            f.write('I am not interested in full time work. ')
            f.write('I am not interested in full time employment. ')

        if data['parttime'] == 'on':
            f.write('I am interested in part time work. ')
            f.write('I am interested in part time employment. ')
        else:
            f.write('I am not interested in part time work. ')
            f.write('I am not interested in part time employment. ')

        if data['contract'] == 'on':
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

        if data['job_search'] == '1':
            f.write('I am actively looking for work. ')
        elif data['job_search'] == '2':
            f.write('I am not actively looking for work, but I am interested in possibilities. ')
        else:
            f.write('I am just seeing what employment opportunities are out there, and I am not actively looking. ')

        if data['availability'] == '1':
            f.write('I need to give at least two weeks notice to my employer before I could start a new job. ')
        else:
            f.write('I am available to start work immediately. ')        

        if data['current_projects'] != '':
            f.write('Some of my current projects include: ' + data['current_projects'] + '. ')

        if data['past_projects'] != '':
            f.write('Some of my past projects include: ' + data['past_projects'] + '. ')

        if data['skills'] != '':
            f.write('I am particularly skilled at: ' + data['skills'] + '. ')

        if data['roles'] != '':
            f.write('I am looking for roles such as: ' + data['roles'] + '. ')

        # Write total_info to db (info_text)
        with open('total_info.txt', 'r') as f:
            tmp_info = f.readlines()
        db.execute('UPDATE USER SET info_text = ? WHERE id = ?', (json.dumps(tmp_info), user_id))
        db.commit()
    return

def writeUploadedResumeFileToDatabase(info: list):
    user_id = session['user_id']
    db = get_db()
    db.execute('UPDATE USER SET resume_text = ? WHERE id = ?', (json.dumps(info), user_id))
    db.commit()

def convertUploadedFile(file, file_name, uid):
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
        writeUploadedResumeFileToDatabase(escaped_text)

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
        writeUploadedResumeFileToDatabase(escaped_text)

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

        return 1

    else:
        return 2


@bp.route('/')
def index():
    return render_template('index.html')

@bp.route('/editinfo', methods=('GET', 'POST'))
def editInfo():
    db = get_db()
    response = {'status': 'Error', 'message': 'Something went wrong'}
    user_id = session['user_id']

    if request.method == 'POST':
        # print(request.form)
        full_name = request.form['fullName']
        email_address = request.form['emailAddress']
        phone_number = request.form['phoneNumber']
        salary_req = request.form['salaryRequirement']

        onsite_interest = request.form.get('onsiteInterest')
        hybrid_interest = request.form.get('hybridInterest')
        remote_interest = request.form.get('remoteInterest')
        
        fulltime_work = request.form.get('fulltimeWork')
        parttime_work = request.form.get('parttimeWork')
        contract_work = request.form.get('contractWork')

        travel_work = request.form.get('travelWork')

        relocate_work = request.form.get('relocateWork')

        # 1 = 'actively looking', 2 = 'interested', 3 = 'just seeing what is available'
        search_status = request.form.get('searchStatus')

        # 0 = 'two weeks notice', 1 = 'immediately'
        start_time = request.form.get('startTime')

        current_projects = request.form.get('currentProjects')
        past_projects = request.form.get('pastProjects')

        job_skills = request.form.get('jobSkills')
        job_roles = request.form.get('jobRoles')

        try:
            # user = db.execute('SELECT * FROM USER WHERE id = ?', (user_id,)).fetchone()
            db.execute('''
            UPDATE USER SET name = ?, email = ?, phone = ?, salary = ?, on_site = ?, 
            hybrid = ?, remote = ?, full_time = ?, part_time = ?, contract = ?,
            travel = ?, relocate = ?, job_search_status = ?, notice_time = ?,
            curr_projects = ?, past_projects = ?, skills = ?, roles = ? WHERE id = ?
            ''',
            (full_name, email_address, phone_number, salary_req, onsite_interest, hybrid_interest,
                remote_interest, fulltime_work, parttime_work, contract_work, 
                travel_work, relocate_work, search_status, start_time, current_projects, 
                past_projects, job_skills, job_roles, user_id
            ))
            db.commit()

            info_to_write = {'full_name': full_name, 'email_address': email_address, 'phone_number': phone_number,
                             'salary': salary_req, 'onsite': onsite_interest, 'hybrid': hybrid_interest, 'remote': remote_interest,
                             'fulltime': fulltime_work, 'parttime': parttime_work, 'contract': contract_work,
                             'travel': travel_work, 'relocate': relocate_work,
                             'job_search': search_status, 'availability': start_time,
                             'current_projects': current_projects, 'past_projects': past_projects,
                             'skills': job_skills, 'roles': job_roles}
            writeDataToFile(info_to_write)

            
            # Now, total_info.txt contains all of this info. It also needs to contain resume info
            # So we need to check if the db contains resume info. If it does, we need to pull it, 
            # append total_info.txt to it, 
            # and then save everything to the db. If the db has no resume info, just save this info to db
            resume_result = db.execute('SELECT * FROM USER WHERE id = ?', (user_id,)).fetchone()
            if resume_result['resume_text'] == '' or resume_result['resume_text'] is None:
                # Write total_info.txt to DB
                with open('total_info.txt', 'r') as f:
                    tmp_info = f.readlines()
                    db.execute('UPDATE USER SET total_info = ? WHERE id = ?', (json.dumps(tmp_info), user_id))
                    db.commit()
            else:
                tmp_info = json.loads(resume_result['resume_text'])
                with open('total_info.txt', 'r') as f:
                    for line in f.readlines():
                        tmp_info.append(line)
                    db.execute('UPDATE USER SET total_info = ? WHERE id = ?', (json.dumps(tmp_info), user_id))
                    db.commit()

            response['status'] = 'Success'
            response['message'] = 'Information updated'
            os.system('rm total_info.txt')

        except Exception as e:
            print('302: ', e)
            response['message'] = str(e)

        return jsonify(response)


    # On initial page load, prefill out data fields and selections
    user = db.execute('SELECT * FROM USER WHERE id = ?', (user_id,)).fetchone()
    # on_site/hybrid/travel/relocate = 0/1
    # full_time/part_time/contract = 'on'/'off'
    f_work = '1' if user['full_time'] else '0'
    p_work = '1' if user['part_time'] else '0'
    c_work = '1' if user['contract'] else '0'

    if user['past_projects'] == '' or user['past_projects'] is None:
        past_projects = ''
    else:
        past_projects = user['past_projects']
    if user['curr_projects'] == '' or user['curr_projects'] is None:
        current_projects = ''
    else:
        current_projects = user['curr_projects']

    if user['salary'] == '' or user['salary'] is None:
        salary_req = ''
    else:
        salary_req = user['salary']
        
    return render_template('editinfo.html', user=g.user, link=g.link, 
        fullName=user['name'], emailAddress=user['email'], 
        phoneNumber=user['phone'], salaryRequirement=salary_req,
        onsiteInterest=str(user['on_site']), hybridInterest=str(user['hybrid']), 
        remoteInterest=str(user['remote']), fulltimeWork=f_work, 
        parttimeWork=p_work, contractWork=c_work,
        travelWork=str(user['travel']), relocateWork=str(user['relocate']), 
        searchStatus=str(user['job_search_status']), startTime=str(user['notice_time']), 
        currentProjects=current_projects, pastProjects=past_projects, 
        jobSkills=user['skills'], jobRoles=user['roles'])

@bp.route('/examples')
def examples():
    return render_template('examples.html')

@bp.route('/faq')
def faq():
    return render_template('faq.html')

@bp.route('/signup')
def signup():
    return render_template('signup.html')

@bp.route('/uploadresume', methods=['GET', 'POST'])
def upload_resume():
    # After uploading a resume, need to "insert it" into total_info (prepending previous info)
    response = {'status': 'Error', 'message': 'Something went wrong'}
    if request.method == 'POST':
        upload = request.files

        if isinstance(upload, ImmutableMultiDict):
            print('file uploaded')
            uid = list(upload.keys())[0]
            f_name = str(upload.getlist(uid)[0].filename)
            saved_resume = upload.getlist(uid)[0]
            saved_resume.save(f_name)
            result = convertUploadedFile(f_name, f_name, uid)

            if result == 1:
                response['status'] = 'Success'
                response['message'] = 'Resume uploaded'
                return redirect(url_for('application.resumeUploaded'))

            else:
                return jsonify(response)

    return render_template('uploadresume.html')

@bp.route('/resumeuploaded')
def resumeUploaded():
    # event = {}
    # event['data'] = {}
    # event['data']['object'] = {}
    # event['data']['object']['name'] = 'Jane Doe'
    # event['data']['object']['email'] = 'test@test.com'
    # customer = event['data']['object']
    # createCustomer(customer)
    return render_template('resumeuploaded.html')

@bp.route('/chat', methods=['GET', 'POST'])
def chat():
    global chroma_collection
    if request.method == 'POST':
        data = request.get_json()
        user_message = data.get('message')
        link_id = data.get('id')

        getChatWindowUserInfo(link_id)
        response = sendChatMessage(user_message)
        return jsonify({'response': response})
    else:
        link_id = request.args.get('id')
        db = get_db()
        user = db.execute('SELECT * FROM USER WHERE link_id = ?', (link_id,)).fetchone()
        return render_template('chat.html', link_id=link_id, name=user['name'])

@bp.route('/close-chat', methods=['POST'])
def close_chat():
    data = request.get_json()
    unique_id = data.get('id')

    deleteChatInfo()
    return jsonify({'message': 'Chat closed successfully'})

@bp.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
#    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = json.loads(payload)
    except json.decoder.JSONDecodeError as e:
        print('Webhook error while parsing basic request.' + str(e))
        return jsonify(success=False)
    if endpoint_secret:
        sig_header = request.headers.get('stripe_signature')
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
        except stripe.error.SignatureVerificationError as e:
            print('Webhook signature verification failed.' + str(e))
            return jsonify(success=False)

    # Handle the event
    logging.info('%s', event['type'])
    if event['type'] == 'customer.created':
        customer = event['data']['object']
        createCustomer(customer)

    elif event['type'] == 'customer.deleted':
        customer = event['data']['object']
        deleteCustomer(customer)

    elif event['type'] == 'customer.updated':
        customer = event['data']['object']
        pass

    elif event['type'] == 'customer.subscription.created':
        subscription = event['data']['object']
        print(subscription)

    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        disableCustomer(subscription)

    elif event['type'] == 'customer.subscription.paused':
        subscription = event['data']['object']
        pauseCustomer(subscription)

    elif event['type'] == 'customer.subscription.resumed':
        subscription = event['data']['object']
        resumeCustomer(subscription)

    elif event['type'] == 'invoice.created':
        invoice = event['data']['object']
        pass

    elif event['type'] == 'invoice.marked_uncollectible':
        subscription = event['data']['object']
        pauseCustomer(subscription)

    elif event['type'] == 'invoice.payment_succeeded':
        customer = event['data']['object']
        pass

    # ... handle other event types
    else:
        print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)

application = create_app()

if __name__ == '__main__':
    application.run(debug=True)
    
