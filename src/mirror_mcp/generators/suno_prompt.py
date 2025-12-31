"""Suno music prompt generator from taste profile."""

from ..models import SunoPrompt, TasteProfile, TimePattern, TopicAnalysis

# Keyword to music style mappings: (genre, mood, tempo)
MUSIC_STYLE_MAP = {
    # Korean music keywords
    "발라드": ("Ballad", "emotional", "slow"),
    "힙합": ("Hip-hop", "energetic", "fast"),
    "케이팝": ("K-pop", "upbeat", "moderate"),
    "재즈": ("Jazz", "smooth", "moderate"),
    "클래식": ("Classical", "elegant", "slow"),
    "로파이": ("Lo-fi", "chill", "slow"),
    "인디": ("Indie", "dreamy", "moderate"),
    "록": ("Rock", "powerful", "fast"),
    "팝": ("Pop", "catchy", "moderate"),
    "알앤비": ("R&B", "soulful", "moderate"),
    # English music keywords
    "edm": ("EDM", "energetic", "fast"),
    "acoustic": ("Acoustic", "warm", "moderate"),
    "indie": ("Indie", "dreamy", "moderate"),
    "rock": ("Rock", "powerful", "fast"),
    "pop": ("Pop", "catchy", "moderate"),
    "jazz": ("Jazz", "smooth", "moderate"),
    "lofi": ("Lo-fi", "chill", "slow"),
    "lo-fi": ("Lo-fi", "chill", "slow"),
    "classical": ("Classical", "elegant", "slow"),
    "hiphop": ("Hip-hop", "energetic", "fast"),
    "hip-hop": ("Hip-hop", "energetic", "fast"),
    "r&b": ("R&B", "soulful", "moderate"),
    "rnb": ("R&B", "soulful", "moderate"),
    "ballad": ("Ballad", "emotional", "slow"),
    "kpop": ("K-pop", "upbeat", "moderate"),
    "k-pop": ("K-pop", "upbeat", "moderate"),
    "ambient": ("Ambient", "atmospheric", "slow"),
    "electronic": ("Electronic", "synthetic", "moderate"),
    "synthwave": ("Synthwave", "retro", "moderate"),
    "chill": ("Chill", "relaxed", "slow"),
    "piano": ("Piano", "melodic", "moderate"),
    "guitar": ("Acoustic", "warm", "moderate"),
}

# Time context to mood mappings
TIME_MOOD_MAP = {
    "late_night": ("Melancholic", "Dreamy", "Introspective"),
    "morning": ("Fresh", "Uplifting", "Energetic"),
    "afternoon": ("Focused", "Productive", "Moderate"),
    "evening": ("Relaxed", "Warm", "Nostalgic"),
}

# BPM mapping by tempo preference
BPM_MAP = {
    "fast": "120-140 BPM",
    "moderate": "90-110 BPM",
    "slow": "60-85 BPM",
}

# Instrument suggestions by genre
INSTRUMENT_MAP = {
    "Lo-fi": "vinyl crackle, mellow piano, soft drums",
    "Jazz": "piano, upright bass, brushed drums, saxophone",
    "Hip-hop": "808 bass, trap hi-hats, synth pads",
    "K-pop": "synth, punchy drums, bass drops, vocal layers",
    "EDM": "synth leads, side-chain compression, build-ups",
    "Indie": "acoustic guitar, soft synths, ambient pads",
    "Pop": "piano, guitar, modern drums, vocal harmonies",
    "Ballad": "piano, strings, soft percussion",
    "Rock": "electric guitar, bass, drums, distortion",
    "Classical": "orchestra, strings, piano",
    "Acoustic": "acoustic guitar, soft percussion, warm bass",
    "R&B": "smooth bass, Rhodes piano, soft drums",
    "Ambient": "synthesizer pads, reverb, atmospheric textures",
    "Electronic": "synthesizers, drum machines, bass",
    "Synthwave": "analog synths, arpeggios, retro drums",
    "Chill": "soft piano, ambient pads, gentle percussion",
    "Piano": "grand piano, soft strings, minimal percussion",
}


