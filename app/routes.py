from flask import Blueprint, render_template, request, jsonify, url_for, redirect, current_app, flash
from .models import db, Site, Category, Post, Setting
import os, json
from werkzeug.utils import secure_filename
from datetime import datetime
import re

main_blueprint = Blueprint('main', __name__)

@main_blueprint.route('/')
def dashboard():
    sites = Site.query.all()
    categories = Category.query.all()
    # تجهيز البيانات لتناسب واجهة المستخدم
    categories_data = [{'id': c.id, 'name': c.name, 'site_name': c.site.name if c.site else ''} for c in categories]
    
    posts = Post.query.order_by(Post.id.desc()).limit(5).all()
    posts_data = [{'id': p.id, 'title': p.title, 'status': p.status, 
                   'site_name': p.site.name if p.site else '', 
                   'cat_name': p.category.name if p.category else ''} for p in posts]
    
    return render_template('dashboard.html', sites=sites, categories=categories_data, posts=posts_data)

@main_blueprint.route('/archive')
def archive():
    site_id = request.args.get('site_id', '')
    cat_id = request.args.get('category_id', '')
    sort_by = request.args.get('sort_by', 'created_desc') 
    page = request.args.get('page', 1, type=int)

    sites = Site.query.all()
    query = Post.query

    if site_id:
        query = query.filter_by(site_id=int(site_id))
    if cat_id:
        query = query.filter_by(category_id=int(cat_id))

    if sort_by == 'created_desc': query = query.order_by(Post.created_at.desc())
    elif sort_by == 'created_asc': query = query.order_by(Post.created_at.asc())
    elif sort_by == 'updated_desc': query = query.order_by(Post.updated_at.desc())
    elif sort_by == 'alpha_asc': query = query.order_by(Post.title.asc())
    elif sort_by == 'alpha_desc': query = query.order_by(Post.title.desc())
    else: query = query.order_by(Post.id.desc())

    pagination = query.paginate(page=page, per_page=20, error_out=False)
    posts = pagination.items
    
    posts_data = [{'id': p.id, 'title': p.title, 'status': p.status, 'created_at': p.created_at, 
                   'updated_at': p.updated_at, 'site_name': p.site.name if p.site else '', 
                   'cat_name': p.category.name if p.category else ''} for p in posts]
    
    return render_template('archive.html', sites=sites, posts=posts_data, page=page, 
                           total_pages=pagination.pages, current_site=site_id, 
                           current_cat=cat_id, current_sort=sort_by)

@main_blueprint.route('/editor')
@main_blueprint.route('/editor/<int:post_id>')
def editor(post_id=None):
    sites = Site.query.all()
    
    # جلب الإعدادات
    settings_rows = Setting.query.all()
    settings_dict = {s.key: s.value for s in settings_rows}
    
    post_dict = None
    if post_id:
        post = Post.query.get(post_id)
        if post:
            post_dict = {'id': post.id, 'title': post.title, 'category_id': post.category_id, 
                         'site_id': post.site_id, 'content': post.content, 'status': post.status}
            
    return render_template('editor.html', sites=sites, post=post_dict, settings=settings_dict)

@main_blueprint.route('/settings', methods=['GET', 'POST'])
def settings():
    if request.method == 'POST':
        export_path = request.form.get('local_export_path', '')
        if export_path and not export_path.endswith('/'):
            export_path += '/'
            
        setting = Setting.query.get('local_export_path')
        if setting:
            setting.value = export_path
        else:
            setting = Setting(key='local_export_path', value=export_path)
            db.session.add(setting)
            
        db.session.commit()
        flash('تم حفظ الإعدادات بنجاح', 'success')
        return redirect(url_for('main.settings'))
    
    settings_rows = Setting.query.all()
    settings_dict = {s.key: s.value for s in settings_rows}
    return render_template('settings.html', settings=settings_dict)

@main_blueprint.route('/add_site', methods=['POST'])
def add_site():
    name = request.form['name']
    new_site = Site(name=name)
    db.session.add(new_site)
    db.session.commit()
    flash('تمت إضافة الموقع بنجاح', 'success')
    return redirect('/')

@main_blueprint.route('/add_category', methods=['POST'])
def add_category():
    name = request.form['name']
    site_id = request.form['site_id']
    new_cat = Category(name=name, site_id=site_id, image_format="")
    db.session.add(new_cat)
    db.session.commit()
    flash('تمت إضافة القسم بنجاح', 'success')
    return redirect('/')

@main_blueprint.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post:
        db.session.delete(post)
        db.session.commit()
        flash('تم حذف المقالة نهائياً', 'error')
    return redirect(request.referrer or '/')

@main_blueprint.route('/delete_site/<int:site_id>', methods=['POST'])
def delete_site(site_id):
    site = Site.query.get(site_id)
    if site:
        if site.categories:
            flash('لا يمكن حذف الموقع لأنه يحتوي على أقسام. الرجاء نقلها أو حذفها أولاً', 'error')
        else:
            db.session.delete(site)
            db.session.commit()
            flash('تم حذف الموقع بنجاح', 'success')
    return redirect('/')

