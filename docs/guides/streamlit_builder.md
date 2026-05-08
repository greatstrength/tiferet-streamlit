# StreamlitBuilder Guide

**Module:** `tiferet_streamlit.builders.main`
**Import:** `from tiferet_streamlit import StreamlitApp` (alias for `StreamlitBuilder`)

## Overview

`StreamlitBuilder` is the application entry point for tiferet-streamlit. It extends Tiferet's `AppBuilder` — following the same pattern as `CliBuilder` — to wire Streamlit's multi-page navigation with Tiferet's DI, feature dispatch, and interface loading.

## Quick Start

```python
from tiferet_streamlit import StreamlitApp
from views import HomeView, CalculatorView

app = StreamlitApp()
app.load_app_service(app_yaml_file='config.yml')
app.run('my_app', pages={
    'home': HomeView,
    'calculator': CalculatorView,
})
```

Run with `streamlit run app.py` from the directory containing `config.yml`.

## Configuration

The builder loads its configuration from Tiferet's standard `config.yml`. At minimum, define an interface:

```yaml
interfaces:
  my_app:
    name: My App
    description: A Streamlit app powered by Tiferet
```

The `load_app_service()` method accepts the config file path:

```python
app.load_app_service(app_yaml_file='config.yml')
```

This defaults to `AppYamlRepository` from Tiferet, which reads interfaces, services, features, and errors from the consolidated config file.

## Registering Pages

### Programmatic (dict of classes)

Map route strings to `ViewContext` subclasses:

```python
app.run('my_app', pages={
    'home': HomeView,
    'calculator': CalculatorView,
    'settings': SettingsView,
})
```

Each route becomes a page in Streamlit's navigation. The view key is set to the route.

### Configuration-Driven (Page domain objects)

Use `Page` objects for YAML-style configuration with metadata:

```python
from tiferet_streamlit import StreamlitApp, Page

page_configs = [
    Page(
        route='home',
        title='Home',
        icon=':house:',
        view_module_path='views',
        view_class_name='HomeView',
    ),
    Page(
        route='calculator',
        title='Calculator',
        icon=':abacus:',
        layout='wide',
        view_module_path='views',
        view_class_name='CalculatorView',
    ),
]

app = StreamlitApp()
app.load_app_service(app_yaml_file='config.yml')
app.run('my_app', page_configs=page_configs)
```

When both `pages` and `page_configs` are provided, `page_configs` takes precedence.

## Methods

### `load_app_service(**parameters)`

Inherited from `AppBuilder`. Loads the Tiferet application service (default: `AppYamlRepository`). Pass `app_yaml_file='config.yml'` to point to your config.

### `create_view(view_cls, app, key, session=None)`

Creates a `ViewContext` instance with a namespaced `SessionCacheContext`:

```python
view = builder.create_view(MyView, interface, key='home')
```

### `build_pages(app, pages)`

Builds a `PageContext` from a `{route: ViewContextClass}` dict.

### `build_pages_from_config(app, page_configs)`

Builds a `PageContext` from a list of `Page` domain objects.

### `run(interface_id, pages=None, page_configs=None)`

Loads the interface, builds pages, and starts Streamlit navigation. Raises `TiferetError` if neither `pages` nor `page_configs` is provided.

## Inheritance

`StreamlitBuilder` extends `AppBuilder`, so all of `AppBuilder`'s methods are available — `load_interface()`, `create_service_provider()`, etc. This is the same pattern as `CliBuilder` in core Tiferet.
