FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# LOOK INTO: after sucessful app creation, app goes missing if using `pip` not `pip3`, never seen that before
RUN pip3 install -r requirements.txt

COPY src/ /app/src

ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
