"""This is the main API package for the ResumeChat application."""

from flask import Blueprint

api = Blueprint('api', __name__)

from . import commandHandler
