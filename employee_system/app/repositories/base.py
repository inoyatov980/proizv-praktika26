from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any


class EmployeeRepository(ABC):
    @abstractmethod
    def create_employee(self, data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def get_employee(self, emp_id: int, version: Optional[int] = None) -> Optional[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_all_employees(self, filters: Optional[Dict] = None) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def update_employee(self, emp_id: int, data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def delete_employee(self, emp_id: int) -> bool:
        pass

    @abstractmethod
    def get_versions(self, emp_id: int) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_all_org_units(self) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def create_org_unit(self, data: Dict[str, Any]) -> int:
        pass

    @abstractmethod
    def get_org_tree(self) -> List[Dict[str, Any]]:
        pass