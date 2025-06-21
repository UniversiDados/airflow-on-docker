# Tutorial: Como Instalar e Executar Apache Airflow com Docker

## 📋 O que você vai aprender

Neste tutorial, você aprenderá a configurar e executar o Apache Airflow usando Docker de forma simples e prática. O Airflow é uma plataforma para desenvolver, agendar e monitorar workflows de dados.

## 🔧 Pré-requisitos

- Sistema operacional: Linux, macOS ou Windows (com WSL2)
- Conexão com internet
- Privilégios de administrador para instalação

## 📦 Passo 1: Instalação do Docker e Docker Compose

### No Ubuntu/Debian:
```bash
# Atualize os pacotes
sudo apt update

# Instale dependências
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# Adicione a chave GPG oficial do Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Adicione o repositório do Docker
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Instale Docker Engine e Docker Compose
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Adicione seu usuário ao grupo docker (para não precisar usar sudo)
sudo usermod -aG docker $USER
```

### No macOS:
1. Baixe o Docker Desktop em: https://www.docker.com/products/docker-desktop
2. Instale o arquivo `.dmg` baixado
3. Abra o Docker Desktop e aguarde a inicialização

### No Windows:
1. Instale o WSL2 (Windows Subsystem for Linux)
2. Baixe o Docker Desktop em: https://www.docker.com/products/docker-desktop
3. Instale seguindo as instruções do instalador
4. Certifique-se de que a integração com WSL2 está habilitada

## ✅ Passo 2: Verificação da Instalação

Após a instalação, **reinicie seu terminal** (ou faça logout/login no Linux) e execute os comandos de verificação:

### Teste o Docker:
```bash
docker run hello-world
```
**O que esperar:** Uma mensagem de boas-vindas confirmando que o Docker está funcionando corretamente.

### Verifique a versão do Docker Compose:
```bash
docker-compose --version
```
**O que esperar:** Algo como `docker-compose version 2.x.x`

> 💡 **Dica:** Se você receber erros de permissão no Linux, certifique-se de ter executado o comando `usermod` e reiniciado o terminal.

## 🚀 Passo 3: Configuração do Apache Airflow

### 3.1 Baixe o arquivo de configuração oficial:
```bash
curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.8.1/docker-compose.yaml'
```
**O que isso faz:** Baixa o arquivo de configuração oficial do Airflow otimizado para Docker.

### 3.2 Crie a estrutura de diretórios:
```bash
mkdir -p ./dags ./logs ./plugins ./config
echo -e "AIRFLOW_UID=$(id -u)" > .env
```
**O que isso faz:**
- `dags/`: Onde você colocará seus workflows (DAGs)
- `logs/`: Armazena logs do sistema
- `plugins/`: Para plugins personalizados
- `config/`: Configurações adicionais
- `.env`: Define o ID do usuário para evitar problemas de permissão

## 🗄️ Passo 4: Inicialização do Banco de Dados

```bash
docker compose up airflow-init
```
**O que isso faz:** Configura o banco de dados interno do Airflow e cria o usuário administrador.

**Aguarde até ver:** Uma mensagem indicando que a inicialização foi concluída com sucesso.

## 🎯 Passo 5: Executar o Airflow

```bash
docker compose up -d --build
```

**O que isso faz:** Inicia todos os serviços do Airflow em segundo plano (modo detached).

**Aguarde:** Cerca de 2-3 minutos para todos os serviços inicializarem completamente.

## 🌐 Passo 6: Acessar a Interface Web

1. Abra seu navegador
2. Acesse: **http://localhost:8080**
3. Use as credenciais:
   - **Usuário:** `airflow`
   - **Senha:** `airflow`

**O que você verá:** A interface principal do Airflow com exemplos de DAGs já carregados.

## 🔍 Passo 7: Verificação dos Serviços

### Veja todos os containers em execução:
```bash
docker-compose ps
```
**O que esperar:** Uma lista mostrando todos os serviços do Airflow rodando (webserver, scheduler, worker, etc.).

### Status esperado:
- ✅ airflow-webserver (porta 8080)
- ✅ airflow-scheduler 
- ✅ airflow-worker
- ✅ postgres (banco de dados)
- ✅ redis (message broker)

## 🛑 Passo 8: Parar o Airflow

Quando quiser parar todos os serviços:
```bash
docker-compose down
```
**O que isso faz:** Para e remove todos os containers, mas mantém os dados persistidos.

## 📁 Estrutura Final do Projeto

Após seguir todos os passos, você terá esta estrutura:
```
meu-projeto-airflow/
├── dags/                    # ← Coloque seus DAGs aqui
├── logs/                    # ← Logs automáticos
├── plugins/                 # ← Plugins personalizados
├── config/                  # ← Configurações extras
├── docker-compose.yaml      # ← Configuração dos serviços
└── .env                     # ← Variáveis de ambiente
```

## 🎉 Próximos Passos

1. **Crie seu primeiro DAG:** Coloque um arquivo Python na pasta `dags/`
2. **Explore a interface:** Navegue pelas abas DAGs, Admin, Browse
3. **Execute workflows:** Ative e execute os DAGs de exemplo
4. **Monitore logs:** Use a interface para acompanhar execuções

## ✨ Configurando Conexões

Para que seus DAGs possam interagir com outros serviços, como o Spark, você precisa configurar as conexões na interface do Airflow.

### Conexão com Spark (Local)

1.  Na interface do Airflow, vá para **Admin -> Connections**.
2.  Clique no botão `+` para adicionar uma nova conexão.
3.  Preencha o formulário com os seguintes valores:
    -   **Connection Id**: `spark_default`
    -   **Connection Type**: `Spark`
    -   **Description**: `Conexão local com Spark via spark-submit`
    -   **Host**: `local[*]`
    -   **Deploy mode**: `client`
    -   **Spark binary**: `spark-submit`
4.  Os outros campos podem ser deixados com seus valores padrão.
5.  Clique em **Save**.

Com esta configuração, você poderá executar tarefas do tipo `SparkSubmitOperator` em sua máquina local.

## 🆘 Solução de Problemas Comuns

### Problema: "Permission denied" no Linux
**Solução:**
```bash
sudo chown -R $USER:$USER ./dags ./logs ./plugins ./config
```

### Problema: Porta 8080 já em uso
**Solução:** Mude a porta no arquivo `docker-compose.yaml`:
```yaml
ports:
  - "8081:8080"  # Usa porta 8081 ao invés de 8080
```

### Problema: Containers não inicializam
**Solução:**
```bash
docker-compose down -v  # Remove volumes
docker-compose up airflow-init  # Reinicializa
docker-compose up -d
```

## 📚 Comandos Úteis para o Dia a Dia

```bash
# Ver logs de um serviço específico
docker-compose logs airflow-webserver

# Reiniciar todos os serviços
docker-compose restart

# Entrar no container do webserver
docker-compose exec airflow-webserver bash

# Atualizar apenas um serviço
docker-compose up -d airflow-webserver
```

---

🎊 **Parabéns!** Você agora tem o Apache Airflow rodando em Docker e está pronto para criar e gerenciar seus workflows de dados!
