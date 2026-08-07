import re


def round_ielts_band(value: float) -> float:
    """Round to the nearest IELTS half band."""
    return round(value * 2) / 2


def overall_band(reading: float, listening: float, writing: float, speaking: float) -> float:
    return round_ielts_band((reading + listening + writing + speaking) / 4)


def writing_feedback(answer: str, task_type: str) -> tuple[float, str]:
    """Deterministic fallback feedback; an LLM can replace this service later."""
    words = re.findall(r"\b[\w'-]+\b", answer)
    sentences = [part for part in re.split(r"[.!?]+", answer) if part.strip()]
    word_count = len(words)
    target = 150 if task_type == "Task 1" else 250
    score = 5.0
    if word_count >= target:
        score += 0.5
    if len(sentences) >= 4:
        score += 0.5
    if len(set(word.lower() for word in words)) / max(word_count, 1) > 0.55:
        score += 0.5
    score = min(score, 7.0)
    feedback = (
        f"Estimated band {score:.1f} (practice estimate). Your response has {word_count} words. "
        + ("It meets the usual length target. " if word_count >= target else f"Aim for at least {target} words. ")
        + "Improve cohesion by using clear paragraphs, topic sentences, and precise examples. "
        + "Review grammar and vocabulary with a qualified IELTS teacher before relying on this score."
    )
    return score, feedback


def university_match(program, result, user) -> dict:
    checks = {
        "overall IELTS": (result.overall if result else None, program.min_ielts),
        "reading": (result.reading if result else None, program.min_reading),
        "listening": (result.listening if result else None, program.min_listening),
        "writing": (result.writing if result else None, program.min_writing),
        "speaking": (result.speaking if result else None, program.min_speaking),
        "CGPA": (user.cgpa, program.min_cgpa),
    }
    unmet, evaluated = [], 0
    for label, (student, minimum) in checks.items():
        if minimum is None:
            continue
        if student is None:
            unmet.append(f"{label}: score is missing (minimum {minimum})")
        else:
            evaluated += 1
            if student < minimum:
                unmet.append(f"{label}: {student} is below {minimum}")
    if not result:
        status, match = "Profile incomplete", 0
    elif not unmet:
        status, match = "Strong match", 95
    elif evaluated and len(unmet) == 1:
        status, match = "Possible match", 70
    else:
        status, match = "Not eligible", max(0, 40 - 10 * len(unmet))
    return {"status": status, "match_percentage": match, "reasons": unmet}
