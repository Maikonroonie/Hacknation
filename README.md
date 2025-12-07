# 🏦 PKO BP Future Index (Hacknation 2025)

System analityczny oparty na AI (Prophet) i Teorii Grafów, służący do oceny kondycji branż i symulacji ryzyk systemowych.

## 🏗️ Architektura

Projekt składa się z dwóch części:

1. **Backend (Python/FastAPI):** Obliczenia, model predykcyjny, algorytm BFS.
2. **Frontend (React):** Interfejs użytkownika, wizualizacje.

## 🚀 Jak uruchomić?

### Krok 1: Backend (API)

Wymagany Python 3.9+

```bash
# Instalacja zależności
pip install fastapi uvicorn pandas numpy prophet networkx

# Uruchomienie serwera
uvicorn api:app --reload
```
