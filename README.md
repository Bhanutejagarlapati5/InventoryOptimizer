Inventory Optimizer API
Overview

Inventory Optimizer is a Flask-based REST API designed to help businesses forecast product demand and optimize inventory levels using machine learning.

The system uses a Random Forest Regression model trained on historical sales data to predict future demand. It also includes authentication, logging, and a SQLite database for data storage.

This API can be integrated with web dashboards, ERP systems, or inventory management tools.

Features

Demand prediction using Random Forest Regressor

REST API built with Flask

User authentication using Flask-Login

SQLite database for storing data

Logging for monitoring API activity

Swagger UI support for API documentation

Model training and prediction pipeline

Data preprocessing using Pandas and NumPy

Project Structure
InventoryOptimizer/
│
└── python_api/
    │
    ├── app.py              # Main Flask API application
    ├── model.py            # Machine learning model logic
    ├── requirements.txt    # Python dependencies
    ├── app.log             # Application logs
    │
    └── venv/               # Virtual environment (should not be committed)
Technologies Used

Python

Flask

Pandas

NumPy

Scikit-learn

SciPy

SQLite

Joblib

Flask-Login

Swagger UI

Installation
1. Clone the repository
git clone https://github.com/yourusername/inventory-optimizer.git
cd inventory-optimizer/python_api
2. Create a virtual environment
python -m venv venv

Activate the environment:

Windows

venv\Scripts\activate

Linux / Mac

source venv/bin/activate
3. Install dependencies
pip install -r requirements.txt
Running the Application

Start the Flask API:

python app.py

The API will start on:

http://localhost:5000
API Documentation

Swagger UI can be accessed at:

http://localhost:5000/swagger

This interface allows you to explore and test API endpoints interactively.

Machine Learning Model

The project uses:

RandomForestRegressor (Scikit-learn)

Steps involved in the ML pipeline:

Load historical sales data

Data preprocessing using Pandas

Feature engineering

Model training

Model evaluation (MAE, MSE)

Save trained model using Joblib

Generate demand predictions

Example Workflow

User logs into the system.

Historical inventory data is uploaded.

The system trains the ML model.

The API predicts future demand.

Results are returned via JSON.

Logging

Application logs are saved to:

app.log

Logs include:

API requests

Errors

Model activity

Security

The API uses:

Password hashing using Werkzeug

Session-based authentication

Login protection for secured routes

Dependencies

Key libraries used:

Flask

Pandas

NumPy

Scikit-learn

SciPy

Joblib

Matplotlib

All dependencies are listed in:

requirements.txt
