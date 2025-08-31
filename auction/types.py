from typing import Protocol


class Archivable(Protocol):
    is_archived: bool
    is_deleted: bool
