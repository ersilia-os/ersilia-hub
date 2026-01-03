from typing import Any, Dict, Union

from python_framework.db.dao.objects import DAORecord
from sqlalchemy.engine.row import LegacyRow


class CountRecord(DAORecord):
    count: int

    def __init__(self, result: dict):
        super().__init__(result)

        self.count = result["count"]

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_insert_query_args()

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()


class MapRecord(DAORecord):
    result: dict[str, Any]

    def __init__(self, result: LegacyRow):
        super().__init__(result)

        self.result = {}

        for key, value in result.items():
            self.result[key] = value

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_insert_query_args()

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()