@main_blueprint.route('/delete_category/<int:cat_id>', methods=['POST'])
def delete_category(cat_id):
    category = Category.query.get(cat_id)
    if category:
        if category.posts:
            flash('لا يمكن حذف القسم لأنه يحتوي على مقالات. الرجاء نقلها أو حذفها أولاً', 'error')
        else:
            db.session.delete(category)
            db.session.commit()
            flash('تم حذف القسم بنجاح', 'success')
    return redirect('/')

@main_blueprint.route('/api/categories/<int:site_id>')
def get_categories(site_id):
    cats = Category.query.filter_by(site_id=site_id).all()
    return jsonify([{'id': c.id, 'name': c.name, 'image_format': c.image_format} for c in cats])

@main_blueprint.route('/api/save_post', methods=['POST'])
def save_post():
    data = request.json
    post_id = data.get('post_id')
    title = data['title']
    cat_id = data['category_id']
    site_id = data['site_id']
    content = data['content']
    status = data.get('status', 'draft')
    
    if post_id:
        existing = Post.query.filter(Post.title == title, Post.site_id == site_id, Post.category_id == cat_id, Post.id != post_id).first()
        if existing:
            return jsonify({"status": "error", "message": "يوجد مقالة أخرى بهذا العنوان في نفس القسم"})
            
        post = Post.query.get(post_id)
        post.title = title
        post.category_id = cat_id
        post.site_id = site_id
        post.content = json.dumps(content)
        post.status = status
        msg = "تم التحديث"
    else:
        existing = Post.query.filter_by(title=title, site_id=site_id, category_id=cat_id).first()
        if existing:
            return jsonify({"status": "error", "message": f"المقالة بعنوان '{title}' موجودة مسبقاً"})
            
        post = Post(title=title, category_id=cat_id, site_id=site_id, content=json.dumps(content), status=status)
        db.session.add(post)
        db.session.flush() # للحصول على الآي دي قبل الكوميت
        post_id = post.id
        msg = "تم الحفظ بنجاح"
        
    db.session.commit()
    return jsonify({"status": "success", "message": msg, "post_id": post_id, "post_status": status})

@main_blueprint.route('/uploadFile', methods=['POST'])
def upload_file():
    if 'image' not in request.files: return jsonify({"success": 0})
    file = request.files['image']
    
    def clean_name(name):
        return re.sub(r'[\\/*?:"<>|]', "", name).replace(' ', '_')
        
    site_name = clean_name(request.form.get('site_name', 'Uncategorized'))
    cat_name = clean_name(request.form.get('cat_name', 'General'))

    if file:
        filename = secure_filename(file.filename)
        save_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], site_name, cat_name)
        os.makedirs(save_dir, exist_ok=True)
        file.save(os.path.join(save_dir, filename))
        rel_path = f"{site_name}/{cat_name}/{filename}"
        return jsonify({"success": 1, "file": {"url": url_for('static', filename=f'uploads/{rel_path}')}})
    return jsonify({"success": 0})

@main_blueprint.route('/edit_site/<int:site_id>', methods=['GET', 'POST'])
def edit_site(site_id):
    site = Site.query.get(site_id)
    if not site: return redirect('/')
    
    if request.method == 'POST':
        site.name = request.form['name']
        db.session.commit()
        flash('تم تعديل اسم الموقع بنجاح', 'success')
        return redirect('/')
    
    return render_template('edit_site.html', site=site)

@main_blueprint.route('/edit_category/<int:cat_id>', methods=['GET', 'POST'])
def edit_category(cat_id):
    category = Category.query.get(cat_id)
    if not category: return redirect('/')
    
    if request.method == 'POST':
        category.name = request.form['name']
        category.site_id = request.form['site_id']
        db.session.commit()
        flash('تم تعديل القسم بنجاح', 'success')
        return redirect('/')
    
    sites = Site.query.all()
    return render_template('edit_category.html', category=category, sites=sites)

@main_blueprint.route('/media')
def media():
    upload_dir = current_app.config['UPLOAD_FOLDER']
    images = []
    if os.path.exists(upload_dir):
        for root, dirs, files in os.walk(upload_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                    full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(full_path, upload_dir).replace('\\', '/')
                    images.append({
                        'path': rel_path,
                        'name': file,
                        'folder': os.path.basename(root),
                        'time': os.path.getmtime(full_path)
                    })
        images = sorted(images, key=lambda x: x['time'], reverse=True)
    return render_template('media.html', images=images)

@main_blueprint.route('/delete_media/<path:filename>', methods=['POST'])
def delete_media(filename):
    if '..' in filename: return "Invalid path", 400
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if os.path.exists(file_path):
        os.remove(file_path)
        flash('تم حذف الصورة من السيرفر بنجاح', 'success')
    return redirect('/media')

@main_blueprint.route('/bulk_delete_posts', methods=['POST'])
def bulk_delete_posts():
    post_ids = request.form.getlist('post_ids')
    if post_ids:
        # استخدام IN للحذف دفعة واحدة بكفاءة
        Post.query.filter(Post.id.in_(post_ids)).delete(synchronize_session=False)
        db.session.commit()
        flash('تم حذف المقالات المحددة نهائياً', 'error') # نستخدم error ليتوافق مع لون الحذف في نظامك
    else:
        flash('لم يتم تحديد أي مقالات للحذف', 'error')
    
    return redirect(request.referrer or '/')

@main_blueprint.route('/tashkeel')
def tashkeel():
    return render_template('tashkeel.html')