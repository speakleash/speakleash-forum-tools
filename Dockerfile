# Use an official Python runtime as a parent image
FROM python:3.11-slim
# Set the working directory in the container
WORKDIR /app

# Copy the pyproject.toml file into the container at /app
COPY pyproject.toml poetry.lock /app/

# Install dependencies specified in pyproject.toml
RUN pip install --no-cache-dir poetry==1.8.3 && poetry install

# Copy the current directory contents into the container at /app
COPY . /app
RUN poetry install
CMD [ "poetry", "run", "speakleash_forum_tools" ]
