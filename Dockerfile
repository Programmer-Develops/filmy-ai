FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

# 2. Set the working directory
WORKDIR /app

# 3. Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy the rest of the application code
COPY . .

# 5. Expose the port (Render typically uses 10000 or expects you to read $PORT)
ENV PORT=8000
EXPOSE 8000

# Run application
CMD ["python", "main.py","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
