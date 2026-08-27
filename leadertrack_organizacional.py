from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd

from saude_emocional_utils import calcular_categoria_medias_app_like


DIMENSOES_MICROAMBIENTE = [
    "Adaptabilidade",
    "Responsabilidade",
    "Performance",
    "Reconhecimento",
    "Nitidez",
    "Colaboração Mútua",
]

ARQUETIPOS = [
    "Imperativo",
    "Resoluto",
    "Cuidativo",
    "Consultivo",
    "Prescritivo",
    "Formador",
]

RECORTES_PADRAO = [
    "empresa",
    "codrodada",
    "emailLider",
    "estado",
    "cidade",
    "sexo",
    "etnia",
    "geracao",
    "departamento",
    "cargo",
]


@dataclass(frozen=True)
class OrganizationalRules:
    min_sample: int = 5
    relevant_delta_points: float = 5.0
    medium_gap: float = 20.0
    critical_gap: float = 35.0
    emotional_attention_score: float = 75.0
    emotional_critical_score: float = 65.0
    max_findings_per_family: int = 12
    rules_version: str = "leadertrack_org_v1"
    prompt_version: str = "leadertrack_org_prompt_v1"
    allowed_demographic_crossings: tuple[str, ...] = field(
        default_factory=lambda: ("sexo", "etnia", "geracao", "estado", "cidade")
    )
    allowed_org_crossings: tuple[str, ...] = field(
        default_factory=lambda: ("empresa", "departamento", "cargo", "area")
    )


def _clean_text(value: Any) -> str:
    text = str(value or "").strip()
    if text.lower() in {"nan", "none", "null", "n/a", "na"}:
        return ""
    return text


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except Exception:
        return default


def _valid_value(value: Any) -> bool:
    return bool(_clean_text(value))


def _generation_from_birthdate(value: Any) -> str:
    text = _clean_text(value)
    if not text:
        return ""

    parsed = pd.to_datetime(text, errors="coerce", dayfirst=True)
    if pd.isna(parsed):
        parsed = pd.to_datetime(text, errors="coerce", dayfirst=False)
    if pd.isna(parsed):
        return ""

    year = int(parsed.year)
    if year <= 1964:
        return "Baby Boomers"
    if year <= 1980:
        return "Geracao X"
    if year <= 1996:
        return "Millennials"
    if year <= 2012:
        return "Geracao Z"
    return "Geracao Alpha"


