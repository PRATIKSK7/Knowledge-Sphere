#!/bin/bash

# Knowledge Sphere - One-Click Export & Release Script
set -e

echo "🚀 Starting Knowledge Sphere Export Process..."

# 1. Cleanup Unnecessary Files
echo "🧹 Cleaning up temporary files and caches..."
find . -name "__pycache__" -type d -exec rm -rf {} +
rm -rf frontend/dist

# 2. Build Frontend
echo "⚛️ Building Frontend..."
cd frontend
npm install
npm run build
cd ..

# 3. Verify Backend
echo "🐍 Verifying Backend..."
cd backend
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi
if command -v python3 &> /dev/null; then
    python3 -m compileall app/ > /dev/null
    echo "Backend syntax verification passed."
else
    echo "Skipping backend python compilation (python3 not found locally)."
fi
cd ..

# 4. Create Release Package Directory
echo "📦 Creating release directory..."
mkdir -p dist

# 5. Generate Release Notes
echo "📝 Generating release notes..."
cat << EOF > dist/release_notes.md
# Knowledge Sphere v1.0.0

## Release Information
- **Date**: $(date +"%Y-%m-%d")
- **Version**: 1.0.0

## Features Included
- Google Gemini 2.0 Flash / OpenAI / Ollama integration
- ChromaDB semantic search vector space (3072-dim)
- Neo4j Knowledge Graph Visualizer
- Celery asynchronous document ingestion pipeline
- Production-ready Docker Compose orchestration

## Installation
Run \`docker-compose up -d --build\` to start the entire stack.
EOF

# 6. Generate ZIP Archive
echo "🗜️ Compressing project into ZIP archive..."
zip -r dist/Knowledge_Sphere_v1.0.zip . -x "dist/*" -x ".git/*" -x "frontend/node_modules/*" -x "backend/venv/*" -x ".DS_Store" -x "backend/.pytest_cache/*" -x "backend/uploads/*" -x "ollama_data/*" > /dev/null

# 7. Generate Checksums
echo "🔐 Generating SHA256 Checksums..."
cd dist
if command -v shasum &> /dev/null; then
    shasum -a 256 Knowledge_Sphere_v1.0.zip > checksums.txt
else
    sha256sum Knowledge_Sphere_v1.0.zip > checksums.txt
fi
cd ..

echo "✅ Export complete! Artifacts generated in dist/ directory:"
ls -lh dist/
