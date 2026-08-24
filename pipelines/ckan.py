"""つくば市オープンデータカタログ (CKAN) からリソースを取得する。

つくば市には市公式サイトのオープンデータ一覧とは別に CKAN のカタログがあり、
そちらのほうが収録が厚い。全リソースが CC BY 4.0 で提供されている。
"""

from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen

logger = logging.getLogger("pipelines.ckan")

CKAN_BASE = "https://t1070170.dupf.jp/ckan"

# 素の urllib は 403 を返される配信元があるので、必ず名乗る
USER_AGENT = "queria-dataset-tsukuba (+https://github.com/queria-io/dataset-tsukuba)"

# ポータルは自治体の共同利用基盤で、一括アクセスで弾かれた実績のある系統。
# 同時取得はせず、1件ごとに間を置く
FETCH_INTERVAL_SEC = 0.3

# 数十件を連続で取るので、1件の一時的な失敗でビルド全体を落とさない。
# レート制限で弾かれた場合に効くよう、待ち時間は指数で伸ばす
MAX_ATTEMPTS = 4
RETRY_BASE_SEC = 2.0


@dataclass(frozen=True)
class Resource:
    dataset_title: str
    name: str
    fmt: str
    url: str


def _get(url: str) -> bytes:
    last: Exception | None = None
    for attempt in range(MAX_ATTEMPTS):
        if attempt:
            wait = RETRY_BASE_SEC * (2 ** (attempt - 1))
            logger.warning("  retry %d/%d in %.0fs: %s", attempt, MAX_ATTEMPTS - 1, wait, last)
            time.sleep(wait)
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=60) as res:
                return res.read()
        except HTTPError as e:
            # 404 や 410 は待っても変わらない。403 はレート制限のことがあるので待つ
            if e.code in (404, 410):
                raise
            last = e
        except (URLError, TimeoutError) as e:
            last = e
    raise RuntimeError(f"{url}: {MAX_ATTEMPTS} 回とも失敗した ({last})")


def to_utf8(raw: bytes) -> bytes:
    """CP932 と UTF-8 が混在する上流を UTF-8 に揃える。

    つくば市の地域・年齢別人口は1件だけが UTF-8 で残りは CP932。読み手側で
    1つの encoding を指定すると必ずどちらかで落ちるので、取得の時点で揃える。

    CP932 は Shift_JIS に NEC/IBM 拡張を足したもので、自治体の CSV では
    丸数字やローマ数字が実際に出てくる。`shift_jis` ではなく `cp932` で読む。
    """
    if raw.startswith(b"\xef\xbb\xbf"):
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        text = raw.decode("cp932")
    return text.encode("utf-8")


def search_resources(query: str, fmt: str) -> list[Resource]:
    """`query` に一致するデータセットの、`fmt` 形式のリソースをすべて返す。

    CKAN の package_search は既定で20件しか返さないので、rows を明示して取り切る。
    """
    url = f"{CKAN_BASE}/api/3/action/package_search?q={quote(query)}&rows=1000"
    payload = json.loads(_get(url))
    result = payload["result"]
    if len(result["results"]) < result["count"]:
        raise RuntimeError(
            f"ckan: {query!r} は {result['count']} 件あるのに {len(result['results'])} 件しか返らなかった"
        )
    logger.info("ckan: %r に %d データセット", query, len(result["results"]))

    resources: list[Resource] = []
    for pkg in result["results"]:
        for res in pkg.get("resources", []):
            if (res.get("format") or "").upper() != fmt.upper():
                continue
            resources.append(
                Resource(
                    dataset_title=pkg.get("title", ""),
                    name=res.get("name") or "",
                    fmt=fmt.upper(),
                    url=res["url"],
                )
            )
    return resources


def download(
    resources: list[Resource], dest: Path, *, normalize_encoding: bool = False
) -> list[Path]:
    """リソースを `dest` に落とし、書き出したファイルを重複なしで返す。

    ファイル名はリソース名をそのまま使う。**リソース名は上流が決める値**なので、
    ディレクトリを跨ぐ名前は受け付けない。

    同名のリソースが複数のデータセットに現れることがある（つくば市の CKAN には
    同一内容・同一ファイル名の重複登録が実在する）。2件目以降は取得しない。

    既にあるファイルは取り直さない。CI は毎回まっさらな作業ディレクトリで走るので
    全件が新しく取得され、この分岐が効くのは手元で繰り返し回すときだけ。
    **手元で上流の差し替えを拾いたいときは `dest` を消してから回す。**

    `normalize_encoding` を立てるとテキストとして UTF-8 に揃える。バイナリには使わない。
    """
    dest.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    seen: set[str] = set()
    for res in resources:
        if res.name in seen:
            continue
        seen.add(res.name)
        if Path(res.name).name != res.name or res.name in ("", ".", ".."):
            raise RuntimeError(f"ckan: リソース名がファイル名として使えない: {res.name!r}")

        path = dest / res.name
        written.append(path)
        if path.exists():
            continue
        raw = _get(res.url)
        path.write_bytes(to_utf8(raw) if normalize_encoding else raw)
        if len(written) % 20 == 1:
            logger.info("  %d/%d %s", len(written), len(resources), res.name)
        time.sleep(FETCH_INTERVAL_SEC)
    return written
