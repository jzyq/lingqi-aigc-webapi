from typing import Annotated
from fastapi import Header

HeaderField = Annotated[str, Header()]