def build_taste_profile(
    topic_analysis: TopicAnalysis,
    time_patterns: TimePattern,
) -> TasteProfile:
    """
    Build a taste profile from analysis results.

    Args:
        topic_analysis: Results from topic/keyword analysis
        time_patterns: Results from time pattern analysis

    Returns:
        TasteProfile with genres, moods, and preferences
    """
    keywords = [k for k, _ in topic_analysis.keywords[:15]]

    # Detect genres from keywords
    detected_genres = []
    detected_moods = []
    tempo_hints = []

    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in MUSIC_STYLE_MAP:
            genre, mood, tempo = MUSIC_STYLE_MAP[keyword_lower]
            if genre not in detected_genres:
                detected_genres.append(genre)
            detected_moods.append(mood)
            tempo_hints.append(tempo)

    # Determine time context
    if time_patterns.late_night_ratio > 0.3:
        time_context = "late_night"
    elif time_patterns.peak_hours and min(time_patterns.peak_hours) < 10:
        time_context = "morning"
    elif time_patterns.peak_hours and max(time_patterns.peak_hours) > 18:
        time_context = "evening"
    else:
        time_context = "afternoon"

    # Add time-based moods
    time_moods = TIME_MOOD_MAP.get(time_context, ("Balanced",))
    detected_moods.extend(time_moods)

    # Determine energy level based on tempo hints
    if tempo_hints:
        tempo_count = {"fast": 0, "moderate": 0, "slow": 0}
        for t in tempo_hints:
            tempo_count[t] += 1
        energy_map = {"fast": "high", "moderate": "medium", "slow": "low"}
        dominant_tempo = max(tempo_count, key=tempo_count.get)
        energy = energy_map[dominant_tempo]
    else:
        energy = "medium"
        dominant_tempo = "moderate"

    # Language preference
    lang_breakdown = topic_analysis.language_breakdown
    korean_count = lang_breakdown.get("korean", 0)
    english_count = lang_breakdown.get("english", 0)

    if korean_count > english_count * 2:
        lang_pref = "korean"
    elif english_count > korean_count * 2:
        lang_pref = "english"
    else:
        lang_pref = "mixed"

    # Default genres if none detected
    if not detected_genres:
        if "music" in topic_analysis.categories:
            detected_genres = ["Pop", "Indie"]
        else:
            detected_genres = ["Lo-fi", "Ambient"]

    # Unique moods
    unique_moods = list(dict.fromkeys(detected_moods))

    return TasteProfile(
        primary_genres=detected_genres[:3],
        mood_keywords=unique_moods[:5] or ["Balanced"],
        energy_level=energy,
        tempo_preference=dominant_tempo,
        time_context=time_context,
        language_preference=lang_pref,
    )


def generate_suno_prompt(taste_profile: TasteProfile) -> SunoPrompt:
    """
    Generate a Suno-compatible music prompt from taste profile.

    Args:
        taste_profile: User's music taste profile

    Returns:
        SunoPrompt with style, mood, tempo, and instruments
    """
    # Build style tags
    genres = ", ".join(taste_profile.primary_genres)
    moods = ", ".join(taste_profile.mood_keywords[:3])
    tempo = BPM_MAP.get(taste_profile.tempo_preference, "100 BPM")

    # Select instruments based on primary genre
    primary_genre = taste_profile.primary_genres[0] if taste_profile.primary_genres else "Pop"
    instruments = INSTRUMENT_MAP.get(primary_genre, "piano, guitar, drums")

    # Build full prompt (within 200 char limit for Suno)
    full_prompt = f"{genres}, {moods}, {tempo}, {instruments}"

    # Truncate if too long
    if len(full_prompt) > 195:
        full_prompt = f"{genres}, {moods}, {tempo}"

    if len(full_prompt) > 195:
        full_prompt = f"{genres}, {moods}"

    return SunoPrompt(
        style_tags=genres,
        mood=moods,
        tempo_bpm=tempo,
        instruments=instruments,
        full_prompt=full_prompt,
    )


def generate_multiple_prompts(
    taste_profile: TasteProfile,
    count: int = 3,
) -> list[SunoPrompt]:
    """
    Generate multiple varied Suno prompts from taste profile.

    Args:
        taste_profile: User's music taste profile
        count: Number of prompts to generate (1-5)

    Returns:
        List of SunoPrompt variations
    """
    count = max(1, min(5, count))  # Limit to 1-5
    prompts = []

    # Base prompt
    base_prompt = generate_suno_prompt(taste_profile)
    prompts.append(base_prompt)

    if count == 1:
        return prompts

    # Variation strategies
    variations = [
        _create_energy_variation,
        _create_mood_variation,
        _create_instrument_variation,
        _create_genre_fusion_variation,
    ]

    for i in range(1, min(count, len(variations) + 1)):
        variation = variations[i - 1](taste_profile, base_prompt)
        prompts.append(variation)

    return prompts


