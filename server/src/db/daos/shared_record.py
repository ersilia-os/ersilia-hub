from typing import Dict, Union

from python_framework.db.dao.objects import DAORecord


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


class CountMapRecord(DAORecord):
    counts: dict[str, int]

    def __init__(self, result: dict[str, int]):
        super().__init__(result)

        self.counts = {}

        for key, value in result:
            if key.startswith("count_"):
                self.counts[key.replace("count_", "")] = int(value)
            elif type(value) == int:
                self.counts[key] = int(value)

    def generate_insert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_insert_query_args()

    def generate_update_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_update_query_args()

    def generate_upsert_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_upsert_query_args()

    def generate_delete_query_args(self) -> Dict[str, Union[str, int, bool, float]]:
        return super().generate_delete_query_args()
