FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY event_listner.py .
COPY contracts_abi/ /app/contracts_abi/

EXPOSE 9999

CMD ["python", "event_listner.py"]