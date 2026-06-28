from typing import List, Optional, Dict, Any
from app.database import get_db_connection


class NativeEmployeeRepository:
    def __init__(self):
        self.conn = get_db_connection()
        self.cursor = self.conn.cursor()

    def create_employee(self, data: Dict[str, Any]) -> int:
        try:
            # Вставляем сотрудника
            self.cursor.execute("""
                INSERT INTO employees (full_name, email, salary, employee_type, org_unit_id, is_active, current_version)
                VALUES (?, ?, ?, ?, ?, 1, 1)
            """, (
                data['full_name'],
                data['email'],
                data['salary'],
                data['employee_type'],
                data.get('org_unit_id')
            ))
            emp_id = self.cursor.lastrowid

            # Вставляем наследника
            emp_type = data['employee_type']
            if emp_type == 'developer':
                self.cursor.execute("""
                    INSERT INTO developers (employee_id, programming_language, github_username, years_of_experience, framework)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    emp_id,
                    data.get('programming_language', 'Python'),
                    data.get('github_username'),
                    data.get('years_of_experience', 0),
                    data.get('framework')
                ))
            elif emp_type == 'manager':
                self.cursor.execute("""
                    INSERT INTO managers (employee_id, team_size, budget, bonus_percent, managed_department_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    emp_id,
                    data.get('team_size', 0),
                    data.get('budget'),
                    data.get('bonus_percent', 0),
                    data.get('managed_department_id')
                ))
            elif emp_type == 'designer':
                self.cursor.execute("""
                    INSERT INTO designers (employee_id, design_tool, portfolio_url, specialization)
                    VALUES (?, ?, ?, ?)
                """, (
                    emp_id,
                    data.get('design_tool'),
                    data.get('portfolio_url'),
                    data.get('specialization')
                ))

            # Создаем версию
            self.cursor.execute("""
                INSERT INTO employee_versions (employee_id, version_number, full_name, email, salary, employee_type, changed_by)
                VALUES (?, 1, ?, ?, ?, ?, 'system')
            """, (
                emp_id,
                data['full_name'],
                data['email'],
                data['salary'],
                data['employee_type']
            ))

            self.conn.commit()
            return emp_id
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_employee(self, emp_id: int, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        try:
            if version:
                self.cursor.execute("""
                    SELECT * FROM employee_versions
                    WHERE employee_id = ? AND version_number = ?
                """, (emp_id, version))
                row = self.cursor.fetchone()
                if not row:
                    return None
                return {
                    'id': emp_id,
                    'full_name': row[3],
                    'email': row[4],
                    'salary': row[5],
                    'employee_type': row[6],
                    'is_version': True,
                    'version_number': version
                }

            self.cursor.execute("""
                SELECT e.id, e.full_name, e.email, e.salary, e.employee_type,
                       e.org_unit_id, e.is_active, e.current_version,
                       d.programming_language, d.github_username, d.years_of_experience, d.framework,
                       m.team_size, m.budget, m.bonus_percent, m.managed_department_id,
                       ds.design_tool, ds.portfolio_url, ds.specialization
                FROM employees e
                LEFT JOIN developers d ON d.employee_id = e.id
                LEFT JOIN managers m ON m.employee_id = e.id
                LEFT JOIN designers ds ON ds.employee_id = e.id
                WHERE e.id = ?
            """, (emp_id,))
            row = self.cursor.fetchone()
            if not row:
                return None

            result = {
                'id': row[0],
                'full_name': row[1],
                'email': row[2],
                'salary': row[3],
                'employee_type': row[4],
                'org_unit_id': row[5],
                'is_active': row[6],
                'current_version': row[7]
            }

            if row[4] == 'developer':
                result['type_details'] = {
                    'programming_language': row[8],
                    'github_username': row[9],
                    'years_of_experience': row[10],
                    'framework': row[11]
                }
            elif row[4] == 'manager':
                result['type_details'] = {
                    'team_size': row[12],
                    'budget': row[13],
                    'bonus_percent': row[14],
                    'managed_department_id': row[15]
                }
            elif row[4] == 'designer':
                result['type_details'] = {
                    'design_tool': row[16],
                    'portfolio_url': row[17],
                    'specialization': row[18]
                }

            return result
        except Exception as e:
            raise e

    def get_all_employees(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        try:
            query = """
                SELECT id, full_name, email, salary, employee_type, current_version
                FROM employees
                WHERE is_active = 1
            """
            params = []

            if filters:
                if filters.get('search'):
                    query += " AND (full_name LIKE ? OR email LIKE ?)"
                    search = f"%{filters['search']}%"
                    params.extend([search, search])
                if filters.get('employee_type'):
                    query += " AND employee_type = ?"
                    params.append(filters['employee_type'])

            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()

            return [{
                'id': r[0],
                'full_name': r[1],
                'email': r[2],
                'salary': r[3],
                'employee_type': r[4],
                'current_version': r[5]
            } for r in rows]
        except Exception as e:
            raise e

    def update_employee(self, emp_id: int, data: Dict[str, Any]) -> int:
        try:
            # Обновляем основные поля
            for key, val in data.items():
                if key in ['full_name', 'email', 'salary']:
                    self.cursor.execute(f"UPDATE employees SET {key} = ? WHERE id = ?", (val, emp_id))

            # Определяем тип сотрудника
            self.cursor.execute("SELECT employee_type FROM employees WHERE id = ?", (emp_id,))
            emp_type = self.cursor.fetchone()[0]

            # Обновляем поля наследника
            if emp_type == 'developer':
                for key in ['programming_language', 'github_username', 'years_of_experience', 'framework']:
                    if key in data:
                        self.cursor.execute(f"UPDATE developers SET {key} = ? WHERE employee_id = ?",
                                            (data[key], emp_id))
            elif emp_type == 'manager':
                for key in ['team_size', 'budget', 'bonus_percent', 'managed_department_id']:
                    if key in data:
                        self.cursor.execute(f"UPDATE managers SET {key} = ? WHERE employee_id = ?", (data[key], emp_id))
            elif emp_type == 'designer':
                for key in ['design_tool', 'portfolio_url', 'specialization']:
                    if key in data:
                        self.cursor.execute(f"UPDATE designers SET {key} = ? WHERE employee_id = ?",
                                            (data[key], emp_id))

            # Получаем текущие данные для версии
            self.cursor.execute("SELECT full_name, email, salary, employee_type FROM employees WHERE id = ?", (emp_id,))
            emp_data = self.cursor.fetchone()

            # Увеличиваем номер версии
            self.cursor.execute("UPDATE employees SET current_version = current_version + 1 WHERE id = ?", (emp_id,))
            self.cursor.execute("SELECT current_version FROM employees WHERE id = ?", (emp_id,))
            new_version = self.cursor.fetchone()[0]

            # Создаем версию
            self.cursor.execute("""
                INSERT INTO employee_versions (employee_id, version_number, full_name, email, salary, employee_type, changed_by)
                VALUES (?, ?, ?, ?, ?, ?, 'user')
            """, (emp_id, new_version, emp_data[0], emp_data[1], emp_data[2], emp_data[3]))

            self.conn.commit()
            return new_version
        except Exception as e:
            self.conn.rollback()
            raise e

    def delete_employee(self, emp_id: int) -> bool:
        try:
            self.cursor.execute("UPDATE employees SET is_active = 0 WHERE id = ?", (emp_id,))
            if self.cursor.rowcount == 0:
                return False
            self.conn.commit()
            return True
        except Exception as e:
            self.conn.rollback()
            raise e

    def get_versions(self, emp_id: int) -> List[Dict[str, Any]]:
        try:
            self.cursor.execute("""
                SELECT * FROM employee_versions
                WHERE employee_id = ?
                ORDER BY version_number DESC
            """, (emp_id,))
            rows = self.cursor.fetchall()
            return [{
                'version_number': r[2],
                'full_name': r[3],
                'email': r[4],
                'salary': r[5],
                'employee_type': r[6],
                'changed_at': r[7],
                'changed_by': r[8]
            } for r in rows]
        except Exception as e:
            raise e

    def get_all_org_units(self) -> List[Dict[str, Any]]:
        """Получить все подразделения"""
        try:
            self.cursor.execute("""
                SELECT id, name, unit_type, parent_id 
                FROM org_units
                ORDER BY id
            """)
            rows = self.cursor.fetchall()
            return [{
                'id': r[0],
                'name': r[1],
                'unit_type': r[2],
                'parent_id': r[3]
            } for r in rows]
        except Exception as e:
            raise e

    def create_org_unit(self, data: Dict[str, Any]) -> int:
        """Создать подразделение"""
        try:
            self.cursor.execute("""
                INSERT INTO org_units (name, unit_type, parent_id)
                VALUES (?, ?, ?)
            """, (data['name'], data['unit_type'], data.get('parent_id')))
            self.conn.commit()
            return self.cursor.lastrowid
        except Exception as e:
            self.conn.rollback()
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
        if hasattr(self, 'cursor'):
            self.cursor.close()
        if hasattr(self, 'conn'):
            self.conn.close()