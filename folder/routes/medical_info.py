from urllib.robotparser import RequestRate
from flask import Blueprint, Response, jsonify, request, url_for, render_template_string, redirect, render_template, flash
import pymongo
from folder.config import users
from folder.functions import Authentication, secret_key
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import jwt, bson, datetime,random, secrets
from bson.errors import InvalidId
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from bson import ObjectId
import os

medicals = Blueprint("users", __name__, url_prefix="/api/medicals")
