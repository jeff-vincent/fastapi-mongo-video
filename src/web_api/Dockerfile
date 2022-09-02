FROM python:3.10
COPY ./src/web_api/ . 
RUN pip install -r requirements.txt
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
