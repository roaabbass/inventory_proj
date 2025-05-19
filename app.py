from flask import Flask , render_templetes, request , redirect , url_for ,flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager , UserMixin, login_user,login_required,logout_
