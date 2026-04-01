from flask import Flask
from .models import db
from .routes import main_blueprint
import os

def create_app():
    app = Flask(__name__)
    app.secret_key = 'my_super_secret_key_for_editor' 
    app.config['UPLOAD_FOLDER'] = 'app/static/uploads'
    
    # إعدادات مسار قاعدة البيانات لتعمل مع SQLAlchemy
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'database.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # تهيئة قاعدة البيانات وارتباطها بالتطبيق
    db.init_app(app)
    
    with app.app_context():
        # هذا الأمر سيقوم بإنشاء الجداول (بما فيها جدول settings الجديد) إذا لم تكن موجودة
        db.create_all() 
    
    app.register_blueprint(main_blueprint)
    return app