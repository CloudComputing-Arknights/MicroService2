FROM python:3.10-slim

WORKDIR /app

# Copy the requirements.txt file from the project directory into the working dirsectory and install the requirements.
COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy over the files
COPY . .

EXPOSE 8000

# An environment variable passed to the application
ENV WHERE_AM_I=DOCKER

# Start will run this command
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]