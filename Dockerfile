# Use Python 3.11 as the base image
FROM  python:3.11.0

LABEL maintainer="kilian.lehn"

# Set the working directory to /app
#WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the app directory contents into the container
COPY [".", "./"]

# Expose the port dash is running on
EXPOSE 5000

# Run locally
CMD gunicorn --bind 0.0.0.0:5000 app:app

