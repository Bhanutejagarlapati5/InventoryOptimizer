# Inventory Optimizer API

A Flask-based REST API that predicts product demand using machine learning to help businesses optimize inventory levels.

The system uses a **Random Forest Regression model** trained on historical sales data to forecast future demand and support inventory decision-making.

---

## Features

- Machine learning demand forecasting using **Random Forest Regressor**
- REST API built with **Flask**
- User authentication using **Flask-Login**
- **SQLite database** for data storage
- API activity logging
- Swagger UI for API documentation
- Data processing with **Pandas** and **NumPy**

---

## Project Structure

```
InventoryOptimizer/
│
└── python_api/
    │
    ├── app.py              # Main Flask API application
    ├── model.py            # Machine learning model logic
    ├── requirements.txt    # Python dependencies
    ├── app.log             # Application logs
    │
    └── venv/               # Virtual environment (not recommended to commit)
```

---

## Technologies Used

- Python
- Flask
- Pandas
- NumPy
- Scikit-learn
- SciPy
- SQLite
- Joblib
- Flask-Login
- Swagger UI

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/inventory-optimizer.git
cd inventory-optimizer/python_api
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate the environment.

**Windows**

```bash
venv\Scripts\activate
```

**Mac / Linux**

```bash
source venv/bin/activate
```

---

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

---

## Running the Application

Start the Flask API server.

```bash
python app.py
```

The API will run on:

```
http://localhost:5000
```

---

## API Documentation

Swagger UI can be accessed at:

```
http://localhost:5000/swagger
```

This interface allows you to test and explore the API endpoints.

---

## Machine Learning Model

The system uses **RandomForestRegressor from Scikit-learn**.

### Workflow

1. Load historical sales data
2. Data preprocessing using Pandas
3. Feature engineering
4. Train Random Forest model
5. Evaluate model performance
6. Save model using Joblib
7. Generate demand predictions

---

## Example Use Case

1. User logs into the system.
2. Historical sales or inventory data is uploaded.
3. The system trains the machine learning model.
4. Future demand predictions are generated.
5. Results are returned through the API.

---

## Logging

Application logs are stored in:

```
app.log
```

Logs include:

- API requests
- Errors
- System activity

---

## Security

The API includes basic security features:

- Password hashing using **Werkzeug**
- Session-based authentication
- Protected API routes

---

## Dependencies

Key libraries used in this project:

- Flask
- Pandas
- NumPy
- Scikit-learn
- SciPy
- Joblib
- Matplotlib

All dependencies are listed in:

```
requirements.txt
```

---

## Future Improvements

Potential improvements for this project:

- Add deep learning forecasting models
- Create a web dashboard for visualization
- Integrate cloud databases
- Implement role-based access control
- Dockerize the application
- Deploy to cloud platforms

---

## License

This project is open-source and available under the MIT License.
