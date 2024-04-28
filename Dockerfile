# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set work directory
WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir --disable-pip-version-check poetry

# Copy the project files into the container
COPY pyproject.toml poetry.lock ./

# Install dependencies
RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi


COPY manage.py ./
COPY app/ ./app
COPY entrypoint.sh ./
RUN chmod +x ./entrypoint.sh


EXPOSE 8000

# Run the Gunicorn server
ENTRYPOINT ["/app/entrypoint.sh"]
