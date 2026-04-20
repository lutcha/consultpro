# ConsultPro Backend

API backend Django REST Framework para a plataforma ConsultPro — gestão de consultoria internacional para concursos de organismos multilaterais (UN, WB, AfDB, UE).

## Stack Tecnológica

- **Django 5.0+** + Django REST Framework
- **PostgreSQL 15+**
- **Redis** (cache + Celery broker)
- **Celery** + Celery Beat (tarefas assíncronas)
- **MinIO** (storage S3-compatible para documentos)
- **JWT** (djangorestframework-simplejwt)
- **OpenAPI/Swagger** (drf-spectacular)

## Estrutura do Projeto

```
backend/
├── apps/
│   ├── users/              # Autenticação e gestão de utilizadores
│   ├── opportunities/      # Oportunidades de consultoria
│   ├── proposals/          # Propostas e editor
│   ├── quality_checks/     # Quality Check e scoring
│   ├── teams/              # Equipas e consultores
│   ├── notifications/      # Alertas e notificações
│   ├── ai_services/        # Integração com serviços de IA
│   └── core/               # Utilitários, permissions, dashboard
├── config/                 # Configuração Django
├── docker/                 # Dockerfiles
├── fixtures/               # Dados iniciais
└── requirements/           # Dependências
```

## Configuração Local

1. Copiar `.env.example` para `.env` e ajustar variáveis
2. Iniciar serviços com Docker Compose:

```bash
docker-compose up -d
```

3. Executar migrations:

```bash
make migrate
```

4. Carregar dados iniciais:

```bash
make fixtures
```

5. Criar superuser:

```bash
make superuser
```

## Comandos Úteis (Makefile)

| Comando | Descrição |
|---------|-----------|
| `make build` | Build das imagens Docker |
| `make up` | Iniciar serviços |
| `make down` | Parar serviços |
| `make migrate` | Executar migrations |
| `make migrations` | Criar migrations |
| `make test` | Executar testes com cobertura |
| `make lint` | Executar flake8 e mypy |
| `make format` | Executar black e isort |
| `make superuser` | Criar superuser |
| `make fixtures` | Carregar dados iniciais |

## Endpoints Principais

- `POST /api/auth/token/` — Obter JWT token
- `POST /api/auth/token/refresh/` — Refresh JWT token
- `GET /api/auth/me/` — Perfil do utilizador
- `GET /api/users/` — Listar utilizadores
- `GET /api/opportunities/` — Listar oportunidades
- `GET /api/proposals/` — Listar propostas
- `POST /api/quality-checks/{id}/run/` — Executar Quality Check
- `GET /api/dashboard/stats/` — Estatísticas do dashboard
- `GET /api/docs/` — Documentação Swagger

## Dados Iniciais

A fixture `fixtures/initial_data.json` contém:
- 3 utilizadores (consultant, manager, admin) — password: `password123`
- 4 oportunidades (UNICEF, World Bank, FAO, AfDB)
- 1 proposta em rascunho com secções, equipa e orçamento
