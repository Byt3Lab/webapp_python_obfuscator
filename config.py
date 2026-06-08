
from pathlib import Path
import os

RACINE = Path(__file__).parent.resolve()
UPLOAD_FOLDER = os.path.join(RACINE, 'tmp', 'uploads')
OUTPUT_FOLDER = os.path.join(RACINE, 'tmp', 'outputs')

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
