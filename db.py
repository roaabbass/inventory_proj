from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    threshold = db.Column(db.Integer, nullable=False, default=5)  # Alert threshold
    price = db.Column(db.Float)
    image = db.Column(db.String(200), default='default.jpg')
    category = db.Column(db.String(50))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    barcode = db.Column(db.String(50), unique=True)  # For barcode scanning
    
    # Relationship with alerts
    alerts = db.relationship('Alert', backref='item', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Item {self.name}>'
    
    def needs_restock(self):
        return self.quantity < self.threshold


class Alert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    resolved = db.Column(db.Boolean, default=False)
    resolved_timestamp = db.Column(db.DateTime)
    severity = db.Column(db.String(20), default='medium')  # low, medium, high
    
    def resolve(self):
        self.resolved = True
        self.resolved_timestamp = datetime.utcnow()
    
    def __repr__(self):
        return f'<Alert for {self.item.name}>'


class InventoryLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    change_amount = db.Column(db.Integer)  # Positive for additions, negative for deductions
    previous_quantity = db.Column(db.Integer)
    new_quantity = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    source = db.Column(db.String(50))  # 'manual', 'scan', 'restock', etc.
    user = db.Column(db.String(50))  # Could be expanded to User model
    
    item = db.relationship('Item', backref='logs')
    
    def __repr__(self):
        return f'<InventoryLog {self.item.name} {self.change_amount:+}>'


class DetectionSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_path = db.Column(db.String(200))
    processed_image_path = db.Column(db.String(200))
    items_detected = db.Column(db.Integer)  # Count of unique items detected
    total_quantity = db.Column(db.Integer)  # Sum of all items counted
    
    # Relationship with detection results
    detections = db.relationship('DetectionResult', backref='session', lazy=True, cascade='all, delete-orphan')


class DetectionResult(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey('detection_session.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    detected_quantity = db.Column(db.Integer)
    confidence = db.Column(db.Float)  # Average confidence of detections
    
    item = db.relationship('Item')