from sqlalchemy import Column, Integer, String, Boolean, Numeric, ForeignKey, Text, Date, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class OrgUnit(Base):
    __tablename__ = 'org_units'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    unit_type = Column(String(50), nullable=False)  # enterprise, department, subdepartment, team
    parent_id = Column(Integer, ForeignKey('org_units.id'))

    children = relationship("OrgUnit", backref="parent", remote_side=[id])


class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True)
    full_name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True)
    salary = Column(Numeric(10, 2))
    employee_type = Column(String(50), nullable=False)  # developer, manager, designer
    org_unit_id = Column(Integer, ForeignKey('org_units.id'))
    is_active = Column(Boolean, default=True)
    current_version = Column(Integer, default=1)

    org_unit = relationship("OrgUnit")

    # Связи с наследниками
    developer = relationship("Developer", back_populates="employee", uselist=False)
    manager = relationship("Manager", back_populates="employee", uselist=False)
    designer = relationship("Designer", back_populates="employee", uselist=False)


class Developer(Base):
    __tablename__ = 'developers'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), unique=True)
    programming_language = Column(String(100), nullable=False)
    github_username = Column(String(100))
    years_of_experience = Column(Integer, default=0)
    framework = Column(String(100))

    employee = relationship("Employee", back_populates="developer")


class Manager(Base):
    __tablename__ = 'managers'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), unique=True)
    team_size = Column(Integer, default=0)
    budget = Column(Numeric(12, 2))
    bonus_percent = Column(Numeric(5, 2), default=0)
    managed_department_id = Column(Integer, ForeignKey('org_units.id'))

    employee = relationship("Employee", back_populates="manager")


class Designer(Base):
    __tablename__ = 'designers'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id', ondelete='CASCADE'), unique=True)
    design_tool = Column(String(100))
    portfolio_url = Column(Text)
    specialization = Column(String(100))

    employee = relationship("Employee", back_populates="designer")


class EmployeeVersion(Base):
    __tablename__ = 'employee_versions'
    id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey('employees.id'))
    version_number = Column(Integer, nullable=False)
    full_name = Column(String(255))
    email = Column(String(255))
    salary = Column(Numeric(10, 2))
    employee_type = Column(String(50))
    changed_at = Column(DateTime, default=datetime.utcnow)
    changed_by = Column(String(100), default='system')

    employee = relationship("Employee", backref="versions")