from time import sleep, time
from typing import Any, Dict, List, Type, Union
from abc import ABC, abstractmethod


class NodeData(ABC):

    timestamp: float

    def __init__(self, timestamp: float):
        super().__init__()

        self.timestamp = timestamp

    @abstractmethod
    def data(self) -> Any:
        pass

    @abstractmethod
    def repr_data(self) -> str:
        pass

    def __repr__(self) -> str:
        return f"({self.timestamp:.3f} - {self.repr_data()})"

    def __lt__(self, other: Union["NodeData", float]) -> bool:
        if isinstance(other, float):
            return self.timestamp < other

        return self.timestamp < other.timestamp

    def __le__(self, other: Union["NodeData", float]) -> bool:
        if isinstance(other, float):
            return self.timestamp <= other

        return self.timestamp <= other.timestamp

    def __gt__(self, other: Union["NodeData", float]) -> bool:
        if isinstance(other, float):
            return self.timestamp > other

        return self.timestamp > other.timestamp

    def __ge__(self, other: Union["NodeData", float]) -> bool:
        if isinstance(other, float):
            return self.timestamp >= other

        return self.timestamp >= other.timestamp

    def __eq__(self, other: Union["NodeData", float]) -> bool:
        if isinstance(other, float):
            return self.timestamp == other

        return self.timestamp == other.timestamp


class LinkedNode:

    previous_node: Union["LinkedNode", None]
    next_node: Union["LinkedNode", None]
    data: Type[NodeData]

    def __init__(
        self,
        data: Type[NodeData],
        previous_node: Union["LinkedNode", None] = None,
        next_node: Union["LinkedNode", None] = None,
    ) -> None:
        self.data = data
        self.previous_node = previous_node
        self.next_node = next_node


