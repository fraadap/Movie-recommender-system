# Base image di AWS Lambda Python 3.11
FROM public.ecr.aws/lambda/python:3.11

# Copia requirements e installa le dipendenze in /var/task
COPY requirements.txt ./
RUN pip install --upgrade pip
RUN pip install -r requirements.txt --target "${LAMBDA_TASK_ROOT}"

# Copia il tuo codice sorgente nel container
COPY lambda_functions/ ${LAMBDA_TASK_ROOT}/lambda_functions/
COPY utils/ ${LAMBDA_TASK_ROOT}/utils/

# (Opzionale) Copia altri file che servono alla tua app, come .env o config
# COPY .env ${LAMBDA_TASK_ROOT}/

# Imposta l'entry point: <modulo>.<funzione>
# Qui handler.py dentro lambda_functions/ contiene la lambda_handler
CMD ["lambda_functions.handler.lambda_handler"]
