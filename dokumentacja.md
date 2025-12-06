<!-- # Indeks branż
**Zamieszczony Program** realizuje zadanie wyznaczenia wiodących branż polskiej gospodarki. Zastosowana została symulacja rynkowa za pomocą modelu sztucznej inteligencji oraz symulacje odziaływań rynkowych za pomocą grafów branż zależnych.

## Jak definiujemy branżę?
W naszym progamie za branżę uznajemy dział gospodarki, reprezentowanej przez dwie pierszwsze cyfry kodu PKD. W ramach symulacji i przewidywań zastosowaliśmy próbkę 15 działów gospodarki, które uznaliśmy jako reprezentatywne.

## Jakie są nasze źródła danych?
Dane podzieliliśmy na dwa rodziaje - twarde dane pozyskane z udostępnionych danych z GUS-u (2007-2024) oraz dane miekkie które pochodzą z analizy Google trends, Yahoo-finance i Wibor,korzystając z wartościowania wyrazów pojawiających się w odniesieniu do danej branży.

## Jakie są cząstkowe składowe indeksu?
Wykresy ukazują nie tylko aktualną (na czas ostatnich dostępnych danych) sytuacje rynku ale są również generowane przez wytrenowany model SI, który kontynuuje wykres dokonując predykcji rozwoju. -->


# Indeks Branż – Dokumentacja Projektu

## Opis rozwiązania
Niniejszy projekt realizuje zadanie wyznaczenia wiodących sektorów polskiej gospodarki poprzez budowę kompleksowego "Indeksu Branż". Rozwiązanie integruje twarde dane historyczne z dynamiczną analizą sentymentu, wykorzystując **modelowanie oparte na sztucznej inteligencji (AI)** oraz **analizę zależności międzysektorowych** (teoria grafów), aby zidentyfikować zarówno obecną kondycję, jak i perspektywy rozwoju poszczególnych.

## Definicja branży i zakres analizy
Zgodnie z sugestią zawartą w wytycznych wyzwania, przyjęto definicję branży na poziomie **działu PKD (2 pierwsze cyfry kodu)**. Takie podejście pozwala na zachowanie równowagi między dostępnością danych a precyzją analizy.

* **Próba badawcza:** Model został opracowany i przetestowany na 15 reprezentatywnych działach gospodarki.

## Źródła danych
Projekt wykorzystuje hybrydowe podejście do gromadzenia danych, łącząc oficjalne statystyki z danymi alternatywnymi:

1.  **Dane fundamentalne (Twarde):**
    * Oficjalne dane makroekonomiczne z Głównego Urzędu Statystycznego (GUS) obejmujące lata 2007–2024.
2.  **Dane alternatywne i rynkowe (Miękkie):**
    * Wskaźniki finansowe i rynkowe (Yahoo Finance, stawki WIBOR).
    * **Analiza sentymentu i trendów:** Wykorzystanie Google Trends oraz wartościowanie słów kluczowych w celu oceny nastrojów wokół danej branży. [cite_start]Pozwala to na wykrycie wczesnych sygnałów zmian rynkowych, niewidocznych w tradycyjnych raportach.

## Komponenty indeksu i metodologia
Indeks nie ogranicza się do wizualizacji danych historycznych. Kluczową wartością dodaną jest element predykcyjny, określający perspektywy rozwoju:

* **Analiza historyczna:** Ocena bieżącej kondycji finansowej i stabilności sektora.
* **Predykcja AI:** Wytrenowany model uczenia maszynowego generuje prognozy rozwoju branży, wykraczając poza dostępne dane historyczne (kontynuacja wykresu).
* **Symulacja oddziaływań:** Wykorzystanie grafów do modelowania zależności między branżami, co pozwala ocenić, jak zmiany w jednym sektorze wpłyną na pozostałe (ryzyko systemowe).