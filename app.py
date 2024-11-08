import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory
from werkzeug.utils import secure_filename
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///products.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'images'  # Thư mục lưu ảnh tải lên
db = SQLAlchemy(app)

# Tạo thư mục images nếu chưa có
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    unit = db.Column(db.String(50), nullable=False)
    image_filename = db.Column(db.String(100), nullable=True)  # Lưu tên file ảnh
    supplier = db.Column(db.String(200), nullable=False)  

with app.app_context():
    db.create_all()

# Tính năng thêm sản phẩm với ảnh từ máy tính
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        price = request.form['price']
        unit = request.form['unit']
        supplier = request.form['supplier']

        # Xử lý file ảnh tải lên
        image_file = request.files['image_file']
        if image_file:
            filename = secure_filename(f"{name}_{image_file.filename}")
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
        else:
            filename = None

        # Tạo sản phẩm mới và lưu vào cơ sở dữ liệu
        new_product = Product(name=name, price=price, unit=unit, image_filename=filename, supplier=supplier)
        db.session.add(new_product)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('add_product.html')

# Hiển thị danh sách sản phẩm
@app.route('/')
def index():
    query = request.args.get('query')
    if query:
        products = Product.query.filter(Product.name.contains(query)).all()
    else:
        products = Product.query.all()
    return render_template('index.html', products=products, query=query)

@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.price = request.form['price']
        product.unit = request.form['unit']
        product.supplier = request.form['supplier']

        # Xử lý cập nhật ảnh nếu có
        image_file = request.files['image_file']
        if image_file:
            filename = secure_filename(f"{product.name}_{image_file.filename}")
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            image_file.save(image_path)
            product.image_filename = filename

        db.session.commit()
        return redirect(url_for('index'))
    
    return render_template('edit_product.html', product=product)

@app.route('/delete_product/<int:product_id>', methods=['POST'])
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.image_filename:
        # Xóa file ảnh khỏi thư mục images nếu có
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], product.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)

    # Xóa sản phẩm khỏi cơ sở dữ liệu
    db.session.delete(product)
    db.session.commit()
    return redirect(url_for('index'))

# Đường dẫn để hiển thị ảnh
@app.route('/images/<filename>')
def display_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
