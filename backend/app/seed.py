from sqlalchemy.orm import Session

from app.models.ielts import IELTSLesson
from datetime import datetime, timezone

from app.models.university import ProgramTestRequirement, Scholarship, University, UniversityProgram


def seed_initial_data(db: Session) -> None:
    if not db.query(IELTSLesson).first():
        db.add_all([
            IELTSLesson(module="Reading", title="Skimming and scanning", level="Beginner", content="Skim for the main idea, then scan for names, dates, and keywords."),
            IELTSLesson(module="Listening", title="Predicting answers", level="Beginner", content="Read questions first and predict the likely word type before audio starts."),
            IELTSLesson(module="Writing", title="Task 2 essay structure", level="Intermediate", content="Use an introduction, two developed body paragraphs, and a conclusion."),
            IELTSLesson(module="Speaking", title="Extending answers", level="Intermediate", content="Answer, explain why, and add a specific example to develop each response."),
        ])
    if not db.query(University).first():
        manchester = University(name="University of Manchester", country="UK", city="Manchester", website="https://www.manchester.ac.uk", ranking=34)
        dundee = University(name="University of Dundee", country="UK", city="Dundee", website="https://www.dundee.ac.uk", ranking=441)
        york = University(name="York University", country="Canada", city="Toronto", website="https://www.yorku.ca", ranking=362)
        db.add_all([manchester, dundee, york])
        db.flush()
        db.add_all([
            UniversityProgram(university_id=manchester.id, program_name="MSc Advanced Computer Science", degree="Master's", field="Computer Science", min_ielts=6.5, min_writing=6.0, min_cgpa=3.0, tuition_fee=33000, application_deadline="Check official website", source_url="https://www.manchester.ac.uk", last_verified_at=datetime.now(timezone.utc)),
            UniversityProgram(university_id=dundee.id, program_name="MSc Computer Science", degree="Master's", field="Computer Science", min_ielts=6.0, min_writing=6.0, min_cgpa=2.7, tuition_fee=23900, application_deadline="Check official website", source_url="https://www.dundee.ac.uk", last_verified_at=datetime.now(timezone.utc)),
            UniversityProgram(university_id=york.id, program_name="MSc Computer Science", degree="Master's", field="Computer Science", min_ielts=6.5, min_writing=6.0, min_cgpa=3.0, tuition_fee=22000, application_deadline="Check official website", source_url="https://www.yorku.ca", last_verified_at=datetime.now(timezone.utc)),
        ])
    db.commit()
    if not db.query(ProgramTestRequirement).first():
        programmes = {program.program_name: program for program in db.query(UniversityProgram).all()}
        db.add_all([
            ProgramTestRequirement(program_id=programmes["MSc Advanced Computer Science"].id, test_name="IELTS Academic", minimum_score="Overall 6.5; Writing 6.0", required=True, source_url="https://www.manchester.ac.uk", last_verified_at=datetime.now(timezone.utc)),
            ProgramTestRequirement(program_id=programmes["MSc Computer Science"].id, test_name="IELTS Academic", minimum_score="Overall 6.5; Writing 6.0", required=True, source_url="https://www.yorku.ca", last_verified_at=datetime.now(timezone.utc)),
        ])
        db.add_all([
            Scholarship(university_id=dundee.id if 'dundee' in locals() else None, name="University scholarship information", amount="Varies", eligibility="Check academic merit and programme-specific criteria.", deadline="Check official website", source_url="https://www.dundee.ac.uk", last_verified_at=datetime.now(timezone.utc)),
        ])
        db.commit()
