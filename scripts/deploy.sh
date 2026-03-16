#!/bin/bash

# Exit on error
set -e

echo "Starting deployment to Firebase..."

# Install Firebase CLI if not already installed
if ! command -v firebase &> /dev/null; then
    echo "Firebase CLI not found. Installing..."
    npm install -g firebase-tools
fi

# Copy necessary files to functions directory
echo "Copying necessary files to functions directory..."
cp -r controllers/CloudRunSpecificInMemoryOpenAiKeyHandling.py functions/controllers/
cp -r controllers/MatrixLayerOne.py functions/controllers/
cp -r controllers/AnswerPatternProcessor.py functions/controllers/
cp -r controllers/EngineRoom.py functions/controllers/
cp -r controllers/GptAgentInteractions.py functions/controllers/
cp -r controllers/GraphPatternProcessor.py functions/controllers/
cp -r logger/ functions/
cp -r sql_queries/ functions/
cp -r templates/ functions/

# Copy templates to functions directory
echo "Copying templates to functions directory..."
cp -r templates/ functions/

# Create json_blueprints directory if it doesn't exist
mkdir -p functions/json_blueprints

# Login to Firebase
echo "Logging in to Firebase..."
firebase login

# Initialize Firebase project if not already initialized
if [ ! -f .firebaserc ]; then
    echo "Initializing Firebase project..."
    firebase init
fi

# Deploy to Firebase
echo "Deploying to Firebase..."
firebase deploy

echo "Deployment completed successfully!"