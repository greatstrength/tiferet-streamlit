# Calculator Example

A sample multi-page Streamlit calculator powered by `tiferet-streamlit`.

## Structure

```
example/
├── app.py              # Streamlit entry point
├── config.yml          # Consolidated Tiferet configuration
├── views.py            # ViewContext and ViewComponent definitions
├── README.md
└── app/
    └── events/
        ├── settings.py # Base domain event with numeric validation
        └── calc.py     # Arithmetic domain events
```

## Running

From the `example/` directory:

```bash
pip install tiferet-streamlit
streamlit run app.py
```

## What It Demonstrates

- **ViewContext** — `CalculatorView` manages state and dispatches Tiferet features for arithmetic
- **ViewComponent** — `NumberInput` and `ResultDisplay` are reusable, composable UI pieces
- **SessionCacheContext** — State persists across Streamlit reruns via namespaced session keys
- **Multi-page navigation** — `CalculatorView` and `AboutView` registered as separate pages
- **Consolidated config.yml** — Interfaces, features, errors, and container in a single file
- **Domain events** — All arithmetic logic lives in Tiferet events, cleanly separated from the UI
