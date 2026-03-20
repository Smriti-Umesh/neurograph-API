# Neurograph API 

It is a brain-inspired knowledge network which introduces learning-based behaviour. The system models entities such as papers, authors, and concepts as nodes, with relationships represented as weighted edges.  These relationships evolve over time using principles inspired by Hebbian learning. Connections strengthen when frequently activated, decay when unused, and can be reactivated if relevant again. This allows the system to simulate how knowledge forms, weakens, and reorganises over time.

## Setup Instructions

### 1. Clone the Repository

```bash
git https://github.com/Smriti-Umesh/neurograph-API.git
cd neurograph-API
```

### Step 2 - Create Environment File (.env) 

```
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

API_BASE_URL=http://127.0.0.1:8000
API_USERNAME= yourusername
API_PASSWORD=yourpassword
PUBMED_NETWORK_NAME=nameofyournetwork
PUBMED_QUERY= ex. hebbian learning
PUBMED_MAX_RECORDS=5
PUBMED_REINGEST_MODE=force_all 
```

### Step 3 - Setup docker container

```
docker-compose up --build

```


### Step 4 - Setup venv 

Depending on python version (python or python3) create venv
```
python -m venv venv
source venv/bin/activate

pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```
available on: http://127.0.0.1:8000/docs


### Step 5 - Frontend

In new terminal window. 

```
source venv/bin/activate
cd frontend
npm install
npm run dev
```

### Step 6 - Authentication Setup

Go to 
```
http://127.0.0.1:8000/docs
```

Register user via 
```
/auth/register
```

Login via 
```
/auth/login
```

Update .env with the setup username and password

```
API_USERNAME= yourusername
API_PASSWORD=yourpassword

```

And then you can normally login in frontend and use the network!

### Step 7 - Create a network name and add that to env. 

In frontend, Create a network name and then add it to .env

```
PUBMED_NETWORK_NAME=nameofyournetwork
```

### Step 8 - Start consumer events

in a new terminal window inside venv run 
```
source venv/bin/activate
python scripts/consumer_events.py

```

RabbitMQ Dashboard
```
http://localhost:15672
```



### Step 9 - A2A + Ingestion 

In a new terminal window inside venv run

```
python scripts/consumer_a2a.py
```


Then in another terminal window run 

```
python scripts/ingest_pubmed_data.py
python scripts/send_a2a_message.py
```


## API Documentation 

[Open API Documentation (PDF)](docs/api_docs_main.pdf)
