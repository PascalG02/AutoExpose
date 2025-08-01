FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for unixodbc, ODBC driver, FAISS, and Ollama
RUN apt-get update && apt-get install -y \
    gnupg \
    curl \
    unixodbc \
    unixodbc-dev \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Add Microsoft ODBC Driver 17 for SQL Server
RUN curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && curl -fsSL https://packages.microsoft.com/config/debian/12/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && rm -rf /var/lib/apt/lists/*

# Install Ollama
RUN curl -fsSL https://ollama.com/install.sh | sh

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Pull Ollama model
RUN ollama pull gemma3:1b

# Set environment variables
ENV PORT=5000

# Start Ollama server and Flask app
CMD ollama serve & sleep 5 && python app.py