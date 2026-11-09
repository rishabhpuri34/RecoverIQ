
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

### 8. Machine learning model requirements

The prediction feature requires two private files in the `ml_models/` directory:

- `recoveriq_ridge_practical_v1.pkl`
- `recoveriq_baseline_v1.json`

These files are not included in this public repository.

Without them, the Django application may start, but submitting a prediction scenario will not work. The trained model and baseline data are retained privately for the course demonstration.

## Project Status

This repository contains a functional research prototype developed for INFO 490.

The current development milestone is the November 9, 2026 P2-A3 submission.

Future work includes improving model validation, simulator usability, prediction reliability, and deployment readiness.
