from .remote_config import AuthToken, Bitable
from loguru import logger
import redis
from .config import RedisConfig, RemoteConfig
from .models import mainpage
import httpx
import secrets
import os
from pydantic import BaseModel, TypeAdapter

BANNER_KEY = "banner配置"
MAGIC_KEY = "magic配置"
MAGIC_SHOWCASE_KEY = "magic showcase"
MAGIC_PROMPT_KEY = "magic prompt"

VIEW_NAME = "表格"


class BannerItem(BaseModel):
    image: str
    video: str


class MainPageRemoteConfig:

    def __init__(self, redis_conf: RedisConfig, remote_conf: RemoteConfig) -> None:
        self._rdb: redis.Redis = redis.Redis(
            host=redis_conf.host,
            port=redis_conf.port,
            db=redis_conf.db,
            decode_responses=True,
        )

        self._auth_token: AuthToken = AuthToken(remote_conf.app_id, remote_conf.secret)
        self._bid: str = remote_conf.bitable_id

    def refresh_banner(self) -> None:
        logger.info("pulling banner config from remote ...")
        bitable = Bitable(self._auth_token, self._bid)

        banner_items: list[BannerItem] = []
        for r in bitable.table(BANNER_KEY).view(VIEW_NAME).rows():
            try:
                conf_id = r.col("id")
                image = r.col("图片")
                video = r.col("视频")

                logger.info(f"find banner config, id {conf_id.int}")

                logger.info(
                    f"downloading banner image, media type {image.media_type}, url {image.url} ..."
                )
                image_filepath = self.download_resource(image.url)

                logger.info(
                    f"downloading banner video, media type {video.media_type}, url {video.url} ..."
                )
                video_filepath = self.download_resource(video.url)

                banner_items.append(
                    BannerItem(
                        image=f"/aigc/api/download/{image_filepath}",
                        video=f"/aigc/api/download/{video_filepath}",
                    )
                )

            except KeyError:
                pass

        adapter = TypeAdapter(list[BannerItem])
        self._rdb.set("aigc:banner", adapter.dump_json(banner_items))

    def refresh_magic(self) -> None:
        logger.info("pulling magic config from remote ...")
        bitable = Bitable(self._auth_token, self._bid)

        magic_name_by_id: dict[str, str] = {}
        showcases_by_name: dict[str, list[mainpage.Showcase]] = {}
        prompts_by_name: dict[str, list[mainpage.Prompt]] = {}

        for r in bitable.table("magic配置").view("表格").rows():
            try:
                magic_name_by_id[r.id] = r.col("name").text
            except KeyError:
                continue
        logger.info(f"have magic config: {magic_name_by_id}")

        logger.info("gathering showcase ...")
        for r in bitable.table("magic showcase").view("表格").rows():
            try:
                link_id = r.col("magic").link_ids[0]
                original_filename = self.download_resource(r.col("原始图").url)
                result_filename = self.download_resource(r.col("处理后图").url)
            except KeyError:
                continue

            sc = mainpage.Showcase(
                original=f"/aigc/api/download/{original_filename}",
                result=f"/aigc/api/download/{result_filename}",
            )

            if link_id not in magic_name_by_id:
                logger.warning("have showcase but no associate to any magic")
                continue
            name = magic_name_by_id[link_id]

            if name not in showcases_by_name:
                showcases_by_name[name] = []
            showcases_by_name[name].append(sc)

        logger.info("gathering prompt ...")
        for r in bitable.table("magic prompt").view("表格").rows():
            try:
                link_id = r.col("magic").link_ids[0]
                name = r.col("name").text
                prompt = r.col("prompt").text
            except KeyError:
                continue

            p = mainpage.Prompt(name=name, prompt=prompt)

            if link_id not in magic_name_by_id:
                logger.warning("have prompt but no associate to any magic")
            name = magic_name_by_id[link_id]

            if name not in prompts_by_name:
                prompts_by_name[name] = []
            prompts_by_name[name].append(p)

        partial = mainpage.ShowcasesAndPrompts(
            showcase=(
                showcases_by_name["partial"] if "partial" in showcases_by_name else []
            ),
            prompts=prompts_by_name["partial"] if "partial" in prompts_by_name else [],
        )
        powerful = mainpage.ShowcasesAndPrompts(
            showcase=(
                showcases_by_name["powerful"] if "powerful" in showcases_by_name else []
            ),
            prompts=(
                prompts_by_name["powerful"] if "powerful" in prompts_by_name else []
            ),
        )
        i2v = mainpage.ShowcasesAndPrompts(
            showcase=showcases_by_name["i2v"] if "i2v" in showcases_by_name else [],
            prompts=prompts_by_name["i2v"] if "i2v" in prompts_by_name else [],
        )

        magic = mainpage.Magic(partial=partial, powerful=powerful, i2v=i2v)
        self._rdb.set("aigc:magic", magic.model_dump_json())
        logger.info("pull magic config down.")

    def download_resource(self, url: str) -> str:
        resp = httpx.get(
            url, headers={"authorization": f"bearer {self._auth_token}"}
        ).raise_for_status()

        media_type: str = resp.headers["content-type"]
        size: int = int(resp.headers["content-length"])

        extend_name = media_type.split("/")[1]
        filename = f"{secrets.token_hex(8)}.{extend_name}"

        if not os.path.exists("static"):
            os.mkdir("static")

        with open("static/" + filename, "wb") as fp:
            fp.write(resp.content)

        logger.info(
            f"resource download complete, type: {media_type}, size: {size}, filename {filename}"
        )
        return filename
