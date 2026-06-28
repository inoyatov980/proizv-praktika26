from fastapi import FastAPI, Request, Form, Query, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from typing import Optional, List, Dict, Any
import os

from app.database import engine
from app.models import Base, Employee, OrgUnit, EmployeeVersion
from sqlalchemy.orm import Session
from datetime import datetime

# Создаем таблицы
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Employee System")

# Шаблоны
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "templates"))

# Простой HTML без сложных структур
SIMPLE_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Система учета сотрудников</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body { font-family: 'Segoe UI', Arial, sans-serif; background: #f0f2f5; padding: 20px; }
        .container { max-width: 1400px; margin: 0 auto; }
        h1 { text-align: center; color: #1a73e8; margin-bottom: 20px; }

        .grid { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
        .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }
        .card-full { grid-column: 1 / -1; }
        .card h2 { font-size: 18px; border-bottom: 2px solid #1a73e8; padding-bottom: 10px; margin-top: 0; margin-bottom: 15px; }

        .form-group { margin-bottom: 12px; }
        label { display: block; font-weight: 600; font-size: 14px; margin-bottom: 4px; }
        input, select { width: 100%; padding: 8px 10px; border: 1px solid #ddd; border-radius: 5px; font-size: 14px; }
        input:focus, select:focus { outline: none; border-color: #1a73e8; }

        button, .btn { background: #1a73e8; color: white; padding: 8px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 14px; text-decoration: none; display: inline-block; }
        .btn-danger { background: #dc3545; }
        .btn-success { background: #28a745; }
        .btn-sm { padding: 4px 12px; font-size: 12px; }

        table { width: 100%; border-collapse: collapse; font-size: 14px; }
        th, td { padding: 10px; text-align: left; border-bottom: 1px solid #eee; }
        th { background: #f8f9fa; font-weight: 600; }
        tr:hover { background: #f8f9fa; }

        .badge { display: inline-block; padding: 2px 12px; border-radius: 12px; font-size: 12px; color: white; }
        .badge-developer { background: #17a2b8; }
        .badge-manager { background: #28a745; }
        .badge-designer { background: #6f42c1; }
        .badge-version { background: #ffc107; color: #333; }

        .tree { margin-top: 10px; font-size: 14px; }
        .tree-item { padding: 5px 0; }
        .tree-item .name { font-weight: 600; }
        .tree-item .type { color: #6c757d; font-size: 12px; }
        .tree-children { margin-left: 20px; padding-left: 15px; border-left: 2px solid #1a73e8; }

        .versions-list { max-height: 300px; overflow-y: auto; }
        .version-item { padding: 8px 12px; margin: 4px 0; background: #f8f9fa; border-radius: 5px; border-left: 3px solid #1a73e8; }
        .version-current { background: #d4edda; border-left-color: #28a745; }

        .details { background: #e8f0fe; padding: 15px; border-radius: 8px; line-height: 1.8; }
        .flex { display: flex; gap: 10px; flex-wrap: wrap; align-items: center; }
        .mt-10 { margin-top: 10px; }
        .mb-10 { margin-bottom: 10px; }
        .text-muted { color: #6c757d; }
        .search-form { display: flex; gap: 10px; flex-wrap: wrap; }
        .search-form input, .search-form select { width: auto; flex: 1; min-width: 150px; }

        @media (max-width: 768px) { .grid { grid-template-columns: 1fr; } }
    </style>
</head>
<body>
<div class="container">
    <h1>👔 Система учета сотрудников</h1>

    <div class="grid">
        <!-- Форма создания сотрудника -->
        <div class="card">
            <h2>➕ Добавить сотрудника</h2>
            <form action="/add" method="post">
                <div class="form-group">
                    <label>ФИО *</label>
                    <input type="text" name="full_name" required>
                </div>
                <div class="form-group">
                    <label>Email *</label>
                    <input type="email" name="email" required>
                </div>
                <div class="form-group">
                    <label>Зарплата *</label>
                    <input type="number" name="salary" step="0.01" required>
                </div>
                <div class="form-group">
                    <label>Тип сотрудника</label>
                    <select name="employee_type" id="empType" onchange="toggleFields()">
                        <option value="developer">Разработчик</option>
                        <option value="manager">Менеджер</option>
                        <option value="designer">Дизайнер</option>
                    </select>
                </div>
                <div id="devFields">
                    <div class="form-group">
                        <label>Язык программирования</label>
                        <input type="text" name="programming_language" value="Python">
                    </div>
                    <div class="form-group">
                        <label>GitHub</label>
                        <input type="text" name="github_username">
                    </div>
                    <div class="form-group">
                        <label>Опыт (лет)</label>
                        <input type="number" name="years_of_experience" value="0">
                    </div>
                </div>
                <div class="form-group">
                    <label>Подразделение</label>
                    <select name="org_unit_id">
                        <option value="">Без подразделения</option>
                        {% for unit in org_units %}
                        <option value="{{ unit.id }}">{{ unit.name }}</option>
                        {% endfor %}
                    </select>
                </div>
                <button type="submit">Создать</button>
            </form>
            {% if error %}
            <div style="background:#f8d7da; color:#721c24; padding:10px; border-radius:5px; margin-top:10px;">
                ❌ Ошибка: {{ error }}
            </div>
            {% endif %}
        </div>

        <!-- Список сотрудников -->
        <div class="card">
            <h2>📋 Список сотрудников</h2>
            <form action="/" method="get" class="search-form">
                <input type="text" name="search" placeholder="Поиск..." value="{{ search or '' }}">
                <select name="employee_type">
                    <option value="">Все типы</option>
                    <option value="developer" {% if employee_type == 'developer' %}selected{% endif %}>Разработчик</option>
                    <option value="manager" {% if employee_type == 'manager' %}selected{% endif %}>Менеджер</option>
                    <option value="designer" {% if employee_type == 'designer' %}selected{% endif %}>Дизайнер</option>
                </select>
                <button type="submit">🔍</button>
                <a href="/" class="btn" style="background:#6c757d;">Сброс</a>
            </form>

            {% if employees %}
            <table>
                <thead>
                    <tr>
                        <th>ФИО</th>
                        <th>Email</th>
                        <th>Тип</th>
                        <th>Зарплата</th>
                        <th>Версия</th>
                        <th></th>
                    </tr>
                </thead>
                <tbody>
                    {% for e in employees %}
                    <tr>
                        <td>{{ e.full_name }}</td>
                        <td>{{ e.email }}</td>
                        <td><span class="badge badge-{{ e.employee_type }}">{{ e.employee_type }}</span></td>
                        <td>{{ e.salary }}</td>
                        <td><span class="badge badge-version">v{{ e.current_version }}</span></td>
                        <td>
                            <a href="/delete/{{ e.id }}" class="btn btn-sm btn-danger" onclick="return confirm('Удалить сотрудника?')">❌</a>
                        </td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% else %}
            <p class="text-muted">Нет сотрудников</p>
            {% endif %}
        </div>

        <!-- Организационная структура -->
        <div class="card card-full">
            <h2>🏢 Организационная структура</h2>

            <div style="margin-bottom: 15px;">
                <h4 style="margin-bottom: 10px;">Добавить подразделение</h4>
                <form action="/add_unit" method="post" class="flex" style="gap:10px;">
                    <input type="text" name="name" placeholder="Название" required style="flex:1;">
                    <select name="unit_type" required>
                        <option value="enterprise">Предприятие</option>
                        <option value="department">Департамент</option>
                        <option value="subdepartment">Отдел</option>
                        <option value="team">Команда</option>
                    </select>
                    <select name="parent_id" style="flex:1;">
                        <option value="">Корневое</option>
                        {% for unit in org_units %}
                        <option value="{{ unit.id }}">{{ unit.name }}</option>
                        {% endfor %}
                    </select>
                    <button type="submit" class="btn-success">Добавить</button>
                </form>
            </div>

            {% if org_tree %}
            <div class="tree">
                {% for unit in org_tree recursive %}
                <div class="tree-item">
                    <span class="name">{{ unit.name }}</span>
                    <span class="type">({{ unit.unit_type }})</span>
                    {% if unit.children %}
                    <div class="tree-children">
                        {{ loop(unit.children) }}
                    </div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
            {% else %}
            <p class="text-muted">Нет подразделений. Добавьте первое!</p>
            {% endif %}
        </div>
    </div>
</div>

<script>
function toggleFields() {
    const type = document.getElementById('empType').value;
    document.getElementById('devFields').style.display = type === 'developer' ? 'block' : 'none';
}
</script>
</body>
</html>
"""


@app.get("/", response_class=HTMLResponse)
async def index(
        request: Request,
        search: Optional[str] = None,
        employee_type: Optional[str] = None,
        error: Optional[str] = None
):
    db = Session(bind=engine)
    try:
        # Получаем сотрудников
        query = db.query(Employee).filter(Employee.is_active == True)
        if search:
            query = query.filter(Employee.full_name.ilike(f"%{search}%"))
        if employee_type:
            query = query.filter(Employee.employee_type == employee_type)
        employees = query.all()

        # Получаем подразделения
        org_units = db.query(OrgUnit).all()

        # Строим дерево
        org_tree = build_tree(org_units)

        # Преобразуем в простые словари
        employees_data = []
        for emp in employees:
            employees_data.append({
                'id': emp.id,
                'full_name': emp.full_name,
                'email': emp.email,
                'salary': float(emp.salary) if emp.salary else 0,
                'employee_type': emp.employee_type,
                'current_version': emp.current_version
            })

        from jinja2 import Template
        template = Template(SIMPLE_HTML)
        html = template.render(
            employees=employees_data,
            org_units=org_units,
            org_tree=org_tree,
            search=search or '',
            employee_type=employee_type or '',
            error=error
        )
        return HTMLResponse(content=html)
    except Exception as e:
        db.rollback()
        return HTMLResponse(content=f"<h1>Ошибка</h1><p>{str(e)}</p>", status_code=500)
    finally:
        db.close()


@app.post("/add")
async def add_employee(
        full_name: str = Form(...),
        email: str = Form(...),
        salary: float = Form(...),
        employee_type: str = Form("developer"),
        programming_language: Optional[str] = Form("Python"),
        github_username: Optional[str] = Form(""),
        years_of_experience: int = Form(0),
        org_unit_id: Optional[int] = Form(None)
):
    db = Session(bind=engine)
    try:
        # Проверяем, существует ли email
        existing = db.query(Employee).filter(Employee.email == email).first()
        if existing:
            db.close()
            return RedirectResponse(f"/?error=Email%20{email}%20уже%20существует", status_code=303)

        emp = Employee(
            full_name=full_name,
            email=email,
            salary=salary,
            employee_type=employee_type,
            org_unit_id=org_unit_id if org_unit_id else None,
            is_active=True,
            current_version=1
        )
        db.add(emp)
        db.commit()
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        db.rollback()
        return RedirectResponse(f"/?error={str(e)}", status_code=303)
    finally:
        db.close()


@app.post("/add_unit")
async def add_unit(
        name: str = Form(...),
        unit_type: str = Form(...),
        parent_id: Optional[int] = Form(None)
):
    db = Session(bind=engine)
    try:
        unit = OrgUnit(
            name=name,
            unit_type=unit_type,
            parent_id=parent_id if parent_id else None
        )
        db.add(unit)
        db.commit()
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        db.rollback()
        return RedirectResponse(f"/?error={str(e)}", status_code=303)
    finally:
        db.close()


@app.get("/delete/{emp_id}")
async def delete_employee(emp_id: int):
    db = Session(bind=engine)
    try:
        emp = db.query(Employee).filter(Employee.id == emp_id).first()
        if emp:
            emp.is_active = False
            db.commit()
        return RedirectResponse("/", status_code=303)
    except Exception as e:
        db.rollback()
        return RedirectResponse(f"/?error={str(e)}", status_code=303)
    finally:
        db.close()


def build_tree(units, parent_id=None):
    """Строит дерево подразделений"""
    result = []
    for unit in units:
        if unit.parent_id == parent_id:
            children = build_tree(units, unit.id)
            unit_data = {
                'id': unit.id,
                'name': unit.name,
                'unit_type': unit.unit_type,
                'children': children
            }
            result.append(unit_data)
    return result


@app.get("/health")
async def health():
    return {"status": "ok"}