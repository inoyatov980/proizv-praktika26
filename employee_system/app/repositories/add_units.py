from app.database import engine
from app.models import OrgUnit
from sqlalchemy.orm import Session

db = Session(bind=engine)

units = [
    OrgUnit(name="ООО \"ТехноПарк\"", unit_type="enterprise", parent_id=None),
    OrgUnit(name="IT Департамент", unit_type="department", parent_id=1),
    OrgUnit(name="Отдел разработки", unit_type="subdepartment", parent_id=2),
    OrgUnit(name="Отдел тестирования", unit_type="subdepartment", parent_id=2),
    OrgUnit(name="Департамент маркетинга", unit_type="department", parent_id=1),
    OrgUnit(name="HR Департамент", unit_type="department", parent_id=1),
    OrgUnit(name="Команда бэкенда", unit_type="team", parent_id=3),
    OrgUnit(name="Команда фронтенда", unit_type="team", parent_id=3),
]

for unit in units:
    db.add(unit)

db.commit()
db.close()
print("✅ Подразделения добавлены!")