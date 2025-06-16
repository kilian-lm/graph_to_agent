# Graph to Agent - Firebase Deployment

This project has been overhauled to deploy to Firebase, transitioning from Google Cloud Platform (GCP) services to Firebase services.

## Overview of Changes

The following major changes were made to deploy the application to Firebase:

1. **Database Migration**: Replaced BigQuery with Firestore for data storage
   - Created a FirestoreHandler class to replace BigQueryHandler
   - Updated data models and queries to work with Firestore's document-based structure

2. **Server Migration**: Adapted the Flask application to run as a Firebase Cloud Function
   - Created a Cloud Function entry point in main.py
   - Modified the Flask routes to work with Firebase Functions Framework

3. **Static Content Hosting**: Set up Firebase Hosting for static assets
   - Created a public directory for static content
   - Added an index.html file as the entry point

4. **Configuration**: Created Firebase configuration files
   - firebase.json - Main configuration file
   - .firebaserc - Project linking
   - firestore.rules - Security rules for Firestore
   - firestore.indexes.json - Indexes for Firestore queries

5. **Deployment**: Created a deployment script (deploy.sh) to automate the deployment process

## Directory Structure

- `/functions` - Contains the Firebase Cloud Functions implementation
  - `/controllers` - Application controllers, including the new FirestoreHandler
  - `/logger` - Logging functionality
  - `/templates` - HTML templates
  - `main.py` - Entry point for the Cloud Function
  - `requirements.txt` - Dependencies for the Cloud Function

- `/public` - Static content for Firebase Hosting
  - `/static` - CSS, JavaScript, and images
  - `index.html` - Entry point for Firebase Hosting

## Deployment Instructions

See the detailed deployment instructions in the [functions/README.md](functions/README.md) file.

## Local Development

To run the application locally:

1. Install dependencies:
   ```
   cd functions
   pip install -r requirements.txt
   ```

2. Run the Flask application:
   ```
   python main.py
   ```

## Benefits of Firebase Deployment

1. **Simplified Infrastructure**: Firebase provides a unified platform for hosting, functions, and database
2. **Reduced Costs**: Firebase offers a generous free tier and pay-as-you-go pricing
3. **Automatic Scaling**: Firebase services scale automatically based on demand
4. **Improved Developer Experience**: Firebase provides a streamlined deployment process and comprehensive monitoring

## Future Enhancements

1. Implement Firebase Authentication for user management
2. Set up Firebase Storage for file uploads
3. Add Firebase Analytics for usage tracking
4. Implement Firebase Cloud Messaging for notifications