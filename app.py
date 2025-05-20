from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_mail import Mail, Message
from db import db, Item, Alert
from werkzeug.utils import secure_filename
import os
from math import ceil
from datetime import datetime
import cv2
import numpy as np
from tensorflow.keras.models import load_model  # or your preferred object detection library

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///inventory.db'
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['DETECTION_FOLDER'] = 'static/detections'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your_email@gmail.com'
app.config['MAIL_PASSWORD'] = 'your_app_password'
app.config['THRESHOLD_QUANTITY'] = 5  # Default threshold for alerts

mail = Mail(app)
db.init_app(app)

# Create upload folders if they don't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DETECTION_FOLDER'], exist_ok=True)

# Initialize object detection model (placeholder - implement your actual model)
class ObjectDetector:
    def __init__(self):
        # Load your trained model here
        # self.model = load_model('path/to/your/model.h5')
        self.class_names = []  # Your item classes
    
    def detect_items(self, image_path):
        """Placeholder for actual detection logic"""
        # This should return a dictionary of {item_name: count}
        return {"sample_item": 3}  # Replace with actual detection

detector = ObjectDetector()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg', 'gif'}

@app.route('/')
def index():
    search_query = request.args.get('search', '')
    page = int(request.args.get('page', 1))
    per_page = 5

    query = Item.query
    if search_query:
        query = query.filter(Item.name.ilike(f'%{search_query}%'))

    total_items = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = ceil(total_items / per_page)

    return render_template('inventory.html', items=items, page=page,
                         total_pages=total_pages, search_query=search_query)

@app.route('/scan', methods=['GET', 'POST'])
def scan_inventory():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('No file selected', 'error')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('No file selected', 'error')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # Perform object detection
            try:
                detected_items = detector.detect_items(filepath)
                
                # Update inventory counts
                for item_name, count in detected_items.items():
                    item = Item.query.filter_by(name=item_name).first()
                    if item:
                        item.quantity = count
                        check_and_alert(item)
                
                db.session.commit()
                
                # Save detection result image (if your detector supports visualization)
                detection_path = os.path.join(app.config['DETECTION_FOLDER'], f"detected_{filename}")
                # Your code to save visualization here
                
                flash('Inventory scanned and updated successfully!', 'success')
                return redirect(url_for('inventory'))
            
            except Exception as e:
                flash(f'Error during detection: {str(e)}', 'error')
                return redirect(request.url)
    
    return render_template('scan.html')

def check_and_alert(item):
    """Check if item is below threshold and create alert if needed"""
    if item.quantity < item.threshold:
        # Check if there's already an unresolved alert
        existing_alert = Alert.query.filter_by(item_id=item.id, resolved=False).first()
        if not existing_alert:
            alert = Alert(item_id=item.id, timestamp=datetime.now())
            db.session.add(alert)
            send_low_stock_email(item)

def send_low_stock_email(item):
    """Send email notification for low stock items"""
    try:
        msg = Message(f"Low Stock Alert: {item.name}",
                      sender=app.config['MAIL_USERNAME'],
                      recipients=['manager@example.com'])  # Add your recipients
        
        msg.body = f"""
        Inventory Alert!
        
        Item: {item.name}
        Current Quantity: {item.quantity}
        Threshold: {item.threshold}
        
        Please restock this item as soon as possible.
        """
        
        mail.send(msg)
    except Exception as e:
        app.logger.error(f"Failed to send email: {str(e)}")

@app.route('/inventory')
def inventory():
    items = Item.query.all()
    shortage_items = [item for item in items if item.quantity < item.threshold]
    return render_template('inventory.html', items=items, shortage_items=shortage_items)

@app.route('/restock/<int:item_id>', methods=['POST'])
def restock_item(item_id):
    item = Item.query.get_or_404(item_id)
    restock_amount = int(request.form.get('amount', 10))  # Default to 10 if not specified
    
    item.quantity += restock_amount
    db.session.commit()
    
    # Resolve any alerts for this item
    Alert.query.filter_by(item_id=item.id, resolved=False).update({'resolved': True})
    db.session.commit()
    
    flash(f'{item.name} restocked by {restock_amount}! New quantity: {item.quantity}', 'success')
    return redirect(url_for('inventory'))

# ... (keep your existing add_item, edit_item, delete_item routes)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)