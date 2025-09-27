# 🚀 Proxy Interno com Rate Limiting e Cache

Este projeto é uma implementação de um serviço de **proxy em Python usando FastAPI** para atender ao desafio **"Proxy Interno"**.

---

## ✨ Funcionalidades Implementadas

- **RF1**: Expõe o endpoint `GET /proxy/score`.
- **Missão 1**: Possui uma **fila interna** para lidar com picos de requisições.
- **Missão 2**: Garante um **rate limit** de no máximo **1 requisição por segundo** para a API externa.
- **Missão 3**: Utiliza um **cache em memória com TTL (Time-To-Live)** para evitar requisições repetidas.

---

## 🏗️ Padrões de Projeto Utilizados

- **Proxy**: O serviço atua como um intermediário, adicionando funcionalidades (**rate limit, cache, fila**) sem expor a complexidade para o cliente final.  
- **Producer-Consumer (Produtor-Consumidor)**:  
  - O **endpoint da API** atua como *Produtor*, adicionando requisições a uma fila.  
  - Um **worker em background** atua como *Consumidor*, processando-as em um ritmo controlado.

---

## ⚙️ Como Executar

### 1. Pré-requisitos
- Python **3.8+**
- `pip` (gerenciador de pacotes do Python)

---

### 2. Instalação

Clone o repositório e instale as dependências:

```bash
# Crie e ative um ambiente virtual (recomendado)
python -m venv venv
source venv/bin/activate   # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
