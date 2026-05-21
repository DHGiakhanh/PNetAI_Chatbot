# PNet AI Chat 2

## Overview
PNet AI Chat 2 is an AI chatbot system designed for a pet social network platform. The project integrates a Retrieval-Augmented Generation (RAG) pipeline with Large Language Models (LLMs) to provide intelligent responses related to pet healthcare, pet behavior, and pet care.

The system combines:
- Embedding models (SBERT / PhoBERT)
- FAISS vector database
- Local LLM inference
- Frontend + Backend architecture
- Retrieval-Augmented Generation (RAG)

---

# Main Features

- AI chatbot for pet consultation
- Semantic search using embeddings
- Retrieval-Augmented Generation (RAG)
- Local LLM inference support
- FastAPI backend API
- Frontend chat interface
- Vector search with FAISS
- Vietnamese language support
- Modular architecture for future expansion

---

# System Architecture

```text
User
  ↓
Frontend (React / Next.js)
  ↓
Backend API (FastAPI)
  ↓
Embedding Model (SBERT / PhoBERT)
  ↓
FAISS Vector Database
  ↓
Retrieve Context
  ↓
LLM Inference
  ↓
AI Response
```

---

# RAG Pipeline

```text
User Question
      ↓
Text Embedding
      ↓
FAISS Similarity Search
      ↓
Retrieve Relevant Context
      ↓
LLM Prompt Construction
      ↓
LLM Inference
      ↓
Final Response
```

---

# Technologies Used

## Backend
- Python
- FastAPI
- Uvicorn

## AI / NLP
- Sentence Transformers (SBERT)
- PhoBERT
- FAISS
- Hugging Face Transformers
- GGUF Models
- Ollama / Local LLM

## Frontend
- React
- Next.js
- TypeScript
- Tailwind CSS

---

# Project Structure

```text
PNet_AI_chat_2/
│
├── backend/                # Backend API
├── frontend/               # Frontend application
├── model/                  # AI models
├── embedding/              # Embedding scripts
├── vector_db/              # FAISS database
├── inference/              # Inference pipeline
├── finetune-llm/           # LLM fine-tuning
├── data/                   # Dataset
├── requirements.txt
├── package.json
└── README.md
```

---

# Installation

## Clone Repository

```bash
git clone https://github.com/Huylao-gia/PNet_AI_chat_2.git
cd PNet_AI_chat_2
```

---

# Backend Setup

## Create Virtual Environment

```bash
python -m venv venv
```

## Activate Environment

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

---

# Frontend Setup

```bash
npm install
```

Run frontend:

```bash
npm run dev
```

---

# Running Backend

```bash
uvicorn main:app --reload
```

---

# AI Model Setup

Place your LLM model inside the model directory.

Example:

```text
model/
└── Llama-3.2-1B-Instruct-Frog.Q4_K_M.gguf
```

---

# Embedding Generation

Generate embeddings for the dataset:

```bash
python embedding/create_embedding.py
```

---

# Build FAISS Vector Database

```bash
python vector_db/build_faiss.py
```

---

# Inference

Run chatbot inference:

```bash
python inference/chat.py
```

Inference Flow:

```text
Input Question
      ↓
Embedding
      ↓
FAISS Retrieval
      ↓
Context Injection
      ↓
LLM Generation
      ↓
Response
```

---

# Fine-tuning

The project supports fine-tuning for:

- Embedding models
- LLM models
- Intent classification
- NER models

Possible evaluation metrics:

- Accuracy
- Precision
- Recall
- F1-score
- BLEU
- ROUGE

---

# Example Dataset Format

## Intent Dataset

```json
{
  "text": "Chó bị sốt phải làm sao",
  "intent": "ask_treatment"
}
```

## Knowledge Dataset

```json
{
  "question": "Mèo bị viêm ruột có nguy hiểm không?",
  "answer": "Nếu không điều trị sớm, mèo có thể mất nước và suy dinh dưỡng."
}
```

---

# API Example

## Chat Endpoint

```http
POST /chat
```

Request:

```json
{
  "message": "Chó bị tiêu chảy phải làm sao?"
}
```

Response:

```json
{
  "response": "Bạn nên cho chó uống đủ nước và theo dõi triệu chứng..."
}
```

---

# Future Improvements

- Voice chatbot
- Multimodal AI
- Real-time streaming response
- Pet image analysis
- Medical recommendation system
- Long-term memory chatbot
- Fine-tuned Vietnamese LLM

---

# Demo

Add screenshots or demo videos here.

Example:

```text
assets/demo.png
```

---

# License

This project is for educational and research purposes.

---

# Author

Developed by Huylao-gia