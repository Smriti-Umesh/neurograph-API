# Neurograph API 

It is a brain-inspired knowledge network which introduces learning-based behaviour. The system models entities such as papers, authors, and concepts as nodes, with relationships represented as weighted edges.  These relationships evolve over time using principles inspired by Hebbian learning. Connections strengthen when frequently activated, decay when unused, and can be reactivated if relevant again. This allows the system to simulate how knowledge forms, weakens, and reorganises over time.

## Setup Instructions

### 1. Clone the Repository

```bash
git https://github.com/Smriti-Umesh/neurograph-API.git
cd neurograph-API

# PostgreSQL
docker run -d \
  --name neurograph-postgres \
  -e POSTGRES_USER=app \
  -e POSTGRES_PASSWORD=app \
  -e POSTGRES_DB=brainnet \
  -p 5432:5432 \
  postgres:16


# RabbitMQ 
docker run -d \
  --name neurograph-rabbit \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management
```


### 2. Activate the venv
```bash
python -m venv venv

# Mac/Linux 
source venv/bin/activate
```

### 3. Install requirements
```bash
pip install -r requirements.txt
```

### 4. Environment variables
```bash
# create .env file in root directory 
DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/brainnet
API_BASE_URL=http://127.0.0.1:8000
```

### 5. Run migrations 
```bash
alembic upgrade head
```

### 6. Run API
```bash
uvicorn app.main:app --reload
 
```

## API Documentation 

[Open API Documentation (PDF)](docs/api_docs_main.pdf)
