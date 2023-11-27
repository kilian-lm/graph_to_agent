## Use Python 3.11 as the base image
FROM python:3.11.0
#
LABEL maintainer="kilian.lehn"
#
## Set the working directory to /app
WORKDIR /app
#
# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Define environment variable
ENV GUNICORN_CMD_ARGS="--bind=0.0.0.0:5000 --workers=3 --threads=4"

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run app.py when the container launches using Gunicorn
CMD ["gunicorn", "app:app"]