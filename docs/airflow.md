# Configuração Spark no Airflow - Guia Passo a Passo

## 📋 Pré-requisitos
- Airflow instalado e rodando
- Spark instalado no ambiente
- Docker configurado (se aplicável)

## ⚙️ Passo 1: Configurar Conexão Spark no Airflow

### 1.1 Acessar a Interface de Administração
1. Abra a UI do Airflow no seu navegador
2. No menu superior, clique em **"Admin"**
3. Selecione **"Connections"** no menu dropdown

### 1.2 Criar Nova Conexão
1. Clique no botão **"+"** (Add a new record) ou **"Create"**
2. Preencha os campos conforme abaixo:

## 📝 Passo 2: Configuração dos Campos da Conexão

### Campos Obrigatórios

| Campo | Valor | Descrição |
|-------|-------|-----------|
| **Connection Id** | `spark_default` | Identificador único da conexão |
| **Connection Type** | `Spark` | Tipo de conexão (selecionar da lista) |
| **Host** | `local[*]` | Modo local usando todos os cores disponíveis |
| **Deploy Mode** | `client` | Modo de deploy mais comum para desenvolvimento |
| **Spark Binary** | `spark-submit` | Comando padrão do Spark |

### Campos Opcionais

| Campo | Valor | Observação |
|-------|-------|------------|
| **Description** | `Conexão Spark Local para Docker` | Descrição opcional |
| **Port** | *Deixar em branco* | Não necessário para modo local |
| **YARN Queue** | *Deixar em branco* | Não utilizando YARN |
| **Kubernetes Namespace** | *Deixar em branco* | Não utilizando Kubernetes |
| **Principal** | *Deixar em branco* | Apenas se usar Kerberos |
| **Keytab** | *Deixar em branco* | Apenas se usar Kerberos |

## 🔧 Passo 3: Configurações Detalhadas

### 3.1 Configuração do Host
- **`local[*]`**: Usa todos os cores da máquina
- **`local[2]`**: Usa apenas 2 cores (alternativa)
- **`local`**: Usa apenas 1 core

### 3.2 Configuração de Deploy Mode
- **`client`**: Recomendado para desenvolvimento local
- **`cluster`**: Para ambientes distribuídos

## ✅ Passo 4: Salvar e Testar a Conexão

### 4.1 Salvar Configuração
1. Após preencher todos os campos necessários
2. Clique em **"Save"** para salvar a conexão
3. Verifique se a conexão `spark_default` aparece na lista

### 4.2 Testar Conexão (Opcional)
1. Na lista de conexões, localize `spark_default`
2. Clique no ícone de **"Test"** (se disponível)
3. Verifique se não há erros de conectividade

## 🚀 Passo 5: Habilitar e Executar a DAG

### 5.1 Localizar a DAG
1. Volte para a página principal do Airflow
2. Procure pela DAG `pipeline_dados_paises` na lista
3. Aguarde alguns instantes caso ela não apareça imediatamente

### 5.2 Ativar a DAG
1. Localize o toggle (botão liga/desliga) ao lado do nome da DAG
2. Clique para **ativar** a DAG (deve ficar verde/azul)

### 5.3 Executar Manualmente
1. Clique no nome da DAG `pipeline_dados_paises`
2. No canto superior direito, clique em **"Trigger DAG"**
3. Confirme a execução

## 📊 Passo 6: Monitorar Execução

### 6.1 Acompanhar Progresso
1. Na visualização da DAG, observe o status das tarefas:
   - 🟢 **Verde**: Sucesso
   - 🔴 **Vermelho**: Erro
   - 🟡 **Amarelo**: Em execução
   - ⚪ **Branco**: Pendente

### 6.2 Verificar Logs
1. Clique em qualquer tarefa para ver detalhes
2. Selecione **"Log"** para ver mensagens detalhadas
3. Diagnostique erros se necessário

## 📁 Passo 7: Verificar Resultados

### 7.1 Localizar Arquivos de Saída
Após execução bem-sucedida, verifique:
```bash
./data/delta/
├── tabela1/
│   ├── _delta_log/
│   └── *.parquet
└── tabela2/
    ├── _delta_log/
    └── *.parquet
```

### 7.2 Inspeção dos Dados
- **Arquivos Parquet**: Dados processados
- **`_delta_log/`**: Logs de transação do Delta Lake
- Verifique se os diretórios foram criados corretamente

## 🔍 Troubleshooting Comum

### Problemas de Conexão
- ✅ Verificar se o Spark está instalado
- ✅ Confirmar que `spark-submit` está no PATH
- ✅ Validar configuração do Docker (se aplicável)

### Problemas de Execução
- ✅ Verificar logs das tarefas no Airflow
- ✅ Confirmar permissões de escrita no diretório `./data/`
- ✅ Validar sintaxe do código Spark

### Problemas de Performance
- ✅ Ajustar `local[*]` para `local[2]` se necessário
- ✅ Monitorar uso de memória e CPU
- ✅ Considerar otimizações específicas do Spark

## 📚 Próximos Passos

1. **Automatizar**: Configure scheduling da DAG
2. **Monitorar**: Configure alertas para falhas
3. **Otimizar**: Ajuste configurações baseado na performance
4. **Escalar**: Considere cluster Spark para dados maiores

---

*Configuração concluída! Sua pipeline Spark está rodando no Airflow.*