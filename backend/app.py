
import os
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Database Configuration
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'budget.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# --- Database Models ---
class Income(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False, default=0.0)

    def __init__(self, amount):
        self.amount = amount

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(100), nullable=False)

    def to_json(self):
        return {
            'id': self.id,
            'description': self.description,
            'amount': self.amount,
            'category': self.category
        }

# --- API Endpoints ---

# Initialize Database
@app.route('/api/db/init', methods=['POST'])
def init_db():
    with app.app_context():
        db.drop_all()
        db.create_all()
        # Initialize with a single income entry
        initial_income = Income(amount=0.0)
        db.session.add(initial_income)
        db.session.commit()
    return jsonify({'message': 'Database initialized successfully!'}), 200

# Income API
@app.route('/api/income', methods=['GET', 'POST'])
def manage_income():
    if request.method == 'POST':
        data = request.get_json()
        income = Income.query.first()
        if not income:
            income = Income(amount=data.get('amount', 0))
            db.session.add(income)
        else:
            income.amount = data.get('amount', income.amount)
        db.session.commit()
        return jsonify({'message': 'Income updated successfully!', 'amount': income.amount}), 200
    
    income = Income.query.first()
    if not income:
        # If no income is set, initialize it to 0
        income = Income(amount=0.0)
        db.session.add(income)
        db.session.commit()
        
    return jsonify({'amount': income.amount})

# Expenses API
@app.route('/api/expenses', methods=['GET', 'POST'])
def manage_expenses():
    if request.method == 'POST':
        data = request.get_json()
        if not data or 'description' not in data or 'amount' not in data or 'category' not in data:
            return jsonify({'error': 'Missing data'}), 400
        
        new_expense = Expense(
            description=data['description'],
            amount=float(data['amount']),
            category=data['category']
        )
        db.session.add(new_expense)
        db.session.commit()
        return jsonify(new_expense.to_json()), 201

    expenses = Expense.query.all()
    return jsonify([expense.to_json() for expense in expenses])

@app.route('/api/expenses/<int:id>', methods=['DELETE'])
def delete_expense(id):
    expense = Expense.query.get(id)
    if expense is None:
        return jsonify({'error': 'Expense not found'}), 404
    
    db.session.delete(expense)
    db.session.commit()
    return jsonify({'message': 'Expense deleted successfully!'}), 200

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Check if income is initialized
        if Income.query.first() is None:
            initial_income = Income(amount=0.0)
            db.session.add(initial_income)
            db.session.commit()
            
    app.run(debug=True, port=5001)

