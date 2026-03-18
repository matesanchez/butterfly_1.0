from enum import Enum


class DocStatus(str, Enum):
    DISCOVERED = 'DISCOVERED'
    FETCHED = 'FETCHED'
    PARSED = 'PARSED'
    EXTRACTED = 'EXTRACTED'
    LOADED = 'LOADED'
    FAILED = 'FAILED'
