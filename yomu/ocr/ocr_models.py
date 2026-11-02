"""Catálogo de modelos de reconhecimento OCR por idioma.

Cada entrada define:
- url: URL pública para download do modelo (PaddleOCR/PP-OCRv3).
- sha256: SHA-256 hex do arquivo .onnx (verificação pós-download).
- label: nome legível para logs e diagnósticos.

Lógica de uso:
    path = ensure_model(lang)  # baixa + verifica se ainda não existir
    engine = RapidOCR(rec_model_path=path)

TRADUTOR_OCR_MODELS_DIR controla onde os modelos ficam em disco.
O valor padrão é <user_data>/yomu_ocr_models (via models_dir()).
"""

from __future__ import annotations

import hashlib
import os
import urllib.request
from pathlib import Path
from typing import TypedDict


class ModelEntry(TypedDict):
    url: str
    sha256: str
    label: str


# Registro de modelos de reconhecimento (rec) por código de idioma.
# Códigos: os mesmos aceitos por OCREngine (PADDLE_LANG_BY_CHOICE + extras).
# SHA-256 deve ser atualizado quando o modelo upstream mudar.
REC_MODELS: dict[str, ModelEntry] = {
    # Inglês — modelo padrão; já vem embutido no rapidocr_onnxruntime.
    "en": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/en_PP-OCRv3_rec_infer.tar",
        "sha256": "",   # embutido; download só se FORCE_MODEL_DOWNLOAD=1
        "label": "inglês (PP-OCRv3)",
    },
    "eng": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/en_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "inglês (PP-OCRv3)",
    },
    # Japonês
    "japan": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/japan_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "japonês (PP-OCRv3)",
    },
    "jpn": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/japan_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "japonês (PP-OCRv3)",
    },
    "ja": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/japan_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "japonês (PP-OCRv3)",
    },
    # Coreano
    "korean": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/korean_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "coreano (PP-OCRv3)",
    },
    "kor": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/korean_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "coreano (PP-OCRv3)",
    },
    "ko": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/korean_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "coreano (PP-OCRv3)",
    },
    # Chinês simplificado
    "ch": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_rec_infer.tar",
        "sha256": "",
        "label": "chinês simplificado (PP-OCRv4)",
    },
    "chinese": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_rec_infer.tar",
        "sha256": "",
        "label": "chinês simplificado (PP-OCRv4)",
    },
    "zh": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv4/chinese/ch_PP-OCRv4_rec_infer.tar",
        "sha256": "",
        "label": "chinês simplificado (PP-OCRv4)",
    },
    # Cirílico (russo, búlgaro, sérvio…)
    "cyrillic": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/cyrillic_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "cirílico/russo (PP-OCRv3)",
    },
    "ru": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/cyrillic_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "cirílico/russo (PP-OCRv3)",
    },
    # Espanhol/Português — PP-OCRv3 latino genérico cobre bem.
    "latin": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/latin_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "latino (PP-OCRv3)",
    },
    "es": {
        "url": "https://paddleocr.bj.bcebos.com/PP-OCRv3/multilingual/latin_PP-OCRv3_rec_infer.tar",
        "sha256": "",
        "label": "espanhol/latino (PP-OCRv3)",
    },
}

MODEL_BASE_URL = "https://paddleocr.bj.bcebos.com"

# Idiomas cujo modelo padrão do rapidocr_onnxruntime já cobre de forma suficiente
# (inglês). Para estes, nenhum download extra é necessário em runtime normal.
_BUNDLED_LANGS: frozenset[str] = frozenset({"en", "eng"})

# CJK: leitura vertical e dicionários específicos
CJK_LANGS: frozenset[str] = frozenset({"ja", "japan", "jpn", "ko", "korean", "kor", "zh", "ch", "chinese"})

# Idiomas com script latino (OCR genérico funciona para deteção; rec específico melhora)
LATIN_EXTRA_LANGS: frozenset[str] = frozenset({"es", "latin"})

# Idiomas cirílicos
CYRILLIC_LANGS: frozenset[str] = frozenset({"ru", "cyrillic"})


_ENGLISH_SOURCE_LANGS: frozenset[str] = frozenset({"en", "eng"})
_CHOICE_TO_LANG: dict[str, str] = {"1": "ja", "2": "ko", "3": "en"}


