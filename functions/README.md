# Graph to Agent - Firebase Deployment

This directory contains the Firebase Cloud Functions implementation of the Graph to Agent application.

## Overview

The Graph to Agent application has been overhauled to deploy to Firebase, using the following Firebase services:

1. **Firebase Hosting** - For serving static content (HTML, CSS, JavaScript)
2. **Firebase Cloud Functions** - For running the Flask application
3. **Firestore** - For storing graph data, replacing BigQuery

## Deployment Instructions

### Prerequisites

- Node.js and npm installed
- Firebase CLI installed (`npm install -g firebase-tools`)
- A Firebase project created in the Firebase Console

### Steps to Deploy

1. Make the deployment script executable:
   ```
   chmod +x deploy.sh
   ```

2. Run the deployment script:
   ```
   ./deploy.sh
   ```

   This script will:
   - Copy necessary files to the functions directory
   - Log in to Firebase
   - Initialize the Firebase project if needed
   - Deploy the application to Firebase

3. After deployment, your application will be available at:
   ```
   https://graph-to-agent.web.app
   ```

## Local Development

To run the application locally for development:

1. Install the dependencies:
   ```
   cd functions
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```
   python main.py
   ```

   The application will be available at `http://localhost:5000`

## Architecture Changes

The following changes were made to adapt the application for Firebase:

1. **BigQuery to Firestore Migration**:
   - Created a FirestoreHandler class to replace BigQueryHandler
   - Updated data storage methods to use Firestore collections instead of BigQuery tables

2. **Flask to Cloud Functions**:
   - Modified the Flask application to work with Firebase Cloud Functions
   - Added a Cloud Function entry point in main.py

3. **Static Content Hosting**:
   - Moved static assets to the public directory for Firebase Hosting
   - Created an index.html file as the entry point for Firebase Hosting

## Environment Variables

The application requires the following environment variables to be set in the Firebase project:

- OPENAI_API_KEY - Your OpenAI API key
- EULA_O_K - Set to "TRUE" if the EULA has been accepted
- Other environment variables as needed by the application

You can set these variables using the Firebase CLI:

```
firebase functions:config:set openai.api_key="your-api-key" eula.ok="TRUE"
```

Or through the Firebase Console under Project Settings > Service Accounts > Environment Variables.