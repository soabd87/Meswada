from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

# تهيئة قاعدة البيانات
db = SQLAlchemy()

class Site(db.Model):
    __tablename__ = 'sites'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    
    # العلاقات (Relations) لتسهيل جلب الأقسام والمقالات التابعة للموقع
    categories = db.relationship('Category', backref='site', lazy=True, cascade="all, delete-orphan")
    posts = db.relationship('Post', backref='site', lazy=True, cascade="all, delete-orphan")

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    image_format = db.Column(db.String(255), default="")
    
    # العلاقات
    posts = db.relationship('Post', backref='category', lazy=True, cascade="all, delete-orphan")

class Post(db.Model):
    __tablename__ = 'posts'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    site_id = db.Column(db.Integer, db.ForeignKey('sites.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    updated_at = db.Column(db.String(50), default=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"), onupdate=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    status = db.Column(db.String(20), default='draft')

class Setting(db.Model):
    __tablename__ = 'settings'
    key = db.Column(db.String(100), primary_key=True)
    value = db.Column(db.Text, nullable=True)