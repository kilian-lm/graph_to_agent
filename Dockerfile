## Use Python 3.11 as the base image
#FROM python:3.11.0
#
#LABEL maintainer="kilian.lehn"
#
## Set the working directory to /app
#WORKDIR /app
#
## Copy the requirements file into the container
#COPY requirements.txt .
#
## Install any needed packages specified in requirements.txt
#RUN pip install --no-cache-dir -r requirements.txt
#
## Copy the necessary files and directories into the container
##COPY app.py .
##COPY controllers ./controllers
##COPY assets ./assets
##COPY logger ./logger
##COPY sql_queries ./sql_queries
##COPY static ./static
##COPY templates ./templates
#
#COPY . /app
#
#
## Expose the port the app is running on
#EXPOSE 5000
#
## Run the application
##CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
#CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5000"]

# Use Python 3.11 as the base image
FROM  python:3.11.0

LABEL maintainer="kilian.lehn"

# Set the working directory to /app
#WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app

WORKDIR /app

# Copy the app directory contents into the container
#COPY [".", "."]

# Set the environment variable for the service account key
#ENV GOOGLE_APPLICATION_CREDENTIALS=cloud_vision_221122
#ENV CLOUD_STORAGE_BUCKET='cloud_vision_221122'
## Mount the local service account key file as a Docker secret
#RUN mkdir /run/secrets
#COPY service_account_key.json /run/secrets/service_account_key.json
#RUN chmod 400 /run/secrets/service_account_key.json

# Expose the port that Flask will run on
#EXPOSE 5000
#ENV PORT 5000
## Run the command to start the Flask app
##CMD ["python", "app.py"]
#
## Set the environment variable to point to your Flask application
ENV FLASK_APP=app.py
#
## Set the default command to run the application
#CMD ["flask", "run", "--host=0.0.0.0"]

#CMD [ "python3", "app.py"]

#CMD exec gunicorn --bind :$PORT app:app
#CMD [ "gunicorn", "--workers=1", "--threads=1", "-b 0.0.0.0:5000", "app:app"]

CMD ["flask", "run", "--host=0.0.0.0"]
