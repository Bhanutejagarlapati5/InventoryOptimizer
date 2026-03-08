# Inventory Optimizer

Inventory Optimizer is a system designed to help businesses forecast product demand and optimize stock levels using machine learning.

The project consists of two main components:

1. **Inventory Dashboard (Java)** – A user interface for managing inventory and viewing insights.
2. **Prediction API (Python + Flask)** – A machine learning service that predicts product demand using historical data.

---

# System Architecture

The system follows a client–server architecture.

InventoryDashboard (Java UI)  
⬇  
Flask API (Python Backend)  
⬇  
Machine Learning Model (Random Forest)  
⬇  
SQLite Database

---

# Components

## 1. Inventory Dashboard (Java)

The Inventory Dashboard provides a graphical interface for interacting with the system.

### Features

- View product inventory
- Upload or manage sales data
- Request demand predictions
- Display forecasting results
- Communicate with the backend prediction API

### Technologies Used

- Java
- Java Swing / JavaFX (depending on your implementation)
- HTTP requests to connect with Flask API

---

## 2. Prediction API (Python)

The backend service is built using **Flask** and provides endpoints for training models and predicting inventory demand.

### Features

- Machine learning demand prediction
- REST API endpoints
- Data processing with Pandas
- Model training using Scikit-learn
- SQLite database support
- Logging system

### Technologies Used

- Python
- Flask
- Pandas
- NumPy
- Scikit-learn
- SQLite
- Joblib

---

# Project Structure

```
InventoryOptimizer/
│
├── InventoryDashboard/        # Java UI application
│
└── python_api/                # Flask ML API
    │
    ├── app.py
    ├── model.py
    ├── requirements.txt
    └── app.log
```

---

# Installation

## 1. Clone the repository

```bash
git clone https://github.com/yourusername/inventory-optimizer.git
cd inventory-optimizer
```

---

# Running the Python API

Navigate to the API folder.

```bash
cd python_api
```

Create virtual environment.

```bash
python -m venv venv
```

Activate environment.

Windows

```bash
venv\Scripts\activate
```

Mac/Linux

```bash
source venv/bin/activate
```

Install dependencies.

```bash
pip install -r requirements.txt
```

Run the API.

```bash
python app.py
```

The API will start at:

```
http://localhost:5000
```

---

# Running the Java Dashboard

Open the **InventoryDashboard** project in your Java IDE.

Supported IDEs:

- IntelliJ IDEA
- Eclipse
- NetBeans

Steps:

1. Open the `InventoryDashboard` folder in the IDE.
2. Build the project.
3. Run the main class.

The dashboard will connect to the Flask API for predictions.

---

# Machine Learning Model

The system uses **RandomForestRegressor from Scikit-learn**.

Workflow:

1. Collect historical sales data
2. Perform data preprocessing
3. Train the model
4. Save the model
5. Generate demand predictions through the API

---

# Logging

API logs are stored in:

```
python_api/app.log
```

---

# Future Improvements

- Add real-time inventory tracking
- Implement deep learning forecasting models
- Deploy API to cloud services
- Add role-based authentication
- Create advanced analytics dashboards

---

# License

This project was developed for academic purposes.
