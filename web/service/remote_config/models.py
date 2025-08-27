from pydantic import BaseModel, field_validator
from typing import Any
from enum import IntEnum


class APIResponse(BaseModel):
    code: int
    msg: str


class APIResponseWithData(APIResponse):
    data: Any


class TenantAccessToken(APIResponse):
    tenant_access_token: str
    expire: int


class Table(BaseModel):
    name: str
    revision: int
    table_id: str


class TableView(BaseModel):
    view_id: str
    view_name: str
    view_public_level: str
    view_type: str


class TableViewRecordFieldType(IntEnum):
    text = 1
    number = 2


class TableViewRecordField(BaseModel):
    name: str
    value: Any

    @property
    def text(self) -> str:
        return self.value[0]["text"]

    @property
    def int(self) -> int:
        return int(self.value)
    
    @property
    def url(self) -> str:
        return self.value[0]["url"]
    
    @property
    def media_type(self) -> str:
        return self.value[0]["type"]
    
    @property
    def link_ids(self) -> list[str]:
        return self.value["link_record_ids"]


class TableViewRecord(BaseModel):
    record_id: str
    fields: dict[str, TableViewRecordField]

    @field_validator("fields", mode="before")
    def parse_fields(cls, v: Any) -> Any:
        fields: dict[str, TableViewRecordField] = {}
        for k in v:
            f = TableViewRecordField(name=k, value=v[k])
            fields[k] = f
        return fields


class Pageable(BaseModel):
    has_more: bool = False
    page_token: str = ""
    total: int = 0


class ListTablesData(Pageable):
    items: list[Table]


class ListViewsData(Pageable):
    items: list[TableView]


class ListRecordsData(Pageable):
    items: list[TableViewRecord]
