FROM public.ecr.aws/lambda/python:3.9

# Install system dependencies for building Python packages
RUN yum update -y && yum install -y \
    gcc \
    gcc-c++ \
    make \
    && yum clean all

# Set working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY lambda_functions/ ./
COPY utils/ ./utils/

# Set permissions
RUN chmod -R 755 .

# Set the CMD to your main lambda handler
CMD ["lambda_function.lambda_handler"]