def source_is_english(lang_choice: str) -> bool:
    """True when *lang_choice* identifies English as the source script."""
    norm = str(lang_choice or "").strip().lower()
    resolved = _CHOICE_TO_LANG.get(norm, norm)
    return resolved in _ENGLISH_SOURCE_LANGS


def source_is_cjk(lang_choice: str) -> bool:
    """True when *lang_choice* is a CJK (Chinese/Japanese/Korean) source script."""
    norm = str(lang_choice or "").strip().lower()
    resolved = _CHOICE_TO_LANG.get(norm, norm)
    return resolved in CJK_LANGS


def models_dir() -> Path:
    """Diretório onde os modelos OCR por idioma são armazenados.

    Lê TRADUTOR_OCR_MODELS_DIR; se vazio, usa <user_data>/yomu_ocr_models.
    """
    env_val = os.environ.get("TRADUTOR_OCR_MODELS_DIR", "").strip()
    if env_val:
        return Path(env_val)
    # Fallback: junto ao diretório de dados do usuário padrão
    data_home = Path(os.environ.get("APPDATA", os.path.expanduser("~")))
    return data_home / "yomu_ocr_models"


def rec_model_for(lang: str) -> ModelEntry | None:
    """Retorna a entrada de modelo de reconhecimento para o idioma dado.

    ``lang`` pode ser qualquer chave de PADDLE_LANG_BY_CHOICE (en, ja, ko, zh,
    ru, es, …).  Retorna None para idiomas desconhecidos.
    """
    return REC_MODELS.get(str(lang or "").strip().lower())


def model_path(lang: str) -> Path | None:
    """Caminho local esperado do modelo .onnx para o idioma.

    O arquivo pode não existir ainda se nunca foi baixado.
    """
    entry = rec_model_for(lang)
    if entry is None:
        return None
    # Deriva um nome de arquivo do URL (último segmento sem .tar)
    fname = entry["url"].rstrip("/").rsplit("/", 1)[-1].replace(".tar", "") + ".onnx"
    return models_dir() / lang / fname


def is_model_available(lang: str) -> bool:
    """True se o modelo já existe em disco ou vem embutido no pacote."""
    norm = str(lang or "").strip().lower()
    if norm in _BUNDLED_LANGS:
        return True
    path = model_path(norm)
    return path is not None and path.exists()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def ensure_model(lang: str, *, force: bool = False) -> Path | None:
    """Garante que o modelo para ``lang`` está disponível em disco.

    Para idiomas embutidos retorna None (sem download necessário).
    Para os demais, baixa se não existir (ou se ``force=True``).
    Lança RuntimeError se o download falhar ou a SHA não bater.

    SHA-256 em branco no catálogo desabilita a verificação (modelo em preview).
    """
    norm = str(lang or "").strip().lower()
    if norm in _BUNDLED_LANGS:
        return None
    entry = rec_model_for(norm)
    if entry is None:
        raise ValueError(f"ocr_models: idioma não suportado: {norm!r}")
    dest = model_path(norm)
    assert dest is not None
    if not force and dest.exists():
        return dest
    dest.parent.mkdir(parents=True, exist_ok=True)
    url = entry["url"]
    # Download do tar e extração simples do .onnx embutido
    tar_path = dest.with_suffix(".tar")
    print(f"OCR_MODEL_DOWNLOAD lang={norm} url={url}", flush=True)
    try:
        urllib.request.urlretrieve(url, tar_path)
    except Exception as exc:
        raise RuntimeError(f"ocr_models: falha no download de {url}: {exc}") from exc
    # Extrai o .onnx do tar
    import tarfile
    with tarfile.open(tar_path) as tf:
        onnx_members = [m for m in tf.getmembers() if m.name.endswith(".onnx")]
        if not onnx_members:
            raise RuntimeError(f"ocr_models: nenhum .onnx no arquivo {tar_path.name}")
        member = onnx_members[0]
        src = tf.extractfile(member)
        if src is None:
            raise RuntimeError(f"ocr_models: não foi possível extrair {member.name}")
        dest.write_bytes(src.read())
    tar_path.unlink(missing_ok=True)
    expected_sha = (entry.get("sha256") or "").strip().lower()
    if expected_sha:
        actual = _sha256_file(dest)
        if actual != expected_sha:
            dest.unlink(missing_ok=True)
            raise RuntimeError(
                f"ocr_models: SHA-256 inválido para {dest.name} "
                f"esperado={expected_sha} obtido={actual}"
            )
    print(f"OCR_MODEL_READY lang={norm} path={dest}", flush=True)
    return dest
