# Architecture

## Directory Structure

wedding_face_finder/
├── api/           # REST endpoints
├── services/      # Face engine, thumbnails, security
├── models.py      # SQLAlchemy models
├── config.py      # Pydantic settings
├── extensions.py  # Flask extensions
└── app.py         # Application factory


## Data Flow

1. Photos uploaded → saved to `uploads/`
2. Face processor extracts encodings → stored in `data/`
3. Thumbnails generated → stored in `thumbnails/`
4. Search query encodes selfie → linear scan against all encodings
5. Results sorted by Euclidean distance → returned as JSON