from fastapi import APIRouter, HTTPException
from sqlalchemy import desc, func

from app.dependencies import CurrentUser, DBSession
from app.models.ielts import IELTSResult
from app.models.university import ProgramTestRequirement, Scholarship, University, UniversityProgram
from app.services import university_match

router = APIRouter(prefix="/api/universities", tags=["University recommendations"])


@router.get("")
def list_programs(db: DBSession, country: str | None = None, field: str | None = None) -> list[dict]:
    query = db.query(UniversityProgram, University).join(University)
    if country:
        query = query.filter(University.country.ilike(country))
    if field:
        query = query.filter(UniversityProgram.field.ilike(f"%{field}%"))
    return [_program_dict(program, university, db) for program, university in query.all()]


@router.get("/recommendations")
def recommendations(user: CurrentUser, db: DBSession, country: str | None = None, field: str | None = None) -> list[dict]:
    result = db.query(IELTSResult).filter_by(user_id=user.id).order_by(desc(IELTSResult.created_at)).first()
    query = db.query(UniversityProgram, University).join(University)
    selected_country = (country or user.target_country or "").strip()
    selected_field = (field or user.target_program or "").strip()
    if selected_country:
        query = query.filter(func.trim(University.country).ilike(selected_country))
    country_query = query
    if selected_field:
        query = query.filter(func.trim(UniversityProgram.field).ilike(f"%{selected_field}%"))
    programmes = query.all()
    # A student should still see country matches if a field label has no exact database match.
    if not programmes and selected_field:
        programmes = country_query.all()
    matches = []
    for program, university in programmes:
        item = _program_dict(program, university, db)
        item.update(university_match(program, result, user))
        matches.append(item)
    return sorted(matches, key=lambda item: item["match_percentage"], reverse=True)


def _program_dict(program: UniversityProgram, university: University, db: DBSession) -> dict:
    tests = db.query(ProgramTestRequirement).filter_by(program_id=program.id).all()
    scholarships = db.query(Scholarship).filter(
        (Scholarship.program_id == program.id) | (Scholarship.university_id == university.id)
    ).all()
    return {
        "program_id": program.id, "university": university.name, "country": university.country,
        "city": university.city, "website": university.website, "program": program.program_name,
        "degree": program.degree, "field": program.field, "min_ielts": program.min_ielts,
        "min_cgpa": program.min_cgpa, "tuition_fee": program.tuition_fee,
        "application_deadline": program.application_deadline,
        "source_url": program.source_url or university.website,
        "last_verified_at": program.last_verified_at.isoformat() if program.last_verified_at else None,
        "tests": [{"name": test.test_name, "minimum_score": test.minimum_score, "required": test.required, "source_url": test.source_url} for test in tests],
        "scholarships": [{"name": scholarship.name, "amount": scholarship.amount, "eligibility": scholarship.eligibility, "deadline": scholarship.deadline, "source_url": scholarship.source_url} for scholarship in scholarships],
    }
