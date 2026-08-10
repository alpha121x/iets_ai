import re

from app.config import settings


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
    return score, gemini_text(
        f"Evaluate this IELTS {task_type} answer. Give concise feedback on task response, coherence, vocabulary, and grammar. Do not claim it is an official score.\n\n{answer}",
        feedback,
    )


def speaking_feedback(transcript: str) -> tuple[float, str]:
    words = re.findall(r"\b[\w'-]+\b", transcript)
    score = 5.0 + (0.5 if len(words) >= 80 else 0) + (0.5 if len(set(word.lower() for word in words)) / max(len(words), 1) > 0.55 else 0)
    fallback = (
        f"Practice estimate: {min(score, 6.5):.1f}. Your transcript contains {len(words)} words. "
        "Develop each answer with a reason and example, vary sentence structures, and record yourself to review pronunciation and pauses."
    )
    return min(score, 6.5), gemini_text(
        f"Give concise IELTS speaking feedback for this response transcript. Do not claim an official score.\n\n{transcript}", fallback
    )


def _ai_feedback(prompt: str, fallback: str) -> str:
    """Use OpenAI only when configured; local development remains fully usable without it."""
    if not settings.OPENAI_API_KEY or settings.OPENAI_API_KEY.startswith("YOUR_"):
        return fallback
    try:
        from openai import OpenAI

        completion = OpenAI(api_key=settings.OPENAI_API_KEY).chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "system", "content": "You are a supportive IELTS coach."}, {"role": "user", "content": prompt}],
            max_tokens=350,
        )
        return completion.choices[0].message.content or fallback
    except Exception:
        return fallback


def coach_reply(message: str, target_program: str | None, target_country: str | None) -> str:
    context = f"The student targets {target_program or 'an international programme'} in {target_country or 'their preferred country'}."
    fallback = (
        f"{context} Start with one focused goal today: practise IELTS Writing Task 2 for 30 minutes, then review coherence, vocabulary and grammar. "
        "Tell me your current IELTS scores or the test you need help with, and I will make a study plan."
    )
    return gemini_text(
        "You are AI Coach, a supportive international-study and test-preparation coach. "
        "Give concise, practical guidance. Never invent university requirements or guarantee admission.\n\n"
        f"{context}\nStudent message: {message}",
        fallback,
    )


def gemini_text(prompt: str, fallback: str) -> str:
    """Generate Gemini content while retaining a safe local fallback."""
    if not settings.GEMINI_API_KEY or settings.GEMINI_API_KEY.startswith("YOUR_"):
        return fallback
    try:
        from google import genai

        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        response = client.models.generate_content(
            model=settings.GEMINI_MODEL,
            contents=prompt,
        )
        return response.text or fallback
    except Exception:
        return fallback


def university_ai_summary(student, matches: list[dict]) -> str:
    shortlist = "\n".join(
        f"- {item['university']} | {item['program']} | {item['status']} | {item['match_percentage']}% | issues: {', '.join(item['reasons']) or 'none'}"
        for item in matches[:10]
    )
    fallback = "Prioritise Strong Match programmes first. Review every official source, deadline and scholarship criterion before applying."
    return gemini_text(
        "You are an international university application advisor. Based only on the supplied structured results, "
        "write a concise student-friendly action plan. Do not claim eligibility beyond the data and do not invent requirements.\n\n"
        f"Student target country: {student.target_country}; field: {student.target_program}; CGPA: {student.cgpa}.\n"
        f"Matches:\n{shortlist}",
        fallback,
    )


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
