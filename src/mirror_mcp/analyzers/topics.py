"""Keyword and topic extraction from video titles."""

import re
from collections import Counter

from ..models import TopicAnalysis, WatchHistoryEntry

# Korean character detection
KOREAN_PATTERN = re.compile(r"[가-힣]+")
ENGLISH_PATTERN = re.compile(r"[a-zA-Z]+")

# Synonym mappings for keyword normalization
SYNONYMS = {
    "kpop": ["k-pop", "케이팝", "k pop", "korean pop"],
    "lofi": ["lo-fi", "로파이", "lo fi", "lofi hip hop"],
    "hiphop": ["hip-hop", "힙합", "hip hop", "랩"],
    "rnb": ["r&b", "알앤비", "rhythm and blues", "알엔비"],
    "edm": ["electronic", "일렉트로닉", "electronic dance", "electronica"],
    "jazz": ["재즈", "jaz"],
    "rock": ["록", "락"],
    "pop": ["팝", "팝송"],
    "classical": ["클래식", "클래시컬", "클랙식"],
    "indie": ["인디", "인디음악"],
    "acoustic": ["어쿠스틱", "통기타"],
    "ballad": ["발라드", "발라드곡"],
    "piano": ["피아노"],
    "guitar": ["기타", "통기타", "일렉기타"],
    "asmr": ["에이에스엠알"],
    "vlog": ["브이로그", "일상", "daily"],
    "gaming": ["게임", "겜", "플레이"],
    "tutorial": ["강의", "튜토리얼", "강좌"],
    "review": ["리뷰", "후기"],
    "mukbang": ["먹방", "eating show"],
}

# Build reverse lookup for fast normalization
_SYNONYM_LOOKUP = {}
for canonical, variants in SYNONYMS.items():
    _SYNONYM_LOOKUP[canonical.lower()] = canonical
    for variant in variants:
        _SYNONYM_LOOKUP[variant.lower()] = canonical


def normalize_keyword(word: str) -> str:
    """
    Normalize a keyword to its canonical form.

    Args:
        word: The keyword to normalize

    Returns:
        The canonical form if found, otherwise the original word
    """
    return _SYNONYM_LOOKUP.get(word.lower(), word.lower())

# Common stopwords to filter
STOPWORDS_EN = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    "this", "that", "these", "those", "it", "its", "my", "your", "our",
    "their", "his", "her", "what", "which", "who", "whom", "how", "when",
    "where", "why", "all", "each", "every", "both", "few", "more", "most",
    "other", "some", "such", "no", "not", "only", "own", "same", "so",
    "than", "too", "very", "just", "also", "now", "here", "there", "then",
    "official", "video", "music", "live", "new", "full", "hd", "mv",
}
STOPWORDS_KR = {
    "그", "이", "저", "것", "수", "등", "및", "더", "를", "을", "에", "의",
    "가", "는", "은", "로", "으로", "에서", "까지", "부터", "와", "과",
    "하다", "되다", "있다", "없다", "같다", "위해", "통해", "대한",
}

# Category keyword mappings
CATEGORY_KEYWORDS = {
    "music": [
        "music", "song", "mv", "cover", "live", "concert", "playlist",
        "음악", "노래", "뮤비", "커버", "라이브", "콘서트",
        "lofi", "lo-fi", "jazz", "rock", "pop", "hip-hop", "hiphop",
        "edm", "classical", "acoustic", "indie", "r&b", "rnb",
        "발라드", "힙합", "재즈", "클래식", "케이팝", "kpop",
    ],
    "gaming": [
        "game", "gaming", "gameplay", "게임", "플레이", "스트리밍",
        "stream", "twitch", "let's play", "walkthrough",
    ],
    "tech": [
        "tech", "review", "unboxing", "coding", "programming",
        "리뷰", "개발", "코딩", "프로그래밍", "tutorial",
        "python", "javascript", "react", "ai", "machine learning",
    ],
    "entertainment": [
        "vlog", "funny", "comedy", "예능", "브이로그", "일상",
        "mukbang", "먹방", "asmr", "reaction", "리액션",
    ],
    "education": [
        "tutorial", "learn", "how to", "강의", "배우기", "공부",
        "lecture", "course", "class", "lesson",
    ],
}


def extract_keywords_simple(titles: list[str], limit: int = 20) -> list[tuple[str, int]]:
    """
    Simple keyword extraction without external NLP libraries.

    Args:
        titles: List of video titles
        limit: Maximum number of keywords to return

    Returns:
        List of (keyword, frequency) tuples with normalized keywords
    """
    all_words = []

    for title in titles:
        # Extract Korean words (2+ characters)
        korean_words = KOREAN_PATTERN.findall(title)
        all_words.extend(
            [normalize_keyword(w) for w in korean_words if len(w) >= 2 and w not in STOPWORDS_KR]
        )

        # Extract English words (3+ characters)
        english_words = ENGLISH_PATTERN.findall(title.lower())
        all_words.extend(
            [normalize_keyword(w) for w in english_words if len(w) >= 3 and w not in STOPWORDS_EN]
        )

    return Counter(all_words).most_common(limit)


def extract_keywords_konlpy(titles: list[str], limit: int = 20) -> list[tuple[str, int]]:
    """
    Advanced Korean keyword extraction using KoNLPy.

    Falls back to simple extraction if KoNLPy not available.

    Args:
        titles: List of video titles
        limit: Maximum number of keywords to return

    Returns:
        List of (keyword, frequency) tuples with normalized keywords
    """
    try:
        from konlpy.tag import Okt

        okt = Okt()

        all_nouns = []
        for title in titles:
            nouns = okt.nouns(title)
            all_nouns.extend([normalize_keyword(n) for n in nouns if len(n) >= 2])

        # Also extract English words
        for title in titles:
            english_words = ENGLISH_PATTERN.findall(title.lower())
            all_nouns.extend(
                [normalize_keyword(w) for w in english_words if len(w) >= 3 and w not in STOPWORDS_EN]
            )

        return Counter(all_nouns).most_common(limit)
    except ImportError:
        return extract_keywords_simple(titles, limit)


def infer_categories(keywords: list[tuple[str, int]]) -> list[str]:
    """
    Infer content categories from keywords.

    Args:
        keywords: List of (keyword, frequency) tuples

    Returns:
        List of detected category names
    """
    keyword_set = {k.lower() for k, _ in keywords}
    detected = []

    for category, category_words in CATEGORY_KEYWORDS.items():
        if any(cw in keyword_set for cw in category_words):
            detected.append(category)

    return detected or ["general"]


def analyze_topics(
    entries: list[WatchHistoryEntry],
    limit: int = 20,
    use_konlpy: bool = True,
) -> TopicAnalysis:
    """
    Extract topics and keywords from video titles.

    Args:
        entries: List of watch history entries
        limit: Maximum number of keywords to return
        use_konlpy: Whether to try using KoNLPy for Korean NLP

    Returns:
        TopicAnalysis with keywords and categories
    """
    titles = [e.clean_title for e in entries]

    # Language breakdown
    korean_count = sum(1 for t in titles if KOREAN_PATTERN.search(t))
    english_only_count = sum(
        1 for t in titles if ENGLISH_PATTERN.search(t) and not KOREAN_PATTERN.search(t)
    )

    # Keyword extraction
    if use_konlpy:
        keywords = extract_keywords_konlpy(titles, limit)
    else:
        keywords = extract_keywords_simple(titles, limit)

    # Category inference
    categories = infer_categories(keywords)

    return TopicAnalysis(
        keywords=keywords,
        language_breakdown={"korean": korean_count, "english": english_only_count},
        categories=categories,
    )
