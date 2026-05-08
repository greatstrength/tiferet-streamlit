# Calculator Example

A complete calculator application demonstrating all `tiferet-streamlit` components working together.

## Prerequisites

- Python 3.10+
- `tiferet-streamlit` installed (see root README)

## Setup

```bash
# From the repository root
pip install -e .
```

## Running

```bash
cd example
streamlit run app.py
```

## What to Expect

The app launches with two pages:

### Calculator Page
- Two number inputs (a, b)
- Six operation buttons: Add, Subtract, Multiply, Divide, Power, Square Root
- Results displayed below the buttons
- Division by zero shows an error message
- Square root uses exponentiation with b=0.5

### About Page
- Static page describing the app architecture and components used

## Architecture

- **`app/events/settings.py`** — `BasicCalcEvent` base class with `verify_number()` validation
- **`app/events/calc.py`** — Five arithmetic domain events
- **`config.yml`** — Consolidated Tiferet configuration (interfaces, services, errors, features)
- **`views.py`** — `CalculatorView`, `AboutView`, `NumberInput`, `ResultDisplay`
- **`app.py`** — Entry point using `StreamlitApp`