class DataBuffer:
    """
    Linked list of [first_node .... last_node].
    """

    _max_age: int
    _size: int

    _first_node: LinkedNode
    _last_node: LinkedNode
    # nodes by second into the buffer, up to 10min; only every 30s
    _indexed_nodes: Dict[int, LinkedNode]
    _remaining_indexes: List[int]

    def __init__(self, max_age: int = 600) -> None:
        self._max_age = max_age
        self._size = 0

        self._first_node = None
        self._last_node = None
        self._indexed_nodes = {}
        self._remaining_indexes = [i * 30 for i in range(1, 20)]

    def __repr__(self) -> str:
        repr_str = "\n=== DataBuffer ===\n\n"
        repr_str += "size = [%d]\n" % self._size
        repr_str += "first_node = [%s]\n" % (
            "NONE" if self._first_node is None else repr(self._first_node.data)
        )
        repr_str += "last_node = [%s]\n" % (
            "NONE" if self._last_node is None else repr(self._last_node.data)
        )

        indexed_nodes_str = ""

        for index, node in self._indexed_nodes.items():
            indexed_nodes_str += "\n  - (i=%d, v=%s)" % (
                index,
                ("NONE" if node is None else repr(node.data)),
            )

        repr_str += "indexed nodes = [%s]\n" % indexed_nodes_str
        repr_str += "remaining indexes = [%s]\n" % self._remaining_indexes
        repr_str += "\n===============\n"

        return repr_str

    def size(self) -> int:
        return self._size

    def append(self, data: NodeData):
        if self._last_node is None and self._first_node is None:
            self._first_node = LinkedNode(data)
            self._last_node = self._first_node

            return

        if self._last_node.data <= data:
            old_last_node = self._last_node
            self._last_node = LinkedNode(data, previous_node=old_last_node)
            old_last_node.next_node = self._last_node
        else:
            index_after_node = self.at_time(data.timestamp)

            if index_after_node is None:
                return

            new_node = LinkedNode(
                data,
                previous_node=index_after_node,
                next_node=index_after_node.next_node,
            )

            if index_after_node.next_node is not None:
                index_after_node.next_node.previous_node = new_node

            index_after_node.next_node = new_node

        self._size += 1

        self._index_first_node()
        self._shift_indexed_nodes()
        self._dequeue_aged_nodes()

    def dequeue(self) -> LinkedNode:
        if self._first_node is None or self._first_node.next_node is None:
            return

        prev_first_node = self._first_node
        self._first_node = prev_first_node.next_node
        self._first_node.previous_node = None

        # make sure we remove the reference
        prev_first_node.next_node = None

        self._size -= 1

        # TODO: make sure it's not one of the indexed_nodes (edge case)

        return prev_first_node

    def _dequeue_aged_nodes(self):
        old_age = self._last_node.data.timestamp - self._max_age

        while (
            self._first_node is not None and self._first_node.data.timestamp < old_age
        ):
            self.dequeue()

    def _shift_indexed_nodes(self):
        current_time = self._last_node.data.timestamp

        for index, node in self._indexed_nodes.items():
            indexed_time = current_time - index
            new_node = self._scan_from(node, indexed_time)
            self._indexed_nodes[index] = new_node

    def _index_first_node(self):
        if len(self._remaining_indexes) == 0:
            return

        current_time = self._last_node.data.timestamp
        new_remaining_indexes: List[int] = []

        for index in self._remaining_indexes:
            if self._first_node.data <= current_time - index:
                self._indexed_nodes[index] = self._first_node
            else:
                new_remaining_indexes.append(index)

        self._remaining_indexes = new_remaining_indexes

    def first(self) -> LinkedNode:
        return self._first_node

    def last(self) -> LinkedNode:
        return self._last_node

    def _scan_from(self, node: LinkedNode, cmp_to: float) -> LinkedNode:
        if node is None:
            return None

        _node = node
        prev_node = node

        while _node is not None and _node.data <= cmp_to:
            prev_node = _node
            _node = _node.next_node

        return prev_node

    def _scan_from_reversed(self, node: LinkedNode, cmp_to: float) -> LinkedNode:
        if node is None:
            return None

        _node = node
        prev_node = node

        while _node is not None and _node.data >= cmp_to:
            prev_node = _node
            _node = _node.previous_node

        return prev_node

    def at_time(self, time_index: float) -> LinkedNode:
        if self._last_node is None:
            return None

        current_time = self._last_node.data.timestamp
        closest_index = -1
        closest_node = None

        if len(self._indexed_nodes) == 0:
            closest_node = self._first_node
        else:
            for index, node in self._indexed_nodes.items():
                if time_index >= current_time - index:
                    if closest_index == -1 or closest_index > index:
                        closest_index = index
                        closest_node = node

        return self._scan_from(closest_node, time_index)

    def slice(self, seconds: int):
        if self._last_node is None:
            return

        slice_time = self._last_node.data.timestamp - seconds
        node = self.at_time(slice_time)

        while node is not None:
            yield node
            node = node.next_node

    def slice_values(self, seconds: int):
        for node in self.slice(seconds):
            yield node.data

    def _is_indexed_node(self, node: LinkedNode) -> bool:
        for i_node in self._indexed_nodes.values():
            if node.data == i_node.data:
                return True

    def debug(self):
        node = self.first()

        while node is not None:
            if self._is_indexed_node(node):
                print(f"{repr(node.data)} *")
            else:
                print(repr(node.data))

            node = node.next_node


class TestDatum(NodeData):

    timestamp: float
    _data: int

    def __init__(self, timestamp: float, data: int):
        super().__init__(timestamp)
        self._data = data

    def data(self) -> Any:
        return self._data

    def repr_data(self) -> str:
        return str(self._data)


if __name__ == "__main__":
    buffer = DataBuffer()
    counter = 0

    while True:
        buffer.append(TestDatum(time(), counter))
        counter += 1

        buffer.debug()
        print()

        total_30s = 0
        count_30s = 0
        max_30s = -1
        min_30s = -1

        for x in buffer.slice_values(30):
            count_30s += 1
            total_30s += x.data()

            if max_30s == -1 or x.data() > max_30s:
                max_30s = x.data()

            if min_30s == -1 or x.data() < min_30s:
                min_30s = x.data()

        print("total 30s = ", total_30s)
        print("min 30s = ", min_30s)
        print("max 30s = ", max_30s)
        print("avg 30s = ", (total_30s / count_30s))

        print("\n\n")

        sleep(3)
