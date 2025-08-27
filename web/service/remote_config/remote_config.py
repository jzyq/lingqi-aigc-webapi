import httpx
from . import models
from datetime import datetime, timedelta
from collections.abc import Iterator


class APIError(Exception):

    def __init__(self, code: int, msg: str, api_url: str) -> None:
        self.code: int = code
        self.msg: str = msg
        self.url: str = api_url

    def __str__(self) -> str:
        return self.msg


class AuthToken:

    def __init__(self, app_id: str, app_secret: str) -> None:
        self._app_id: str = app_id
        self._app_secret: str = app_secret

        self._access_token: str | None = None
        self._expires: datetime | None = None

    def refresh_token(self) -> str:
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        resp = httpx.post(
            url=url, json={"app_id": self._app_id,
                           "app_secret": self._app_secret}
        ).raise_for_status()

        resp = models.TenantAccessToken.model_validate_json(resp.content)
        if resp.code != 0:
            raise APIError(resp.code, resp.msg, url)

        self._access_token = resp.tenant_access_token
        self._expires = datetime.now() + timedelta(seconds=resp.expire)

        return resp.tenant_access_token

    @property
    def token(self) -> str:
        if self._access_token is None:
            return self.refresh_token()

        assert self._expires is not None
        if datetime.now() < self._expires:
            return self._access_token

        return self.refresh_token()

    def __str__(self) -> str:
        return self.token


class Row:

    def __init__(self, metadata: models.TableViewRecord) -> None:
        self._meta: models.TableViewRecord = metadata

        self._cols: dict[str, models.TableViewRecordField] = {}
        for f in self._meta.fields:
            self._cols[f] = self._meta.fields[f]

    @property
    def id(self) -> str:
        return self._meta.record_id

    def col(self, name: str) -> models.TableViewRecordField:
        return self._cols[name]


class View:

    def __init__(self, auth_token: AuthToken, bid: str, tid: str, metadata: models.TableView) -> None:
        self._token: AuthToken = auth_token
        self._bid: str = bid
        self._tid: str = tid
        self._metadata: models.TableView = metadata

        self._records: list[models.TableViewRecord] = self._list_records()

    def _list_records(self) -> list[models.TableViewRecord]:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self._bid}/tables/{self._tid}/records/search"
        resp = httpx.post(
            url=url,
            headers={"authorization": f"bearer {self._token}"},
            json={"view_id": self._metadata.view_id},
        ).raise_for_status()

        resp = models.APIResponseWithData.model_validate_json(resp.content)
        if resp.code != 0:
            raise APIError(resp.code, resp.msg, url)
        return models.ListRecordsData.model_validate(resp.data).items

    def rows(self) -> Iterator[Row]:
        for r in self._records:
            yield Row(r)


class Table:

    def __init__(self, auth_token: AuthToken, bitable_id: str, metadata: models.Table) -> None:
        self._token: AuthToken = auth_token
        self._bitable_id: str = bitable_id
        self._meta: models.Table = metadata
        self._views: list[models.TableView] = self._list_views()

        self._view_index: dict[str, models.TableView] = {}
        for v in self._views:
            self._view_index[v.view_name] = v

    def view(self, key: str) -> View:
        meta = self._view_index[key]
        return View(self._token, self._bitable_id, self._meta.table_id, meta)

    # list views in a table.
    def _list_views(self) -> list[models.TableView]:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self._bitable_id}/tables/{self._meta.table_id}/views"
        resp = httpx.get(
            url=url,
            headers={
                "authorization": f"bearer {self._token}",
                "content-type": "application/json;charset=utf-8",
            },
        ).raise_for_status()

        resp = models.APIResponseWithData.model_validate_json(resp.content)
        if resp.code != 0:
            raise APIError(resp.code, resp.msg, url)
        return models.ListViewsData.model_validate(resp.data).items


class Bitable:

    def __init__(self, auth_token: AuthToken, table_id: str) -> None:
        self._token: AuthToken = auth_token
        self._node_id: str = self._get_wiki_node(table_id)
        self._tables: list[models.Table] = self._list_tables()

        self._table_index: dict[str, models.Table] = {}
        for t in self._tables:
            self._table_index[t.name] = t

    def table(self, key: str) -> Table:
        meta = self._table_index[key]
        return Table(self._token, self._node_id, meta)

    # Get the actual
    def _get_wiki_node(self, bitable_token: str) -> str:
        url = "https://open.feishu.cn/open-apis/wiki/v2/spaces/get_node"
        resp = httpx.get(
            url=url,
            params={"token": bitable_token},
            headers={"authorization": f"bearer {self._token}"},
        )
        data = resp.json()
        return data["data"]["node"]["obj_token"]

    # list tables in a bitable.
    def _list_tables(self) -> list[models.Table]:
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self._node_id}/tables"
        resp = httpx.get(
            url=url,
            headers={
                "authorization": f"bearer {self._token}",
                "content-type": "application/json;charset=utf-8",
            },
        ).raise_for_status()

        resp = models.APIResponseWithData.model_validate_json(resp.content)
        if resp.code != 0:
            raise APIError(resp.code, resp.msg, url)
        return models.ListTablesData.model_validate(resp.data).items
