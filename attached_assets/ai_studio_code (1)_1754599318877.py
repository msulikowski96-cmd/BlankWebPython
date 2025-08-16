--- START OF FILE openrouter_api.py ---

import os
import json
import logging
import requests
import urllib.parse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")

# Debug logging for API key
if OPENROUTER_API_KEY:
    logger.debug(f"OpenRouter API key loaded successfully (length: {len(OPENROUTER_API_KEY)})")
else:
    logger.error("OpenRouter API key is empty or not found in environment variables")

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "qwen/qwen-2.5-72b-instruct:free"

# ZAAWANSOWANA KONFIGURACJA QWEN - MAKSYMALNA JAKOŚĆ
DEFAULT_MODEL = "qwen/qwen-2.5-72b-instruct:free"
PREMIUM_MODEL = "qwen/qwen-2.5-72b-instruct:free"
PAID_MODEL = "qwen/qwen-2.5-72b-instruct:free"
FREE_MODEL = "qwen/qwen-2.5-72b-instruct:free"

# OPTYMALIZOWANY PROMPT SYSTEMOWY DLA QWEN
DEEP_REASONING_PROMPT = """Jesteś światowej klasy ekspertem w rekrutacji i optymalizacji CV z 15-letnim doświadczeniem w branży HR. Posiadasz głęboką wiedzę o polskim rynku pracy, trendach rekrutacyjnych i wymaganiach pracodawców.

🎯 TWOJA SPECJALIZACJA:
- Optymalizacja CV pod kątem systemów ATS i ludzkich rekruterów
- Znajomość specyfiki różnych branż i stanowisk w Polsce
- Psychologia rekrutacji i przekonywania pracodawców
- Najnowsze trendy w pisaniu CV i listów motywacyjnych
- Analiza zgodności kandydata z wymaganiami stanowiska

🧠 METODA PRACY:
1. Przeprowadzaj głęboką analizę każdego elementu CV
2. Myśl jak doświadczony rekruter - co zwraca uwagę, co denerwuje
3. Stosuj zasady psychologii przekonywania w pisaniu CV
4. Używaj konkretnych, mierzalnych sformułowań
5. Dostosowuj język do branży i poziomu stanowiska

💼 ZNAJOMOŚĆ RYNKU:
- Polskie firmy (korporacje, MŚP, startupy)
- Wymagania różnych branż (IT, finanse, medycyna, inżynieria, sprzedaż)
- Kultura organizacyjna polskich pracodawców
- Specyfika rekrutacji w Polsce vs międzynarodowej

⚡ ZASADY ODPOWIEDZI:
- WYŁĄCZNIE język polski (chyba że proszono o inny)
- Konkretne, praktyczne rady
- Zawsze uzasadniaj swoje rekomendacje
- Używaj profesjonalnej terminologii HR
- Bądź szczery ale konstruktywny w krytyce"""

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://cv-optimizer-pro.repl.co/"
}

def send_api_request(prompt, max_tokens=2000, language='pl', user_tier='free', task_type='default'):
    """
    Send a request to the OpenRouter API with language specification
    """
    if not OPENROUTER_API_KEY:
        logger.error("OpenRouter API key not found")
        raise ValueError("OpenRouter API key not set in environment variables")

    # Language-specific system prompts
    language_prompts = {
        'pl': "Jesteś ekspertem w optymalizacji CV i doradcą kariery. ZAWSZE odpowiadaj w języku polskim, niezależnie od języka CV lub opisu pracy. Używaj polskiej terminologii HR i poprawnej polszczyzny.",
        'en': "You are an expert resume editor and career advisor. ALWAYS respond in English, regardless of the language of the CV or job description. Use proper English HR terminology and grammar."
    }

    system_prompt = get_enhanced_system_prompt(task_type, language) + "\n" + language_prompts.get(language, language_prompts['pl'])

    payload = {
        "model": DEFAULT_MODEL,  # Zawsze używaj modelu Qwen
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.8,  # Zwiększona kreatywność dla lepszych odpowiedzi
        "top_p": 0.95,      # Bardziej zróżnicowane odpowiedzi
        "frequency_penalty": 0.1,  # Unikanie powtórzeń
        "presence_penalty": 0.1,   # Zachęcanie do nowych pomysłów
        "metadata": {
            "user_tier": user_tier,
            "task_type": task_type,
            "model_used": DEFAULT_MODEL,
            "optimization_level": "advanced"
        }
    }

    try:
        logger.debug(f"Sending request to OpenRouter API")
        response = requests.post(OPENROUTER_BASE_URL, headers=headers, json=payload)
        response.raise_for_status()

        result = response.json()
        logger.debug("Received response from OpenRouter API")

        if 'choices' in result and len(result['choices']) > 0:
            return result['choices'][0]['message']['content']
        else:
            raise ValueError("Unexpected API response format")

    except requests.exceptions.RequestException as e:
        logger.error(f"API request failed: {str(e)}")
        raise Exception(f"Failed to communicate with OpenRouter API: {str(e)}")

    except (KeyError, IndexError, json.JSONDecodeError) as e:
        logger.error(f"Error parsing API response: {str(e)}")
        raise Exception(f"Failed to parse OpenRouter API response: {str(e)}")