def preparar_dataframe_organizacional(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    prepared = df.copy()
    for col in RECORTES_PADRAO:
        if col not in prepared.columns:
            prepared[col] = ""

    if "geracao" not in df.columns or not prepared["geracao"].astype(str).str.strip().any():
        nascimento_col = "nascimento" if "nascimento" in prepared.columns else None
        if nascimento_col:
            prepared["geracao"] = prepared[nascimento_col].apply(_generation_from_birthdate)

    for col in RECORTES_PADRAO:
        prepared[col] = prepared[col].apply(_clean_text)

    return prepared


def _apply_filters(df: pd.DataFrame, filtros: dict[str, Any] | None) -> pd.DataFrame:
    if df is None or df.empty:
        return pd.DataFrame()

    filtered = df.copy()
    filtros = filtros or {}
    aliases = {"holding": "holding", "lider": "emailLider", "emaillider": "emailLider"}

    for raw_col, raw_value in filtros.items():
        col = aliases.get(raw_col, raw_col)
        if col not in filtered.columns:
            continue
        if isinstance(raw_value, (list, tuple, set)):
            values = {_clean_text(v).lower() for v in raw_value if _valid_value(v)}
            if values:
                filtered = filtered[filtered[col].astype(str).str.lower().isin(values)]
            continue

        value = _clean_text(raw_value)
        if not value or value.lower() in {"todos", "todas"}:
            continue
        col_values = filtered[col].apply(_clean_text)
        if not col_values.any():
            continue
        candidate = filtered[col_values.str.lower() == value.lower()]
        if not candidate.empty:
            filtered = candidate

    return filtered


def _sample_info(df: pd.DataFrame) -> dict[str, Any]:
    if df is None or df.empty:
        return {"respondentes": 0, "lideres": 0}
    return {
        "respondentes": int(len(df)),
        "lideres": int(df["emailLider"].nunique()) if "emailLider" in df.columns else 0,
    }


def _distribution(df: pd.DataFrame, column: str, min_sample: int) -> list[dict[str, Any]]:
    if df is None or df.empty or column not in df.columns:
        return []

    rows = []
    total = max(len(df), 1)
    counts = df[column].fillna("").astype(str).str.strip()
    for value, count in counts[counts != ""].value_counts().items():
        if int(count) < min_sample:
            continue
        rows.append(
            {
                "campo": column,
                "valor": value,
                "n": int(count),
                "percentual": round(float(count) * 100.0 / total, 1),
            }
        )
    return rows


def _aggregate_dict_column(df: pd.DataFrame, dict_column: str, keys: list[str]) -> dict[str, float]:
    result = {}
    if df is None or df.empty or dict_column not in df.columns:
        return result

    for key in keys:
        values = []
        for item in df[dict_column]:
            if isinstance(item, dict) and key in item:
                values.append(_safe_float(item.get(key), np.nan))
        values = [v for v in values if not pd.isna(v)]
        if values:
            result[key] = round(float(np.mean(values)), 1)
    return result


def _micro_scores(df_micro: pd.DataFrame) -> dict[str, Any]:
    real = _aggregate_dict_column(df_micro, "dimensoes_real", DIMENSOES_MICROAMBIENTE)
    ideal = _aggregate_dict_column(df_micro, "dimensoes_ideal", DIMENSOES_MICROAMBIENTE)
    dimensoes = {}

    for dim in DIMENSOES_MICROAMBIENTE:
        if dim not in real or dim not in ideal:
            continue
        gap = round(ideal[dim] - real[dim], 1)
        dimensoes[dim] = {
            "real": real[dim],
            "ideal": ideal[dim],
            "gap": gap,
            "nivel_gap": "critico" if gap >= 35 else "medio" if gap >= 20 else "baixo",
        }

    return {
        "dimensoes": dimensoes,
        "gap_medio": round(float(np.mean([v["gap"] for v in dimensoes.values()])), 1)
        if dimensoes
        else None,
    }


def _archetype_scores(df_arq: pd.DataFrame) -> dict[str, float]:
    if df_arq is None or df_arq.empty or "arquétipos" not in df_arq.columns:
        return {}
    values_by_arq = {name: [] for name in ARQUETIPOS}
    for item in df_arq["arquétipos"]:
        if not isinstance(item, dict):
            continue
        for name in ARQUETIPOS:
            if name in item:
                values_by_arq[name].append(_safe_float(item.get(name), np.nan))
    return {
        name: round(float(np.mean(values)), 1)
        for name, values in values_by_arq.items()
        if values and not pd.isna(np.mean(values))
    }


def _health_scores(
    matriz_arq: pd.DataFrame,
    matriz_micro: pd.DataFrame,
    df_arq: pd.DataFrame,
    df_micro: pd.DataFrame,
    filtros: dict[str, Any],
) -> dict[str, Any]:
    if df_arq is None or df_arq.empty or df_micro is None or df_micro.empty:
        return {"score_final": None, "categorias": {}}

    categorias, score_final = calcular_categoria_medias_app_like(
        matriz_arq,
        matriz_micro,
        df_arq,
        df_micro,
        filtros,
    )
    if score_final == "—":
        score_final = None
    return {
        "score_final": score_final,
        "categorias": categorias,
    }


def _build_group_filters(base_filters: dict[str, Any], column: str, value: Any) -> dict[str, Any]:
    filters = dict(base_filters or {})
    filters[column] = value
    return filters


def _compare_health_by_column(
    matriz_arq: pd.DataFrame,
    matriz_micro: pd.DataFrame,
    df_arq: pd.DataFrame,
    df_micro: pd.DataFrame,
    base_filters: dict[str, Any],
    column: str,
    baseline_score: float | None,
    rules: OrganizationalRules,
) -> list[dict[str, Any]]:
    if baseline_score is None or df_micro is None or df_micro.empty or column not in df_micro.columns:
        return []

    findings = []
    values = df_micro[column].dropna().astype(str).str.strip()
    for value, count in values[values != ""].value_counts().items():
        if int(count) < rules.min_sample:
            continue
        filters = _build_group_filters(base_filters, column, value)
        arq_cut = _apply_filters(df_arq, {column: value})
        micro_cut = _apply_filters(df_micro, {column: value})
        if len(micro_cut) < rules.min_sample:
            continue

        score = _health_scores(matriz_arq, matriz_micro, arq_cut, micro_cut, filters).get("score_final")
        if score is None:
            continue

        delta = round(float(score) - float(baseline_score), 1)
        if abs(delta) < rules.relevant_delta_points:
            continue

        findings.append(
            {
                "tipo": "saude_emocional",
                "campo": column,
                "valor": value,
                "n": int(len(micro_cut)),
                "score": round(float(score), 1),
                "media_contexto": round(float(baseline_score), 1),
                "delta": delta,
                "direcao": "abaixo_da_media" if delta < 0 else "acima_da_media",
                "severidade": "critica"
                if score < rules.emotional_critical_score
                else "atencao"
                if score < rules.emotional_attention_score
                else "diferenca_relevante",
                "mensagem_base": (
                    f"{column}={value} apresentou score de saude emocional {abs(delta):.1f} "
                    f"pontos {'abaixo' if delta < 0 else 'acima'} da media do contexto."
                ),
            }
        )

    return sorted(findings, key=lambda item: abs(item["delta"]), reverse=True)[
        : rules.max_findings_per_family
    ]


def _micro_findings_by_column(
    df_micro: pd.DataFrame,
    column: str,
    rules: OrganizationalRules,
) -> list[dict[str, Any]]:
    if df_micro is None or df_micro.empty or column not in df_micro.columns:
        return []

    findings = []
    for value, group in df_micro.groupby(column, dropna=True):
        value = _clean_text(value)
        if not value or len(group) < rules.min_sample:
            continue
        scores = _micro_scores(group)
        for dim, values in scores.get("dimensoes", {}).items():
            gap = values["gap"]
            if gap < rules.medium_gap:
                continue
            findings.append(
                {
                    "tipo": "microambiente_gap",
                    "campo": column,
                    "valor": value,
                    "n": int(len(group)),
                    "dimensao": dim,
                    "real": values["real"],
                    "ideal": values["ideal"],
                    "gap": gap,
                    "severidade": "critico" if gap >= rules.critical_gap else "medio",
                    "mensagem_base": (
                        f"{column}={value} apresentou gap {gap:.1f} em {dim} "
                        f"({values['real']:.1f} real vs {values['ideal']:.1f} ideal)."
                    ),
                }
            )

    return sorted(findings, key=lambda item: item["gap"], reverse=True)[
        : rules.max_findings_per_family
    ]


def _crossing_columns(df: pd.DataFrame, rules: OrganizationalRules) -> list[tuple[str, str]]:
    candidates = list(rules.allowed_demographic_crossings) + list(rules.allowed_org_crossings)
    candidates = [col for col in candidates if col in df.columns]
    return list(combinations(candidates, 2))


def _compare_health_by_crossing(
    matriz_arq: pd.DataFrame,
    matriz_micro: pd.DataFrame,
    df_arq: pd.DataFrame,
    df_micro: pd.DataFrame,
    base_filters: dict[str, Any],
    columns: tuple[str, str],
    baseline_score: float | None,
    rules: OrganizationalRules,
) -> list[dict[str, Any]]:
    if baseline_score is None or df_micro is None or df_micro.empty:
        return []

    col_a, col_b = columns
    if col_a not in df_micro.columns or col_b not in df_micro.columns:
        return []

    findings = []
    grouped = df_micro.groupby([col_a, col_b], dropna=True)
    for (value_a, value_b), group in grouped:
        value_a = _clean_text(value_a)
        value_b = _clean_text(value_b)
        if not value_a or not value_b or len(group) < rules.min_sample:
            continue

        cut_filters = {col_a: value_a, col_b: value_b}
        filters = dict(base_filters or {})
        filters.update(cut_filters)
        arq_cut = _apply_filters(df_arq, cut_filters)
        micro_cut = _apply_filters(df_micro, cut_filters)
        if len(micro_cut) < rules.min_sample:
            continue

        score = _health_scores(matriz_arq, matriz_micro, arq_cut, micro_cut, filters).get("score_final")
        if score is None:
            continue

        delta = round(float(score) - float(baseline_score), 1)
        if abs(delta) < rules.relevant_delta_points:
            continue

        label = f"{col_a}={value_a} + {col_b}={value_b}"
        findings.append(
            {
                "tipo": "saude_emocional_cruzamento",
                "campos": [col_a, col_b],
                "valores": [value_a, value_b],
                "rotulo": label,
                "n": int(len(micro_cut)),
                "score": round(float(score), 1),
                "media_contexto": round(float(baseline_score), 1),
                "delta": delta,
                "direcao": "abaixo_da_media" if delta < 0 else "acima_da_media",
                "severidade": "critica"
                if score < rules.emotional_critical_score
                else "atencao"
                if score < rules.emotional_attention_score
                else "diferenca_relevante",
                "mensagem_base": (
                    f"{label} apresentou score de saude emocional {abs(delta):.1f} "
                    f"pontos {'abaixo' if delta < 0 else 'acima'} da media do contexto."
                ),
            }
        )

    return sorted(findings, key=lambda item: abs(item["delta"]), reverse=True)[
        : rules.max_findings_per_family
    ]


def _micro_findings_by_crossing(
    df_micro: pd.DataFrame,
    columns: tuple[str, str],
    rules: OrganizationalRules,
) -> list[dict[str, Any]]:
    if df_micro is None or df_micro.empty:
        return []

    col_a, col_b = columns
    if col_a not in df_micro.columns or col_b not in df_micro.columns:
        return []

    findings = []
    for (value_a, value_b), group in df_micro.groupby([col_a, col_b], dropna=True):
        value_a = _clean_text(value_a)
        value_b = _clean_text(value_b)
        if not value_a or not value_b or len(group) < rules.min_sample:
            continue

        label = f"{col_a}={value_a} + {col_b}={value_b}"
        scores = _micro_scores(group)
        for dim, values in scores.get("dimensoes", {}).items():
            gap = values["gap"]
            if gap < rules.medium_gap:
                continue
            findings.append(
                {
                    "tipo": "microambiente_gap_cruzamento",
                    "campos": [col_a, col_b],
                    "valores": [value_a, value_b],
                    "rotulo": label,
                    "n": int(len(group)),
                    "dimensao": dim,
                    "real": values["real"],
                    "ideal": values["ideal"],
                    "gap": gap,
                    "severidade": "critico" if gap >= rules.critical_gap else "medio",
                    "mensagem_base": (
                        f"{label} apresentou gap {gap:.1f} em {dim} "
                        f"({values['real']:.1f} real vs {values['ideal']:.1f} ideal)."
                    ),
                }
            )

    return sorted(findings, key=lambda item: item["gap"], reverse=True)[
        : rules.max_findings_per_family
    ]


def _micro_profile(df_micro: pd.DataFrame) -> dict[str, Any]:
    scores = _micro_scores(df_micro)
    dimensoes = []
    for dim, values in (scores.get("dimensoes") or {}).items():
        dimensoes.append({
            "dimensao": dim,
            "real": values.get("real"),
            "ideal": values.get("ideal"),
            "gap": values.get("gap"),
            "nivel_gap": values.get("nivel_gap"),
        })
    dimensoes = sorted(dimensoes, key=lambda item: float(item.get("gap") or 0), reverse=True)
    return {
        "n": int(len(df_micro)) if df_micro is not None else 0,
        "gap_medio": scores.get("gap_medio"),
        "dimensoes": dimensoes,
        "maior_gap": dimensoes[0] if dimensoes else None,
        "menor_gap": dimensoes[-1] if dimensoes else None,
    }


def _profile_with_context_comparison(
    profile: dict[str, Any],
    baseline_profile: dict[str, Any] | None,
) -> dict[str, Any]:
    if not isinstance(profile, dict):
        return {}
    if not isinstance(baseline_profile, dict):
        return profile

    baseline_dims = {
        item.get("dimensao"): item
        for item in baseline_profile.get("dimensoes", [])
        if isinstance(item, dict) and item.get("dimensao")
    }

    compared_dims = []
    for item in profile.get("dimensoes", []):
        if not isinstance(item, dict):
            continue
        dim = item.get("dimensao")
        baseline = baseline_dims.get(dim) or {}
        compared = dict(item)
        compared["media_contexto_real"] = baseline.get("real")
        compared["media_contexto_ideal"] = baseline.get("ideal")
        compared["media_contexto_gap"] = baseline.get("gap")
        if item.get("real") is not None and baseline.get("real") is not None:
            compared["delta_real_vs_contexto"] = round(
                float(item.get("real")) - float(baseline.get("real")), 1
            )
        if item.get("gap") is not None and baseline.get("gap") is not None:
            compared["delta_gap_vs_contexto"] = round(
                float(item.get("gap")) - float(baseline.get("gap")), 1
            )
        compared_dims.append(compared)

    result = dict(profile)
    result["dimensoes"] = compared_dims
    result["comparacao_contexto"] = {
        "gap_medio_contexto": baseline_profile.get("gap_medio"),
        "delta_gap_medio_vs_contexto": (
            round(float(profile.get("gap_medio")) - float(baseline_profile.get("gap_medio")), 1)
            if profile.get("gap_medio") is not None and baseline_profile.get("gap_medio") is not None
            else None
        ),
        "maior_gap_contexto": baseline_profile.get("maior_gap"),
    }
    return result


def _micro_profiles_by_column(
    df_micro: pd.DataFrame,
    column: str,
    rules: OrganizationalRules,
    baseline_profile: dict[str, Any] | None = None,
    limit: int = 12,
) -> list[dict[str, Any]]:
    if df_micro is None or df_micro.empty or column not in df_micro.columns:
        return []

    rows = []
    for value, group in df_micro.groupby(column, dropna=True):
        value = _clean_text(value)
        if not value or len(group) < rules.min_sample:
            continue
        profile = _profile_with_context_comparison(_micro_profile(group), baseline_profile)
        rows.append({
            "campo": column,
            "valor": value,
            **profile,
        })

    return sorted(
        rows,
        key=lambda item: abs(float((item.get("comparacao_contexto") or {}).get("delta_gap_medio_vs_contexto") or item.get("gap_medio") or 0)),
        reverse=True,
    )[:limit]


def _micro_profiles_by_crossing(
    df_micro: pd.DataFrame,
    columns: tuple[str, str],
    rules: OrganizationalRules,
    baseline_profile: dict[str, Any] | None = None,
    limit: int = 15,
) -> list[dict[str, Any]]:
    if df_micro is None or df_micro.empty:
        return []

    col_a, col_b = columns
    if col_a not in df_micro.columns or col_b not in df_micro.columns:
        return []

    rows = []
    for (value_a, value_b), group in df_micro.groupby([col_a, col_b], dropna=True):
        value_a = _clean_text(value_a)
        value_b = _clean_text(value_b)
        if not value_a or not value_b or len(group) < rules.min_sample:
            continue
        profile = _profile_with_context_comparison(_micro_profile(group), baseline_profile)
        rows.append({
            "campos": [col_a, col_b],
            "valores": [value_a, value_b],
            "rotulo": f"{col_a}={value_a} + {col_b}={value_b}",
            **profile,
        })

    return sorted(
        rows,
        key=lambda item: abs(float((item.get("comparacao_contexto") or {}).get("delta_gap_medio_vs_contexto") or item.get("gap_medio") or 0)),
        reverse=True,
    )[:limit]


def _question_gap_rows(
    df_micro: pd.DataFrame,
    matriz_micro: pd.DataFrame,
    rules: OrganizationalRules,
    limit: int = 20,
) -> list[dict[str, Any]]:
    if df_micro is None or df_micro.empty or matriz_micro is None or matriz_micro.empty:
        return []
    if "respostas" not in df_micro.columns:
        return []

    rows = []
    matriz_questoes = matriz_micro[[
        "COD",
        "AFIRMACAO",
        "DIMENSAO",
        "SUBDIMENSAO",
        "name_real",
        "name_ideal",
        "CHAVE",
        "PONTUACAO_REAL",
        "PONTUACAO_IDEAL",
    ]].drop_duplicates(subset=["COD", "name_real", "name_ideal"])

    for _, questao in matriz_questoes.iterrows():
        reais = []
        ideais = []
        real_key = _clean_text(questao.get("name_real"))
        ideal_key = _clean_text(questao.get("name_ideal"))
        codigo = _clean_text(questao.get("COD"))
        if not real_key or not ideal_key:
            continue

        for _, resp in df_micro.iterrows():
            respostas = resp.get("respostas") or {}
            if not isinstance(respostas, dict):
                continue
            if real_key not in respostas or ideal_key not in respostas:
                continue
            try:
                real = int(respostas.get(real_key))
                ideal = int(respostas.get(ideal_key))
            except Exception:
                continue

            chave = f"{codigo}_I{ideal}_R{real}"
            linha = matriz_micro[matriz_micro["CHAVE"] == chave]
            if linha.empty:
                continue
            reais.append(_safe_float(linha["PONTUACAO_REAL"].iloc[0], np.nan))
            ideais.append(_safe_float(linha["PONTUACAO_IDEAL"].iloc[0], np.nan))

        reais = [v for v in reais if not pd.isna(v)]
        ideais = [v for v in ideais if not pd.isna(v)]
        n = min(len(reais), len(ideais))
        if n < rules.min_sample:
            continue

        real_media = round(float(np.mean(reais)), 1)
        ideal_media = round(float(np.mean(ideais)), 1)
        gap = round(ideal_media - real_media, 1)
        rows.append({
            "codigo": codigo,
            "afirmacao": _clean_text(questao.get("AFIRMACAO")),
            "dimensao": _clean_text(questao.get("DIMENSAO")),
            "subdimensao": _clean_text(questao.get("SUBDIMENSAO")),
            "n": int(n),
            "real": real_media,
            "ideal": ideal_media,
            "gap": gap,
            "severidade": "critico" if gap >= rules.critical_gap else "medio" if gap >= rules.medium_gap else "baixo",
        })

    return sorted(rows, key=lambda item: float(item.get("gap") or 0), reverse=True)[:limit]


def _participation_summary(df_micro: pd.DataFrame, rules: OrganizationalRules) -> dict[str, Any]:
    if df_micro is None or df_micro.empty:
        return {}

    df_equipe = df_micro[df_micro["tipo"] == "Avaliação Equipe"] if "tipo" in df_micro.columns else df_micro
    total = max(len(df_equipe), 1)

    def by_column(column: str, limit: int = 12, anonymize: bool = False) -> list[dict[str, Any]]:
        if column not in df_equipe.columns:
            return []
        rows = []
        for idx, (value, count) in enumerate(
            df_equipe[column].fillna("").astype(str).str.strip().value_counts().items(),
            start=1,
        ):
            if not value or int(count) < 1:
                continue
            rows.append({
                "campo": column,
                "valor": f"Lider {idx:02d}" if anonymize else value,
                "respostas": int(count),
                "percentual_da_amostra": round(float(count) * 100.0 / total, 1),
            })
        return rows[:limit]

    return {
        "observacao": (
            "Percentual calculado sobre as respostas de equipe carregadas no recorte. "
            "Taxa exata sobre tokens enviados exige denominador de tokens emitidos por area/lider."
        ),
        "total_respostas_equipe": int(len(df_equipe)),
        "por_departamento": by_column("departamento"),
        "por_area": by_column("area"),
        "por_lider": by_column("emailLider", limit=20, anonymize=True),
        "por_empresa": by_column("empresa"),
    }


def gerar_analise_profunda(
    matriz_micro: pd.DataFrame,
    df_micro: pd.DataFrame,
    rules: OrganizationalRules,
) -> dict[str, Any]:
    df_equipe = df_micro[df_micro["tipo"] == "Avaliação Equipe"] if "tipo" in df_micro.columns else df_micro
    baseline_profile = _micro_profile(df_equipe)

    recortes = {}
    recorte_columns = [
        "empresa",
        "filial_nome",
        "branch_name",
        "estado",
        "cidade",
        "geracao",
        "sexo",
        "etnia",
        "departamento",
        "area",
        "cargo",
    ]
    for column in recorte_columns:
        perfis = _micro_profiles_by_column(df_equipe, column, rules, baseline_profile=baseline_profile)
        if perfis:
            recortes[column] = perfis

    cruzamentos = {}
    crossing_candidates = [
        "empresa",
        "filial_nome",
        "branch_name",
        "estado",
        "cidade",
        "geracao",
        "sexo",
        "etnia",
        "departamento",
        "area",
        "cargo",
    ]
    crossing_pairs = [
        pair
        for pair in combinations([col for col in crossing_candidates if col in df_equipe.columns], 2)
        if pair not in {("cidade", "estado"), ("branch_name", "filial_nome")}
    ]
    for pair in crossing_pairs:
        perfis = _micro_profiles_by_crossing(df_equipe, pair, rules, baseline_profile=baseline_profile, limit=8)
        if perfis:
            cruzamentos[" + ".join(pair)] = perfis
    cruzamentos_priorizados = dict(
        sorted(
            cruzamentos.items(),
            key=lambda item: max(
                abs(float((row.get("comparacao_contexto") or {}).get("delta_gap_medio_vs_contexto") or 0))
                for row in item[1]
            ),
            reverse=True,
        )[:18]
    )

    return {
        "referencia_contexto": baseline_profile,
        "microambiente_por_recorte": recortes,
        "microambiente_por_interseccao": cruzamentos_priorizados,
        "comparativo_empresas_mesma_holding": recortes.get("empresa", []),
        "afirmacoes_mais_impactantes": _question_gap_rows(df_equipe, matriz_micro, rules),
        "participacao": _participation_summary(df_micro, rules),
    }


def detectar_achados_organizacionais(
    matriz_arq: pd.DataFrame,
    matriz_micro: pd.DataFrame,
    df_arq: pd.DataFrame,
    df_micro: pd.DataFrame,
    filtros: dict[str, Any] | None = None,
    rules: OrganizationalRules | None = None,
) -> list[dict[str, Any]]:
    rules = rules or OrganizationalRules()
    filtros = filtros or {}
    base_health = _health_scores(matriz_arq, matriz_micro, df_arq, df_micro, filtros)
    baseline_score = base_health.get("score_final")

    findings = []
    columns = [c for c in RECORTES_PADRAO if c in df_micro.columns]

    for column in columns:
        findings.extend(
            _compare_health_by_column(
                matriz_arq,
                matriz_micro,
                df_arq,
                df_micro,
                filtros,
                column,
                baseline_score,
                rules,
            )
        )
        findings.extend(_micro_findings_by_column(df_micro, column, rules))

    for crossing in _crossing_columns(df_micro, rules):
        findings.extend(
            _compare_health_by_crossing(
                matriz_arq,
                matriz_micro,
                df_arq,
                df_micro,
                filtros,
                crossing,
                baseline_score,
                rules,
            )
        )
        findings.extend(_micro_findings_by_crossing(df_micro, crossing, rules))

    return sorted(
        findings,
        key=lambda item: (
            0 if item.get("severidade") in {"critica", "critico"} else 1,
            -abs(float(item.get("delta", item.get("gap", 0)))),
        ),
    )[: rules.max_findings_per_family * 3]


def gerar_pacote_organizacional(
    matriz_arq: pd.DataFrame,
    matriz_micro: pd.DataFrame,
    df_arquetipos: pd.DataFrame,
    df_microambiente: pd.DataFrame,
    filtros: dict[str, Any] | None = None,
    contexto: dict[str, Any] | None = None,
    rules: OrganizationalRules | None = None,
) -> dict[str, Any]:
    rules = rules or OrganizationalRules()
    filtros = filtros or {}
    contexto = contexto or {}

    df_arq = preparar_dataframe_organizacional(df_arquetipos)
    df_micro = preparar_dataframe_organizacional(df_microambiente)
    df_arq = _apply_filters(df_arq, filtros)
    df_micro = _apply_filters(df_micro, filtros)

    sample = _sample_info(df_micro)
    distributions = {
        column: _distribution(df_micro, column, rules.min_sample)
        for column in RECORTES_PADRAO
        if column in df_micro.columns
    }

    health = _health_scores(matriz_arq, matriz_micro, df_arq, df_micro, filtros)
    micro = _micro_scores(df_micro)
    df_arq_equipe = (
        df_arq[df_arq["tipo"] == "Avaliação Equipe"]
        if "tipo" in df_arq.columns
        else pd.DataFrame()
    )
    archetypes = _archetype_scores(df_arq_equipe)
    findings = detectar_achados_organizacionais(
        matriz_arq,
        matriz_micro,
        df_arq,
        df_micro,
        filtros,
        rules,
    )
    deep_analysis = gerar_analise_profunda(matriz_micro, df_micro, rules)

    return {
        "tipo": "devolutiva_organizacional_leadertrack",
        "gerado_em": datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "contexto": contexto,
        "filtros": filtros,
        "governanca": {
            "publico_autorizado": ["RH", "CEO", "diretoria", "gestao_autorizada"],
            "saude_emocional_entrega_individual": False,
            "min_sample": rules.min_sample,
            "regras": rules.rules_version,
            "prompt": rules.prompt_version,
            "sem_diagnostico_clinico": True,
            "sem_dados_inventados": True,
        },
        "amostra": sample,
        "distribuicoes": distributions,
        "saude_emocional": health,
        "microambiente": micro,
        "arquetipos": archetypes,
        "achados_relevantes": findings,
        "analise_profunda": deep_analysis,
    }


def _compactar_perfil_para_ia(item: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(item, dict):
        return {}

    comparacao = item.get("comparacao_contexto") or {}
    maior_gap = item.get("maior_gap") or {}
    return {
        "campo": item.get("campo"),
        "valor": item.get("valor"),
        "campos": item.get("campos"),
        "valores": item.get("valores"),
        "rotulo": item.get("rotulo"),
        "n": item.get("n"),
        "gap_medio": item.get("gap_medio"),
        "delta_gap_medio_vs_contexto": comparacao.get("delta_gap_medio_vs_contexto"),
        "maior_gap": {
            "dimensao": maior_gap.get("dimensao"),
            "real": maior_gap.get("real"),
            "ideal": maior_gap.get("ideal"),
            "gap": maior_gap.get("gap"),
            "delta_gap_vs_contexto": maior_gap.get("delta_gap_vs_contexto"),
        } if isinstance(maior_gap, dict) else None,
    }


def pacote_organizacional_para_ia(pacote: dict[str, Any], limite_achados: int = 18) -> dict[str, Any]:
    if not isinstance(pacote, dict):
        return {}

    achados = pacote.get("achados_relevantes") or []
    if isinstance(achados, list):
        achados = achados[:limite_achados]
    else:
        achados = []

    distribuicoes_resumidas = {}
    for campo, linhas in (pacote.get("distribuicoes") or {}).items():
        if not isinstance(linhas, list):
            continue
        distribuicoes_resumidas[campo] = linhas[:12]

    analise = pacote.get("analise_profunda") or {}
    analise_resumida = {
        "referencia_contexto": {
            "n": (analise.get("referencia_contexto") or {}).get("n"),
            "gap_medio": (analise.get("referencia_contexto") or {}).get("gap_medio"),
            "maior_gap": (analise.get("referencia_contexto") or {}).get("maior_gap"),
        },
        "microambiente_por_recorte": {},
        "microambiente_por_interseccao_prioritaria": [],
        "comparativo_empresas_mesma_holding": [],
        "afirmacoes_mais_impactantes": [],
        "participacao": {},
    }
    for campo, linhas in (analise.get("microambiente_por_recorte") or {}).items():
        if isinstance(linhas, list):
            analise_resumida["microambiente_por_recorte"][campo] = [
                _compactar_perfil_para_ia(item) for item in linhas[:5]
            ]

    interseccoes = []
    for campo, linhas in (analise.get("microambiente_por_interseccao") or {}).items():
        if isinstance(linhas, list):
            for item in linhas[:3]:
                compactado = _compactar_perfil_para_ia(item)
                compactado["tipo_cruzamento"] = campo
                interseccoes.append(compactado)
    interseccoes = sorted(
        interseccoes,
        key=lambda item: abs(float(item.get("delta_gap_medio_vs_contexto") or 0)),
        reverse=True,
    )
    analise_resumida["microambiente_por_interseccao_prioritaria"] = interseccoes[:12]

    if isinstance(analise.get("comparativo_empresas_mesma_holding"), list):
        analise_resumida["comparativo_empresas_mesma_holding"] = [
            _compactar_perfil_para_ia(item)
            for item in analise["comparativo_empresas_mesma_holding"][:8]
        ]
    if isinstance(analise.get("afirmacoes_mais_impactantes"), list):
        analise_resumida["afirmacoes_mais_impactantes"] = analise["afirmacoes_mais_impactantes"][:10]

    participacao = analise.get("participacao") or {}
    analise_resumida["participacao"] = {
        "observacao": participacao.get("observacao"),
        "total_respostas_equipe": participacao.get("total_respostas_equipe"),
        "por_departamento": (participacao.get("por_departamento") or [])[:6],
        "por_area": (participacao.get("por_area") or [])[:6],
        "por_lider": (participacao.get("por_lider") or [])[:8],
        "por_empresa": (participacao.get("por_empresa") or [])[:8],
    }

    return {
        "tipo": pacote.get("tipo"),
        "gerado_em": pacote.get("gerado_em"),
        "contexto": pacote.get("contexto") or {},
        "filtros": pacote.get("filtros") or {},
        "governanca": pacote.get("governanca") or {},
        "amostra": pacote.get("amostra") or {},
        "distribuicoes_resumidas": distribuicoes_resumidas,
        "saude_emocional": pacote.get("saude_emocional") or {},
        "microambiente": pacote.get("microambiente") or {},
        "arquetipos": pacote.get("arquetipos") or {},
        "analise_profunda": analise_resumida,
        "achados_relevantes": achados,
        "observacao_de_resumo": (
            "Este pacote foi resumido para IA. O pacote completo permanece disponivel "
            "no dashboard para download e auditoria."
        ),
    }


def build_organizational_prompt(pacote: dict[str, Any]) -> str:
    return (
        "Voce e o Assistente Inteligente LeaderTrack em modo de devolutiva organizacional "
        "para RH, CEO e diretoria. Use exclusivamente o pacote analitico JSON recebido. "
        "Nao invente percentuais, causas, diagnosticos, nomes, historico ou cruzamentos. "
        "Se um dado ou cruzamento nao estiver no pacote, diga que nao ha informacao suficiente "
        "ou simplesmente omita o ponto. Saude emocional pode ser analisada somente em nivel "
        "organizacional/agregado; nunca escreva como devolutiva individual para lider. "
        "Nao faca diagnostico clinico nem atribua culpa a lideres. "
        "Use Daniel Goleman/HBR apenas como apoio conceitual de repertorio situacional, "
        "sem citacao textual, sem dizer que Goleman prova o resultado e sem substituir o modelo LeaderTrack. "
        "Separe fato medido, hipotese prudente e recomendacao pratica. "
        "Gere uma devolutiva premium, visual e executiva, com resumo, achados prioritarios, "
        "graficos sugeridos, riscos, fortalezas e plano 30/60/90 dias. "
        "Responda em JSON valido com secoes: resumo_executivo, indicadores_chave, "
        "saude_emocional_organizacional, microambiente, arquetipos, achados_prioritarios, "
        "graficos_recomendados, plano_30_60_90, cuidados_de_leitura.\n\n"
        f"PACOTE_ANALITICO_JSON:\n{json.dumps(pacote, ensure_ascii=False, indent=2, default=str)}"
    )
