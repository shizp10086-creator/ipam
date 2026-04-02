# Use Python 3.10 standard image
FROM python:3.10

# Set pip mirror to use PKU
RUN pip config set global.index-url http://mirrors.pku.edu.cn/pypi/web/simple/ && \
    pip config set install.trusted-host mirrors.pku.edu.cn

# Set working directory
WORKDIR /app

# Set Debian mirror to use PKU
RUN sed -i 's/deb.debian.org/mirrors.pku.edu.cn/g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's/deb.debian.org/mirrors.pku.edu.cn/g' /etc/apt/sources.list 2>/dev/null || true

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    default-libmysqlclient-dev \
    pkg-config \
    curl \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