def _create_energy_variation(
    taste_profile: TasteProfile,
    base: SunoPrompt,
) -> SunoPrompt:
    """Create higher/lower energy variation."""
    energy = taste_profile.energy_level

    if energy == "low":
        new_tempo = "90-110 BPM"
        new_mood = "uplifting, energetic"
        energy_suffix = "energized"
    elif energy == "high":
        new_tempo = "60-75 BPM"
        new_mood = "calm, peaceful"
        energy_suffix = "relaxed"
    else:
        new_tempo = "120-140 BPM"
        new_mood = "powerful, intense"
        energy_suffix = "intense"

    full = f"{base.style_tags}, {new_mood}, {new_tempo}, {base.instruments}"
    if len(full) > 195:
        full = f"{base.style_tags}, {new_mood}, {new_tempo}"

    return SunoPrompt(
        style_tags=base.style_tags,
        mood=new_mood,
        tempo_bpm=new_tempo,
        instruments=base.instruments,
        full_prompt=full,
    )


def _create_mood_variation(
    taste_profile: TasteProfile,
    base: SunoPrompt,
) -> SunoPrompt:
    """Create contrasting mood variation."""
    # Mood contrasts
    mood_contrasts = {
        "chill": "upbeat, happy",
        "energetic": "mellow, laid-back",
        "emotional": "confident, triumphant",
        "smooth": "edgy, bold",
        "dreamy": "grounded, rhythmic",
    }

    current_moods = base.mood.split(", ")
    new_moods = []
    for mood in current_moods:
        mood_lower = mood.lower()
        if mood_lower in mood_contrasts:
            new_moods.append(mood_contrasts[mood_lower])
        else:
            new_moods.append(mood)

    new_mood = ", ".join(new_moods[:2])
    full = f"{base.style_tags}, {new_mood}, {base.tempo_bpm}, {base.instruments}"
    if len(full) > 195:
        full = f"{base.style_tags}, {new_mood}, {base.tempo_bpm}"

    return SunoPrompt(
        style_tags=base.style_tags,
        mood=new_mood,
        tempo_bpm=base.tempo_bpm,
        instruments=base.instruments,
        full_prompt=full,
    )


def _create_instrument_variation(
    taste_profile: TasteProfile,
    base: SunoPrompt,
) -> SunoPrompt:
    """Create variation with different instruments."""
    # Alternative instrument sets
    alt_instruments = {
        "vinyl crackle, mellow piano, soft drums": "warm synth pads, gentle guitar, subtle percussion",
        "piano, upright bass, brushed drums, saxophone": "electric piano, acoustic bass, brushes, trumpet",
        "808 bass, trap hi-hats, synth pads": "deep bass, minimal drums, vocal chops",
        "synth, punchy drums, bass drops, vocal layers": "guitar riffs, live drums, bass groove, harmonies",
        "acoustic guitar, soft synths, ambient pads": "piano, strings, gentle electronic elements",
    }

    new_instruments = alt_instruments.get(
        base.instruments,
        "piano, soft synths, ambient textures, gentle percussion"
    )

    full = f"{base.style_tags}, {base.mood}, {base.tempo_bpm}, {new_instruments}"
    if len(full) > 195:
        full = f"{base.style_tags}, {base.mood}, {base.tempo_bpm}"

    return SunoPrompt(
        style_tags=base.style_tags,
        mood=base.mood,
        tempo_bpm=base.tempo_bpm,
        instruments=new_instruments,
        full_prompt=full,
    )


def _create_genre_fusion_variation(
    taste_profile: TasteProfile,
    base: SunoPrompt,
) -> SunoPrompt:
    """Create genre fusion variation."""
    # Fusion suggestions based on primary genre
    genre_fusions = {
        "Lo-fi": ("Lo-fi Jazz", "smooth, sophisticated"),
        "Jazz": ("Jazz Fusion", "groovy, experimental"),
        "Hip-hop": ("Hip-hop Soul", "soulful, rhythmic"),
        "K-pop": ("K-pop R&B", "smooth, melodic"),
        "Pop": ("Electropop", "modern, synth-driven"),
        "Indie": ("Indie Electronic", "atmospheric, textured"),
        "EDM": ("Future Bass", "melodic, emotional"),
        "Rock": ("Alternative Rock", "atmospheric, dynamic"),
        "Classical": ("Neoclassical", "cinematic, epic"),
        "Ballad": ("Soul Ballad", "deep, expressive"),
    }

    current_genres = base.style_tags.split(", ")
    primary = current_genres[0] if current_genres else "Pop"

    fusion_style, fusion_mood = genre_fusions.get(primary, (f"{primary} Fusion", "fresh, unique"))

    full = f"{fusion_style}, {fusion_mood}, {base.tempo_bpm}, {base.instruments}"
    if len(full) > 195:
        full = f"{fusion_style}, {fusion_mood}, {base.tempo_bpm}"

    return SunoPrompt(
        style_tags=fusion_style,
        mood=fusion_mood,
        tempo_bpm=base.tempo_bpm,
        instruments=base.instruments,
        full_prompt=full,
    )
