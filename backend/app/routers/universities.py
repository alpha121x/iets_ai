from fastapi import APIRouter, HTTPException
from sqlalchemy import desc

from app.dependencies import CurrentUser, DBSession
from app.models.ielts import IELTSResult
from app.models.university import University, UniversityProgram
from app.services import university_match

router = APIRouter(prefix="/api/universities", tags=["University recommendations"])


@router.get("")
def list_programs(db: DBSession, country: str | None = None, field: str | None = None) -> list[dict]:
    query = db.query(UniversityProgram, University).join(University)
    if country:
        query = query.filter(University.country.ilike(country))
    if field:
        query = query.filter(UniversityProgram.field.ilike(f"%{field}%"))
    return [_program_dict(program, university) for program, university in query.all()]


@router.get("/recommendations")
def recommendations(user: CurrentUser, db: DBSession, country: str | None = None, field: str | None = None) -> list[dict]:
    result = db.query(IELTSResult).filter_by(user_id=user.id).order_by(desc(IELTSResult.created_at)).first()
    query = db.query(UniversityProgram, University).join(University)
    if country or user.target_country:
        query = query.filter(University.country.ilike(country or user.target_country))
    if field or user.target_program:
        query = query.filter(UniversityProgram.field.ilike(f"%{field or user.target_program}%"))
    matches = []
    for program, university in query.all():
        item = _program_dict(program, university)
        item.update(university_match(program, result, user))
        matches.append(item)
    return sorted(matches, key=lambda item: item["match_percentage"], reverse=True)


def _program_dict(program: UniversityProgram, university: University) -> dict:
    return {
        "program_id": program.id, "university": university.name, "country": university.country,
        "city": university.city, "website": university.website, "program": program.program_name,
        "degree": program.degree, "field": program.field, "min_ielts": program.min_ielts,
        "min_cgpa": program.min_cgpa, "tuition_fee": program.tuition_fee,
        "application_deadline": program.application_deadline,
    }
