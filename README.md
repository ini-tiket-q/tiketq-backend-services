# tiketq-backend-services
Monorepo for TiketQ OTA microservices — flights, ferries, hotels, PPOB, payments, and gateway.
----

### Structure
```bash
/tiketq-backend/
│
├── docker-compose.yml
├── .env
├── README.md
│
├── nginx/
│   └── nginx.conf
│
├── shared/
│   ├── logger.py               # logging config
│   ├── config.py               # Env loader or helpers
│   └── requirements.txt        
│
├── api-gateway/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── utils/
│       └── forwarder.py
│
├── auth-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── models.py
│
├── flights-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── services/
│       └── garuda_api.py
│
├── ferries-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── services/
│       └── pelni_api.py
│
├── hotels-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── services/
│       └── tiketcom_wrapper.py
│
├── ppob-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── services/
│       └── pln_api.py
│
├── payment-service/
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── midtrans.py
│   └── webhooks.py
│
└── postgres/
    └── init.sql                # DB schema bootstrap
```