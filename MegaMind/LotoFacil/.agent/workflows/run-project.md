---
description: Como rodar o projeto LotoMind Enterprise usando Docker Compose
---

Siga estes passos para subir o ambiente completo:

1. Acesse o diretório raiz do projeto: `c:\Users\widso\OneDrive\Documentos\Projetos\LotoFacil`

2. Crie o arquivo `.env` a partir do exemplo:
```powershell
copy .env.example .env
```

3. Instale as dependências do frontend (opcional para rodar via Docker, mas recomendado para o VS Code reconhecer os tipos):
```powershell
cd frontend
npm install
cd ..
```

// turbo
4. Suba os containers usando Docker Compose:
```powershell
docker-compose up --build -d
```

5. Verifique se os serviços estão rodando:
```powershell
docker-compose ps
```

### Endpoints Disponíveis:
- **Frontend**: [http://localhost:3000](http://localhost:3000)
- **Backend Java**: [http://localhost:8080/api/v1](http://localhost:8080/api/v1)
- **Backend Python**: [http://localhost:8000/api/v1](http://localhost:8000/api/v1)
- **Adminer / PG Admin** (se adicionado futuramente)

### Logs:
Para ver os logs de um serviço específico:
```powershell
docker-compose logs -f backend-java
```
