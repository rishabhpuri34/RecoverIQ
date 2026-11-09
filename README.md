
# RecoverIQ
### Machine Learning-Based Decision Support for Struvite Recovery

RecoverIQ is a Django-based web application developed to explore how wastewater treatment operating conditions relate to phosphorus conversion in struvite recovery reactors.

The application integrates a machine learning model with a scenario simulator, allowing users to enter operating conditions, generate predictions, and compare results against a historical reference.

## Features

- User authentication and scenario-specific access
- Interactive what-if scenario simulator
- Ridge Regression model for phosphorus conversion prediction
- Historical baseline versus scenario comparison
- Predicted conversion differences in percentage points
- Historical operating-range warnings
- Scenario history stored in a SQLite database

## Machine Learning Model

RecoverIQ uses a Ridge Regression model trained on historical struvite reactor operating data.

- Model: Ridge Regression
- Input features: 30
- Training observations: 242
- Testing observations: 61
- Chronological train-test split: 80/20
- Test R²: 0.8321
- Test RMSE: 0.0357
- Test MAE: 0.0283

The model estimates phosphorus conversion as a fraction between 0 and 1 in the observed dataset. Predictions are not automatically constrained to this interval.

## Scenario Simulator

Users can enter:

- MgCl2 dosing flow (L/min)
- NaOH dosing flow (L/min)
- Recycle flow (L/min)
- Feed orthophosphate concentration (mg P/L)
- Temperature (°C)

Recycle flow is currently recorded but does not influence the ML prediction.

Other model inputs are populated from a fixed historical reference observation.

## Model Limitations

RecoverIQ is a research prototype, not an operational control system.

- Predictions represent statistical associations, not demonstrated causal effects.
- The baseline is a fixed historical observation, not live reactor data.
- The application checks selected inputs against historical training ranges.
- Inputs within individual training ranges may still represent unusual combinations.
- Feed total phosphorus is fixed at its historical baseline value.
- Predictions outside historical operating conditions may be unreliable.
- No commands are sent to physical treatment equipment.

## Model Files and Data Privacy

The trained model (`.pkl`) and historical baseline (`.json`) are excluded from the public GitHub repository.

The application requires these files in the `ml_models/` directory to generate predictions.

Historical wastewater treatment datasets are not publicly distributed through this repository.

## Technology Stack

- Python
- Django
- scikit-learn
- pandas
- joblib
- SQLite
- HTML and CSS


## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/rishabhpuri34/RecoverIQ.git
cd RecoverIQ
```

### 2. Create a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

Install the Python packages required by the application:

```bash
python -m pip install -r requirements.txt
```

### 4. Configure the application

Create a local `.env` file with the Django environment settings required by the project.

The `.env` file is excluded from GitHub and should never contain publicly shared credentials.

### 5. Initialize the database

```bash
python manage.py migrate
```

### 6. Create an administrator account

```bash
python manage.py createsuperuser
```

### 7. Run the application

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser.

### 8. Install the private machine learning model

RecoverIQ uses a trained Ridge Regression model and a historical baseline observation to generate phosphorus conversion predictions.

For research confidentiality, the model artifacts are not included in the public GitHub repository.

The following files are required:

- `recoveriq_ridge_practical_v1.pkl`
- `recoveriq_baseline_v1.json`

**For authorized course evaluation:**

1. Obtain `RecoverIQ_Private_Model_Files.zip` directly from the project developer after permission to share the artifacts has been confirmed.
2. Create an `ml_models/` directory inside the RecoverIQ project folder if it does not already exist.
3. Extract both files from the private ZIP into `ml_models/`.

The resulting directory structure should be:

```text
RecoverIQ/
├── core/
├── ml_models/
│   ├── recoveriq_ridge_practical_v1.pkl
│   └── recoveriq_baseline_v1.json
├── manage.py
├── requirements.txt
└── README.md
```

4. Start the Django development server using `python manage.py runserver`.
5. Log in to the application and open the scenario simulator.
6. Enter operating conditions, submit a scenario, and review the predicted phosphorus conversion and historical baseline comparison.

**Important:** Model artifacts should only be obtained from an authorized, trusted source. Serialized Python model files (`.pkl`) should never be loaded from unknown sources.

Without these private files, the application can start, but ML predictions cannot be generated.

The original historical training dataset is not required to run the application and is not included in the demonstration package.

## Project Status

This repository contains a functional research prototype developed for INFO 490.

The current development milestone is the November 16, 2026 P2-A3 first-draft submission.

Future work includes improving model validation, simulator usability, prediction reliability, and deployment readiness.
