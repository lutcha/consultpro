# Deploy ConsultPro no Digital Ocean

## Opção 1: Droplet com Docker (Recomendada)

### 1. Criar Droplet
- **OS:** Ubuntu 24.04 (LTS)
- **Plan:** Basic, $12/mo (2GB RAM / 1 CPU) mínimo
- **Datacenter:** mais próximo de ti (Frankfurt ou Amsterdam)
- **Auth:** SSH key (recomendado) ou password

### 2. Aceder ao Droplet
```bash
ssh root@<IP_DO_DROPLET>
```

### 3. Instalar Docker & Docker Compose
```bash
# Update
apt update && apt upgrade -y

# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker root

# Instalar Docker Compose plugin
apt install docker-compose-plugin -y

# Verificar
docker version
docker compose version
```

### 4. Clonar repositório
```bash
git clone https://github.com/<USER>/consultpro-backend.git /opt/consultpro
cd /opt/consultpro
```

### 5. Configurar .env
```bash
cp .env.example .env
nano .env
```

Alterar:
```env
DEBUG=False
SECRET_KEY=<gerar-uma-chave-segura>
DJANGO_SETTINGS_MODULE=config.settings.production
ALLOWED_HOSTS=<IP_DO_DROPLET>,api.consultpro.com

POSTGRES_HOST=db
POSTGRES_PASSWORD=<password-forte>

CELERY_BROKER_URL=redis://redis:6379/1
CELERY_RESULT_BACKEND=redis://redis:6379/2

AWS_S3_ENDPOINT_URL=http://minio:9000
OPENAI_API_KEY=sk-...
```

### 6. Gerar SECRET_KEY segura
```bash
docker run --rm python:3.11-slim python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 7. Iniciar serviços
```bash
docker compose up -d db redis minio
docker compose build api celery celery-beat
docker compose up -d api celery celery-beat
```

### 8. Migrations + Fixtures
```bash
docker compose exec api python manage.py migrate
docker compose exec api python manage.py loaddata fixtures/initial_data.json
```

### 9. Criar superuser
```bash
docker compose exec api python manage.py createsuperuser
```

### 10. Configurar Nginx (reverse proxy)
```bash
apt install nginx -y
```

Criar `/etc/nginx/sites-available/consultpro`:
```nginx
server {
    listen 80;
    server_name <IP_DO_DROPLET> api.consultpro.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /opt/consultpro/staticfiles/;
    }

    location /media/ {
        alias /opt/consultpro/media/;
    }
}
```

```bash
ln -s /etc/nginx/sites-available/consultpro /etc/nginx/sites-enabled/
nginx -t
systemctl restart nginx
```

### 11. Firewall
```bash
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw enable
```

### 12. HTTPS (Let's Encrypt) - Opcional
```bash
apt install certbot python3-certbot-nginx -y
certbot --nginx -d api.consultpro.com
```

---

## Opção 2: App Platform (PaaS)

Para deploy mais rápido sem gerir servidor:

1. Criar app no DO App Platform
2. Conectar ao repositório GitHub
3. Definir variáveis de ambiente
4. Adicionar Postgres Managed Database
5. Deploy automático a cada push

**Nota:** Para App Platform, precisas de um `Dockerfile` de produção e um `app.yaml`.

---

## Comandos úteis de manutenção

```bash
# Ver logs
docker compose logs -f api
docker compose logs -f celery

# Restart
docker compose restart api

# Backup DB
docker compose exec db pg_dump -U consultpro consultpro > backup_$(date +%F).sql

# Restore DB
docker compose exec -T db psql -U consultpro < backup_2024-01-01.sql

# Atualizar (após git pull)
docker compose build api
docker compose up -d api
docker compose exec api python manage.py migrate
```
