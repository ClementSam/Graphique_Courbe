# Graphique Courbe

Graphique Courbe is a PyQt-based application for managing and visualizing sets of curves. It provides tools to load, edit and display multiple graphs using custom widgets built on top of PyQt5 and pyqtgraph.

## Directory Structure

```
core/         - application logic, models and services
controllers/  - controller classes linking UI and core logic
ui/
  widgets/    - custom widgets used throughout the interface
  dialogs/    - dialogs for loading data and managing layouts
io/           - import/export helpers for curves, graphs and projects
tests/        - unit tests
```

## Dependencies

The project mainly relies on the following libraries:

- PyQt5
- pyqtgraph
- pandas
- numpy
- pytest (for running the tests)
