from flask import Blueprint, flash, g, redirect
from flask import render_template, request, session, url_for

from werkzeug.exceptions import abort

from resumechat.auth import login_required
from resumechat.db import get_db

bp = Blueprint('blog', __name__)

@bp.route('/')
def index():
    db = get_db()


    return render_template('index.html')    
