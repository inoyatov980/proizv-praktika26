from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from typing import List, Optional, Dict, Any
from app.database import engine
from app.models import Employee, Developer, Manager, Designer, EmployeeVersion, OrgUnit
from app.repositories.base import EmployeeRepository


class ORMEmployeeRepository:
    def __init__(self):
        self.session: Session = Session(bind=engine)

    def create_employee(self, data: Dict[str, Any]) -> int:
        try:
            # Создаем базового сотрудника
            emp = Employee(
                full_name=data['full_name'],
                email=data['email'],
                salary=data['salary'],
                employee_type=data['employee_type'],
                org_unit_id=data.get('org_unit_id'),
                is_active=True,
                current_version=1
            )
            self.session.add(emp)
            self.session.flush()

            # Создаем наследника в зависимости от типа
            emp_type = data['employee_type']
            if emp_type == 'developer':
                dev = Developer(
                    employee_id=emp.id,
                    programming_language=data.get('programming_language', 'Python'),
                    github_username=data.get('github_username'),
                    years_of_experience=data.get('years_of_experience', 0),
                    framework=data.get('framework')
                )
                self.session.add(dev)
            elif emp_type == 'manager':
                mgr = Manager(
                    employee_id=emp.id,
                    team_size=data.get('team_size', 0),
                    budget=data.get('budget'),
                    bonus_percent=data.get('bonus_percent', 0),
                    managed_department_id=data.get('managed_department_id')
                )
                self.session.add(mgr)
            elif emp_type == 'designer':
                dsgn = Designer(
                    employee_id=emp.id,
                    design_tool=data.get('design_tool'),
                    portfolio_url=data.get('portfolio_url'),
                    specialization=data.get('specialization')
                )
                self.session.add(dsgn)

            # Создаем первую версию
            version = EmployeeVersion(
                employee_id=emp.id,
                version_number=1,
                full_name=data['full_name'],
                email=data['email'],
                salary=data['salary'],
                employee_type=data['employee_type'],
                changed_by='system'
            )
            self.session.add(version)

            self.session.commit()
            return emp.id
        except Exception as e:
            self.session.rollback()
            raise e

    def get_employee(self, emp_id: int, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        try:
            if version:
                v = self.session.query(EmployeeVersion).filter(
                    EmployeeVersion.employee_id == emp_id,
                    EmployeeVersion.version_number == version
                ).first()
                if not v:
                    return None
                return {
                    'id': emp_id,
                    'full_name': v.full_name,
                    'email': v.email,
                    'salary': float(v.salary) if v.salary else 0,
                    'employee_type': v.employee_type,
                    'is_version': True,
                    'version_number': version
                }

            emp = self.session.query(Employee).filter(Employee.id == emp_id).first()
            if not emp:
                return None

            result = {
                'id': emp.id,
                'full_name': emp.full_name,
                'email': emp.email,
                'salary': float(emp.salary) if emp.salary else 0,
                'employee_type': emp.employee_type,
                'org_unit_id': emp.org_unit_id,
                'is_active': emp.is_active,
                'current_version': emp.current_version
            }

            # Добавляем данные наследника
            if emp.employee_type == 'developer' and emp.developer:
                result['type_details'] = {
                    'programming_language': emp.developer.programming_language,
                    'github_username': emp.developer.github_username,
                    'years_of_experience': emp.developer.years_of_experience,
                    'framework': emp.developer.framework
                }
            elif emp.employee_type == 'manager' and emp.manager:
                result['type_details'] = {
                    'team_size': emp.manager.team_size,
                    'budget': float(emp.manager.budget) if emp.manager.budget else None,
                    'bonus_percent': float(emp.manager.bonus_percent) if emp.manager.bonus_percent else 0,
                    'managed_department_id': emp.manager.managed_department_id
                }
            elif emp.employee_type == 'designer' and emp.designer:
                result['type_details'] = {
                    'design_tool': emp.designer.design_tool,
                    'portfolio_url': emp.designer.portfolio_url,
                    'specialization': emp.designer.specialization
                }

            return result
        except Exception as e:
            raise e

    def get_all_employees(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        try:
            query = self.session.query(Employee).filter(Employee.is_active == True)

            if filters:
                if filters.get('search'):
                    query = query.filter(
                        or_(
                            Employee.full_name.ilike(f"%{filters['search']}%"),
                            Employee.email.ilike(f"%{filters['search']}%")
                        )
                    )
                if filters.get('employee_type'):
                    query = query.filter(Employee.employee_type == filters['employee_type'])

            employees = query.all()
            result = []
            for emp in employees:
                result.append({
                    'id': emp.id,
                    'full_name': emp.full_name,
                    'email': emp.email,
                    'salary': float(emp.salary) if emp.salary else 0,
                    'employee_type': emp.employee_type,
                    'current_version': emp.current_version
                })
            return result
        except Exception as e:
            raise e

    def update_employee(self, emp_id: int, data: Dict[str, Any]) -> int:
        try:
            emp = self.session.query(Employee).filter(Employee.id == emp_id).first()
            if not emp:
                raise ValueError("Employee not found")

            # Обновляем основные поля
            for key, val in data.items():
                if hasattr(emp, key) and key not in ['employee_type', 'programming_language',
                                                     'github_username', 'years_of_experience', 'framework', 'team_size',
                                                     'budget',
                                                     'bonus_percent', 'managed_department_id', 'design_tool',
                                                     'portfolio_url', 'specialization']:
                    setattr(emp, key, val)

            # Обновляем поля наследника
            if emp.employee_type == 'developer' and emp.developer:
                for f in ['programming_language', 'github_username', 'years_of_experience', 'framework']:
                    if f in data:
                        setattr(emp.developer, f, data[f])
            elif emp.employee_type == 'manager' and emp.manager:
                for f in ['team_size', 'budget', 'bonus_percent', 'managed_department_id']:
                    if f in data:
                        setattr(emp.manager, f, data[f])
            elif emp.employee_type == 'designer' and emp.designer:
                for f in ['design_tool', 'portfolio_url', 'specialization']:
                    if f in data:
                        setattr(emp.designer, f, data[f])

            # Создаем новую версию
            emp.current_version += 1
            version = EmployeeVersion(
                employee_id=emp.id,
                version_number=emp.current_version,
                full_name=emp.full_name,
                email=emp.email,
                salary=emp.salary,
                employee_type=emp.employee_type,
                changed_by='user'
            )
            self.session.add(version)

            self.session.commit()
            return emp.current_version
        except Exception as e:
            self.session.rollback()
            raise e

    def delete_employee(self, emp_id: int) -> bool:
        try:
            emp = self.session.query(Employee).filter(Employee.id == emp_id).first()
            if not emp:
                return False
            emp.is_active = False
            self.session.commit()
            return True
        except Exception as e:
            self.session.rollback()
            raise e

    def get_versions(self, emp_id: int) -> List[Dict[str, Any]]:
        try:
            versions = self.session.query(EmployeeVersion).filter(
                EmployeeVersion.employee_id == emp_id
            ).order_by(EmployeeVersion.version_number.desc()).all()

            return [{
                'version_number': v.version_number,
                'full_name': v.full_name,
                'email': v.email,
                'salary': float(v.salary) if v.salary else 0,
                'employee_type': v.employee_type,
                'changed_at': v.changed_at,
                'changed_by': v.changed_by
            } for v in versions]
        except Exception as e:
            raise e

    def get_all_org_units(self) -> List[Dict[str, Any]]:
        """Получить все подразделения"""
        try:
            units = self.session.query(OrgUnit).all()
            return [{
                'id': u.id,
                'name': u.name,
                'unit_type': u.unit_type,
                'parent_id': u.parent_id
            } for u in units]
        except Exception as e:
            raise e

    def create_org_unit(self, data: Dict[str, Any]) -> int:
        """Создать подразделение"""
        try:
            unit = OrgUnit(
                name=data['name'],
                unit_type=data['unit_type'],
                parent_id=data.get('parent_id')
            )
            self.session.add(unit)
            self.session.commit()
            return unit.id
        except Exception as e:
            self.session.rollback()
            raise e

    def get_org_tree(self) -> List[Dict[str, Any]]:
        """Получить дерево подразделений"""
        try:
            units = self.get_all_org_units()
            return self._build_tree_from_list(units)
        except Exception as e:
            raise e

    def _build_tree_from_list(self, units, parent_id=None):
        """Строит дерево из списка подразделений"""
        result = []
        for unit in units:
            if unit.get('parent_id') == parent_id:
                children = self._build_tree_from_list(units, unit.get('id'))
                unit_data = {
                    'id': unit.get('id'),
                    'name': unit.get('name'),
                    'unit_type': unit.get('unit_type'),
                    'children': children
                }
                result.append(unit_data)
        return result

    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()