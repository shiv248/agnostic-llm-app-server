FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY src/ .

# Run the handler function
CMD ["uvicorn", "main:app", "--host", "0.0.0.0"]