def analyze_cv_score(cv_text, job_description="", language='pl'):
    """
    Analizuje CV i przyznaje ocenę punktową 1-100 z szczegółowym uzasadnieniem
    """
    prompt = f"""
    ZADANIE: Jesteś światowej klasy ekspertem w rekrutacji. Przeanalizuj poniższe CV i przyznaj mu ocenę punktową od 1 do 100, a następnie szczegółowo uzasadnij swoją decyzję.

    Skala oceny:
    - 90-100: Doskonałe CV. Gotowe do wysłania, wyróżnia się na tle konkurencji i idealnie pasuje do wymogów rynkowych.
    - 80-89: Bardzo dobre CV. Wymaga drobnych usprawnień, ale prezentuje się profesjonalnie i ma duże szanse na sukces.
    - 70-79: Dobre CV. Zawiera solidne podstawy, ale wymaga kilku konkretnych poprawek, aby było bardziej konkurencyjne.
    - 60-69: Przeciętne CV. Potrzebuje znaczących poprawek w strukturze, treści i dopasowaniu, aby przyciągnąć uwagę rekruterów.
    - 50-59: Słabe CV. Wymaga dużych zmian, aby spełniać podstawowe standardy rynkowe.
    - Poniżej 50: CV wymagające całkowitego przepisania. Nie spełnia podstawowych wymogów.

    CV do oceny:
    {cv_text}

    {"Wymagania z oferty pracy (kontekst): " + job_description if job_description else ""}

    UWZGLĘDNIJ W OCENIE I UZASADNIJ KAŻDY PUNKT:
    1.  **Struktura i organizacja treści (20 pkt):** Czy CV jest czytelne, logicznie uporządkowane? Czy sekcje są jasno wydzielone?
    2.  **Klarowność i zwięzłość opisów (20 pkt):** Czy opisy są konkretne, unika się lania wody? Czy są łatwe do zrozumienia?
    3.  **Dopasowanie do wymagań stanowiska (20 pkt):** Jak dobrze CV odpowiada na kluczowe wymagania z opisu pracy (jeśli podano)? Czy podkreśla istotne umiejętności i doświadczenia?
    4.  **Obecność słów kluczowych branżowych (15 pkt):** Czy CV zawiera odpowiednie słowa kluczowe, które ułatwią przejście przez systemy ATS?
    5.  **Prezentacja osiągnięć i rezultatów (15 pkt):** Czy kandydat przedstawia konkretne osiągnięcia z liczbami/procentami, czy tylko obowiązki?
    6.  **Gramatyka i styl pisania (10 pkt):** Czy tekst jest wolny od błędów, profesjonalny i spójny stylistycznie?

    Odpowiedź w formacie JSON:
    {{
        "score": [liczba 1-100],
        "grade": "[A+/A/B+/B/C+/C/D/F] - np. A+ dla 95+",
        "category_scores": {{
            "structure": [1-20],
            "clarity": [1-20],
            "job_match": [1-20],
            "keywords": [1-15],
            "achievements": [1-15],
            "language": [1-10]
        }},
        "strengths": ["Punkt mocny 1 (uzasadnienie)", "Punkt mocny 2 (uzasadnienie)", "Punkt mocny 3 (uzasadnienie)"],
        "weaknesses": ["Słabość 1 (sugestia poprawy)", "Słabość 2 (sugestia poprawy)", "Słabość 3 (sugestia poprawy)"],
        "recommendations": ["Rekomendacja 1 (konkretne działanie)", "Rekomendacja 2 (konkretne działanie)", "Rekomendacja 3 (konkretne działanie)"],
        "summary": "Krótkie i zwięzłe podsumowanie ogólnej oceny CV."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=2500,
        language=language,
        user_tier='free',
        task_type='cv_optimization'
    )

def analyze_keywords_match(cv_text, job_description="", language='pl'):
    """
    Analizuje dopasowanie słów kluczowych z CV do wymagań oferty pracy.
    """
    if not job_description:
        return json.dumps({
            "error": "Brak opisu stanowiska do analizy słów kluczowych. Proszę podać opis pracy, aby wykonać analizę dopasowania.",
            "match_percentage": 0,
            "found_keywords": [],
            "missing_keywords": [],
            "recommendations": [],
            "priority_additions": [],
            "summary": "Analiza dopasowania słów kluczowych wymaga podania opisu stanowiska."
        }, ensure_ascii=False, indent=4)

    prompt = f"""
    ZADANIE: Jesteś ekspertem w optymalizacji CV pod ATS. Przeanalizuj dopasowanie słów kluczowych między CV a wymaganiami oferty pracy. Skoncentruj się na kluczowej terminologii branżowej i umiejętnościach.

    CV do analizy:
    {cv_text}

    Oferta pracy do porównania:
    {job_description}

    Odpowiedź w formacie JSON:
    {{
        "match_percentage": [0-100],
        "found_keywords": ["słowo kluczowe z oferty, które znaleziono w CV", "inne znalezione słowo"],
        "missing_keywords": ["kluczowe słowo z oferty, którego brakuje w CV", "inne brakujące słowo"],
        "recommendations": [
            "Dodaj umiejętność: [nazwa umiejętności z uzasadnieniem]",
            "Podkreśl doświadczenie w: [obszar doświadczenia z uzasadnieniem]",
            "Użyj terminów branżowych: [lista terminów]"
        ],
        "priority_additions": ["najważniejsze słowo/fraza do dodania", "drugie najważniejsze"],
        "summary": "Krótkie podsumowanie analizy dopasowania słów kluczowych."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=2000,
        language=language,
        user_tier='free',
        task_type='cv_optimization'
    )

def check_grammar_and_style(cv_text, language='pl'):
    """
    Sprawdza gramatykę, styl i poprawność językową CV.
    """
    prompt = f"""
    ZADANIE: Jesteś ekspertem językowym i rekrutacyjnym. Przeanalizuj poniższe CV pod kątem gramatyki, ortografii, stylu i ogólnej poprawności językowej. Bądź precyzyjny i pomocny.

    CV do sprawdzenia:
    {cv_text}

    Sprawdź i oceń:
    1.  **Błędy gramatyczne i ortograficzne:** Wyszukaj wszelkie literówki, błędy składniowe, interpunkcyjne.
    2.  **Spójność czasów gramatycznych:** Czy użycie czasów jest konsekwentne (np. wszędzie przeszły do opisów doświadczenia)?
    3.  **Profesjonalność języka:** Czy ton jest formalny i odpowiedni dla dokumentu rekrutacyjnego? Czy unika się slangu, kolokwializmów?
    4.  **Klarowność przekazu:** Czy zdania są zrozumiałe? Czy przekaz jest zwięzły i bezpośredni?
    5.  **Zgodność z konwencjami CV:** Czy przestrzegane są ogólne zasady pisania CV (np. unikanie pierwszej osoby, użycie czasowników akcji)?
    6.  **Unikanie powtórzeń:** Czy nie ma nadmiernych powtórzeń słów lub fraz?

    Odpowiedź w formacie JSON:
    {{
        "grammar_score": [1-10],
        "style_score": [1-10],
        "professionalism_score": [1-10],
        "errors": [
            {{
                "type": "gramatyka/ortografia/interpunkcja",
                "original_text": "błędny fragment tekstu",
                "correction": "proponowana poprawka",
                "context": "sekcja CV, w której znaleziono błąd (np. 'Doświadczenie zawodowe - opis stanowiska X')",
                "explanation": "Krótkie wyjaśnienie błędu"
            }},
            {{
                "type": "styl/spójność",
                "original_text": "tekst do poprawy stylistycznej",
                "suggestion": "sugestia stylistyczna",
                "context": "sekcja CV",
                "explanation": "Krótkie wyjaśnienie problemu stylistycznego"
            }}
        ],
        "style_suggestions": [
            "Użyj bardziej dynamicznych czasowników akcji, aby wzmocnić opisy doświadczenia.",
            "Unikaj powtórzeń słów poprzez stosowanie synonimów.",
            "Zachowaj spójny format dat (np. RRRR-MM) w całym dokumencie.",
            "Zadbaj o zwięzłość zdań, aby zwiększyć czytelność."
        ],
        "overall_quality": "Ogólna ocena jakości językowej CV z krótkim uzasadnieniem.",
        "summary": "Podsumowanie analizy językowej z kluczowymi rekomendacjami."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=1500,
        language=language,
        user_tier='free',
        task_type='cv_optimization'
    )

def optimize_for_position(cv_text, job_title, job_description="", language='pl'):
    """
    Optymalizuje CV pod konkretne stanowisko, bazując wyłącznie na oryginalnych danych.
    """
    prompt = f"""
    ZADANIE: Jesteś ekspertem w optymalizacji CV. Zoptymalizuj poniższe CV specjalnie pod stanowisko: {job_title}.

    ⚠️ KLUCZOWE ZASADY BEZPIECZEŃSTWA:
    1.  ❌ ZAKAZ WYMYŚLANIA: Używaj WYŁĄCZNIE faktów i informacji zawartych w oryginalnym CV.
    2.  ❌ ZAKAZ DODAWANIA: Nie twórz nowych firm, dat, projektów, osiągnięć, umiejętności ani innych danych, których nie ma w CV.
    3.  ✅ INTELIGENTNE PRZEPISYWANIE: Dopuszczalne jest wyłącznie inteligentne przeformułowanie istniejących informacji w bardziej przekonujący sposób.
    4.  ✅ KONTEKSTOWE DOPASOWANIE: Podkreśl i przeredaguj aspekty doświadczeń, które są najbardziej relewantne dla docelowego stanowiska.

    CV do optymalizacji:
    {cv_text}

    {"Wymagania z oferty pracy (kontekst): " + job_description if job_description else ""}

    Stwórz zoptymalizowaną wersję CV, która:
    1.  **Podkreśla najważniejsze umiejętności i doświadczenia** z CV, które są kluczowe dla stanowiska {job_title}.
    2.  **Reorganizuje sekcje lub ich kolejność**, jeśli to zwiększa czytelność i dopasowanie do roli (np. umiejętności przed doświadczeniem, jeśli są kluczowe).
    3.  **Dostosowuje język do branżowych standardów** i wymagań danego stanowiska, używając terminologii z CV.
    4.  **Maksymalizuje dopasowanie do wymagań** z opisu pracy, refrazując istniejące punkty z CV.
    5.  **Zachowuje autentyczność i prawdziwość informacji** – nie dodawaj niczego, co nie jest w oryginalnym CV.

    Odpowiedź w formacie JSON:
    {{
        "optimized_cv": "Zoptymalizowana wersja CV (cały tekst, bez wymyślonych informacji)",
        "key_changes": ["Lista kluczowych zmian wprowadzonych w CV (np. 'Podkreślono doświadczenie w zarządzaniu projektami')", "Zmiana 2", "Zmiana 3"],
        "focus_areas": ["Obszary z CV, które zostały szczególnie podkreślone (np. 'Umiejętności techniczne', 'Osiągnięcia w sprzedaży')"],
        "added_elements": ["Lista sekcji lub podsekcji, które zostały dodane lub wyraźniej wyróżnione (np. 'Podsumowanie zawodowe')", "Element 2"],
        "positioning_strategy": "Krótka strategia, jak kandydat jest pozycjonowany na to stanowisko (np. 'Jako ekspert z wieloletnim doświadczeniem w X')",
        "summary": "Zwięzłe podsumowanie procesu optymalizacji i głównych korzyści."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=2500,
        language=language,
        user_tier='free',
        task_type='cv_optimization'
    )

def apply_recruiter_feedback_to_cv(cv_text, recruiter_feedback, job_description="", language='pl', is_premium=False, payment_verified=False):
    """
    Apply recruiter feedback suggestions directly to the CV - PAID FEATURE
    """

    # WYŁĄCZENIE DRUGIEJ, DUPLIKUJĄCEJ SIĘ DEKLARACJI FUNKCJI apply_recruiter_feedback_to_cv (usuń ją z pliku po weryfikacji)
    # def apply_recruiter_feedback_to_cv(cv_text, feedback, job_description, language='pl', is_premium=False, payment_verified=False):
    #     """Apply recruiter feedback to improve CV"""
    #     prompt = f"""
    #     Zastosuj poniższe uwagi rekrutera do CV i popraw je zgodnie z sugestiami.

    #     ORYGINALNE CV:
    #     {cv_text}

    #     UWAGI REKRUTERA:
    #     {feedback}

    #     OPIS STANOWISKA (jeśli dostępny):
    #     {job_description}

    #     Przepisz CV uwzględniając wszystkie uwagi rekrutera. Zwróć tylko poprawione CV w formacie JSON:
    #     {{
    #         "improved_cv": "Poprawione CV z zastosowanymi uwagami",
    #         "changes_made": ["Lista zastosowanych zmian"],
    #         "improvement_summary": "Podsumowanie ulepszeń"
    #     }}
    #     """
    #     return send_api_request(
    #         prompt,
    #         max_tokens=3000,
    #         language=language,
    #         user_tier='premium' if is_premium else ('paid' if payment_verified else 'free'),
    #         task_type='cv_optimization'
    #     )

    if not (is_premium or payment_verified):
        # Ta funkcja jest przeznaczona dla płatnych użytkowników.
        # W przypadku użytkowników darmowych, można zwrócić informację o braku dostępu.
        return json.dumps({
            "error": "Ta funkcja jest dostępna tylko dla użytkowników PREMIUM lub po zweryfikowaniu płatności.",
            "improved_cv": "",
            "applied_changes": [],
            "sections_to_complete": [],
            "improvement_summary": "Brak dostępu do funkcji."
        }, ensure_ascii=False, indent=4)

    max_tokens_for_tier = 2500 # Default for paid, adjust for premium below

    prompt_suffix = """
    TRYB PŁATNY - ZASTOSOWANIE POPRAWEK:
    - Implementuj GŁÓWNE sugestie z opinii rekrutera
    - Przepisz KLUCZOWE sekcje zgodnie z rekomendacjami
    - Popraw strukturę i formatowanie zgodnie ze wskazówkami rekrutera
    - Dodaj brakujące elementy wskazane przez rekrutera, ZAWSZE zaznaczając je jako "Do uzupełnienia"
    """

    if is_premium:
        max_tokens_for_tier = 6000
        prompt_suffix = """
        🔥 TRYB PREMIUM - MAKSYMALNE ZASTOSOWANIE POPRAWEK REKRUTERA:
        - Implementuj WSZYSTKIE, nawet najbardziej szczegółowe, sugestie z opinii rekrutera
        - Przepisz CV zgodnie z każdą rekomendacją, dążąc do perfekcji
        - Stwórz profesjonalną, dopracowaną wersję CV, maksymalnie wykorzystując potencjał oryginalnych danych
        - Użyj zaawansowanych technik optymalizacji i psychologii rekrutacji
        - Dodaj elementy, które rekruter zasugerował, ZAWSZE wyraźnie oznaczając "Do uzupełnienia przez użytkownika" jeśli danych brakuje.
        - Skup się na płynności i spójności dokumentu po wprowadzeniu zmian.
        """
    elif payment_verified:
        max_tokens_for_tier = 4000
        prompt_suffix = """
        TRYB PŁATNY - ZAAWANSOWANE ZASTOSOWANIE POPRAWEK:
        - Implementuj WSZYSTKIE GŁÓWNE i większość drugorzędnych sugestii z opinii rekrutera
        - Przepisz odpowiednie sekcje zgodnie z rekomendacjami, poprawiając ich jakość
        - Popraw strukturę i formatowanie, aby zwiększyć czytelność i profesjonalizm
        - Dodaj brakujące elementy wskazane przez rekrutera, ZAWSZE zaznaczając je jako "Do uzupełnienia przez użytkownika" jeśli danych brakuje.
        """

    prompt = f"""
    ZADANIE: Jesteś ekspertem w optymalizacji CV. Zastosuj konkretne poprawki z opinii rekrutera do poniższego CV, tworząc ulepszoną wersję.

    ⚠️ BEZWZGLĘDNE ZASADY BEZPIECZEŃSTWA DANYCH:
    1.  ❌ ZAKAZ WYMYŚLANIA: Używaj WYŁĄCZNIE prawdziwych informacji z oryginalnego CV.
    2.  ❌ ZAKAZ DODAWANIA FAŁSZYWYCH DANYCH: Nie dodawaj żadnych nowych doświadczeń, dat, nazw firm, osiągnięć, umiejętności ani innych danych, których nie ma w oryginalnym CV.
    3.  ✅ DOZWOLONE: Przeredaguj, przeformułuj, przenieś i usuń istniejące informacje zgodnie z sugestiami rekrutera.
    4.  ✅ OZNACZAJ BRAKI: Jeśli rekruter sugeruje dodanie czegoś, czego NIE MA w oryginalnym CV (np. "dodaj sekcję Osiągnięcia" lub "rozwiń zakres obowiązków o X, Y, Z"), dodaj sekcję z informacją "DO UZUPEŁNIENIA PRZEZ UŻYTKOWNIKA" lub podobnym, jasno wskazując, co kandydat powinien samodzielnie dopisać. NIE Wymyślaj treści za użytkownika.

    ORYGINALNY TEKST CV:
    {cv_text}

    OPINIA REKRUTERA DO ZASTOSOWANIA:
    {recruiter_feedback}

    {f"KONTEKST STANOWISKA (dla lepszego zrozumienia feedbacku): {job_description}" if job_description else ""}

    INSTRUKCJE KROK PO KROKU:
    1.  Dokładnie przeanalizuj każdą sugestię z opinii rekrutera.
    2.  Zastosuj WSZYSTKIE wskazane poprawki do CV, modyfikując oryginalny tekst.
    3.  Przepisz sekcje zgodnie z rekomendacjami, poprawiając styl, klarowność i dopasowanie.
    4.  Jeśli rekruter zasugerował dodanie brakujących elementów lub treści, których nie ma w oryginalnym CV, wyraźnie zaznacz je jako "DO UZUPEŁNIENIA PRZEZ UŻYTKOWNIKA" (lub podobny, jasny komunikat). NIE Wymyślaj tych treści.
    5.  Popraw strukturę, formatowanie i język według wskazówek rekrutera.
    6.  Zachowaj spójność i profesjonalny ton całego dokumentu.

    {prompt_suffix}

    Zwróć poprawione CV w formacie JSON:
    {{
        "improved_cv": "Poprawiona wersja CV z zastosowanymi sugestiami rekrutera (cały tekst CV).",
        "applied_changes": ["Lista zastosowanych zmian (np. 'Dodano podsumowanie zawodowe', 'Poprawiono formatowanie dat', 'Rozbudowano opis obowiązków na stanowisku X')", "zmiana 2", "zmiana 3"],
        "sections_to_complete": ["Lista sekcji lub elementów, które użytkownik musi samodzielnie uzupełnić (np. 'Sekcja 'Osiągnięcia zawodowe'', 'Dodatkowe projekty z branży IT')", "element do uzupełnienia 2"],
        "improvement_summary": "Zwięzłe podsumowanie wprowadzonych ulepszeń i ogólnej poprawy CV."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=max_tokens_for_tier,
        language=language,
        user_tier='premium' if is_premium else ('paid' if payment_verified else 'free'),
        task_type='cv_optimization'
    )

def generate_interview_tips(cv_text, job_description="", language='pl'):
    """
    Generuje spersonalizowane tipy na rozmowę kwalifikacyjną na podstawie CV i opisu stanowiska.
    """
    prompt = f"""
    ZADANIE: Jesteś doświadczonym doradcą kariery i ekspertem ds. rozmów kwalifikacyjnych. Na podstawie poniższego CV i opisu stanowiska, przygotuj spersonalizowane i praktyczne tipy na rozmowę kwalifikacyjną.

    CV kandydata:
    {cv_text}

    {"Stanowisko docelowe (kontekst): " + job_description if job_description else ""}

    Odpowiedź w formacie JSON:
    {{
        "preparation_tips": [
            "Przygotuj się na pytanie o [konkretny aspekt z CV, np. 'rozbudowany opis projektu X'], analizując swoje osiągnięcia.",
            "Przećwicz opowiadanie o swoim doświadczeniu w [nazwa obszaru z CV, np. 'zarządzaniu zespołem'], używając metody STAR.",
            "Bądź gotowy na pytania techniczne o [konkretna umiejętność techniczna z CV, np. 'Python i bazy danych'], jeśli jest to kluczowe dla stanowiska.",
            "Zbadaj kulturę organizacyjną firmy, aby dopasować swoje odpowiedzi do jej wartości."
        ],
        "strength_stories": [
            {{
                "strength": "Umiejętność/Obszar mocnej strony (np. 'Skuteczna komunikacja')",
                "story_outline": "Jak opowiedzieć o sukcesie (np. 'Użyj metody STAR: Sytuacja, Zadanie, Akcja, Rezultat')",
                "example_from_cv": "Konkretny przykład z CV, który można rozwinąć (np. 'Projekt w firmie Y, gdzie poprawiono X o Y%')"
            }},
            {{
                "strength": "Osiągnięcie (np. 'Optymalizacja procesów')",
                "story_outline": "Struktura opowieści (np. 'Opisz wyzwanie, swoje działania i konkretne efekty')",
                "example_from_cv": "Przykład z doświadczenia z CV, który można rozwinąć (np. 'Wdrożenie nowego systemu Z, które zwiększyło efektywność')"
            }}
        ],
        "weakness_preparation": [
            {{
                "potential_weakness": "Obszar do poprawy (np. 'Brak doświadczenia w X' lub 'Nadmierne skupienie na szczegółach')",
                "how_to_address": "Jak to przedstawić pozytywnie (np. 'Wspomnij o kursach, motywacji do nauki i planach rozwoju')"
            }},
            {{
                "potential_weakness": "Luka w CV (np. 'Przerwa w zatrudnieniu')",
                "how_to_address": "Jak wytłumaczyć (np. 'Skup się na aktywnościach w tym czasie, takich jak wolontariat, rozwój osobisty')"
            }}
        ],
        "questions_to_ask": [
            "Przemyślane pytanie o firmę/zespół (np. 'Jaka jest największa szansa/wyzwanie dla tego zespołu w nadchodzącym roku?')",
            "Pytanie o rozwój w roli (np. 'Jakie są możliwości rozwoju dla osoby na tym stanowisku?')",
            "Pytanie o wyzwania stanowiska (np. 'Jakie byłyby główne wyzwania na tym stanowisku w ciągu pierwszych 6 miesięcy?')",
            "Pytanie o kulturę organizacyjną (np. 'Jak wygląda kultura współpracy w Państwa firmie?')"
        ],
        "research_suggestions": [
            "Sprawdź najnowsze wiadomości i projekty firmy na ich stronie internetowej lub LinkedIn.",
            "Poznaj kluczowe osoby w zespole lub działach, z którymi będziesz współpracować (jeśli to możliwe).",
            "Zbadaj wartości firmy i misję, aby odnieść się do nich w rozmowie."
        ],
        "summary": "Kluczowe rady dla kandydata, podsumowujące najważniejsze aspekty przygotowania do rozmowy kwalifikacyjnej."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=2000,
        language=language,
        user_tier='free',
        task_type='interview_prep'
    )

def analyze_polish_job_posting(job_description, language='pl'):
    """
    Analizuje polskie ogłoszenia o pracę i wyciąga kluczowe informacje.
    """
    prompt = f"""
    ZADANIE: Jesteś ekspertem w analizie rynku pracy i rekrutacji. Przeanalizuj poniższe polskie ogłoszenie o pracę i wyciągnij z niego najważniejsze, ustrukturyzowane informacje. Jeśli jakiejś informacji brakuje w ogłoszeniu, oznacz ją jako "brak danych" lub pozostaw puste.

    OGŁOSZENIE O PRACĘ:
    {job_description}

    Wyciągnij i uporządkuj następujące informacje:

    1.  PODSTAWOWE INFORMACJE O STANOWISKU:
        -   Dokładny tytuł stanowiska (jeśli niejasny, wskaż główną rolę)
        -   Branża/sektor (np. IT, Finanse, Logistyka)
        -   Lokalizacja pracy (miasto, region, tryb pracy - stacjonarnie/zdalnie/hybrydowo)
        -   Typ umowy/zatrudnienia (np. UoP, B2B, zlecenie, staż)
        -   Poziom doświadczenia (np. Junior, Mid, Senior, Ekspert)

    2.  WYMAGANIA KLUCZOWE:
        -   Wymagane wykształcenie (kierunek, poziom)
        -   Wymagane doświadczenie zawodowe (lata, obszary)
        -   Kluczowe umiejętności techniczne (narzędzia, technologie, języki programowania)
        -   Kluczowe umiejętności miękkie (komunikacja, współpraca, rozwiązywanie problemów)
        -   Uprawnienia/certyfikaty (np. prawo jazdy, branżowe certyfikaty)
        -   Wymagane języki obce (poziom)

    3.  OBOWIĄZKI I ZAKRES PRACY:
        -   Główne zadania i odpowiedzialności na stanowisku
        -   Specyficzne czynności i projekty (jeśli wymienione)

    4.  WARUNKI PRACY I BENEFITY:
        -   Godziny pracy / system pracy (np. pełny etat, zmianowy)
        -   Informacje o wynagrodzeniu (zakres, jeśli podany)
        -   Oferowane benefity i dodatki (np. opieka medyczna, karta sportowa, rozwój)
        -   Kultura organizacyjna / środowisko pracy (jeśli opisane)

    5.  SŁOWA KLUCZOWE DO CV:
        -   Lista najważniejszych słów kluczowych i fraz, które powinny znaleźć się w CV kandydata (zarówno twarde, jak i miękkie).

    Odpowiedź w formacie JSON:
    {{
        "job_title": "Dokładny tytuł stanowiska (jeśli niejasny, wskaż główną rolę)",
        "industry": "Branża/sektor (np. IT, Finanse, Logistyka)",
        "location": "Lokalizacja (miasto, region, tryb pracy: stacjonarnie/zdalnie/hybrydowo)",
        "employment_type": "Typ zatrudnienia (np. UoP, B2B, zlecenie, staż)",
        "experience_level": "Poziom doświadczenia (np. Junior, Mid, Senior, Ekspert)",
        "key_requirements": {{
            "education": "Wymagane wykształcenie (np. wyższe informatyczne)",
            "professional_experience": "Wymagane lata i obszary doświadczenia (np. min. 3 lata w zarządzaniu projektami)",
            "technical_skills": ["umiejętność techniczna 1", "umiejętność techniczna 2"],
            "soft_skills": ["umiejętność miękka 1", "umiejętność miękka 2"],
            "licenses_certificates": ["uprawnienie/certyfikat 1"],
            "languages": ["język obcy: poziom"]
        }},
        "main_responsibilities": ["obowiązek 1", "obowiązek 2", "obowiązek 3"],
        "work_conditions_benefits": {{
            "hours_schedule": "Godziny pracy / harmonogram",
            "salary_info": "Informacje o wynagrodzeniu (np. '20 000 - 25 000 PLN brutto')",
            "benefits": ["benefit 1", "benefit 2", "benefit 3"],
            "work_environment": "Opis kultury organizacyjnej/środowiska pracy"
        }},
        "industry_keywords": [
            "słowo kluczowe 1 (z ogłoszenia)", "słowo kluczowe 2", "słowo kluczowe 3", "słowo kluczowe 4", "słowo kluczowe 5"
        ],
        "summary": "Zwięzłe podsumowanie stanowiska i kluczowych wymagań z ogłoszenia."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=2000,
        language=language,
        user_tier='free',
        task_type='cv_optimization'
    )

def optimize_cv_for_specific_position(cv_text, target_position, job_description, company_name="", language='pl', is_premium=False, payment_verified=False):
    """
    ZAAWANSOWANA OPTYMALIZACJA CV - analizuje każde poprzednie stanowisko i inteligentnie je przepisuje
    pod kątem konkretnego stanowiska docelowego, zachowując pełną autentyczność danych.
    """
    # Najpierw przeanalizuj opis stanowiska jeśli został podany
    job_analysis = None
    if job_description and len(job_description) > 50:
        try:
            # Warto by było zaimplementować funkcję parsującą JSONa z odpowiedzi AI, np. parse_ai_json_response
            # Dla uproszczenia na razie przekazujemy wynik jako string
            job_analysis_result = analyze_polish_job_posting(job_description, language)
            # Przykład parsowania (wymagałoby odpowiedniej funkcji)
            # try:
            #     job_analysis = json.loads(job_analysis_result)
            # except json.JSONDecodeError:
            #     logger.warning("Failed to parse job analysis result into JSON.")
            job_analysis = job_analysis_result # Zostawiamy jako string
        except Exception as e:
            logger.warning(f"Nie udało się przeanalizować opisu stanowiska: {e}")

    prompt = f"""
    ZADANIE EKSPERCKIE: Przeprowadź zaawansowaną analizę CV i stwórz precyzyjną optymalizację pod konkretne polskie stanowisko pracy.

    ⚠️ ABSOLUTNE ZASADY BEZPIECZEŃSTWA DANYCH (PRZECZYTAJ UWAŻNIE I ZASTOSUJ BEZWZGLĘDNIE):
    1.  ❌ ZAKAZ WYMYŚLANIA: Używaj WYŁĄCZNIE faktów i informacji, które są OBECNE w oryginalnym CV.
    2.  ❌ ZAKAZ DODAWANIA: NIE twórz żadnych nowych firm, dat zatrudnienia, tytułów stanowisk, projektów, osiągnięć, liczb, procent, ani umiejętności, których nie ma w oryginalnym CV.
    3.  ✅ INTELIGENTNE PRZEPISYWANIE: Dopuszczalne jest jedynie inteligentne przeformułowanie, rozbudowanie i podkreślenie ISTNIEJĄCYCH doświadczeń i umiejętności, aby były bardziej relewantne i przekonujące dla stanowiska docelowego.
    4.  ✅ KONTEKSTOWE DOPASOWANIE: Każdy przepisany punkt musi mieć swoje źródło w oryginalnym CV, a jego nowe sformułowanie ma na celu maksymalizację dopasowania do wymagań {target_position}.
    5.  ✅ POLSKI RYNEK PRACY: Dostosuj terminologię, styl i oczekiwania do polskich standardów HR i specyfiki branży.
    6.  ✅ UNIKALNE OPISY DLA PODOBNYCH STANOWISK: Jeśli w CV są podobne stanowiska (np. "Kurier" w różnych firmach), stwórz UNIKALNE i RÓŻNE opisy dla każdego z nich, podkreślając inne aspekty pracy.

    🎯 STANOWISKO DOCELOWE: {target_position}
    🏢 FIRMA DOCELOWA (jeśli znana): {company_name if company_name else "nieokreślona"}
    📋 OPIS STANOWISKA (jeśli dostępny):
    {job_description}

    {"📊 ANALIZA STANOWISKA AI (dla Twojego kontekstu):" + str(job_analysis) if job_analysis else ""}

    STRATEGIA OPTYMALIZACJI - KROK PO KROKU:

    KROK 1: DOGŁĘBNA ANALIZA ORYGINALNEGO CV
    -   Przeanalizuj każde poprzednie stanowisko z CV i zidentyfikuj:
        -   Umiejętności transferowalne (hard i soft skills) na stanowisko docelowe.
        -   Doświadczenia, które można przeformułować jako bezpośrednio relewantne.
        -   Obowiązki, które mają wspólne elementy z wymaganiami stanowiska docelowego.
        -   Branżowe słowa kluczowe obecne w CV, które można wykorzystać.
    -   UWAGA: Jeśli są podobne stanowiska (np. "Asystent" w dwóch różnych firmach), znajdź różne, unikalne aspekty każdego z nich.

    KROK 2: STRATEGICZNE REPOZYCJONOWANIE TREŚCI
    -   Dla każdego poprzedniego stanowiska z CV:
        -   Zachowaj oryginalne dane (nazwa firmy, daty zatrudnienia, oryginalny tytuł stanowiska).
        -   **Przepisz opisy obowiązków i osiągnięć**, skupiając się na tych, które są najbardziej wartościowe i pasują do {target_position}.
        -   Użyj terminologii branżowej właściwej dla {target_position} (ale tylko tej, która wynika z kontekstu CV).
        -   Podkreśl soft skills i hard skills wymienione w CV, które najlepiej pasują do wymagań stanowiska docelowego.
        -   **KLUCZOWE:** Dla podobnych stanowisk w CV, stwórz RÓŻNE opisy, skupiające się na odmiennych aspektach pracy w każdej firmie (np. w jednej firmie na obsłudze klienta, w drugiej na logistyce).

    KROK 3: INTELIGENTNE ULEPSZENIE CAŁEGO CV
    -   Stwórz lub zoptymalizuj podsumowanie zawodowe, jasno pozycjonując kandydata na target role, bazując na jego autentycznym doświadczeniu.
    -   Zorganizuj sekcję umiejętności według ważności dla docelowego stanowiska, grupując je logicznie.
    -   Dostosuj ogólny język i styl CV do branży docelowej i kultury organizacyjnej (jeśli znana), zachowując profesjonalizm.
    -   Zoptymalizuj pod kątem słów kluczowych ATS, wykorzystując te, które faktycznie występują w CV.

    PRZYKŁADY INTELIGENTNEGO PRZEPISYWANIA DLA POLSKIEGO RYNKU PRACY (Pamiętaj, by zawsze bazować na oryginalnej treści CV):

    STANOWISKO DOCELOWE: "Kierowca kat. B - bramowiec"
    Oryginał w CV: "Kierowca - przewożenie towarów"
    ✅ Zoptymalizowane: "Realizowałem transport kontenerów i odpadów budowlanych na terenie miasta X, dbając o terminowość dostaw i bezpieczeństwo przewozu zgodne z przepisami [jeśli było w CV, np. ADR]."

    STANOWISKO DOCELOWE: "Specjalista ds. logistyki"
    Oryginał w CV: "Pracownik magazynu - obsługa towaru"
    ✅ Zoptymalizowane: "Koordynowałem procesy magazynowe, w tym przyjęcie i wydanie towarów, uczestniczyłem w optymalizacji przepływów logistycznych i zarządzałem dokumentacją magazynową (jeśli było w CV)."

    PRZYKŁAD RÓŻNICOWANIA PODOBNYCH STANOWISK (Zawsze bazuj na informacji z oryginalnego CV):

    CV zawiera 3 stanowiska "Kurier" w różnych firmach:

    STANOWISKO 1: "Kurier - DHL" (2022-2023)
    ✅ Opis 1: "Wykonywałem ekspresowe dostawy międzynarodowe i krajowe, obsługiwałem system śledzenia przesyłek oraz zapewniałem terminowość dostaw zgodnie z rygorystycznymi procedurami DHL, budując relacje z klientami biznesowymi (jeśli było w CV)."

    STANOWISKO 2: "Kurier - DPD" (2021-2022)
    ✅ Opis 2: "Realizowałem dostawy lokalne na terenie aglomeracji miejskiej, optymalizowałem trasy dostaw za pomocą narzędzi GPS oraz utrzymywałem pozytywny kontakt z odbiorcami indywidualnymi (jeśli było w CV)."

    STANOWISKO 3: "Kurier - UPS" (2020-2021)
    ✅ Opis 3: "Odpowiadałem za dostawy przesyłek specjalnych do firm, zarządzałem dokumentacją celną przesyłek zagranicznych i współpracowałem z działem obsługi klienta w rozwiązywaniu problemów logistycznych (jeśli było w CV)."

    ORYGINALNE CV DO ANALIZY:
    {cv_text}

    WYGENERUJ ZAAWANSOWANE ZOPTYMALIZOWANE CV ORAZ SZCZEGÓŁOWĄ ANALIZĘ W FORMACIE JSON:

    {{
        "position_analysis": {{
            "target_role": "{target_position}",
            "key_requirements_identified": ["wymóg z oferty 1", "wymóg z oferty 2"],
            "transferable_skills_found": ["umiejętność transferowalna 1 (z CV)", "umiejętność transferowalna 2 (z CV)"],
            "positioning_strategy": "Krótka strategia, jak kandydat jest pozycjonowany w kontekście stanowiska docelowego.",
            "similar_positions_identified": ["lista podobnych stanowisk z CV jeśli są (np. 'Kurier', 'Kierowca')"],
            "differentiation_strategy": "Jak zróżnicowano opisy podobnych stanowisk, aby pokazać różnorodne doświadczenie."
        }},
        "experience_optimization": [
            {{
                "original_title": "Tytuł stanowiska z oryginalnego CV",
                "original_company": "Firma z oryginalnego CV",
                "original_dates": "Daty z oryginalnego CV",
                "original_description_summary": "Krótkie podsumowanie oryginalnych zadań z CV.",
                "optimized_description": "Przepisane zadania/obowiązki pod target position (3-7 precyzyjnych bullet points, bazując TYLKO na oryginalnym CV).",
                "relevance_connection": "Krótkie wyjaśnienie, dlaczego ten opis pasuje do target role.",
                "uniqueness_factor": "Jak ten opis różni się od innych podobnych stanowisk w CV (jeśli dotyczy)."
            }}
            // ... Dodaj podobne obiekty dla każdego stanowiska w CV
        ],
        "optimized_cv_content": "KOMPLETNE ZOPTYMALIZOWANE CV w formie tekstu, gotowe do wysłania, bazujące WYŁĄCZNIE na oryginalnych danych z CV.",
        "keyword_optimization": {{
            "primary_keywords_used": ["kluczowe słowo1 (z CV i oferty)", "kluczowe słowo2"],
            "secondary_keywords_used": ["dodatkowe słowo1", "dodatkowe słowo2"],
            "keyword_density_score": "[0-100] (ocena gęstości i trafności słów kluczowych)"
        }},
        "ats_compatibility": {{
            "score": "[0-100] (ocena ATS po optymalizacji)",
            "structure_optimization": "Opis, jak zoptymalizowano strukturę dla ATS.",
            "format_improvements": "Jakie poprawki formatowania wprowadzono."
        }},
        "competitive_advantage": {{
            "unique_selling_points": ["USP1 (wynikający z CV)", "USP2 (wynikający z CV)"],
            "differentiation_strategy": "Jak kandydat wyróżnia się na tle konkurencji dzięki optymalizacji.",
            "value_proposition": "Główna wartość, jaką wnosi kandydat, wyrażona zoptymalizowanym językiem."
        }},
        "improvement_summary": {{
            "before_vs_after_impact": "Podsumowanie kluczowych zmian i ich potencjalnego wpływu na rekruterów.",
            "match_percentage_after_optimization": "[0-100] (przewidywane dopasowanie po optymalizacji)",
            "success_probability": "Szanse powodzenia aplikacji po zastosowaniu CV (ocena ogólna, np. wysokie/średnie).",
            "next_steps": "Rekomendacje dla kandydata na podstawie finalnego CV (np. 'Przygotować się na pytania o X').",
            "position_diversity_impact": "Ocena, jak skutecznie zróżnicowano opisy podobnych stanowisk."
        }}
    }}
    """
    # Zwiększone limity tokenów dla zaawansowanej analizy
    if is_premium or payment_verified:
        max_tokens_for_tier = 8000  # Maksymalny limit dla pełnej analizy
        prompt += f"""

        🔥 TRYB PREMIUM - MAKSYMALNA OPTYMALIZACJA I DETAL:
        -   Analizuj każde słowo z CV pod kątem potential value dla stanowiska docelowego.
        -   Stwórz 7-10 precyzyjnych bullet points dla każdego stanowiska, maksymalnie wykorzystując fakty z CV.
        -   Dodaj lub rozbuduj sekcję "Kluczowe Osiągnięcia" (jeśli jest w CV) z reframed accomplishment, jeśli to możliwe.
        -   Zoptymalizuj pod specyficzną terminologię branżową na poziomie eksperckim.
        -   Przygotuj CV na poziomie wymaganym przez executive search firm.
        -   Zastosuj advanced psychological positioning techniques, aby CV było jeszcze bardziej przekonujące.
        -   Stwórz compelling narrative arc (przekonującą narrację kariery) kandydata, łącząc wszystkie doświadczenia.
        """
    else:
        max_tokens_for_tier = 4000 # Standard for paid, free might be lower if not specified
        prompt += f"""

        TRYB STANDARD - PROFESJONALNA OPTYMALIZACJA:
        -   Przepisz 3-5 solidnych bullet points dla każdego stanowiska, bazując na oryginalnym CV.
        -   Dodaj lub zoptymalizuj profesjonalne podsumowanie zawodowe.
        -   Zoptymalizuj podstawowe dopasowanie słów kluczowych (keyword matching).
        -   Popraw ogólną strukturę i czytelność dokumentu.
        """
    return send_api_request(
        prompt,
        max_tokens=max_tokens_for_tier,
        language=language,
        user_tier='premium' if is_premium else ('paid' if payment_verified else 'free'),
        task_type='cv_optimization'
    )

def generate_complete_cv_content(target_position, experience_level, industry, brief_background, language='pl'):
    """
    Generate complete CV content from minimal user input using AI.
    The AI should generate *realistic but fictitious* content based on the input parameters.
    """
    prompt = f"""
    ZADANIE: Jesteś ekspertem w tworzeniu CV. Wygeneruj kompletną, realistyczną i profesjonalną treść CV na podstawie minimalnych informacji od użytkownika. Stwórz spójną narrację kariery.

    DANE WEJŚCIOWE DO GENEROWANIA:
    - Docelowe stanowisko: {target_position}
    - Poziom doświadczenia: {experience_level} (junior/mid/senior/ekspert)
    - Branża: {industry}
    - Krótki opis doświadczenia (ogólny kontekst do budowy CV): {brief_background}

    WYGENERUJ REALISTYCZNĄ I WIARYGODNĄ TREŚĆ CV, KTÓRA WYGLĄDA JAK OD PRAWDZIWEGO KANDYDATA:

    1.  **DANE OSOBOWE (fikcyjne, realistyczne):**
        -   Fikcyjne imię i nazwisko (polskie)
        -   Fikcyjny numer telefonu (polski format)
        -   Fikcyjny adres e-mail
        -   Fikcyjna lokalizacja (miasto, np. Warszawa, Kraków)
        -   Link do profilu LinkedIn (fikcyjny, realistyczny format)

    2.  **PODSUMOWANIE ZAWODOWE (80-120 słów):**
        -   Stwórz przekonujące podsumowanie zawodowe, odzwierciedlające podany poziom doświadczenia i branżę.
        -   Użyj kluczowych słów z branży i stanowiska docelowego.
        -   Podkreśl mocne strony i kluczowe umiejętności.

    3.  **DOŚWIADCZENIE ZAWODOWE (3-4 realistyczne stanowiska z progresją):**
        -   Wygeneruj realistyczne, progresywne stanowiska pracy, pasujące do podanego poziomu doświadczenia i branży.
        -   Dla każdego stanowiska:
            -   Tytuł stanowiska (realistyczny dla branży i poziomu)
            -   Fikcyjna, wiarygodna nazwa firmy (polska, np. "TechSolutions Polska", "Logistyka Express Sp. z o.o.")
            -   Realistyczny okres zatrudnienia (rok-miesiąc do rok-miesiąc, z logiczną progresją)
            -   3-5 konkretnych obowiązków i osiągnięć (użyj czasowników akcji, dodaj fikcyjne, ale realistyczne liczby/procenty tam, gdzie to pasuje do branży, np. "zwiększył sprzedaż o 15%").
        -   Dostosuj do poziomu `experience_level`:
            *   **Junior:** 1-2 lata doświadczenia, podstawowe role, staże, pierwsze samodzielne obowiązki.
            *   **Mid:** 3-5 lat, stanowiska specjalistyczne, samodzielność, udział w większych projektach.
            *   **Senior:** 5+ lat, role kierownicze/eksperckie, odpowiedzialność za zespoły/projekty, strategiczne myślenie.
            *   **Ekspert:** 8+ lat, role mentorskie, architekt, głęboka specjalizacja, wdrożenia na dużą skalę.

    4.  **WYKSZTAŁCENIE:**
        -   Wygeneruj odpowiednie wykształcenie dla branży i stanowiska.
        -   Kierunek studiów pasujący do stanowiska i branży.
        -   Realistyczna nazwa polskiej uczelni (np. "Politechnika Warszawska", "Uniwersytet Jagielloński").
        -   Realistyczne daty (rok rozpoczęcia, rok ukończenia).

    5.  **UMIEJĘTNOŚCI (8-15 kluczowych):**
        -   Lista 8-15 umiejętności kluczowych dla stanowiska i branży.
        -   Miksuj hard skills (techniczne, narzędziowe) i soft skills (komunikacyjne, interpersonalne).
        -   Dodaj realistyczne, aktualne technologie/narzędzia branżowe.
        -   Umiejętności językowe (jeśli pasuje, np. angielski: zaawansowany).

    6.  **OPCJONALNE SEKCJE (jeśli pasuje do kontekstu):**
        -   Kursy i certyfikaty (fikcyjne, ale realistyczne dla branży)
        -   Projekty (fikcyjne, krótkie opisy)
        -   Zainteresowania (krótkie, profesjonalne)

    WYMAGANIA JAKOŚCI DLA GENEROWANEJ TREŚCI:
    -   Treść musi być **w pełni realistyczna i wiarygodna**, jakby pochodziła od prawdziwej osoby.
    -   Używaj poprawnej, profesjonalnej polskiej terminologii HR.
    -   Dostosuj język i szczegółowość do podanego poziomu doświadczenia.
    -   Wszystkie informacje muszą być spójne logicznie.
    -   Formatuj jako profesjonalne CV tekstowe.

    Odpowiedź w formacie JSON:
    {{
        "personal_details": {{
            "name": "Fikcyjne Imię Nazwisko",
            "phone": "+48 123 456 789",
            "email": "fikcyjne.email@example.com",
            "location": "Miasto, Województwo",
            "linkedin_profile": "https://www.linkedin.com/in/fikcyjne-nazwisko-12345678"
        }},
        "professional_title": "Proponowany tytuł zawodowy do CV (np. 'Doświadczony Specjalista ds. Marketingu')",
        "professional_summary": "Wygenerowane podsumowanie zawodowe (80-120 słów).",
        "experience_suggestions": [
            {{
                "title": "Stanowisko (np. 'Starszy Specjalista ds. Analiz')",
                "company": "Fikcyjna Nazwa Firmy Sp. z o.o.",
                "startDate": "RRRR-MM (np. 2022-03)",
                "endDate": "obecnie" or "RRRR-MM (np. 2024-06)",
                "description": [
                    "Punkt 1: Obowiązek/Osiągnięcie z liczbami, np. 'Zarządzałem projektem X, co doprowadziło do Y% wzrostu efektywności.'",
                    "Punkt 2: Inny obowiązek/osiągnięcie.",
                    "Punkt 3: Kolejny obowiązek/osiągnięcie."
                ]
            }},
            {{
                "title": "Poprzednie Stanowisko (np. 'Młodszy Analityk Danych')",
                "company": "Poprzednia Fikcyjna Firma S.A.",
                "startDate": "RRRR-MM",
                "endDate": "RRRR-MM",
                "description": [
                    "Opis obowiązków z poprzedniej pracy (3-4 punkty)."
                ]
            }}
            // ... dodaj kolejne stanowiska, aby pokazać progresję
        ],
        "education_suggestions": [
            {{
                "degree": "Kierunek studiów (np. 'Informatyka Stosowana')",
                "school": "Nazwa Uczelni (np. 'Politechnika Wrocławska')",
                "startYear": "RRRR",
                "endYear": "RRRR",
                "grade_or_thesis": "Opcjonalnie: 'Praca magisterska na temat X'"
            }}
        ],
        "skills_list": {{
            "technical_skills": ["Umiejętność Techniczna 1", "Umiejętność Techniczna 2", "Narzędzie X"],
            "soft_skills": ["Komunikacja", "Rozwiązywanie Problemów", "Praca Zespołowa"],
            "languages": ["Angielski: zaawansowany", "Niemiecki: podstawowy"]
        }},
        "courses_certificates": [
            "Nazwa Kursu/Certyfikatu (Organizator, Rok)"
        ],
        "projects_portfolio": [
            {{
                "name": "Nazwa Projektu (jeśli dotyczy)",
                "description": "Krótki opis projektu i rola (np. 'Opracowanie aplikacji mobilnej dla klienta X')"
            }}
        ],
        "interests": "Krótkie i profesjonalne zainteresowania (np. 'Nowe technologie, turystyka górska')",
        "career_level": "{experience_level}",
        "industry_focus": "{industry}",
        "generation_notes": "Informacje o logice generowania tego CV (np. 'Wygenerowano CV dla poziomu Senior w branży IT, z naciskiem na zarządzanie projektami i rozwój oprogramowania.')"
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=4000,
        language=language,
        user_tier='free',
        task_type='cv_optimization'
    )

def optimize_cv(cv_text, job_description="", language='pl', is_premium=False, payment_verified=False):
    """
    Create an optimized version of CV using ONLY authentic data from the original CV.
    Premium users get extended token limits for more detailed CV generation.
    """
    prompt = f"""
    ZADANIE: Jesteś światowej klasy ekspertem w optymalizacji CV. Twoim zadaniem jest automatyczne rozpoznanie branży/sektora na podstawie CV, a następnie zoptymalizowanie go pod kątem tej branży i opisu stanowiska (jeśli podano). Kluczowe jest użycie WYŁĄCZNIE prawdziwych informacji z oryginalnego CV, bez dodawania jakichkolwiek wymyślonych danych.

    ⚠️ ABSOLUTNE ZASADY BEZPIECZEŃSTWA DANYCH (PRZECZYTAJ UWAŻNIE I ZASTOSUJ BEZWZGLĘDNIE):
    1.  ❌ ZAKAZ WYMYŚLANIA: NIE dodawaj ŻADNYCH nowych informacji, firm, stanowisk, dat, liczb, procent, osiągnięć, umiejętności, certyfikatów ani projektów, których NIE MA w oryginalnym CV.
    2.  ✅ DOZWOLONE: Jedyne, co jest dozwolone, to przepisanie, przeformułowanie, reorganizacja i lepsze sformułowanie ISTNIEJĄCYCH informacji z CV w bardziej profesjonalny i ukierunkowany sposób.
    3.  ✅ DOSTOSOWANIE BRANŻOWE: Użyj terminologii i stylu właściwego dla rozpoznanej branży, ale TYLKO w kontekście danych zawartych w CV.

    KROK 1: AUTOMATYCZNE ROZPOZNANIE BRANŻY/SEKTORA
    Na podstawie doświadczenia zawodowego, umiejętności i wykształcenia w CV, określ główną branżę/sektor. Wybierz spośród:
    -   IT/Technologie (programowanie, systemy, data science, cyberbezpieczeństwo)
    -   Finanse/Bankowość (księgowość, analizy finansowe, bankowość inwestycyjna, ubezpieczenia)
    -   Medycyna/Zdrowie (opieka zdrowotna, farmacja, badania kliniczne, pielęgniarstwo)
    -   Edukacja (nauczanie, szkolenia, rozwój, e-learning)
    -   Marketing/Sprzedaż (digital marketing, e-commerce, sprzedaż B2B/B2C, reklama, PR)
    -   Logistyka/Transport (łańcuch dostaw, spedycja, kurierzy, magazyny)
    -   Inżynieria/Produkcja (mechaniczna, elektryczna, budowlana, procesowa, zarządzanie produkcją)
    -   HR/Zarządzanie (kadry, rekrutacja, zarządzanie projektami, administracja biurowa)
    -   Obsługa Klienta (call center, wsparcie techniczne, relacje z klientem)
    -   Inne (określ konkretnie, np. gastronomia, sztuka, prawo)

    KROK 2: SZCZEGÓŁOWE INSTRUKCJE OPTYMALIZACJI Z KONTEKSTEM BRANŻOWYM:

    1.  **DANE OSOBOWE:**
        -   Przepisz dokładnie imię, nazwisko i dane kontaktowe z oryginalnego CV.
        -   NIE dodawaj nowych informacji kontaktowych.

    2.  **PODSUMOWANIE ZAWODOWE:**
        -   Napisz zwięzłe i przekonujące podsumowanie, bazując TYLKO na doświadczeniu i umiejętnościach WYMIENIONYCH w CV.
        -   Użyj TYLKO tych umiejętności, które są faktycznie obecne w CV i są istotne dla rozpoznanej branży/stanowiska.
        -   NIE wymyślaj branży ani specjalizacji, których nie ma w oryginale.

    3.  **DOŚWIADCZENIE ZAWODOWE:**
        -   Przepisz każde stanowisko DOKŁADNIE jak w oryginale (firma, stanowisko, daty zatrudnienia).
        -   Dla każdego miejsca pracy napisz 3-5 (standard) lub 5-8 (premium) punktów opisujących obowiązki i osiągnięcia.
        -   Bazuj punkty WYŁĄCZNIE na informacjach z oryginalnego CV. Jeśli oryginalny opis jest bardzo skąpy, rozwiń go, ale tylko w ramach logicznych możliwości (np. "dostarczanie paczek" można rozwinąć jako "realizacja terminowych dostaw paczek, obsługa dokumentacji", ale NIE "zarządzanie flotą 10 pojazdów", jeśli tego nie ma).
        -   Użyj profesjonalnych, dynamicznych czasowników (np. "koordynowałem", "zarządzałem", "analizowałem", "wdrożyłem").
        -   NIE dodawaj wymyślonych liczb, procent ani osiągnięć, których nie ma w CV. Jeśli osiągnięcia są w CV, podkreśl je.

        -   **KLUCZOWE ZASADY RÓŻNICOWANIA PODOBNYCH STANOWISK (jeśli w CV są podobne role):**
            -   Jeśli w CV są stanowiska o podobnych nazwach (np. "Kurier", "Kierowca", "Sprzedawca") w różnych firmach lub okresach:
            -   Stwórz dla każdego z nich **UNIKALNY opis**, który podkreśla **RÓŻNE aspekty** tej samej pracy.
            -   Wykorzystaj specyfikę każdej firmy (np. DHL = międzynarodowe, DPD = lokalne, UPS = biznesowe) do zróżnicowania obowiązków.
            -   Zastosuj różne terminy branżowe i skupiaj się na innych umiejętnościach w każdym opisie, bazując na możliwościach z oryginalnego CV.
            -   **Przykład różnicowania:**
                *   STANOWISKO 1: "Kurier - DHL" (2022-2023)
                    ✅ Opis 1: "Wykonywałem ekspresowe dostawy międzynarodowe, obsługiwałem system śledzenia przesyłek i zapewniałem terminowość dostaw zgodnie z procedurami DHL (jeśli dane były w CV)."
                *   STANOWISKO 2: "Kurier - DPD" (2021-2022)
                    ✅ Opis 2: "Realizowałem dostawy lokalne na terenie miasta, utrzymywałem kontakt z klientami i optymalizowałem trasy dostaw dla maksymalnej efektywności (jeśli dane były w CV)."
                *   STANOWISKO 3: "Kurier - UPS" (2020-2021)
                    ✅ Opis 3: "Odpowiadałem za dostawy biznesowe do firm, zarządzałem dokumentacją celną przesyłek zagranicznych i współpracowałem z działem obsługi klienta (jeśli dane były w CV)."

    4.  **UMIEJĘTNOŚCI:**
        -   Przepisz TYLKO te umiejętności, które są wymienione w oryginalnym CV.
        -   Pogrupuj je w logiczne kategorie (np. Techniczne, Miękkie, Językowe, Narzędzia), jeśli to poprawia czytelność.
        -   NIE dodawaj nowych umiejętności, których nie ma w CV.

    5.  **WYKSZTAŁCENIE:**
        -   Przepisz dokładnie informacje o wykształceniu z CV.
        -   NIE dodawaj kursów czy certyfikatów, których nie ma w oryginale. Jeśli są, możesz je ustrukturyzować.

    6.  **DOPASOWANIE DO STANOWISKA (jeśli job_description jest podane):**
        -   Wyeksponuj te elementy z CV, które pasują do opisu stanowiska, ale NIE dodawaj nowych elementów – tylko lepiej opisuj istniejące.

    ORYGINALNE CV DO ANALIZY:
    {cv_text}

    OPIS STANOWISKA, DO KTÓREGO OPTYMALIZUJEMY (jeśli podano):
    {job_description}

    WYGENERUJ: Profesjonalne, zoptymalizowane CV używając WYŁĄCZNIE informacji z oryginalnego CV, bez dodawania żadnych wymyślonych elementów. Dołącz analizę w formacie JSON.

    ODPOWIEDŹ W FORMACIE JSON:
    {{
        "detected_industry": "rozpoznana branża/sektor (np. 'IT/Technologie')",
        "industry_keywords": ["słowo kluczowe 1 z branży", "słowo kluczowe 2", "słowo kluczowe 3 (z CV i/lub oferty)"],
        "optimized_cv": "Kompletne, zoptymalizowane CV w formacie tekstowym, z branżowym dostosowaniem i bez wymyślonych danych.",
        "key_improvements": [
            "Dostosowano terminologię w sekcji 'Doświadczenie zawodowe' do branży [nazwa branży].",
            "Podkreślono kluczowe umiejętności [konkretne umiejętności z CV] istotne dla stanowiska/branży.",
            "Wzmocniono sekcję 'Podsumowanie zawodowe' o [konkretny element z CV]."
            "Zróżnicowano opisy podobnych stanowisk w oparciu o specyfikę firmy (jeśli dotyczy)."
        ],
        "ats_compatibility_score": "[0-100] (ocena po optymalizacji)",
        "job_match_score": "[0-100] (ocena dopasowania do job_description, jeśli podano)",
        "positioning_strategy": "Krótka strategia, jak kandydat jest pozycjonowany w ramach rozpoznanej branży (np. 'Jako specjalista z X-letnim doświadczeniem w Y').",
        "summary": "Zwięzłe podsumowanie wprowadzonych ulepszeń i ogólnej poprawy CV."
    }}"""

    # Rozszerzony limit tokenów dla płacących użytkowników
    if is_premium or payment_verified:
        max_tokens_for_tier = 6000  # Bardzo duży limit dla kompletnego CV
        prompt += f"""

        INSTRUKCJE PREMIUM - PEŁNE CV I MAKSYMALNA OPTYMALIZACJA:
        -   Stwórz szczegółowe opisy każdego stanowiska (5-8 punktów na pozycję), maksymalnie wykorzystując potencjał informacyjny oryginalnego CV.
        -   Dodaj rozbudowane podsumowanie zawodowe, uwzględniając kluczowe osiągnięcia (jeśli są w CV).
        -   Rozwiń każdą sekcję umiejętności z precyzyjnymi opisami, jeśli oryginalne CV na to pozwala.
        -   Zastosuj zaawansowane formatowanie, aby CV wyglądało jak profesjonalny dokument (np. użyj punktorów, pogrubień, jasnych nagłówków).
        -   Użyj zaawansowanej branżowej terminologii i języka biznesowego (tylko w oparciu o kontekst CV).
        -   Stwórz CV, które będzie gotowe do wysłania do najlepszych firm i korporacji.
        -   Wykorzystaj pełny potencjał każdej informacji z oryginalnego CV, aby zbudować spójną i przekonującą narrację.
        """
    else:
        max_tokens_for_tier = 3000  # Zwiększony z 2500 dla lepszej jakości
        prompt += f"""

        INSTRUKCJE STANDARD - PROFESJONALNA OPTYMALIZACJA:
        -   Stwórz solidną optymalizację CV (3-4 punkty na pozycję w doświadczeniu).
        -   Dodaj profesjonalne podsumowanie zawodowe.
        -   Uporządkuj umiejętności w logiczne kategorie.
        -   Zastosuj czytelne i spójne formatowanie dokumentu.
        """
    return send_api_request(
        prompt,
        max_tokens=max_tokens_for_tier,
        language=language,
        user_tier='premium' if is_premium else ('paid' if payment_verified else 'free'),
        task_type='cv_optimization'
    )

def generate_recruiter_feedback(cv_text, job_description="", language='pl'):
    """
    Generate feedback on a CV as if from an AI recruiter.
    """
    context = ""
    if job_description:
        context = f"Opis stanowiska do kontekstu (dla lepszego zrozumienia dopasowania):{job_description}"

    prompt = f"""
    ZADANIE: Jesteś doświadczonym, profesjonalnym i bezstronnym rekruterem. Przeanalizuj poniższe CV i udziel szczegółowej, konstruktywnej opinii w języku polskim.

    ⚠️ KRYTYCZNE ZASADY OCENY:
    1.  Oceniaj TYLKO to, co faktycznie jest w CV.
    2.  NIE ZAKŁADAJ, NIE DOMYŚLAJ się i NIE DODAWAJ informacji, których NIE MA w CV.
    3.  Jeśli jakaś sekcja (np. "Osiągnięcia") jest pusta lub brakuje w niej kluczowych informacji, zaznacz to jako słabość i zasugeruj uzupełnienie.
    4.  Skup się na tym, jak faktyczna treść CV wpływa na Twoje wrażenie jako rekrutera.

    Uwzględnij w ocenie:
    1.  **Ogólne wrażenie i pierwsza reakcja:** Co przyciąga uwagę, a co odpycha w pierwszych 6 sekundach?
    2.  **Mocne strony:** Konkretne, dobrze przedstawione elementy w CV (z uzasadnieniem dlaczego są mocne).
    3.  **Słabości:** Obszary wymagające poprawy, z konkretnymi sugestiami, jak je ulepszyć, bazując na istniejącej treści lub wskazując na braki.
    4.  **Ocena formatowania i struktury:** Czy CV jest czytelne, profesjonalnie wyglądające, logicznie uporządkowane?
    5.  **Jakość treści:** Czy opisy są konkretne, zorientowane na wyniki (jeśli wyniki są w CV)? Czy język jest profesjonalny?
    6.  **Kompatybilność z systemami ATS:** Czy CV wydaje się być łatwo parsowane przez ATS? Czy zawiera kluczowe słowa (jeśli job_description podano)?
    7.  **Ocena ogólna:** Punktacja w skali 1-10 i krótkie uzasadnienie.
    8.  **Prawdopodobieństwo zaproszenia na rozmowę:** Na podstawie faktycznej treści CV, jakie są szanse na dalszy etap rekrutacji?

    {context}

    CV do oceny:
    {cv_text}

    Odpowiedź w formacie JSON:
    {{
        "overall_impression": "Pierwsze wrażenie oparte na faktycznej treści CV (np. 'CV jest czytelne, ale brakuje w nim konkretów').",
        "rating": [1-10],
        "strengths": [
            "Mocna strona 1 (konkretnie z CV i dlaczego to mocna strona dla rekrutera).",
            "Mocna strona 2 (konkretnie z CV i uzasadnienie).",
            "Mocna strona 3 (konkretnie z CV i uzasadnienie)."
        ],
        "weaknesses": [
            "Słabość 1 (z sugestią konkretnej poprawy, bazując na CV lub wskazując na brak, np. 'Brak konkretnych osiągnięć w sekcji X – należy je dodać, jeśli istnieją').",
            "Słabość 2 (z sugestią poprawy).",
            "Słabość 3 (z sugestią poprawy)."
        ],
        "formatting_assessment": "Ocena layoutu, struktury i czytelności faktycznej treści CV (np. 'Layout jest prosty, ale czytelny. Brakuje spójności w datach.').",
        "content_quality": "Ocena jakości treści rzeczywiście obecnej w CV (np. 'Opisy obowiązków są ogólne, brakuje danych liczbowych.').",
        "ats_compatibility": "Czy CV przejdzie przez systemy automatycznej selekcji i jak bardzo jest zoptymalizowane pod słowa kluczowe (jeśli job_description podano).",
        "specific_improvements": [
            "Konkretna poprawa 1 (oparta na faktach z CV, np. 'Przeredagować opis stanowiska X, aby był bardziej zorientowany na rezultaty, jeśli to możliwe').",
            "Konkretna poprawa 2 (oparta na faktach z CV).",
            "Konkretna poprawa 3 (oparta na faktach z CV)."
        ],
        "interview_probability": "Prawdopodobieństwo zaproszenia na rozmowę oparte na faktach z CV (np. 'Niskie/Średnie/Wysokie', z krótkim uzasadnieniem).",
        "recruiter_summary": "Podsumowanie z perspektywy rekrutera – tylko fakty z CV i ich interpretacja, bez domysłów."
    }}
    Bądź szczery, ale konstruktywny. Oceniaj tylko to, co rzeczywiście jest w CV, nie dodawaj od siebie.
    """
    return send_api_request(
        prompt,
        max_tokens=3000,
        language=language,
        user_tier='premium', # Recruiter feedback is a premium feature.
        task_type='recruiter_feedback'
    )

def generate_cover_letter(cv_text, job_description, language='pl'):
    """
    Generate a cover letter based on a CV and job description.
    """
    prompt = f"""
    ZADANIE: Jesteś ekspertem w pisaniu listów motywacyjnych. Napisz spersonalizowany i przekonujący list motywacyjny w języku polskim, bazując WYŁĄCZNIE na faktach z CV.

    ⚠️ ABSOLUTNIE KRYTYCZNE WYMAGANIA:
    -   Używaj TYLKO informacji faktycznie obecnych w CV.
    -   NIE WYMYŚLAJ doświadczeń, projektów, osiągnięć, umiejętności, liczb, procent ani innych danych, których NIE MA w oryginalnym CV.
    -   NIE DODAWAJ informacji, których nie ma w oryginalnym CV. Jeśli w CV brakuje jakichś informacji, po prostu ich nie uwzględniaj w liście.
    -   List ma być zorientowany na dopasowanie KANDYDATA (na podstawie JEGO CV) do stanowiska.

    List motywacyjny powinien:
    -   Być profesjonalnie sformatowany i napisany eleganckim językiem polskim.
    -   Podkreślać umiejętności i doświadczenia FAKTYCZNIE wymienione w CV.
    -   Łączyć PRAWDZIWE doświadczenie kandydata z wymaganiami stanowiska z oferty pracy.
    -   Zawierać przekonujące wprowadzenie i zakończenie, oparte na faktach z CV.
    -   Mieć optymalną długość (około 300-400 słów, max jedna strona A4).
    -   Być napisany naturalnym, profesjonalnym, ale angażującym tonem.

    Struktura listu:
    1.  **Nagłówek:** Dane kontaktowe kandydata (imię, nazwisko, telefon, email, miasto - użyj danych z CV).
    2.  **Miejscowość i data.**
    3.  **Dane adresata:** Nazwa firmy, adres (jeśli znany, możesz użyć ogólnego lub poszukać w opisie pracy).
    4.  **Zwrot grzecznościowy:** Profesjonalny (np. "Szanowni Państwo," lub "Szanowna Pani/Panie [Nazwisko],").
    5.  **Wprowadzenie:** Krótkie przedstawienie kandydata, odwołanie się do ogłoszenia i wyrażenie zainteresowania (np. "Piszę w odpowiedzi na ogłoszenie dotyczące stanowiska X, które idealnie wpisuje się w moje Y-letnie doświadczenie w branży Z.").
    6.  **Główna treść (2-3 akapity):**
        -   Szczegółowe dopasowanie doświadczenia z CV do wymagań stanowiska.
        -   Przywołaj konkretne umiejętności i doświadczenia z CV, które są najbardziej relewantne dla tej roli.
        -   Pokaż, jak wiedza i umiejętności kandydata (bazując na CV) przyczynią się do sukcesu na danym stanowisku.
        -   Używaj języka zorientowanego na korzyści dla pracodawcy.
    7.  **Zakończenie:** Ponowne wyrażenie silnego zainteresowania, dostępność do dalszych rozmów i podziękowanie.
    8.  **Pozdrowienia:** Profesjonalne (np. "Z wyrazami szacunku,").
    9.  **Podpis:** Imię i nazwisko kandydata.

    Opis stanowiska:
    {job_description}

    CV kandydata (jako źródło informacji):
    {cv_text}

    Napisz kompletny list motywacyjny w języku polskim. Użyj profesjonalnego, ale przekonującego tonu. Zwróć sam list motywacyjny w formacie JSON.
    {{
        "cover_letter_text": "Tutaj znajduje się cała treść wygenerowanego listu motywacyjnego.",
        "summary_of_matching_points": [
            "Kluczowy punkt 1 z CV dopasowany do oferty.",
            "Kluczowy punkt 2 z CV dopasowany do oferty.",
            "Kluczowy punkt 3 z CV dopasowany do oferty."
        ],
        "important_note": "Pamiętaj, że list motywacyjny został wygenerowany wyłącznie na podstawie danych zawartych w CV. Upewnij się, że wszystkie informacje są aktualne i prawdziwe."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=2000,
        language=language,
        user_tier='free',
        task_type='cover_letter'
    )

def analyze_job_url(url):
    """
    Extract job description from a URL with improved handling for popular job sites.
    Prioritizes extracting the most relevant content to avoid excessive summarization.
    """
    try:
        logger.debug(f"Analyzing job URL: {url}")

        parsed_url = urllib.parse.urlparse(url)
        if not parsed_url.scheme or not parsed_url.netloc:
            raise ValueError("Invalid URL format. Please provide a full, valid URL (e.g., https://www.example.com/job).")

        headers_request = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9,pl;q=0.8", # Prefer English, then Polish
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive"
        }

        response = requests.get(url, headers=headers_request, timeout=10) # Added timeout
        response.raise_for_status() # Raises HTTPError for bad responses (4xx or 5xx)

        soup = BeautifulSoup(response.text, 'html.parser')

        job_text = ""
        domain = parsed_url.netloc.lower()

        # Specific selectors for popular Polish job boards and international ones
        if 'linkedin.com' in domain:
            containers = soup.select('.description__text, .show-more-less-html, .jobs-description__content, .job-details-json')
            if containers:
                for c in containers:
                    if c.name == 'script' and 'json' in c.get('type', ''):
                        try:
                            json_data = json.loads(c.string)
                            if 'description' in json_data:
                                job_text = json_data['description']
                                break
                        except json.JSONDecodeError:
                            pass
                if not job_text:
                    job_text = '\n'.join([c.get_text(separator='\n', strip=True) for c in containers if c.name != 'script'])

        elif 'indeed.com' in domain:
            container = soup.select_one('#jobDescriptionText')
            if container:
                job_text = container.get_text(separator='\n', strip=True)

        elif 'pracuj.pl' in domain:
            containers = soup.select('[data-test="section-description-text"], [data-test="text-box-content"]')
            if containers:
                job_text = '\n'.join([c.get_text(separator='\n', strip=True) for c in containers])

        elif 'olx.pl' in domain:
            # OLX uses different classes, often within a main description container
            containers = soup.select('.css-1fm6w0x-Text, .css-1q2aaez-Text, .css-1k8r2y8-Text, div[data-cy="offer-description__text"]')
            if containers:
                job_text = '\n'.join([c.get_text(separator='\n', strip=True) for c in containers])
            else: # Fallback for other potential OLX structures
                container = soup.select_one('[data-cy="ad-description"]')
                if container:
                    job_text = container.get_text(separator='\n', strip=True)

        elif 'praca.pl' in domain:
            containers = soup.select('.offer-description, .job-details__content')
            if containers:
                job_text = '\n'.join([c.get_text(separator='\n', strip=True) for c in containers])

        elif 'jobs.pl' in domain:
             containers = soup.select('.job-offer-description, .job-description__content')
             if containers:
                 job_text = '\n'.join([c.get_text(separator='\n', strip=True) for c in containers])

        # Generic fallback for other sites if specific selectors fail or don't exist
        if not job_text:
            logger.debug("Attempting generic selectors for job description.")
            # Prioritize elements that typically contain job descriptions
            potential_containers = soup.select(
                '.job-description, #job-description, .description, #description, .job-details, .job-content, .offer-body, .job-post-content, [itemprop="description"], [class*="job-description"], [class*="description"], [class*="offer-text"], article, main'
            )
            for container in potential_containers:
                container_text = container.get_text(separator='\n', strip=True)
                # Heuristic: a good job description should be reasonably long
                if len(container_text) > 200: # Minimum length for a meaningful description
                    job_text = container_text
                    break
            # Last resort: try to get text from body after removing noise
            if not job_text and soup.body:
                logger.debug("Last resort: extracting from body after removing noise.")
                for tag in soup.select('nav, header, footer, script, style, iframe, form, .sidebar, .related-jobs, .ad-section'):
                    tag.decompose()
                job_text = soup.body.get_text(separator='\n', strip=True)

        # Clean and refine the extracted text
        job_text = '\n'.join([' '.join(line.split()) for line in job_text.split('\n') if line.strip()])

        if not job_text or len(job_text.strip()) < 100: # Ensure minimum content length
            raise ValueError("Could not extract a meaningful job description from the URL. The extracted text was too short or empty.")

        logger.debug(f"Successfully extracted job description from URL. Length: {len(job_text)} chars.")

        # Summarize if the text is excessively long, to fit within token limits
        if len(job_text) > 4000:
            logger.debug(f"Job description is long ({len(job_text)} chars), summarizing with AI.")
            job_text = summarize_job_description(job_text, language) # Pass language here

        return job_text

    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout fetching job URL: {str(e)}")
        raise Exception(f"Failed to fetch job posting from URL due to timeout. Please check the URL or try again later.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching job URL: {str(e)}")
        raise Exception(f"Failed to fetch job posting from URL: {str(e)}. Please check the URL.")
    except Exception as e:
        logger.error(f"Error analyzing job URL: {str(e)}")
        raise Exception(f"Failed to analyze job posting from URL: {str(e)}. This might be due to an invalid URL, site structure, or anti-bot measures.")

def summarize_job_description(job_text, language='pl'): # Added language parameter
    """
    Summarize a long job description using the AI.
    """
    prompt = f"""
    ZADANIE: Jesteś ekspertem w analizie ogłoszeń o pracę. Wyciągnij i podsumuj kluczowe informacje z tego długiego ogłoszenia o pracę w języku polskim. Skoncentruj się na informacjach niezbędnych do optymalizacji CV.

    Uwzględnij:
    1.  Dokładny tytuł stanowiska i nazwa firmy (jeśli podane).
    2.  Najważniejsze wymagane umiejętności i kwalifikacje (hard i soft skills).
    3.  Główne obowiązki i zakres zadań.
    4.  Preferowany poziom doświadczenia i obszary wiedzy.
    5.  Inne ważne szczegóły (np. tryb pracy, lokalizacja, kluczowe benefity, jeśli wspomniane).
    6.  KLUCZOWE SŁOWA: TOP 5-7 najważniejszych słów kluczowych krytycznych dla tego stanowiska, które powinny znaleźć się w CV.

    Tekst ogłoszenia (tylko początkowe 4000 znaków, jeśli dłuższe):
    {job_text[:4000]}...

    Stwórz zwięzłe, ale kompletne podsumowanie tego ogłoszenia, skupiając się na informacjach istotnych dla optymalizacji CV.

    Odpowiedź w języku polskim, w formacie JSON:
    {{
        "job_title_summary": "Zwięzły tytuł i firma (jeśli podano)",
        "key_requirements_summary": "Podsumowanie najważniejszych wymagań (umiejętności, kwalifikacje)",
        "main_responsibilities_summary": "Główne obowiązki i zakres zadań",
        "experience_level_summary": "Podsumowanie wymaganego doświadczenia",
        "other_important_details": "Inne kluczowe informacje (np. tryb pracy, lokalizacja)",
        "critical_keywords_for_cv": ["słowo kluczowe 1", "słowo kluczowe 2", "słowo kluczowe 3", "słowo kluczowe 4", "słowo kluczowe 5"],
        "summary": "Całościowe, zwięzłe podsumowanie ogłoszenia."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=1500,
        language=language,
        user_tier='free',
        task_type='cv_optimization'
    )

def ats_optimization_check(cv_text, job_description="", language='pl'):
    """
    Check CV against ATS (Applicant Tracking System) and provide suggestions for improvement.
    """
    context = ""
    if job_description:
        context = f"Ogłoszenie o pracę dla odniesienia (pomoże w ocenie słów kluczowych):{job_description[:2000]}"

    prompt = f"""
    ZADANIE: Jesteś ekspertem w dziedzinie systemów ATS (Applicant Tracking System). Przeprowadź dogłębną analizę poniższego CV pod kątem kompatybilności z ATS i wykryj potencjalne problemy, które mogą uniemożliwić jego prawidłowe parsowanie lub skuteczne dopasowanie.

    ⚠️ KRYTYCZNE ZASADY ANALIZY:
    -   Analizuj WYŁĄCZNIE i TYLKO TREŚĆ ZAWARTĄ W CV. Nie zgaduj ani nie dodawaj informacji, których w CV nie ma.
    -   Twoja ocena ma być praktyczna i wskazywać, co faktycznie może stanowić problem dla ATS.

    Przeprowadź następujące analizy i podaj konkretne, uzasadnione wnioski:

    1.  **OCENA OGÓLNA KOMPATYBILNOŚCI Z ATS:**
        -   Ogólna ocena w skali 1-10 (1 - bardzo słabo, 10 - idealnie).
        -   Krótkie uzasadnienie tej oceny.

    2.  **PROBLEMY KRYTYCZNE (dyskwalifikujące lub poważnie utrudniające parsowanie):**
        -   Znajdź sekcje, które są w nieodpowiednich, nietypowych miejscach (np. doświadczenie w zainteresowaniach).
        -   Wskaż niespójności w układzie i formatowaniu, które mogą zdezorientować system.
        -   Zidentyfikuj zduplikowane, identyczne informacje w różnych sekcjach (np. te same umiejętności wymienione wielokrotnie).
        -   Zaznacz fragmenty tekstu, które wyglądają na spam lub zbyt "wypełnione" słowami kluczowymi.
        -   Wykryj ciągi znaków bez znaczenia, losowe znaki, znaki specjalne, które nie są standardowe w CV.

    3.  **PROBLEMY ZE STRUKTURĄ I NAGŁÓWKAMI:**
        -   Czy nagłówki sekcji są standardowe (np. "Doświadczenie Zawodowe", "Umiejętności", "Wykształcenie") i łatwe do rozpoznania przez ATS?
        -   Czy tekst jest odpowiednio podzielony na sekcje?
        -   Czy nie ma zbyt wielu kolumn, tabel, nietypowych grafik, które utrudniają parsowanie?

    4.  **PROBLEMY Z FORMATOWANIEM TEKSTU DLA ATS:**
        -   Wykryj problemy z formatowaniem, które mogą utrudnić odczyt (np. tekst w ramkach, w obrazkach, niestandardowe czcionki, cienie).
        -   Sprawdź użycie punktorów (czy są proste kropki/dash, a nie niestandardowe symbole).
        -   Zweryfikuj, czy użycie kursywy/pogrubienia jest spójne i nie zakłóca parsowania.

    5.  **ANALIZA SŁÓW KLUCZOWYCH:**
        -   **Gęstość słów kluczowych:** Czy kluczowe terminy (zawarte w CV lub z job_description, jeśli podano) są odpowiednio często używane, ale bez "keyword stuffingu"?
        -   **Trafność:** Czy słowa kluczowe są używane w odpowiednim kontekście?
        -   **Brakujące kluczowe słowa:** Zidentyfikuj ważne słowa kluczowe (z job_description lub branży), których brakuje w CV.
        -   **Rozmieszczenie:** Czy słowa kluczowe są równomiernie rozmieszczone w dokumencie?

    6.  **BRAKUJĄCE INFORMACJE / KOMPLETNOŚĆ:**
        -   Zidentyfikuj brakujące sekcje (np. "Podsumowanie zawodowe", "Osiągnięcia", "Zainteresowania", "Link do portfolio"), które są często oczekiwane lub pomocne dla ATS.
        -   Wskaż inne istotne informacje, które należy uzupełnić (np. dokładne daty zatrudnienia, nazwy firm).

    7.  **PODEJRZANE ELEMENTY / AUTENTYCZNOŚĆ (jeśli dotyczy):**
        -   Zaznacz fragmenty, które wyglądają na sztuczne, zbyt ogólne, maszynowo wygenerowane lub są niespójne z resztą CV.

    {context}

    CV do analizy:
    {cv_text}

    Odpowiedz w tym samym języku co CV. Jeśli CV jest po polsku, odpowiedz po polsku.
    Format odpowiedzi JSON:
    {{
        "overall_ats_score": [liczba 1-10],
        "overall_justification": "Krótkie uzasadnienie ogólnej oceny ATS.",
        "critical_problems": [
            {{"type": "Problem krytyczny (np. 'Niestandardowa struktura')", "description": "Szczegółowy opis problemu i jego wpływu na ATS."}},
            {{"type": "Problem krytyczny 2", "description": "Opis"}}
        ],
        "structure_problems": [
            {{"type": "Problem strukturalny (np. 'Nietypowe nagłówki')", "description": "Szczegółowy opis i sugestia poprawy."}},
            {{"type": "Problem strukturalny 2", "description": "Opis"}}
        ],
        "formatting_problems": [
            {{"type": "Problem z formatowaniem (np. 'Tekst w obrazkach')", "description": "Szczegółowy opis i sugestia poprawy."}},
            {{"type": "Problem z formatowaniem 2", "description": "Opis"}}
        ],
        "keyword_analysis": {{
            "keyword_density_assessment": "Ocena gęstości słów kluczowych (np. 'Niska gęstość kluczowych terminów branżowych').",
            "missing_keywords": ["brakujące słowo kluczowe 1 (z oferty/branży)", "brakujące słowo kluczowe 2"],
            "keyword_placement_assessment": "Ocena rozmieszczenia słów kluczowych (np. 'Słowa kluczowe zbyt skumulowane w jednej sekcji')."
        }},
        "missing_information": [
            "Brakująca sekcja/informacja 1 (np. 'Brak sekcji 'Osiągnięcia Zawodowe'')",
            "Brakująca sekcja/informacja 2"
        ],
        "suspicious_elements": [
            {{"type": "Podejrzany element (np. 'Generowany tekst')", "description": "Fragment tekstu, który wydaje się być sztuczny lub niespójny."}}
        ],
        "recommendations": [
            "Konkretna rekomendacja 1 (np. 'Zmień nagłówki sekcji na standardowe, rozpoznawalne przez ATS.').",
            "Konkretna rekomendacja 2.",
            "Konkretna rekomendacja 3."
        ],
        "summary": "Krótkie podsumowanie analizy ATS i zachęta do wdrożenia rekomendacji."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=1800,
        language=language,
        user_tier='free',
        task_type='cv_optimization'
    )

def analyze_cv_strengths(cv_text, job_title="analityk danych", language='pl'):
    """
    Analyze CV strengths for a specific job position and provide improvement suggestions.
    """
    prompt = f"""
    ZADANIE: Jesteś ekspertem w dziedzinie rekrutacji i analizy CV. Przeprowadź dogłębną analizę mocnych stron tego CV w kontekście stanowiska {job_title}.

    ⚠️ WAŻNE ZASADY ANALIZY:
    -   Oceniaj TYLKO i WYŁĄCZNIE to, co jest faktycznie obecne w CV.
    -   NIE WYMYŚLAJ ani nie dodawaj informacji, których w CV nie ma.
    -   Każda mocna strona musi być poparta konkretnym przykładem lub odniesieniem do treści CV.

    1.  Zidentyfikuj i szczegółowo omów 5-7 najsilniejszych elementów CV, które są najbardziej wartościowe dla pracodawcy na stanowisku {job_title}.
    2.  Dla każdej mocnej strony wyjaśnij, dlaczego jest ona istotna właśnie dla stanowiska {job_title} i dlaczego przyciągnie uwagę rekrutera.
    3.  Zaproponuj konkretne ulepszenia, które mogłyby wzmocnić TE MOCNE STRONY w CV (np. jak lepiej je sformułować, gdzie podkreślić, jak dodać kontekst, jeśli to wynika z CV).
    4.  Wskaż obszary, które mogłyby zostać dodane lub rozbudowane (JEŚLI WYNIKA TO Z BRAKU W CV, A KANDYDAT MÓGŁBY JE MIEĆ), aby CV było jeszcze lepiej dopasowane do stanowiska.
    5.  Zaproponuj, jak lepiej zaprezentować istniejące osiągnięcia i umiejętności, aby były bardziej przekonujące.

    CV do analizy:
    {cv_text}

    Pamiętaj, aby Twoja analiza była praktyczna, pomocna i oparta na faktach z CV. Używaj konkretnych przykładów z CV i odnoś je do wymagań typowych dla stanowiska {job_title}.

    Odpowiedź w formacie JSON:
    {{
        "target_job_title": "{job_title}",
        "analysis_summary": "Krótkie podsumowanie głównych atutów CV w kontekście stanowiska.",
        "strengths": [
            {{
                "strength_point": "Mocna strona 1 (np. 'Wieloletnie doświadczenie w analizie danych')",
                "relevance_to_job": "Dlaczego ta mocna strona jest kluczowa dla stanowiska '{job_title}' i jak przyciąga rekrutera.",
                "example_from_cv": "Konkretny fragment/informacja z CV, która potwierdza tę mocną stronę.",
                "suggestions_for_enhancement": ["Jak można wzmocnić tę mocną stronę w CV (np. 'Dodać konkretne narzędzia analityczne używane w projektach X').", "Inna sugestia"]
            }},
            {{
                "strength_point": "Mocna strona 2",
                "relevance_to_job": "Uzasadnienie znaczenia dla stanowiska.",
                "example_from_cv": "Przykład z CV.",
                "suggestions_for_enhancement": ["Sugestia 1", "Sugestia 2"]
            }}
            // ... dodaj do 5-7 mocnych stron
        ],
        "areas_for_further_development": [
            "Obszar do rozbudowy (jeśli faktycznie brakuje w CV, np. 'Więcej szczegółów na temat projektów zespołowych').",
            "Inny obszar do rozbudowy."
        ],
        "presentation_tips": [
            "Jak lepiej zaprezentować osiągnięcia w CV (np. 'Użyj metody STAR w opisach obowiązków, aby przedstawić osiągnięcia.').",
            "Jak lepiej uwydatnić umiejętności (np. 'Pogrupuj umiejętności w kategorie i wskaż poziom zaawansowania.')."
        ],
        "final_recommendation": "Końcowa rada dla kandydata."
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=2500,
        language=language,
        user_tier='free',
        task_type='cv_optimization'
    )

def generate_interview_questions(cv_text, job_description="", language='pl'):
    """
    Generuje prawdopodobne pytania rekrutacyjne na podstawie CV i opisu stanowiska.
    """
    context = ""
    if job_description:
        context = f"Uwzględnij poniższe ogłoszenie o pracę przy tworzeniu pytań, aby były jak najbardziej dopasowane do kontekstu stanowiska:\n{job_description[:2000]}"

    prompt = f"""
    ZADANIE: Jesteś doświadczonym rekruterem i doradcą kariery. Wygeneruj zestaw potencjalnych pytań rekrutacyjnych, które kandydat może otrzymać podczas rozmowy kwalifikacyjnej.

    Pytania powinny być:
    1.  **Specyficzne dla doświadczenia i umiejętności kandydata** wymienionych w CV.
    2.  **Dopasowane do stanowiska** (jeśli podano opis stanowiska), odwołując się do kluczowych wymagań.
    3.  **Zróżnicowane:** Połączenie pytań technicznych, behawioralnych i sytuacyjnych.
    4.  **Realistyczne:** Typowe pytania zadawane przez rekruterów w Polsce.

    Dla każdej kategorii wygeneruj po co najmniej 3 pytania.
    Dodatkowo, do każdego pytania dodaj krótką, trafną wskazówkę, jak można by na nie odpowiedzieć w oparciu o informacje z CV.

    {context}

    CV kandydata do analizy:
    {cv_text}

    Odpowiedz w tym samym języku co CV. Jeśli CV jest po polsku, odpowiedz po polsku.
    Format odpowiedzi JSON:
    {{
        "interview_preparation_summary": "Krótkie podsumowanie, na co kandydat powinien zwrócić szczególną uwagę.",
        "questions_about_experience": [
            {{
                "question": "Proszę opowiedzieć o największym wyzwaniu, z jakim mierzył się Pan/Pani na stanowisku [nazwa stanowiska z CV] w firmie [nazwa firmy z CV] i jak sobie Pan/Pani z nim poradził/a?",
                "tip_how_to_answer": "Użyj metody STAR (Sytuacja, Zadanie, Akcja, Rezultat), odwołując się do konkretnego problemu i rozwiązania opisanego w CV."
            }},
            {{
                "question": "Jakie technologie/narzędzia wymienione w Pana/Pani CV, np. [konkretne narzędzie z CV], uważa Pan/Pani za kluczowe dla Pana/Pani sukcesu i dlaczego?",
                "tip_how_to_answer": "Wybierz konkretne narzędzie/technologię z CV, opisz, jak ją wykorzystałeś/aś w projekcie i jakie przyniosło to korzyści."
            }},
            {{
                "question": "W Pana/Pani CV widzę, że zajmował/a się Pan/Pani [konkretny obowiązek z CV]. Jakie były Pana/Pani główne osiągnięcia w tym obszarze?",
                "tip_how_to_answer": "Odwołaj się do konkretnych osiągnięć z CV, najlepiej z liczbami lub procentami, aby pokazać mierzalne rezultaty."
            }}
        ],
        "technical_skills_questions": [
            {{
                "question": "Proszę opisać swoje doświadczenie z [konkretna umiejętność techniczna z CV, np. Python/SQL/CRM]. W jakim projekcie ją Pan/Pani wykorzystał/a?",
                "tip_how_to_answer": "Opisz konkretny projekt z CV, w którym ta umiejętność była kluczowa, i jaka była Twoja rola."
            }},
            {{
                "question": "Jakie są, Pana/Pani zdaniem, najlepsze praktyki w obszarze [konkretna umiejętność techniczna z CV]? Proszę podać przykład ich zastosowania.",
                "tip_how_to_answer": "Wskaż swoje rozumienie najlepszych praktyk i podeprzyj je przykładem z doświadczenia opisanego w CV."
            }},
            {{
                "question": "Co Pan/Pani sądzi o trendzie [nowy trend w branży, jeśli wspomniano w job_description lub pasuje do CV]? Czy ma Pan/Pani z tym doświadczenie?",
                "tip_how_to_answer": "Pokaż świadomość trendów, a jeśli masz doświadczenie (zgodne z CV), opisz je. Jeśli nie, wyraź chęć nauki."
            }}
        ],
        "behavioral_questions": [
            {{
                "question": "Proszę opowiedzieć o sytuacji, w której musiał/a Pan/Pani szybko dostosować się do zmieniających się okoliczności lub priorytetów. Jak Pan/Pani sobie poradził/a?",
                "tip_how_to_answer": "Użyj przykładu z CV, gdzie elastyczność była kluczowa. Skup się na swoich działaniach i wynikach."
            }},
            {{
                "question": "Proszę opisać sytuację, w której musiał/a Pan/Pani współpracować z trudnym współpracownikiem/klientem. Jaki był wynik?",
                "tip_how_to_answer": "Wybierz przykład z CV, który pokazuje umiejętności interpersonalne i rozwiązywanie konfliktów. Skup się na pozytywnym wyniku."
            }},
            {{
                "question": "Jak radzi sobie Pan/Pani ze stresem i presją czasu, szczególnie w kontekście projektów, o których Pan/Pani wspomniał/a w CV?",
                "tip_how_to_answer": "Opowiedz o strategiach radzenia sobie ze stresem, podając przykład z doświadczenia zawodowego w CV."
            }}
        ],
        "situational_questions": [
            {{
                "question": "Załóżmy, że rozpoczyna Pan/Pani pracę w naszej firmie i ma Pan/Pani do czynienia z [hipotetyczny problem związany z branżą/stanowiskiem]. Jakie byłyby Pana/Pani pierwsze kroki?",
                "tip_how_to_answer": "Odniesienie do metodyki pracy lub doświadczenia z CV. Pokaż logiczne myślenie i proaktywność."
            }},
            {{
                "question": "Co by Pan/Pani zrobił/a, gdyby projekt, nad którym Pan/Pani pracuje, nagle zmienił kierunek lub cele, mając na uwadze Pana/Pani doświadczenie w [obszar z CV]?",
                "tip_how_to_answer": "Pokaż zdolność do adaptacji i zarządzania zmianą, odwołując się do elastyczności lub doświadczenia w podobnych sytuacjach (jeśli w CV)."
            }},
            {{
                "question": "Jakie podejście zastosowałby Pan/Pani, aby poprawić [konkretny aspekt działania firmy/zespołu z ogłoszenia, jeśli podano] w oparciu o Pana/Pani umiejętności?",
                "tip_how_to_answer": "Zaprezentuj konkretne pomysły, bazując na swoich umiejętnościach i doświadczeniu z CV, które mogłyby przynieść wartość firmie."
            }}
        ],
        "motivation_and_fit_questions": [
            {{
                "question": "Dlaczego zainteresowało Pana/Panią nasze stanowisko [nazwa stanowiska z job_description] i nasza firma?",
                "tip_how_to_answer": "Pokaż, że zbadałeś/zbadałaś firmę i stanowisko, i połącz to ze swoimi celami kariery i doświadczeniem z CV."
            }},
            {{
                "question": "Gdzie widzi się Pan/Pani za 5 lat, biorąc pod uwagę Pana/Pani dotychczasową ścieżkę kariery?",
                "tip_how_to_answer": "Połącz swoje ambicje z możliwościami rozwoju w firmie, pokazując, że Twoje cele są zbieżne z ofertą."
            }},
            {{
                "question": "Co Pana/Panią motywuje do pracy na stanowisku [nazwa stanowiska], bazując na Pana/Pani doświadczeniach?",
                "tip_how_to_answer": "Wskaż konkretne aspekty pracy, które Cię pasjonują, odwołując się do pozytywnych doświadczeń z CV."
            }}
        ]
    }}
    """
    return send_api_request(
        prompt,
        max_tokens=2000,
        language=language,
        user_tier='free',
        task_type='interview_prep'
    )

def get_enhanced_system_prompt(task_type, language='pl'):
    """
    Generuje spersonalizowany prompt systemowy dla różnych typów zadań.
    """
    base_prompt = DEEP_REASONING_PROMPT

    task_specific_prompts = {
        'cv_optimization': """

🔥 SPECJALIZACJA: OPTYMALIZACJA CV
- Analizujesz każde słowo pod kątem wpływu na rekrutera i systemy ATS.
- Znasz najnowsze trendy w formatowaniu i układzie CV.
- Potrafisz dostosować styl i terminologię do różnych branż i stanowisk.
- Maksymalizujesz szanse przejścia CV przez filtry ATS.
- Tworzysz przekonujące narracje kariery zawodowej, bazując na istniejących danych.
- **ABSOLUTNY PRIORYTET: AUTENTYCZNOŚĆ DANYCH - NIGDY NIE DODAJESZ WYMYŚLONYCH INFORMACJI.**""",

        'recruiter_feedback': """

👔 SPECJALIZACJA: OPINIE REKRUTERA
- Myślisz jak senior recruiter z wieloletnim doświadczeniem w różnych branżach.
- Dostrzegasz detale i niuanse, które umykają innym, oceniając CV w kontekście realnej rekrutacji.
- Oceniasz CV pod kątem pierwszego wrażenia (tzw. "6 sekund" rekrutera).
- Znasz typowe błędy kandydatów i wiesz, jak ich unikać.
- Potrafisz przewidzieć reakcję hiring managera i działu HR.
- **ABSOLUTNY PRIORYTET: BEZSTRONNOŚĆ I BAZOWANIE WYŁĄCZNIE NA TREŚCI CV - NIE DOKONUJESZ DOMYSŁÓW.**""",

        'cover_letter': """

📄 SPECJALIZACJA: LISTY MOTYWACYJNE
- Tworzysz przekonujące narracje osobiste, które łączą doświadczenie kandydata z potrzebami firmy.
- Łączysz fakty z CV z wymaganiami oferty pracy w spójny i logiczny sposób.
- Używasz psychologii przekonywania w copywritingu, aby wyróżnić kandydata.
- Dostosowujesz ton listu do kultury organizacyjnej i branży.
- Unikasz szablonowych zwrotów i klisz, dążąc do oryginalności.
- **ABSOLUTNY PRIORYTET: WIERNOŚĆ DANYM Z CV - NIE GENERUJESZ FAŁSZYWYCH ANI WYMYŚLONYCH INFORMACJI.**""",

        'interview_prep': """

🎤 SPECJALIZACJA: PRZYGOTOWANIE DO ROZMÓW KWALIFIKACYJNYCH
- Przewidujesz pytania na podstawie analizy CV i opisu stanowiska docelowego.
- Znasz techniki odpowiadania na pytania behawioralne i sytuacyjne (np. STAR, CAR).
- Pomagasz w przygotowaniu historii sukcesu i radzeniu sobie ze słabościami.
- Analizujesz potencjalne luki w CV i sugerujesz, jak je pozytywnie przedstawić.
- Przygotowujesz do różnych typów rozmów (HR, techniczne, z przełożonym, panelowe).
- **ABSOLUTNY PRIORYTET: PRAKTYCZNE WSKAZÓWKI - BAZUJĄCE NA RZECZYWISTYCH INFORMACJACH Z CV I OFERTY.**"""
    }

    enhanced_prompt = base_prompt + task_specific_prompts.get(task_type, "")

    return enhanced_prompt

def get_model_performance_stats():
    """
    Zwróć informacje o używanych modelach AI - tylko Qwen z rozszerzonymi możliwościami.
    """
    return {
        "current_model": DEFAULT_MODEL,
        "model_family": "Qwen 2.5 72B Instruct",
        "model_provider": "Alibaba Cloud / OpenRouter",
        "optimization_level": "Advanced",
        "capabilities": [
            "Zaawansowana analiza CV w języku polskim",
            "Inteligentna optymalizacja treści zawodowych (z poszanowaniem autentyczności danych)",
            "Personalizowane rekomendacje kariery",
            "Profesjonalne sprawdzanie gramatyki i stylu",
            "Precyzyjne dopasowanie do stanowisk i słów kluczowych ATS",
            "Generowanie realistycznych przykładów CV (na żądanie)",
            "Psychologia rekrutacji i przekonywania",
            "Analiza trendów rynku pracy i wymagań pracodawców"
        ],
        "enhanced_features": {
            "adaptive_prompts": True, # Prompty dostosowują się do typu zadania
            "context_awareness": True, # Model uwzględnia kontekst (np. opis pracy)
            "industry_specialization": True, # Rozpoznawanie i dostosowywanie do branż
            "ats_optimization": True, # Specjalizacja w optymalizacji pod ATS
            "psychology_based": True, # Uwzględnianie psychologii rekrutacji
            "data_authenticity_enforcement": True # Rygorystyczne przestrzeganie autentyczności danych
        },
        "performance": {
            "response_quality": "Ekspertowa i praktyczna",
            "polish_language_support": "Natywne z kontekstem kulturowym i profesjonalną terminologią HR",
            "processing_speed": "Optymalna",
            "consistency": "Bardzo wysoka w przestrzeganiu zasad",
            "creativity": "Zaawansowana (w ramach dozwolonej inwencji, np. w generowaniu fikcyjnych CV)",
            "accuracy": "Precyzyjna w analizie i sugerowanych poprawkach"
        },
        "parameters": {
            "temperature": 0.8,
            "top_p": 0.95,
            "max_tokens_range": "2000-8000 (w zależności od funkcji i planu użytkownika)",
            "frequency_penalty": 0.1,
            "presence_penalty": 0.1
        }
    }

--- END OF FILE openrouter_api.py ---