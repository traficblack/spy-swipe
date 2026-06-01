# GUGÃO / XMX Corp — Intelligence Dashboard

Dashboard de inteligência para monitoramento de produtos, nichos e produtores.

## Estrutura do Projeto

```
nutra-swipe/
├── index.html              # Dashboard principal (abrir no browser)
├── data.js                 # Dados gerados (não editar manualmente)
├── data_clickup.json       # Cache das tarefas do ClickUp
├── data_docx.json          # Cache dos produtos extraídos dos .docx
├── .env                    # Credenciais (não commitar)
├── docx/                   # Arquivos .docx com swipe nativo
│   ├── diabetes.docx
│   ├── ed.docx
│   └── ...
└── scripts/
    ├── parse_clickup.py    # Busca tarefas do ClickUp
    ├── parse_docx.py       # Extrai produtos dos .docx
    └── update_dashboard.py # Orquestrador: roda tudo e gera data.js
```

## Como Atualizar os Dados

### Atualização Completa (ClickUp + Docx)

```bash
cd /Users/ghost/nutra-swipe
python3 scripts/update_dashboard.py
```

Isso vai:
1. Buscar todas as tarefas do ClickUp (com paginação automática)
2. Reler todos os arquivos .docx
3. Gerar `data.js` novo

### Atualizar Só os Docx

```bash
python3 scripts/parse_docx.py
```

### Atualizar Só o ClickUp

```bash
python3 scripts/parse_clickup.py
```

Depois de qualquer atualização parcial, rode o update_dashboard.py para regenerar o data.js.

## Dependências

```bash
pip3 install requests python-docx
```

## Adicionar Novo Arquivo Docx

1. Coloque o arquivo `.docx` na pasta `docx/`
2. O nome do arquivo vira o nicho (ex: `articulações.docx` → nicho `articulações`)
3. Para adicionar cor/label, edite `NICHES` em `scripts/update_dashboard.py`
4. Rode `python3 scripts/update_dashboard.py`

## Adicionar Novo Produtor

Edite `PRODUCERS` em `scripts/parse_docx.py` e `scripts/parse_clickup.py`:

```python
PRODUCERS = {
    'novo_produtor': ['Produto A', 'Produto B'],
    ...
}
```

E adicione o produtor em `PRODUCER_DEFS` no `update_dashboard.py`.

## Deploy

O dashboard é 100% estático. Para fazer deploy:

1. Rode `python3 scripts/update_dashboard.py` para gerar `data.js` atualizado
2. Copie `index.html` e `data.js` para qualquer servidor web ou abra localmente

### Abrir Localmente

```bash
open /Users/ghost/nutra-swipe/index.html
```

Ou servir localmente (evita problemas de CORS com alguns browsers):

```bash
cd /Users/ghost/nutra-swipe
python3 -m http.server 8080
# Abrir: http://localhost:8080
```

## Configuração (.env)

```
CLICKUP_API_KEY=pk_...
CLICKUP_LIST_ID=901320141781
```

Nunca commite o `.env`.
