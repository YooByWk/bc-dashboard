FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY contracts_abi/ /app/contracts_abi/

EXPOSE 58000

CMD ["python", "event_listener.py"]
