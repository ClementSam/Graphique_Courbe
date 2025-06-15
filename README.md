# Graphique Courbe

This project is a graphical application for managing plots.

## Setup

Install dependencies using pip:

```bash
pip install -r requirements.txt
```

Then run the application:

```bash
python main.py
```

When importing curves from files (CSV, JSON, BIN, etc.) a selection dialog
lets you choose which curves are actually added to the project.

## Bit grouping

To create grouped bit curves, open the curve properties panel, check "Afficher les bits", then add groups using the table. Enter bit indices separated by commas in the order from LSB to MSB. For example, to create a group named "bit1_3" using bit 1 as MSB and bit 3 as LSB, type "3,1" in the Bits column.
