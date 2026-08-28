import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client, Client
import pandas as pd
import json
import html
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import openpyxl
import time
import urllib.error
import urllib.request
from urllib.parse import quote
from leadertrack_organizacional import (
    OrganizationalRules,
    gerar_pacote_organizacional,
    pacote_organizacional_para_ia,
)

# === Configuração global ===
NORMALIZAR_POR_SUBDIMENSAO = False
PARECER_INTELIGENTE_ORG_URL = (
    "https://parecer-inteligente.onrender.com/"
    "gerar-devolutiva-organizacional-leadertrack"
)

# ==================== FUNÇÕES SAÚDE EMOCIONAL ====================

def analisar_afirmacoes_saude_emocional(matriz_arq, matriz_micro, df_arquetipos, df_microambiente, filtros):
    import pandas as pd
    import os

    arquivo_csv = 'TABELA_SAUDE_EMOCIONAL.csv'
    if not os.path.exists(arquivo_csv):
        st.error(f"❌ CSV não encontrado: {arquivo_csv}")
        return [], df_arquetipos, df_microambiente

    df_csv = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig')
    df_csv['TIPO'] = df_csv['TIPO'].astype(str).str.strip().str.upper()
    df_csv['COD_AFIRMACAO'] = df_csv['COD_AFIRMACAO'].astype(str).str.strip()
    df_csv['DIMENSAO_SAUDE_EMOCIONAL'] = (
        df_csv['DIMENSAO_SAUDE_EMOCIONAL']
        .astype(str).str.strip()
        .replace({'Equilíbrio Vida- Trabalho': 'Equilíbrio Vida-Trabalho'})
    )

    st.info(f"✅ CSV de Saúde Emocional carregado: {len(df_csv)} afirmações (esperado: 97)")
    contagem_dim = df_csv['DIMENSAO_SAUDE_EMOCIONAL'].value_counts().sort_index()
    st.write("📋 Distribuição por dimensão (TABELA_SAUDE_EMOCIONAL):")
    for dim, qtd in contagem_dim.items():
        st.write(f"- {dim}: {qtd} afirmações")

    df_arq_filtrado = df_arquetipos.copy()
    df_micro_filtrado = df_microambiente.copy()

    if filtros['empresa'] != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['empresa'] == filtros['empresa']]
    if filtros['codrodada'] != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['codrodada'] == filtros['codrodada']]
    if filtros.get('emaillider', "Todos") != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['emailLider'] == filtros['emaillider']]
    if filtros['estado'] != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['estado'] == filtros['estado']]
    if filtros['sexo'] != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['sexo'] == filtros['sexo']]
    if filtros['etnia'] != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['etnia'] == filtros['etnia']]
    if filtros['departamento'] != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['departamento'] == filtros['departamento']]
    if filtros['cargo'] != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['cargo'] == filtros['cargo']]
    if 'holding' in filtros and filtros['holding'] != "Todas":
        if 'holding' in df_arq_filtrado.columns:
            holding_filtro = str(filtros['holding']).upper().strip()
            df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro]

    if filtros['empresa'] != "Todas":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['empresa'] == filtros['empresa']]
    if filtros['codrodada'] != "Todas":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['codrodada'] == filtros['codrodada']]
    if filtros['estado'] != "Todos":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['estado'] == filtros['estado']]
    if filtros['sexo'] != "Todos":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['sexo'] == filtros['sexo']]
    if filtros['etnia'] != "Todas":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['etnia'] == filtros['etnia']]
    if filtros['departamento'] != "Todos":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['departamento'] == filtros['departamento']]
    if filtros['cargo'] != "Todos":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['cargo'] == filtros['cargo']]
    if 'holding' in filtros and filtros['holding'] != "Todas":
        if 'holding' in df_micro_filtrado.columns:
            holding_filtro = str(filtros['holding']).upper().strip()
            df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro]

    csv_dict = {}
    for _, row in df_csv.iterrows():
        tipo = str(row['TIPO']).upper().strip()
        codigo = str(row['COD_AFIRMACAO']).strip()
        dimensao_se = row['DIMENSAO_SAUDE_EMOCIONAL']
        if tipo.startswith('ARQ'):
            tipo_codigo = f"arq_{codigo}"
        elif tipo.startswith('MICRO'):
            tipo_codigo = f"micro_{codigo}"
        else:
            continue
        csv_dict[tipo_codigo] = dimensao_se

    afirmacoes_se = []
    codigos_processados = set()

    matriz_arq_unicos = matriz_arq[['COD_AFIRMACAO', 'AFIRMACAO', 'ARQUETIPO']].drop_duplicates(subset=['COD_AFIRMACAO'])
    for _, row in matriz_arq_unicos.iterrows():
        codigo = str(row['COD_AFIRMACAO']).strip()
        tipo_codigo = f"arq_{codigo}"
        if tipo_codigo in csv_dict and tipo_codigo not in codigos_processados:
            afirmacoes_se.append({
                'tipo': 'Arquétipo',
                'afirmacao': row['AFIRMACAO'],
                'dimensao': row['ARQUETIPO'],
                'subdimensao': 'N/A',
                'chave': codigo,
                'dimensao_saude_emocional': csv_dict[tipo_codigo]
            })
            codigos_processados.add(tipo_codigo)

    matriz_micro_unicos = matriz_micro[['COD', 'AFIRMACAO', 'DIMENSAO', 'SUBDIMENSAO']].drop_duplicates(subset=['COD'])
    for _, row in matriz_micro_unicos.iterrows():
        codigo = str(row['COD']).strip()
        tipo_codigo = f"micro_{codigo}"
        if tipo_codigo in csv_dict and tipo_codigo not in codigos_processados:
            afirmacoes_se.append({
                'tipo': 'Microambiente',
                'afirmacao': row['AFIRMACAO'],
                'dimensao': row['DIMENSAO'],
                'subdimensao': row['SUBDIMENSAO'],
                'chave': codigo,
                'dimensao_saude_emocional': csv_dict[tipo_codigo]
            })
            codigos_processados.add(tipo_codigo)

    st.info(f"📊 Total encontrado na página de Saúde Emocional: {len(afirmacoes_se)} afirmações (esperado: 97)")
    return afirmacoes_se, df_arq_filtrado, df_micro_filtrado


def mapear_compliance_nr1(afirmacoes_saude_emocional):
    requisitos_nr1 = {
        'Prevenção de Estresse': [],
        'Ambiente Psicológico Seguro': [],
        'Suporte Emocional': [],
        'Comunicação Positiva': [],
        'Equilíbrio Vida-Trabalho': []
    }
    for afirmacao in afirmacoes_saude_emocional:
        dimensao_se = afirmacao.get('dimensao_saude_emocional', 'Suporte Emocional')
        if dimensao_se in requisitos_nr1:
            requisitos_nr1[dimensao_se].append(afirmacao)
        else:
            requisitos_nr1['Suporte Emocional'].append(afirmacao)
    return requisitos_nr1


def chamar_parecer_organizacional(pacote_analitico, gerar_com_ia=True):
    payload = {
        "pacote_analitico": pacote_analitico,
        "gerarComIA": bool(gerar_com_ia),
        "persistir": False,
        "modelo": "gpt-4o-mini",
        "maxTokens": 3400,
        "timeout": 45,
    }

    def enviar(payload_atual):
        body = json.dumps(payload_atual, ensure_ascii=False, default=str).encode("utf-8")
        req = urllib.request.Request(
            PARECER_INTELIGENTE_ORG_URL,
            data=body,
            method="POST",
            headers={
                "Content-Type": "application/json",
                "Origin": "https://gestor.thehrkey.tech",
            },
        )
        with urllib.request.urlopen(req, timeout=140) as resp:
            texto = resp.read().decode("utf-8")
            return json.loads(texto)

    ultimo_erro = None
    for tentativa in range(1, 3):
        try:
            resposta = enviar(payload)
            if tentativa > 1 and isinstance(resposta, dict):
                resposta.setdefault("geracao_ia", {})
                resposta["geracao_ia"]["tentativas_dashboard"] = tentativa
            return resposta, None
        except urllib.error.HTTPError as e:
            try:
                detalhe = e.read().decode("utf-8")
            except Exception:
                detalhe = str(e)
            ultimo_erro = f"Erro HTTP {e.code} ao chamar o bot: {detalhe}"
            if e.code < 500 or tentativa == 2:
                break
        except Exception as e:
            ultimo_erro = f"Erro ao chamar o bot: {str(e)}"
            if tentativa == 2:
                break
        time.sleep(3)

    return None, (
        f"{ultimo_erro}\n\n"
        "A primeira tentativa pode falhar quando o Render acorda ou quando a IA demora. "
        "Tente novamente; se repetir, gere sem IA para manter os dados e depois rode a camada executiva."
    )


def exibir_resposta_parecer_organizacional(resposta):
    if not isinstance(resposta, dict):
        st.write(resposta)
        return

    devolutiva = resposta.get("devolutiva")
    if not isinstance(devolutiva, dict):
        st.json(resposta)
        return

    for chave, valor in devolutiva.items():
        titulo = str(chave).replace("_", " ").title()
        st.subheader(titulo)
        exibir_bloco_parecer_organizacional(valor)


def enviar_parecer_organizacional_para_wordpress(resposta, pacote):
    if not isinstance(resposta, dict):
        return

    devolutiva = resposta.get("devolutiva")
    if not isinstance(devolutiva, dict):
        return

    payload = {
        "tipo": "hrkey_leadertrack_devolutiva_executiva",
        "versao": "v1",
        "gerado_em": datetime.utcnow().isoformat() + "Z",
        "contexto": resposta.get("contexto") or (pacote or {}).get("contexto") or {},
        "filtros": resposta.get("filtros") or (pacote or {}).get("filtros") or {},
        "amostra": resposta.get("amostra") or (pacote or {}).get("amostra") or {},
        "governanca": resposta.get("governanca") or (pacote or {}).get("governanca") or {},
        "geracao_ia": resposta.get("geracao_ia") or {},
        "devolutiva": devolutiva,
        "base_analitica": {
            "distribuicoes": (pacote or {}).get("distribuicoes") or {},
            "saude_emocional": (pacote or {}).get("saude_emocional") or {},
            "microambiente": (pacote or {}).get("microambiente") or {},
            "arquetipos": (pacote or {}).get("arquetipos") or {},
            "achados_relevantes": (pacote or {}).get("achados_relevantes") or [],
            "analise_profunda": (pacote or {}).get("analise_profunda") or {},
        },
    }

    components.html(
        f"""
        <script>
        (function () {{
          const message = {{
            type: "hrkey:leadertrack:devolutiva-executiva",
            payload: {json.dumps(payload, ensure_ascii=False, default=str)}
          }};
          const targetOrigin = "https://gestor.thehrkey.tech";
          const targets = [window.parent, window.parent && window.parent.parent, window.top];
          try {{
            targets.forEach(function (target) {{
              if (target) target.postMessage(message, targetOrigin);
            }});
          }} catch (e) {{}}
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def exibir_bloco_parecer_organizacional(valor, nivel=0):
    if valor is None:
        st.caption("Sem informação suficiente no pacote analítico.")
        return

    if isinstance(valor, str):
        st.markdown(valor)
        return

    if isinstance(valor, (int, float, bool)):
        st.write(valor)
        return

    if isinstance(valor, list):
        if not valor:
            st.caption("Sem itens para exibir.")
            return
        if all(isinstance(item, dict) for item in valor):
            for idx, item in enumerate(valor, start=1):
                titulo_item = (
                    item.get("titulo")
                    or item.get("achado")
                    or item.get("descricao")
                    or item.get("horizonte")
                    or item.get("nome")
                    or f"Item {idx}"
                )
                with st.expander(str(titulo_item), expanded=idx <= 3):
                    exibir_bloco_parecer_organizacional(item, nivel + 1)
            return
        for item in valor:
            if isinstance(item, str):
                st.markdown(f"- {item}")
            else:
                exibir_bloco_parecer_organizacional(item, nivel + 1)
        return

    if isinstance(valor, dict):
        for chave, conteudo in valor.items():
            rotulo = str(chave).replace("_", " ").capitalize()
            if isinstance(conteudo, (dict, list)):
                st.markdown(f"**{rotulo}**")
                exibir_bloco_parecer_organizacional(conteudo, nivel + 1)
            else:
                st.markdown(f"**{rotulo}:** {conteudo}")
        return

    st.write(valor)


def _primeira_coluna_texto(df):
    for col in df.columns:
        if df[col].dtype == "object":
            return col
    return df.columns[0] if len(df.columns) else None


def _primeira_coluna_numerica(df, preferidas=None):
    preferidas = preferidas or ["score", "score_final", "media", "percentual", "gap", "delta", "n"]
    for col in preferidas:
        if col in df.columns and pd.api.types.is_numeric_dtype(pd.to_numeric(df[col], errors="coerce")):
            return col
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(pd.to_numeric(df[col], errors="coerce")):
            return col
    return None


def exibir_grafico_lista_organizacional(titulo, linhas, limite=12):
    if not isinstance(linhas, list) or not linhas:
        return
    df = pd.DataFrame(linhas).head(limite)
    if df.empty:
        return
    x_col = _primeira_coluna_texto(df)
    y_col = _primeira_coluna_numerica(df)
    if not x_col or not y_col:
        st.dataframe(df, use_container_width=True, hide_index=True)
        return
    df[y_col] = pd.to_numeric(df[y_col], errors="coerce")
    df = df.dropna(subset=[y_col])
    if df.empty:
        return
    fig = px.bar(df, x=x_col, y=y_col, title=titulo, text=y_col)
    fig.update_layout(height=360, margin=dict(l=20, r=20, t=55, b=20))
    st.plotly_chart(fig, use_container_width=True)


def exibir_visao_visual_parecer_organizacional(pacote):
    if not isinstance(pacote, dict):
        return

    st.subheader("Painel visual do parecer")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        micro = pacote.get("microambiente") or {}
        for chave in ["dimensoes", "subdimensoes", "gaps_dimensoes", "gaps_subdimensoes"]:
            if isinstance(micro.get(chave), list) and micro.get(chave):
                exibir_grafico_lista_organizacional(
                    f"Microambiente - {chave.replace('_', ' ')}",
                    micro.get(chave),
                )
                break
    with col_v2:
        arquetipos = pacote.get("arquetipos") or {}
        for chave in ["dominantes", "scores", "arquetipos"]:
            if isinstance(arquetipos.get(chave), list) and arquetipos.get(chave):
                exibir_grafico_lista_organizacional(
                    f"Arquétipos - {chave.replace('_', ' ')}",
                    arquetipos.get(chave),
                )
                break

    saude = pacote.get("saude_emocional") or {}
    for chave in ["recortes", "dimensoes", "cruzamentos"]:
        if isinstance(saude.get(chave), list) and saude.get(chave):
            exibir_grafico_lista_organizacional(
                f"Saúde emocional - {chave.replace('_', ' ')}",
                saude.get(chave),
            )
            break

    distribuicoes = pacote.get("distribuicoes") or {}
    if isinstance(distribuicoes, dict) and distribuicoes:
        st.subheader("Distribuições da amostra")
        cols_dist = st.columns(2)
        idx = 0
        for campo, linhas in distribuicoes.items():
            if not isinstance(linhas, list) or not linhas:
                continue
            with cols_dist[idx % 2]:
                exibir_grafico_lista_organizacional(
                    f"Amostra por {str(campo).replace('_', ' ')}",
                    linhas,
                    limite=10,
                )
            idx += 1


def _fmt_pct_org(valor):
    try:
        return f"{float(valor):.1f}%"
    except Exception:
        return "—"


def exibir_conceitos_leadertrack_organizacional():
    st.subheader("Caderno conceitual LeaderTrack")
    col_c1, col_c2, col_c3 = st.columns(3)
    with col_c1:
        st.markdown(
            """
            **Arquétipos de gestão**

            Os arquétipos representam padrões comportamentais percebidos na liderança. Eles não são rótulos fixos de personalidade: indicam repertórios que podem aparecer com mais ou menos força conforme contexto, pressão, maturidade da equipe e momento organizacional.

            Na leitura organizacional, o objetivo não é classificar um líder, mas observar quais repertórios aparecem com mais presença na cultura de gestão do recorte selecionado.
            """
        )
    with col_c2:
        st.markdown(
            """
            **Microambiente**

            O microambiente compara duas percepções: como a equipe percebe a experiência real e como entende que ela deveria ser. O gap é a distância entre prática percebida e expectativa coletiva.

            Na devolutiva executiva, o gap médio mostra onde a cultura está mais distante do ambiente desejável para colaboração, clareza, reconhecimento, responsabilidade, adaptabilidade e performance.
            """
        )
    with col_c3:
        st.markdown(
            """
            **Saúde emocional organizacional**

            A saúde emocional é tratada somente em nível agregado. Ela observa sinais coletivos de segurança psicológica percebida, reconhecimento, suporte, comunicação positiva e equilíbrio.

            Este bloco não deve ser usado para diagnóstico clínico nem para devolutiva individual. A leitura serve para orientar perguntas de governança, cuidado institucional e qualidade das relações de trabalho.
            """
        )


def _linhas_arquetipos_por_questao(df_filtrado_arq, matriz_arq):
    if df_filtrado_arq is None or df_filtrado_arq.empty or matriz_arq is None or matriz_arq.empty:
        return []
    df_equipe_arq = df_filtrado_arq[df_filtrado_arq["tipo"] == "Avaliação Equipe"]
    if df_equipe_arq.empty:
        return []
    linhas = []
    matriz_base = matriz_arq[["COD_AFIRMACAO", "AFIRMACAO", "ARQUETIPO"]].drop_duplicates()
    for _, row in matriz_base.iterrows():
        codigo = row.get("COD_AFIRMACAO")
        arquetipo = row.get("ARQUETIPO")
        percentual, tendencia, n_resp = calcular_tendencia_arquetipos_por_questao(
            df_equipe_arq, matriz_arq, codigo, arquetipo
        )
        if percentual is None:
            continue
        linhas.append({
            "Questão": codigo,
            "Afirmação": row.get("AFIRMACAO"),
            "Arquétipo": arquetipo,
            "% Tendência": round(float(percentual), 1),
            "Tendência": tendencia,
            "N": n_resp,
        })
    return sorted(linhas, key=lambda item: abs(float(item.get("% Tendência") or 0)), reverse=True)


def _linhas_microambiente_por_questao(df_filtrado_micro, matriz_micro):
    if df_filtrado_micro is None or df_filtrado_micro.empty or matriz_micro is None or matriz_micro.empty:
        return []
    df_equipe_micro = df_filtrado_micro[df_filtrado_micro["tipo"] == "Avaliação Equipe"]
    if df_equipe_micro.empty:
        return []
    linhas = []
    matriz_base = matriz_micro[["COD", "AFIRMACAO", "DIMENSAO", "SUBDIMENSAO"]].drop_duplicates()
    for _, row in matriz_base.iterrows():
        real, ideal, gap = calcular_real_ideal_gap_por_questao(df_equipe_micro, matriz_micro, row.get("COD"))
        if real is None:
            continue
        linhas.append({
            "Questão": _MAP_MATRIZ_TO_FORM.get(row.get("COD"), row.get("COD")),
            "Afirmação": row.get("AFIRMACAO"),
            "Dimensão": row.get("DIMENSAO"),
            "Subdimensão": row.get("SUBDIMENSAO"),
            "Real (%)": round(float(real), 1),
            "Ideal (%)": round(float(ideal), 1),
            "Gap": round(float(gap), 1),
        })
    return sorted(linhas, key=lambda item: float(item.get("Gap") or 0), reverse=True)


def _grafico_waterfall_gaps(linhas_micro):
    top = [linha for linha in linhas_micro if float(linha.get("Gap") or 0) > 0][:12]
    if not top:
        return None
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=["relative"] * len(top),
        x=[linha["Questão"] for linha in top],
        y=[linha["Gap"] for linha in top],
        text=[f"{linha['Gap']:.1f}" for linha in top],
        connector={"line": {"color": "rgba(15,23,42,0.25)"}},
        increasing={"marker": {"color": "#ef4444"}},
        decreasing={"marker": {"color": "#0f766e"}},
    ))
    fig.update_layout(
        title="Waterfall dos maiores gaps de microambiente",
        yaxis_title="Gap médio",
        height=420,
        showlegend=False,
    )
    return fig


def _valor_float_org(valor, padrao=0.0):
    try:
        if valor is None or valor == "":
            return padrao
        return float(valor)
    except Exception:
        return padrao


def _texto_curto_org(valor, limite=140):
    texto = str(valor or "").strip()
    if len(texto) <= limite:
        return texto
    return texto[: limite - 1].rstrip() + "…"


def _chunks_org(lista, tamanho):
    for idx in range(0, len(lista), tamanho):
        yield lista[idx: idx + tamanho]


def _card_metrica_html_org(label, valor, nota=""):
    nota_html = f"<small>{html.escape(str(nota))}</small>" if nota else ""
    return (
        '<div class="metric-card">'
        f'<span>{html.escape(str(label))}</span>'
        f'<strong>{html.escape(str(valor))}</strong>'
        f"{nota_html}</div>"
    )


def _barra_dupla_html_org(titulo, labels, serie_a, serie_b, nome_a, nome_b):
    if not labels:
        return ""
    linhas = []
    for label, valor_a, valor_b in zip(labels, serie_a, serie_b):
        va = max(0, min(100, _valor_float_org(valor_a)))
        vb = max(0, min(100, _valor_float_org(valor_b)))
        linhas.append(
            '<div class="bar-row">'
            f'<div class="bar-label">{html.escape(str(label))}</div>'
            '<div class="bar-track">'
            f'<i class="bar-a" style="width:{va:.1f}%"></i>'
            f'<b>{va:.1f}%</b>'
            '</div>'
            '<div class="bar-track">'
            f'<i class="bar-b" style="width:{vb:.1f}%"></i>'
            f'<b>{vb:.1f}%</b>'
            '</div>'
            '</div>'
        )
    return (
        '<section class="page page-white">'
        f'<h2>{html.escape(titulo)}</h2>'
        f'<p class="legend"><span class="dot blue"></span>{html.escape(nome_a)} '
        f'<span class="dot orange"></span>{html.escape(nome_b)}</p>'
        '<div class="chart-card bar-chart">'
        + "".join(linhas)
        + '</div></section>'
    )


def _radar_svg_html_org(titulo, labels, serie_a, serie_b, nome_a, nome_b):
    if not labels:
        return ""
    cx, cy, raio = 300, 255, 160
    total = len(labels)

    def ponto(idx, valor):
        ang = -np.pi / 2 + (2 * np.pi * idx / max(total, 1))
        r = raio * max(0, min(100, _valor_float_org(valor))) / 100
        return cx + np.cos(ang) * r, cy + np.sin(ang) * r

    def poligono(valores):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in [ponto(i, v) for i, v in enumerate(valores)])

    grade = []
    for pct in [20, 40, 60, 80, 100]:
        pts = []
        for i in range(total):
            ang = -np.pi / 2 + (2 * np.pi * i / max(total, 1))
            r = raio * pct / 100
            pts.append(f"{cx + np.cos(ang) * r:.1f},{cy + np.sin(ang) * r:.1f}")
        grade.append(f'<polygon points="{" ".join(pts)}" fill="none" stroke="#d8e1ec" stroke-width="1"/>')

    eixos = []
    textos = []
    for i, label in enumerate(labels):
        ang = -np.pi / 2 + (2 * np.pi * i / max(total, 1))
        x = cx + np.cos(ang) * raio
        y = cy + np.sin(ang) * raio
        tx = cx + np.cos(ang) * (raio + 46)
        ty = cy + np.sin(ang) * (raio + 30)
        eixos.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" stroke="#e2e8f0"/>')
        textos.append(
            f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" '
            f'font-size="11" font-weight="700" fill="#172033">{html.escape(str(label))}</text>'
        )

    return (
        '<section class="page page-white">'
        + f'<h2>{html.escape(titulo)}</h2>'
        + '<p class="legend">'
        + f'<span class="dot blue"></span>{html.escape(nome_a)} '
        + f'<span class="dot orange"></span>{html.escape(nome_b)}</p>'
        + '<div class="chart-card radar-card">'
        + '<svg viewBox="0 0 600 520" role="img">'
        + "".join(grade)
        + "".join(eixos)
        + f'<polygon points="{poligono(serie_a)}" fill="rgba(55,151,228,.18)" stroke="#3797e4" stroke-width="4"/>'
        + f'<polygon points="{poligono(serie_b)}" fill="rgba(255,128,29,.18)" stroke="#ff801d" stroke-width="4"/>'
        + "".join(textos)
        + '</svg></div></section>'
    )


def _linha_svg_html_org(titulo, labels, real, ideal):
    if not labels:
        return ""
    largura, altura = 760, 360
    margem_x, margem_y = 70, 48
    plot_w, plot_h = largura - 2 * margem_x, altura - 2 * margem_y

    def pontos(valores):
        pts = []
        for i, valor in enumerate(valores):
            x = margem_x + (plot_w * i / max(len(labels) - 1, 1))
            y = margem_y + plot_h - (plot_h * max(0, min(100, _valor_float_org(valor))) / 100)
            pts.append((x, y))
        return pts

    pts_real = pontos(real)
    pts_ideal = pontos(ideal)

    linhas_grade = []
    for pct in [0, 25, 50, 75, 100]:
        y = margem_y + plot_h - (plot_h * pct / 100)
        linhas_grade.append(f'<line x1="{margem_x}" y1="{y:.1f}" x2="{largura-margem_x}" y2="{y:.1f}" stroke="#e5edf5"/>')
        linhas_grade.append(f'<text x="28" y="{y+4:.1f}" font-size="10" fill="#64748b">{pct}%</text>')

    rotulos = []
    for i, label in enumerate(labels):
        x = margem_x + (plot_w * i / max(len(labels) - 1, 1))
        rotulos.append(
            f'<text x="{x:.1f}" y="{altura-18}" text-anchor="middle" font-size="10" '
            f'font-weight="700" fill="#334155">{html.escape(_texto_curto_org(label, 16))}</text>'
        )

    def poly(pts):
        return " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)

    circulos = []
    for pts, cor in [(pts_real, "#ff801d"), (pts_ideal, "#1e3a8a")]:
        for x, y in pts:
            circulos.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="5" fill="{cor}"/>')

    return (
        '<section class="page page-white">'
        f'<h2>{html.escape(titulo)}</h2>'
        '<p class="legend"><span class="dot orange"></span>Como é percebido '
        '<span class="dot navy"></span>Como deveria ser</p>'
        '<div class="chart-card">'
        f'<svg viewBox="0 0 {largura} {altura}" role="img">'
        + "".join(linhas_grade)
        + f'<polyline points="{poly(pts_real)}" fill="none" stroke="#ff801d" stroke-width="4"/>'
        + f'<polyline points="{poly(pts_ideal)}" fill="none" stroke="#1e3a8a" stroke-width="4"/>'
        + "".join(circulos)
        + "".join(rotulos)
        + '</svg></div></section>'
    )


def _waterfall_html_org(titulo, linhas):
    top = [linha for linha in (linhas or []) if _valor_float_org(linha.get("Gap")) > 0][:12]
    if not top:
        return ""
    max_gap = max([_valor_float_org(item.get("Gap")) for item in top] + [1])
    barras = []
    for item in top:
        gap = _valor_float_org(item.get("Gap"))
        largura = min(100, gap / max_gap * 100)
        barras.append(
            '<div class="water-row">'
            f'<span>{html.escape(str(item.get("Questão") or ""))}</span>'
            f'<i style="width:{largura:.1f}%"></i>'
            f'<b>{gap:.1f} p.p.</b>'
            '</div>'
        )
    return (
        '<section class="page page-white">'
        f'<h2>{html.escape(titulo)}</h2>'
        '<p>Maiores distâncias entre experiência real percebida e ambiente desejável no recorte selecionado.</p>'
        '<div class="chart-card waterfall">'
        + "".join(barras)
        + '</div></section>'
    )


def _estrelas_html_org(percentual):
    estrelas = int(round(max(0, min(100, _valor_float_org(percentual))) / 100 * 6))
    cheias = "&#9733;" * estrelas
    vazias = "&#9734;" * (6 - estrelas)
    return f'<span class="stars">{cheias}<span>{vazias}</span></span>'


def _tabela_html_org(titulo, linhas, colunas):
    if not linhas:
        return f'<section class="page page-white"><h2>{html.escape(titulo)}</h2><p>Sem dados suficientes para este bloco.</p></section>'
    head = "".join(f"<th>{html.escape(str(col))}</th>" for col in colunas)
    body_rows = []
    for linha in linhas:
        cells = []
        for col in colunas:
            valor = linha.get(col, "")
            cells.append(f"<td>{html.escape(str(valor))}</td>")
        body_rows.append("<tr>" + "".join(cells) + "</tr>")
    return (
        f'<section class="page page-white table-page"><h2>{html.escape(titulo)}</h2>'
        f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body_rows)}</tbody></table></section>"
    )


def _tabela_paginas_html_org(titulo, linhas, colunas, por_pagina=18):
    if not linhas:
        return _tabela_html_org(titulo, linhas, colunas)
    partes = []
    for idx, bloco in enumerate(_chunks_org(linhas, por_pagina), start=1):
        sufixo = "" if idx == 1 else f" continuação {idx}"
        partes.append(_tabela_html_org(f"{titulo}{sufixo}", bloco, colunas))
    return "".join(partes)


def _render_parecer_ia_html_org(resposta):
    if not isinstance(resposta, dict):
        return ""
    ignorar = {"contexto", "filtros", "amostra", "governanca", "pacote_analitico", "status", "erro"}
    blocos = []
    for chave, valor in resposta.items():
        if chave in ignorar or valor in (None, "", [], {}):
            continue
        titulo = str(chave).replace("_", " ").title()
        if isinstance(valor, dict):
            itens = []
            for sub, conteudo in valor.items():
                if conteudo in (None, "", [], {}):
                    continue
                if isinstance(conteudo, list):
                    texto = "; ".join(str(x) for x in conteudo[:6])
                elif isinstance(conteudo, dict):
                    texto = "; ".join(f"{k}: {v}" for k, v in list(conteudo.items())[:8])
                else:
                    texto = str(conteudo)
                itens.append(f"<p><strong>{html.escape(str(sub).replace('_', ' ').title())}:</strong> {html.escape(texto)}</p>")
            conteudo_html = "".join(itens)
        elif isinstance(valor, list):
            lis = []
            for item in valor[:8]:
                if isinstance(item, dict):
                    texto = "; ".join(f"{k}: {v}" for k, v in list(item.items())[:8])
                else:
                    texto = str(item)
                lis.append(f"<li>{html.escape(texto)}</li>")
            conteudo_html = "<ul>" + "".join(lis) + "</ul>"
        else:
            conteudo_html = f"<p>{html.escape(str(valor))}</p>"
        if conteudo_html:
            blocos.append(f'<section class="page page-white insight-page"><h2>{html.escape(titulo)}</h2>{conteudo_html}</section>')
    return "".join(blocos)


def _linha_perfil_micro_org(item, rotulo=None):
    comparacao = item.get("comparacao_contexto") or {}
    maior_gap = item.get("maior_gap") or {}
    return {
        "Recorte": rotulo or item.get("rotulo") or item.get("valor") or "Contexto",
        "N": item.get("n", ""),
        "Gap médio": item.get("gap_medio", ""),
        "Vs contexto": comparacao.get("delta_gap_medio_vs_contexto", ""),
        "Maior gap": maior_gap.get("dimensao", ""),
        "Real": maior_gap.get("real", ""),
        "Ideal": maior_gap.get("ideal", ""),
        "Gap": maior_gap.get("gap", ""),
    }


def _render_base_analitica_html_org(pacote):
    analise = (pacote or {}).get("analise_profunda") or {}
    if not isinstance(analise, dict):
        return ""

    partes = [
        '<section class="page section-cover">'
        '<div class="kicker">05</div>'
        '<h1>Base analítica do parecer</h1>'
        '<p class="cover-sub">Relatórios calculados a partir do filtro selecionado, com comparação contra a média do contexto quando disponível.</p>'
        '</section>'
    ]

    referencia = analise.get("referencia_contexto") or {}
    if isinstance(referencia, dict):
        dims = referencia.get("dimensoes") or []
        cards_ref = "".join([
            _card_metrica_html_org("N do contexto", referencia.get("n", "—")),
            _card_metrica_html_org("Gap médio do contexto", _fmt_pct_org(referencia.get("gap_medio"))),
            _card_metrica_html_org("Maior gap", (referencia.get("maior_gap") or {}).get("dimensao", "—")),
            _card_metrica_html_org("Menor gap", (referencia.get("menor_gap") or {}).get("dimensao", "—")),
        ])
        linhas_dims = [
            {
                "Dimensão": item.get("dimensao"),
                "Real": item.get("real"),
                "Ideal": item.get("ideal"),
                "Gap": item.get("gap"),
                "Nível": item.get("nivel_gap"),
            }
            for item in dims
            if isinstance(item, dict)
        ]
        partes.append(
            '<section class="page page-white"><h2>Referência média do contexto</h2>'
            f'<div class="metric-grid">{cards_ref}</div>'
            + _tabela_html_org("Dimensões do contexto", linhas_dims, ["Dimensão", "Real", "Ideal", "Gap", "Nível"]).replace('class="page page-white table-page"', 'class="inline-table"').replace('class="page page-white"', 'class="inline-table"')
            + '</section>'
        )

    empresas = analise.get("comparativo_empresas_mesma_holding") or []
    if isinstance(empresas, list) and empresas:
        linhas_empresas = [_linha_perfil_micro_org(item, item.get("valor")) for item in empresas if isinstance(item, dict)]
        partes.append(_tabela_paginas_html_org("Comparativo de empresas da mesma holding", linhas_empresas, ["Recorte", "N", "Gap médio", "Vs contexto", "Maior gap", "Real", "Ideal", "Gap"], por_pagina=16))

    recortes = analise.get("microambiente_por_recorte") or {}
    if isinstance(recortes, dict):
        nomes = {
            "geracao": "Microambiente por geração",
            "sexo": "Microambiente por gênero",
            "etnia": "Microambiente por etnia",
            "departamento": "Microambiente por departamento",
            "area": "Microambiente por área",
            "cargo": "Microambiente por cargo",
            "estado": "Microambiente por estado",
            "cidade": "Microambiente por cidade",
            "empresa": "Microambiente por empresa",
            "filial_nome": "Microambiente por filial",
            "branch_name": "Microambiente por unidade",
        }
        for chave, titulo in nomes.items():
            linhas = recortes.get(chave) or []
            if not isinstance(linhas, list) or not linhas:
                continue
            linhas_render = [
                _linha_perfil_micro_org(item, f"{chave}: {item.get('valor')}")
                for item in linhas
                if isinstance(item, dict)
            ]
            partes.append(_tabela_paginas_html_org(titulo, linhas_render, ["Recorte", "N", "Gap médio", "Vs contexto", "Maior gap", "Real", "Ideal", "Gap"], por_pagina=16))

    cruzamentos = analise.get("microambiente_por_interseccao") or {}
    if isinstance(cruzamentos, dict):
        linhas_cruzamentos = []
        for _, linhas in cruzamentos.items():
            if not isinstance(linhas, list):
                continue
            for item in linhas:
                if isinstance(item, dict):
                    linhas_cruzamentos.append(_linha_perfil_micro_org(item, item.get("rotulo")))
        if linhas_cruzamentos:
            partes.append(_tabela_paginas_html_org("Interseccionalidades e cruzamentos críticos", linhas_cruzamentos, ["Recorte", "N", "Gap médio", "Vs contexto", "Maior gap", "Real", "Ideal", "Gap"], por_pagina=16))

    afirmacoes = analise.get("afirmacoes_mais_impactantes") or []
    if isinstance(afirmacoes, list) and afirmacoes:
        linhas_afirmacoes = [
            {
                "Código": item.get("codigo"),
                "Afirmação": item.get("afirmacao"),
                "Dimensão": item.get("dimensao"),
                "Subdimensão": item.get("subdimensao"),
                "N": item.get("n"),
                "Real": item.get("real"),
                "Ideal": item.get("ideal"),
                "Gap": item.get("gap"),
                "Severidade": item.get("severidade"),
            }
            for item in afirmacoes
            if isinstance(item, dict)
        ]
        partes.append(_tabela_paginas_html_org("Afirmações mais impactantes", linhas_afirmacoes, ["Código", "Afirmação", "Dimensão", "Subdimensão", "N", "Real", "Ideal", "Gap", "Severidade"], por_pagina=14))

    participacao = analise.get("participacao") or {}
    if isinstance(participacao, dict):
        partes_part = []
        for chave, titulo in [
            ("por_empresa", "Aderência por empresa"),
            ("por_departamento", "Aderência por departamento"),
            ("por_area", "Aderência por área"),
            ("por_lider", "Líderes com maior volume de respostas"),
        ]:
            linhas = participacao.get(chave) or []
            if not isinstance(linhas, list) or not linhas:
                continue
            linhas_render = [
                {
                    "Campo": item.get("campo"),
                    "Valor": item.get("valor"),
                    "Respostas": item.get("respostas"),
                    "% amostra": item.get("percentual_da_amostra"),
                }
                for item in linhas
                if isinstance(item, dict)
            ]
            partes_part.append(_tabela_html_org(titulo, linhas_render, ["Campo", "Valor", "Respostas", "% amostra"]).replace('class="page page-white table-page"', 'class="inline-table"').replace('class="page page-white"', 'class="inline-table"'))
        if partes_part:
            partes.append(
                '<section class="page page-white"><h2>Participação e aderência</h2>'
                f'<p>{html.escape(str(participacao.get("observacao") or ""))}</p>'
                + "".join(partes_part)
                + '</section>'
            )

    return "".join(partes)


def gerar_caderno_executivo_organizacional_html(
    pacote,
    linhas_arq,
    linhas_micro,
    filtros,
    termo_label,
    gap_medio_questoes,
    gaps_relevantes,
    medias_auto=None,
    medias_equipe=None,
    arquetipos=None,
    medias_real_equipe=None,
    medias_ideal_equipe=None,
    dimensoes=None,
    resposta_ia=None,
):
    contexto = (pacote or {}).get("contexto") or {}
    amostra = (pacote or {}).get("amostra") or {}
    saude = (pacote or {}).get("saude_emocional") or {}
    categorias_saude = saude.get("categorias") or {}
    linhas_saude = [
        {"Categoria": nome, "Score": _fmt_pct_org(valor)}
        for nome, valor in categorias_saude.items()
        if valor is not None
    ] if isinstance(categorias_saude, dict) else []

    filtros_ativos = {
        k: v for k, v in (filtros or {}).items()
        if str(v or "").strip() and str(v).strip().lower() not in {"todos", "todas"}
    }
    filtros_html = "".join(
        f"<span>{html.escape(str(k))}: <strong>{html.escape(str(v))}</strong></span>"
        for k, v in filtros_ativos.items()
    ) or "<span>Contexto consolidado sem filtro secundário.</span>"

    top_arq = linhas_arq[:30]
    top_micro = linhas_micro[:30]
    top_gaps = gaps_relevantes[:12]
    arquetipos = arquetipos or ["Imperativo", "Resoluto", "Cuidativo", "Consultivo", "Prescritivo", "Formador"]
    medias_auto = medias_auto or [0] * len(arquetipos)
    medias_equipe = medias_equipe or [0] * len(arquetipos)
    dimensoes = dimensoes or ["Adaptabilidade", "Colaboração Mútua", "Nitidez", "Performance", "Reconhecimento", "Responsabilidade"]
    medias_real_equipe = medias_real_equipe or [0] * len(dimensoes)
    medias_ideal_equipe = medias_ideal_equipe or [0] * len(dimensoes)
    data_emissao = datetime.now().strftime("%d/%m/%Y")
    nivel_contexto = (
        contexto.get("nivel_contexto")
        or filtros.get("nivel_contexto")
        or "contexto"
    )
    contexto_nome = (
        contexto.get("contexto_nome")
        or contexto.get("holding_nome")
        or contexto.get("empresa_nome")
        or contexto.get("filial_nome")
        or filtros.get("holding")
        or filtros.get("empresa")
        or "Contexto selecionado"
    )
    rodada = filtros.get("codrodada") or contexto.get("codrodada") or "Todas"
    empresa = filtros.get("empresa") or contexto.get("empresa_nome") or "Todas"

    cards = "".join([
        _card_metrica_html_org("Contexto", contexto_nome),
        _card_metrica_html_org("Nível", str(nivel_contexto).title()),
        _card_metrica_html_org("Empresa", empresa),
        _card_metrica_html_org("Rodada", rodada),
        _card_metrica_html_org("Respondentes", amostra.get("respondentes", "—")),
        _card_metrica_html_org("Líderes", amostra.get("lideres", "—")),
        _card_metrica_html_org("Saúde emocional", _fmt_pct_org(saude.get("score_final"))),
        _card_metrica_html_org("Gap médio", _fmt_pct_org(gap_medio_questoes)),
        _card_metrica_html_org("Termômetro", termo_label),
    ])

    resumo_achados = "".join(
        f'<li><strong>{html.escape(str(item.get("Questão") or item.get("Codigo") or ""))}</strong> '
        f'{html.escape(_texto_curto_org(item.get("Afirmação") or item.get("afirmacao") or "", 190))} '
        f'<span>{html.escape(str(item.get("Gap") or item.get("gap") or ""))} p.p.</span></li>'
        for item in top_gaps[:8]
        if isinstance(item, dict)
    ) or "<li>Sem gaps relevantes no recorte selecionado.</li>"

    arq_cards = "".join(
        '<div class="question-card">'
        f'<h3>{html.escape(str(item.get("Questão") or ""))} | {html.escape(str(item.get("Arquétipo") or ""))}</h3>'
        f'<p>{html.escape(_texto_curto_org(item.get("Afirmação"), 210))}</p>'
        f'<div>{_estrelas_html_org(item.get("% Tendência"))}<strong>{html.escape(str(item.get("% Tendência") or ""))}%</strong>'
        f'<span>{html.escape(str(item.get("Tendência") or ""))}</span></div>'
        '</div>'
        for item in top_arq[:18]
    )

    micro_cards = "".join(
        '<div class="question-card">'
        f'<h3>{html.escape(str(item.get("Questão") or ""))} | {html.escape(str(item.get("Dimensão") or ""))}</h3>'
        f'<p>{html.escape(_texto_curto_org(item.get("Afirmação"), 210))}</p>'
        f'<div class="gap-line"><span>Real {_fmt_pct_org(item.get("Real (%)"))}</span>'
        f'<span>Ideal {_fmt_pct_org(item.get("Ideal (%)"))}</span>'
        f'<strong>Gap {_fmt_pct_org(item.get("Gap"))}</strong></div>'
        '</div>'
        for item in top_micro[:18]
    )

    return f"""<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <title>Caderno Executivo LeaderTrack</title>
  <style>
    @page {{ size: A4; margin: 0; }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; background: #eef3f7; color: #24324a; font-family: Inter, Arial, sans-serif; }}
    .page {{ width: 210mm; min-height: 297mm; margin: 0 auto 14px; padding: 18mm 20mm; background: #fff; page-break-after: always; position: relative; overflow: hidden; }}
    .page::after {{ content: "LeaderTrack | Página " counter(page); position: absolute; right: 18mm; bottom: 10mm; color: #64748b; font-size: 10px; font-weight: 700; }}
    .cover, .section-cover {{ color: #fff; background: linear-gradient(135deg, #1d2a3b 0%, #0f8f80 52%, #2f71c9 100%); padding: 28mm 23mm; }}
    .cover::before, .section-cover::before {{ content: ""; position: absolute; inset: 0; background: radial-gradient(circle at 84% 18%, rgba(255,255,255,.20) 0 50px, transparent 51px), radial-gradient(circle at 18% 82%, rgba(0,70,74,.28) 0 150px, transparent 151px); }}
    .cover > *, .section-cover > * {{ position: relative; z-index: 1; }}
    .kicker {{ letter-spacing: .16em; text-transform: uppercase; font-size: 12px; font-weight: 800; opacity: .88; }}
    h1 {{ font-size: 38px; line-height: 1.05; margin: 16px 0 10px; color: inherit; }}
    h2 {{ color: #233b6e; font-size: 24px; line-height: 1.18; margin: 0 0 16px; }}
    h3 {{ color: #00826f; font-size: 15px; margin: 14px 0 8px; }}
    p {{ font-size: 14px; line-height: 1.65; margin: 0 0 14px; }}
    .cover-sub {{ font-size: 20px; max-width: 650px; }}
    .cover-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; position: absolute; left: 23mm; right: 23mm; bottom: 27mm; }}
    .cover-box, .metric-card {{ border: 1px solid rgba(255,255,255,.32); border-radius: 8px; padding: 12px; background: rgba(255,255,255,.10); }}
    .cover-box span, .metric-card span {{ display: block; text-transform: uppercase; letter-spacing: .08em; font-size: 10px; font-weight: 900; color: inherit; opacity: .78; }}
    .cover-box strong, .metric-card strong {{ display: block; margin-top: 7px; font-size: 16px; line-height: 1.15; color: inherit; }}
    .metric-grid {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 22px 0; }}
    .metric-grid .metric-card {{ color: #14213d; border-color: #cbd7e4; background: #f7fafc; }}
    .metric-card small {{ display: block; color: #64748b; margin-top: 6px; font-size: 10px; }}
    .chips span {{ display: inline-block; border: 1px solid #d8e1ec; border-radius: 999px; padding: 7px 10px; margin: 0 6px 8px 0; font-size: 11px; background: #f8fafc; }}
    .concept-table, table {{ width: 100%; border-collapse: collapse; margin-top: 14px; font-size: 11px; }}
    th, td {{ border: 1px solid #d6dee8; padding: 8px; text-align: left; vertical-align: top; }}
    th {{ background: #f0f4f8; color: #3b4a62; text-transform: uppercase; font-size: 9px; letter-spacing: .06em; }}
    .chart-card {{ border: 1px solid #d5dee9; border-radius: 12px; background: #fff; padding: 18px; box-shadow: 0 18px 36px rgba(15,23,42,.08); }}
    .legend {{ font-size: 12px; color: #52627a; font-weight: 700; }}
    .dot {{ display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin: 0 6px 0 14px; }}
    .dot:first-child {{ margin-left: 0; }}
    .blue {{ background: #3797e4; }} .orange {{ background: #ff801d; }} .navy {{ background: #1e3a8a; }}
    .bar-row {{ display: grid; grid-template-columns: 115px 1fr 1fr; gap: 9px; align-items: center; margin: 12px 0; }}
    .bar-label {{ font-size: 11px; font-weight: 800; color: #22324b; }}
    .bar-track {{ height: 26px; background: #eef3f7; border-radius: 5px; position: relative; overflow: hidden; }}
    .bar-track i {{ display: block; height: 100%; border-radius: 5px; }}
    .bar-track b {{ position: absolute; right: 7px; top: 6px; font-size: 10px; color: #18283f; }}
    .bar-a {{ background: #3797e4; }} .bar-b {{ background: #ff9a3d; }}
    .water-row {{ display: grid; grid-template-columns: 72px 1fr 70px; gap: 10px; align-items: center; margin: 12px 0; }}
    .water-row span {{ font-weight: 900; color: #00826f; }}
    .water-row i {{ display: block; height: 25px; background: linear-gradient(90deg, #ffb15c, #ef4444); border-radius: 5px; }}
    .water-row b {{ font-size: 11px; }}
    .question-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }}
    .question-card {{ border: 1px solid #d6dee8; border-radius: 10px; padding: 12px; background: #fbfdff; break-inside: avoid; }}
    .question-card p {{ font-size: 11px; line-height: 1.45; }}
    .question-card div {{ display: flex; gap: 10px; align-items: center; font-size: 11px; }}
    .stars {{ color: #ff801d; font-size: 18px; letter-spacing: 1px; white-space: nowrap; }}
    .stars span {{ color: #dbe2ea; }}
    .gap-line {{ justify-content: space-between; }}
    .note {{ padding: 14px; border: 1px solid #f4cf74; background: #fff8dc; border-radius: 10px; }}
    .qr {{ width: 118px; height: 118px; border: 1px solid #cbd5e1; border-radius: 10px; float: right; margin-left: 18px; background: repeating-linear-gradient(45deg, #111 0 4px, #fff 4px 8px); }}
    .print-hint {{ margin: 0 auto 16px; width: 210mm; background: #0f766e; color: white; padding: 12px 16px; font-weight: 800; }}
    @media print {{
      body {{ background: #fff; }}
      .print-hint {{ display: none; }}
      .page {{ margin: 0; box-shadow: none; }}
    }}
  </style>
</head>
<body>
  <div class="print-hint no-print">Use Ctrl+P ou o comando Imprimir do navegador e salve como PDF.</div>
  <section class="page cover">
    <div class="kicker">The HR Key | LeaderTrack</div>
    <h1>Devolutiva Executiva Organizacional</h1>
    <p class="cover-sub">Leitura corporativa agregada do microambiente, arquétipos de liderança, saúde emocional organizacional e comparativos do recorte selecionado.</p>
    <div class="cover-grid">
      <div class="cover-box"><span>Contexto</span><strong>{html.escape(str(contexto_nome))}</strong></div>
      <div class="cover-box"><span>Nível</span><strong>{html.escape(str(nivel_contexto).title())}</strong></div>
      <div class="cover-box"><span>Empresa</span><strong>{html.escape(str(empresa))}</strong></div>
      <div class="cover-box"><span>Rodada</span><strong>{html.escape(str(rodada))}</strong></div>
    </div>
  </section>
  <section class="page section-cover">
    <div class="kicker">01</div>
    <h1>Guia executivo de leitura</h1>
    <p class="cover-sub">Este caderno foi desenhado para apoiar CEO, diretoria, RH e lideranças autorizadas na leitura do contexto organizacional, sem expor pessoas individualmente.</p>
  </section>
  <section class="page page-white">
    <h2>Fundamentos técnicos</h2>
    <p><strong>Arquétipos:</strong> padrões comportamentais percebidos na liderança, tratados como repertórios situacionais. A leitura executiva observa quais formas de liderar ganham força no recorte, sem reduzir a análise a rótulo individual.</p>
    <p><strong>Microambiente:</strong> compara a experiência real percebida pela equipe com o ambiente considerado desejável. O gap é a distância entre prática percebida e expectativa coletiva.</p>
    <p><strong>Saúde emocional:</strong> leitura agregada de segurança psicológica, reconhecimento, suporte, comunicação positiva, equilíbrio e qualidade relacional. Em linguagem inspirada por Daniel Goleman, a análise observa sinais coletivos de autoconsciência, autorregulação, empatia, motivação e qualidade das relações no ambiente de trabalho.</p>
    <div class="qr"></div>
    <h3>Como a IA entra nesta entrega</h3>
    <p>A base do caderno é calculada a partir dos dados reais do filtro. A IA atua como camada interpretativa: organiza hipóteses prudentes, perguntas executivas e sugestões de investigação, sempre subordinada aos indicadores e às regras de amostra mínima.</p>
    <div class="note">Saúde emocional é sempre agregada. Este material não é diagnóstico clínico, avaliação individual, nem ranking de pessoas.</div>
  </section>
  <section class="page page-white">
    <h2>Resumo executivo do recorte</h2>
    <div class="chips">{filtros_html}</div>
    <div class="metric-grid">{cards}</div>
    <h3>Questões mais sensíveis para decisão executiva</h3>
    <ul class="summary-list">{resumo_achados}</ul>
  </section>
  {_render_parecer_ia_html_org(resposta_ia)}
  <section class="page section-cover">
    <div class="kicker">02</div>
    <h1>Arquétipos</h1>
    <p class="cover-sub">Repertório de liderança observado no recorte selecionado.</p>
  </section>
  <section class="page page-white">
    <h2>Guia rápido dos arquétipos</h2>
    <table class="concept-table"><thead><tr><th>Arquétipo</th><th>O que costuma ativar</th><th>Quando funciona bem</th><th>Quando pede equilíbrio</th></tr></thead><tbody>
      <tr><td>Resoluto</td><td>Direção, clareza de rumo e foco em prioridades.</td><td>Quando a equipe precisa entender para onde ir.</td><td>Sem escuta suficiente, pode parecer unilateral.</td></tr>
      <tr><td>Consultivo</td><td>Escuta, participação e construção conjunta.</td><td>Quando há maturidade para envolver a equipe.</td><td>Em excesso, pode tornar decisões lentas.</td></tr>
      <tr><td>Formador</td><td>Desenvolvimento, autonomia progressiva e aprendizagem.</td><td>Quando o objetivo é fortalecer capacidade.</td><td>Em urgências, precisa ser combinado com direção.</td></tr>
      <tr><td>Cuidativo</td><td>Vínculo, acolhimento, confiança e cuidado.</td><td>Quando a equipe precisa de segurança relacional.</td><td>Pode adiar conversas difíceis se virar padrão único.</td></tr>
      <tr><td>Prescritivo</td><td>Padrão, método e qualidade de execução.</td><td>Quando há pessoas novas ou processo crítico.</td><td>Pode reduzir autonomia quando domina.</td></tr>
      <tr><td>Imperativo</td><td>Comando, decisão rápida e correção imediata.</td><td>Quando há urgência operacional.</td><td>Como padrão frequente, pode reduzir abertura e confiança.</td></tr>
    </tbody></table>
  </section>
  {_barra_dupla_html_org("Comparativo de Arquétipos", arquetipos, medias_auto, medias_equipe, "Autoavaliações médias", "Percepção média das equipes")}
  {_radar_svg_html_org("Arquétipos | Spider de repertório", arquetipos, medias_auto, medias_equipe, "Autoavaliações médias", "Percepção média das equipes")}
  <section class="page page-white"><h2>Afirmações de arquétipos mais marcantes</h2><div class="question-grid">{arq_cards}</div></section>
  {_tabela_paginas_html_org("Relatório analítico por questão de arquétipos", linhas_arq, ["Questão", "Afirmação", "Arquétipo", "% Tendência", "Tendência", "N"])}
  <section class="page section-cover">
    <div class="kicker">03</div>
    <h1>Microambiente</h1>
    <p class="cover-sub">Distância entre experiência real percebida e ambiente desejável.</p>
  </section>
  {_linha_svg_html_org("Microambiente | Real versus ideal", dimensoes, medias_real_equipe, medias_ideal_equipe)}
  {_waterfall_html_org("Waterfall dos maiores gaps", top_micro)}
  <section class="page page-white"><h2>Questões críticas de microambiente</h2><div class="question-grid">{micro_cards}</div></section>
  {_tabela_paginas_html_org("Maiores gaps de microambiente", gaps_relevantes, ["Questão", "Afirmação", "Dimensão", "Subdimensão", "Real (%)", "Ideal (%)", "Gap"])}
  {_tabela_paginas_html_org("Relatório analítico por questão de microambiente", linhas_micro, ["Questão", "Afirmação", "Dimensão", "Subdimensão", "Real (%)", "Ideal (%)", "Gap"])}
  <section class="page section-cover">
    <div class="kicker">04</div>
    <h1>Saúde emocional</h1>
    <p class="cover-sub">Clima emocional agregado e protegido por amostra mínima.</p>
  </section>
  <section class="page page-white">
    <h2>Leitura técnica de saúde emocional</h2>
    <p>A saúde emocional organizacional observa sinais coletivos de segurança para falar, percepção de suporte, reconhecimento, equilíbrio, comunicação e qualidade das relações. O objetivo é orientar governança e investigação, não produzir diagnóstico individual.</p>
    <div class="metric-grid">
      {_card_metrica_html_org("Score agregado", _fmt_pct_org(saude.get("score_final")))}
      {_card_metrica_html_org("Amostra", amostra.get("respondentes", "—"))}
      {_card_metrica_html_org("Recorte", contexto_nome)}
      {_card_metrica_html_org("Cuidado", "Agregado")}
    </div>
  </section>
  {_tabela_paginas_html_org("Score de saúde emocional por categoria", linhas_saude, ["Categoria", "Score"], por_pagina=22)}
  {_render_base_analitica_html_org(pacote)}
  <section class="page page-white note">
    <h2>Cuidados de leitura</h2>
    <p>Este caderno usa somente dados carregados no filtro atual. Recortes com amostra pequena devem ser lidos como sinais de investigação, não como conclusão fechada. A saúde emocional é sempre agregada.</p>
  </section>
</body>
</html>"""


def exibir_entrega_executiva_organizacional(
    pacote,
    matriz_arq,
    matriz_micro,
    df_arquetipos,
    df_microambiente,
    filtros,
):
    st.divider()
    st.header("Devolutiva executiva ampliada")
    st.caption(
        "Camada calculada com os mesmos fundamentos da devolutiva individual, "
        "mas agregada para o filtro organizacional selecionado."
    )

    exibir_conceitos_leadertrack_organizacional()

    (
        arquétipos,
        medias_auto,
        medias_equipe,
        df_filtrado_arq,
    ) = calcular_medias_arquetipos(df_arquetipos, filtros)
    (
        dimensoes,
        _medias_real_auto,
        _medias_ideal_auto,
        medias_real_equipe,
        medias_ideal_equipe,
        _medias_sub_real,
        _medias_sub_ideal,
        df_filtrado_micro,
    ) = calcular_medias_microambiente(df_microambiente, filtros)

    linhas_arq = _linhas_arquetipos_por_questao(df_filtrado_arq, matriz_arq)
    linhas_micro = _linhas_microambiente_por_questao(df_filtrado_micro, matriz_micro)
    gaps_relevantes = [linha for linha in linhas_micro if float(linha.get("Gap") or 0) >= 20]
    gap_medio_questoes = float(np.mean([linha["Gap"] for linha in linhas_micro])) if linhas_micro else 0.0
    termo_label = "ALTO ESTÍMULO" if gap_medio_questoes <= 5 else "ESTÍMULO" if gap_medio_questoes <= 10 else "NEUTRO" if gap_medio_questoes <= 15 else "BAIXO ESTÍMULO" if gap_medio_questoes <= 20 else "DESMOTIVAÇÃO"

    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric("Gap médio das questões", _fmt_pct_org(gap_medio_questoes))
    with col_m2:
        st.metric("Questões com gap >= 20", len(gaps_relevantes))
    with col_m3:
        st.metric("Termômetro médio", termo_label)
    with col_m4:
        score_saude = ((pacote or {}).get("saude_emocional") or {}).get("score_final")
        st.metric("Saúde emocional", "—" if score_saude is None else _fmt_pct_org(score_saude))

    aba_conceito, aba_arq, aba_micro, aba_saude, aba_export = st.tabs([
        "Base conceitual",
        "Arquétipos por questão",
        "Microambiente e gaps",
        "Saúde emocional",
        "Exportações",
    ])

    with aba_conceito:
        st.markdown(
            """
            Esta versão organizacional não substitui a devolutiva individual do líder. Ela muda a unidade de leitura: sai a pessoa específica e entra o recorte selecionado no dashboard, como holding, empresa, filial, região, área, cargo, geração, gênero, etnia ou combinação protegida por amostra mínima.

            A interpretação deve sempre separar três camadas: o dado medido, a hipótese prudente e a pergunta executiva. Quando o dado não existir, a página deve apontar a limitação em vez de preencher lacuna com suposição.
            """
        )

    with aba_arq:
        st.plotly_chart(
            gerar_grafico_arquetipos(
                medias_auto,
                medias_equipe,
                arquétipos,
                "Arquétipos médios do recorte selecionado",
                "📈 Gráfico Simples",
            ),
            use_container_width=True,
        )
        if linhas_arq:
            st.subheader("Relatório analítico por questão de arquétipos")
            df_arq_questoes = pd.DataFrame(linhas_arq)
            st.dataframe(df_arq_questoes, use_container_width=True, hide_index=True)
        else:
            st.info("Sem questões de arquétipos suficientes para o recorte selecionado.")

    with aba_micro:
        st.plotly_chart(
            gerar_grafico_microambiente_linha(
                medias_real_equipe,
                medias_ideal_equipe,
                dimensoes,
                "Microambiente médio do recorte selecionado",
            ),
            use_container_width=True,
        )
        fig_waterfall = _grafico_waterfall_gaps(linhas_micro)
        if fig_waterfall:
            st.plotly_chart(fig_waterfall, use_container_width=True)
        if linhas_micro:
            st.subheader("Relatório analítico por questão de microambiente")
            df_micro_questoes = pd.DataFrame(linhas_micro)
            st.dataframe(df_micro_questoes, use_container_width=True, hide_index=True)
        else:
            st.info("Sem questões de microambiente suficientes para o recorte selecionado.")

    with aba_saude:
        saude = (pacote or {}).get("saude_emocional") or {}
        categorias = saude.get("categorias") or {}
        if isinstance(categorias, dict) and categorias:
            df_saude = pd.DataFrame([
                {"Categoria": nome, "Score": valor}
                for nome, valor in categorias.items()
                if valor is not None
            ])
            if not df_saude.empty:
                fig_saude = px.bar(
                    df_saude,
                    x="Score",
                    y="Categoria",
                    orientation="h",
                    text="Score",
                    title="Score de saúde emocional por categoria",
                )
                fig_saude.update_traces(texttemplate="%{text:.1f}%", marker_color="#0f766e")
                fig_saude.update_layout(xaxis=dict(range=[0, 100]), height=420)
                st.plotly_chart(fig_saude, use_container_width=True)
                st.dataframe(df_saude, use_container_width=True, hide_index=True)
        st.warning(
            "Saúde emocional é apresentada somente em nível agregado. "
            "Não use este bloco como diagnóstico individual nem como julgamento clínico."
        )

    with aba_export:
        st.subheader("Caderno LeaderTrack")
        st.caption(
            "Versão para impressão ou PDF, montada com os dados reais do filtro atual."
        )
        rodada_exportacao = str((filtros or {}).get("codrodada") or "").strip()
        if not rodada_exportacao or rodada_exportacao.lower() in {"todas", "todos"}:
            st.warning(
                "Selecione uma rodada específica e encerrada para gerar a devolutiva executiva. "
                "O caderno executivo não deve ser emitido com rodadas abertas ou com todas as rodadas combinadas."
            )
            st.stop()
        st.info(
            "Use esta exportação somente após o encerramento da rodada selecionada. "
            "Como a rodada encerrada é estática, o HTML reflete exatamente o contexto e os filtros atuais."
        )
        caderno_html = gerar_caderno_executivo_organizacional_html(
            pacote,
            linhas_arq,
            linhas_micro,
            filtros,
            termo_label,
            gap_medio_questoes,
            gaps_relevantes,
            medias_auto=medias_auto,
            medias_equipe=medias_equipe,
            arquetipos=arquétipos,
            medias_real_equipe=medias_real_equipe,
            medias_ideal_equipe=medias_ideal_equipe,
            dimensoes=dimensoes,
            resposta_ia=st.session_state.get("parecer_corporativo_resposta"),
        )
        st.success(
            "Caderno HTML premium disponível: capa, fundamentos, IA, gráficos, relatórios analíticos, microambiente, arquétipos e saúde emocional."
        )
        st.info(
            "Fluxo recomendado: baixar o HTML, abrir no navegador e usar Ctrl+P para salvar como PDF. "
            "Esse caminho preserva melhor o layout editorial do que imprimir a página do dashboard."
        )
        st.download_button(
            label="Baixar caderno HTML",
            data=caderno_html,
            file_name="caderno-executivo-leadertrack-organizacional.html",
            mime="text/html",
            key="download_caderno_organizacional_html",
        )


st.set_page_config(page_title="🎯 LeaderTrack Dashboard", page_icon="", layout="wide")

SUPABASE_URL = "https://xmsjjknpnowsswwrbvpc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtc2pqa25wbm93c3N3d3JidnBjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MDg0NDUsImV4cCI6MjA2ODA4NDQ0NX0.OexXJX7lK_DefGb72VDWGLDcUXamoQIgYOv5Zo_e9L4"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def get_query_param(nome, default=None):
    try:
        val = st.query_params.get(nome, default)
        if isinstance(val, list):
            return val[0] if val else default
        return val
    except Exception:
        try:
            val = st.experimental_get_query_params().get(nome, [default])
            return val[0] if isinstance(val, list) else val
        except Exception:
            return default


def contexto_url():
    return {
        "nivel_contexto": str(get_query_param("nivel_contexto", "") or "").strip().lower(),
        "holding_id": str(get_query_param("holding_id", "") or "").strip(),
        "holding_nome": str(get_query_param("holding_nome", "") or "").strip(),
        "empresa_id": str(get_query_param("empresa_id", "") or "").strip(),
        "empresa_nome": str(get_query_param("empresa_nome", "") or "").strip(),
        "filial_id": str(get_query_param("filial_id", "") or "").strip(),
        "filial_nome": str(get_query_param("filial_nome", "") or "").strip(),
        "contexto_nome": str(get_query_param("contexto_nome", "") or "").strip(),
        "contexto_codigo": str(get_query_param("contexto_codigo", "") or "").strip(),
        "wp_user_email": str(get_query_param("wp_user_email", "") or "").strip().lower(),
    }


def persistir_contexto_no_navegador(ctx):
    if not isinstance(ctx, dict) or not ctx.get("nivel_contexto"):
        return

    campos_contexto = [
        "nivel_contexto",
        "holding_id",
        "holding_nome",
        "empresa_id",
        "empresa_nome",
        "filial_id",
        "filial_nome",
        "contexto_nome",
        "contexto_codigo",
        "company",
        "codrodada",
        "emaillider",
        "wp_user_email",
        "pode_administrar",
    ]
    payload = {
        campo: str(ctx.get(campo) or "").strip()
        for campo in campos_contexto
        if str(ctx.get(campo) or "").strip()
    }

    components.html(
        f"""
        <script>
        try {{
          window.parent.localStorage.setItem(
            "hrkey_leadertrack_contexto",
            {json.dumps(json.dumps(payload))}
          );
        }} catch (e) {{}}
        </script>
        """,
        height=0,
        width=0,
    )


def corrigir_menu_streamlit_com_contexto(ctx):
    if not isinstance(ctx, dict) or not ctx.get("nivel_contexto"):
        return

    campos_contexto = [
        "nivel_contexto",
        "holding_id",
        "holding_nome",
        "empresa_id",
        "empresa_nome",
        "filial_id",
        "filial_nome",
        "contexto_nome",
        "contexto_codigo",
        "company",
        "codrodada",
        "emaillider",
        "wp_user_email",
        "pode_administrar",
    ]
    payload = {
        campo: str(ctx.get(campo) or "").strip()
        for campo in campos_contexto
        if str(ctx.get(campo) or "").strip()
    }
    query_string = "&".join(
        f"{quote(str(campo))}={quote(str(valor))}"
        for campo, valor in payload.items()
    )

    components.html(
        f"""
        <script>
        (function () {{
          const queryString = {json.dumps(query_string)};
          if (!queryString) return;

          const targetPath = "/visao_executiva?" + queryString;
          const storageKey = "hrkey_leadertrack_contexto";

          try {{
            window.parent.localStorage.setItem(storageKey, {json.dumps(json.dumps(payload))});
          }} catch (e) {{}}

          function patchLinks() {{
            const doc = window.parent.document;
            const links = Array.from(doc.querySelectorAll("a"));

            links.forEach(function (link) {{
              const href = String(link.getAttribute("href") || "");
              const text = String(link.textContent || "").trim().toLowerCase();

              const isExecutive =
                href.includes("visao_executiva") ||
                text === "visao executiva" ||
                text === "visão executiva";

              if (isExecutive) {{
                link.setAttribute("href", targetPath);
              }}
            }});
          }}

          patchLinks();
          window.parent.addEventListener("focus", patchLinks);
          setInterval(patchLinks, 1000);
        }})();
        </script>
        """,
        height=0,
        width=0,
    )


def filtros_url_dashboard():
    return {
        "nivel_contexto": str(get_query_param("nivel_contexto", "") or "").strip().lower(),

        "holding_id": str(get_query_param("holding_id", "") or "").strip(),
        "holding_nome": str(get_query_param("holding_nome", "") or "").strip(),

        "empresa_id": str(get_query_param("empresa_id", "") or "").strip(),
        "empresa_nome": str(get_query_param("empresa_nome", "") or "").strip(),

        "filial_id": str(get_query_param("filial_id", "") or "").strip(),
        "filial_nome": str(get_query_param("filial_nome", "") or "").strip(),

        "contexto_nome": str(get_query_param("contexto_nome", "") or "").strip(),
        "contexto_codigo": str(get_query_param("contexto_codigo", "") or "").strip(),

        "company": str(get_query_param("company", "") or "").strip().lower(),
        "codrodada": str(get_query_param("codrodada", "") or "").strip().lower(),
        "emaillider": str(get_query_param("emaillider", "") or "").strip().lower(),

        "wp_user_email": str(get_query_param("wp_user_email", "") or "").strip().lower(),
        "pode_administrar": str(get_query_param("pode_administrar", "") or "").strip().lower(),
    }


def norm_txt(v):
    return str(v or "").strip().upper()


def contexto_cache_key(ctx):
    campos = [
        "nivel_contexto",
        "holding_id",
        "holding_nome",
        "empresa_id",
        "empresa_nome",
        "filial_id",
        "filial_nome",
        "contexto_nome",
        "contexto_codigo",
    ]
    return tuple((campo, str((ctx or {}).get(campo) or "").strip()) for campo in campos)


def contexto_from_cache_key(ctx_key):
    return {campo: valor for campo, valor in (ctx_key or ()) if valor}


def filtro_consulta_cache_key(filtros_consulta):
    campos = ["holding", "empresa", "codrodada", "emaillider"]
    pares = []
    for campo in campos:
        valor = (filtros_consulta or {}).get(campo)
        if isinstance(valor, (list, tuple, set)):
            valor = tuple(sorted(str(v).strip() for v in valor if str(v or "").strip()))
        else:
            valor = str(valor or "").strip()
        pares.append((campo, valor))
    return tuple(pares)


def filtros_consulta_from_cache_key(filtro_key):
    return {campo: valor for campo, valor in (filtro_key or ()) if valor}


def valor_filtro_sidebar(nome, default=""):
    valor = st.session_state.get(nome, default)
    return str(valor or "").strip()


def normalizar_filtro_consulta(valor, todos_label):
    texto = str(valor or "").strip()
    if not texto or texto.lower() == todos_label.lower():
        return todos_label
    return texto


def filtro_todos(valor, todos_label):
    return str(valor or "").strip().lower() == todos_label.lower()


def filtros_preconsulta_dashboard(ctx):
    filtros_url = filtros_url_dashboard()
    nivel_contexto_url = str(filtros_url.get("nivel_contexto") or "").strip().lower()

    holding = normalizar_filtro_consulta(
        valor_filtro_sidebar("filtro_holding", filtros_url.get("holding_nome") or "Todas"),
        "Todas",
    )

    empresa_default = "Todas"
    if nivel_contexto_url != "holding":
        empresa_default = filtros_url.get("company") or filtros_url.get("empresa_nome") or "Todas"
    empresa = normalizar_filtro_consulta(
        valor_filtro_sidebar("filtro_empresa", empresa_default),
        "Todas",
    )

    codrodada = normalizar_filtro_consulta(
        valor_filtro_sidebar("filtro_codrodada", filtros_url.get("codrodada") or "Todas"),
        "Todas",
    )
    emaillider = normalizar_filtro_consulta(
        valor_filtro_sidebar("filtro_emaillider", filtros_url.get("emaillider") or "Todos"),
        "Todos",
    )

    return {
        "holding": holding.upper() if holding != "Todas" else "Todas",
        "empresa": empresa.lower() if empresa != "Todas" else "Todas",
        "codrodada": codrodada.lower() if codrodada != "Todas" else "Todas",
        "emaillider": emaillider.lower() if emaillider != "Todos" else "Todos",
    }


def aplicar_filtro_contexto_query(query, ctx, *, incluir_texto=True):
    nivel = norm_txt((ctx or {}).get("nivel_contexto"))

    if nivel == "HOLDING":
        holding_id = str((ctx or {}).get("holding_id") or "").strip()
        holding_nome = str(
            (ctx or {}).get("holding_nome")
            or (ctx or {}).get("contexto_nome")
            or (ctx or {}).get("contexto_codigo")
            or ""
        ).strip()

        if holding_id:
            return query.eq("holding_id", holding_id)
        if incluir_texto and holding_nome:
            return query.eq("holding", holding_nome)

    if nivel == "EMPRESA":
        empresa_id = str((ctx or {}).get("empresa_id") or "").strip()
        empresa_nome = str(
            (ctx or {}).get("empresa_nome")
            or (ctx or {}).get("company")
            or (ctx or {}).get("contexto_nome")
            or (ctx or {}).get("contexto_codigo")
            or ""
        ).strip()

        if empresa_id:
            return query.eq("empresa_id", empresa_id)
        if incluir_texto and empresa_nome:
            return query.eq("empresa", empresa_nome)

    if nivel == "FILIAL":
        filial_id = str((ctx or {}).get("filial_id") or "").strip()
        empresa_id = str((ctx or {}).get("empresa_id") or "").strip()

        if filial_id:
            return query.eq("filial_id", filial_id)
        if empresa_id:
            return query.eq("empresa_id", empresa_id)

    return query


def aplicar_filtros_dashboard_query(query, filtros_consulta):
    filtros_consulta = filtros_consulta or {}

    holding = norm_txt(filtros_consulta.get("holding"))
    empresa = str(filtros_consulta.get("empresa") or "").strip()
    codrodada = str(filtros_consulta.get("codrodada") or "").strip()
    emaillider = filtros_consulta.get("emaillider")

    if holding == "PROSPERA" and (not empresa or filtro_todos(empresa, "Todas")):
        query = query.in_("empresa", PROSPERA_EMPRESAS_LEADERTRACK)
    if empresa and not filtro_todos(empresa, "Todas"):
        query = query.ilike("empresa", empresa)
    if codrodada and not filtro_todos(codrodada, "Todas"):
        query = query.ilike("codrodada", codrodada)
    if isinstance(emaillider, tuple):
        emaillider = list(emaillider)
    if isinstance(emaillider, list):
        lideres = [str(v).strip().lower() for v in emaillider if str(v or "").strip()]
        if lideres:
            query = query.in_("emaillider", lideres)
    else:
        email = str(emaillider or "").strip().lower()
        if email and not filtro_todos(email, "Todos"):
            query = query.ilike("emaillider", email)

    return query


def executar_query_com_fallback(supabase, tabela, colunas, ctx, *, incluir_texto=True, limite=None):
    base = supabase.table(tabela).select(colunas)
    filtrada = aplicar_filtro_contexto_query(
        supabase.table(tabela).select(colunas),
        ctx,
        incluir_texto=incluir_texto,
    )

    if limite:
        base = base.limit(limite)
        filtrada = filtrada.limit(limite)

    if (ctx or {}).get("nivel_contexto"):
        try:
            return filtrada.execute().data
        except Exception:
            return base.execute().data

    return base.execute().data


PROSPERA_EMPRESAS_LEADERTRACK = [
    "astro34",
    "spectral_v",
    "spectral_a",
    "spectral_sales",
    "fastco",
    "futurex",
]


def combinar_rows_unicas(*listas):
    rows = []
    vistos = set()
    for lista in listas:
        for row in lista or []:
            chave = row.get("id") if isinstance(row, dict) else None
            if chave is None:
                chave = json.dumps(row, sort_keys=True, default=str)
            if chave in vistos:
                continue
            vistos.add(chave)
            rows.append(row)
    return rows


def consultar_consolidado_leadertrack(supabase, tabela, ctx, filtros_consulta=None):
    def query_base():
        return aplicar_filtros_dashboard_query(
            supabase.table(tabela).select("*"),
            filtros_consulta,
        )

    if not (ctx or {}).get("nivel_contexto"):
        return query_base().execute().data

    nivel = norm_txt((ctx or {}).get("nivel_contexto"))
    empresa_nome = str(
        (ctx or {}).get("empresa_nome")
        or (ctx or {}).get("company")
        or (ctx or {}).get("contexto_nome")
        or (ctx or {}).get("contexto_codigo")
        or ""
    ).strip()
    holding_nome = norm_txt(
        (ctx or {}).get("holding_nome")
        or (ctx or {}).get("contexto_nome")
        or (ctx or {}).get("contexto_codigo")
    )

    try:
        if nivel in {"EMPRESA", "FILIAL"} and empresa_nome:
            return query_base().ilike("empresa", empresa_nome).execute().data

        if nivel == "HOLDING":
            if holding_nome == "PROSPERA":
                return (
                    query_base()
                    .in_("empresa", PROSPERA_EMPRESAS_LEADERTRACK)
                    .execute()
                    .data
                )

            if holding_nome == "LEVEN":
                por_codrodada = (
                    query_base()
                    .ilike("codrodada", "%leven%")
                    .execute()
                    .data
                )
                por_empresa = (
                    query_base()
                    .ilike("empresa", "%leven%")
                    .execute()
                    .data
                )
                return combinar_rows_unicas(por_codrodada, por_empresa)

            if holding_nome:
                return query_base().ilike("empresa", holding_nome).execute().data
    except Exception:
        pass

    return query_base().execute().data


def filtro_restrito(valor, todos_label):
    if isinstance(valor, (list, tuple, set)):
        return any(str(v or "").strip() for v in valor)
    texto = str(valor or "").strip()
    return bool(texto and not filtro_todos(texto, todos_label))


def filtros_consulta_com_fallbacks(filtros_consulta):
    filtros = dict(filtros_consulta or {})
    yield filtros

    if filtro_restrito(filtros.get("emaillider"), "Todos"):
        sem_lider = dict(filtros)
        sem_lider["emaillider"] = "Todos"
        yield sem_lider
        filtros = sem_lider

    if filtro_restrito(filtros.get("codrodada"), "Todas"):
        sem_rodada = dict(filtros)
        sem_rodada["codrodada"] = "Todas"
        yield sem_rodada
        filtros = sem_rodada

    if filtro_restrito(filtros.get("empresa"), "Todas"):
        sem_empresa = dict(filtros)
        sem_empresa["empresa"] = "Todas"
        yield sem_empresa


def consultar_consolidados_com_fallback(supabase, ctx, filtros_consulta):
    ultimo_arq, ultimo_micro = [], []
    for filtros_tentativa in filtros_consulta_com_fallbacks(filtros_consulta):
        arq = consultar_consolidado_leadertrack(
            supabase,
            'consolidado_arquetipos',
            ctx,
            filtros_tentativa,
        )
        micro = consultar_consolidado_leadertrack(
            supabase,
            'consolidado_microambiente',
            ctx,
            filtros_tentativa,
        )
        ultimo_arq, ultimo_micro = arq, micro
        if arq and micro:
            return arq, micro
    return ultimo_arq, ultimo_micro


def primeiro_valido(*valores):
    for valor in valores:
        if valor is None:
            continue
        texto = str(valor).strip()
        if texto and texto.upper() not in {"N/A", "NONE", "NAN", "NULL"}:
            return valor
    return None


def mask_por_codrodada_contexto(df, nome_contexto):
    if df is None or df.empty or "codrodada" not in df.columns:
        return pd.Series(False, index=df.index if df is not None else None)

    contexto_norm = str(nome_contexto or "").strip().lower()
    if not contexto_norm:
        return pd.Series(False, index=df.index)

    return df["codrodada"].astype(str).str.lower().str.contains(contexto_norm, na=False)


def filtrar_leadertrack_por_contexto(df, ctx):
    if df is None or df.empty:
        return df

    nivel = norm_txt(ctx.get("nivel_contexto"))

    if not nivel:
        return df

    df_filtrado = df.copy()

    if nivel == "HOLDING":
        holding_id = ctx.get("holding_id")
        holding_nome = ctx.get("holding_nome") or ctx.get("contexto_nome") or ctx.get("contexto_codigo")

        mask = pd.Series(False, index=df_filtrado.index)

        if holding_id and "holding_id" in df_filtrado.columns:
            mask = mask | (df_filtrado["holding_id"].astype(str).str.strip() == str(holding_id).strip())

        if holding_nome and "holding" in df_filtrado.columns:
            mask = mask | (
                df_filtrado["holding"].astype(str).str.upper().str.strip() == norm_txt(holding_nome)
            )

        # Fallback operacional para rodadas novas cuja resposta ainda nao traz holding_id/holding.
        # Ex.: LEVEN consolidada como avleven0726.
        mask = mask | mask_por_codrodada_contexto(df_filtrado, holding_nome)

        if mask.any():
            return df_filtrado[mask]

        return df_filtrado.iloc[0:0]

    if nivel == "EMPRESA":
        empresa_id = ctx.get("empresa_id")
        empresa_nome = ctx.get("empresa_nome") or ctx.get("contexto_nome") or ctx.get("contexto_codigo")

        mask = pd.Series(False, index=df_filtrado.index)

        if empresa_id and "empresa_id" in df_filtrado.columns:
            mask = mask | (df_filtrado["empresa_id"].astype(str).str.strip() == str(empresa_id).strip())

        if empresa_nome and "empresa" in df_filtrado.columns:
            mask = mask | (
                df_filtrado["empresa"].astype(str).str.upper().str.strip() == norm_txt(empresa_nome)
            )

        if empresa_nome and "company_name" in df_filtrado.columns:
            mask = mask | (
                df_filtrado["company_name"].astype(str).str.upper().str.strip() == norm_txt(empresa_nome)
            )

        if mask.any():
            return df_filtrado[mask]

        return df_filtrado.iloc[0:0]

    if nivel == "FILIAL":
        empresa_id = ctx.get("empresa_id")
        filial_id = ctx.get("filial_id")
        empresa_nome = ctx.get("empresa_nome")
        filial_nome = ctx.get("filial_nome") or ctx.get("contexto_nome") or ctx.get("contexto_codigo")

        mask = pd.Series(True, index=df_filtrado.index)

        if empresa_id and "empresa_id" in df_filtrado.columns:
            mask = mask & (df_filtrado["empresa_id"].astype(str).str.strip() == str(empresa_id).strip())
        elif empresa_nome:
            mask_empresa = pd.Series(False, index=df_filtrado.index)
            if "empresa" in df_filtrado.columns:
                mask_empresa = mask_empresa | (
                    df_filtrado["empresa"].astype(str).str.upper().str.strip() == norm_txt(empresa_nome)
                )
            if "company_name" in df_filtrado.columns:
                mask_empresa = mask_empresa | (
                    df_filtrado["company_name"].astype(str).str.upper().str.strip() == norm_txt(empresa_nome)
                )
            mask = mask & mask_empresa

        # Neste app.py, os consolidados geralmente não têm filial_id.
        # Então tentamos filtrar por campos textuais, se existirem.
        mask_filial = pd.Series(False, index=df_filtrado.index)

        if filial_id and "filial_id" in df_filtrado.columns:
            mask_filial = mask_filial | (df_filtrado["filial_id"].astype(str).str.strip() == str(filial_id).strip())

        campos_filial = ["filial", "branch_name", "filial_nome", "cidade", "estado"]

        campos_existentes = [c for c in campos_filial if c in df_filtrado.columns]

        if filial_nome and campos_existentes:
            mask_filial = pd.Series(False, index=df_filtrado.index)

            for campo in campos_existentes:
                mask_filial = mask_filial | (
                    df_filtrado[campo].astype(str).str.upper().str.strip() == norm_txt(filial_nome)
                )

        if mask_filial.any():
            mask = mask & mask_filial

        return df_filtrado[mask]

    return df_filtrado


@st.cache_data(ttl=3600)
def carregar_classificacoes_saude_emocional():
    import os
    arquivo_csv = 'TABELA_SAUDE_EMOCIONAL.csv'
    caminho_completo = os.path.abspath(arquivo_csv)
    try:
        if not os.path.exists(arquivo_csv):
            st.error("❌ **ARQUIVO NÃO ENCONTRADO!**")
            return {}
        df_classificacoes = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig')
        df_classificacoes['TIPO'] = df_classificacoes['TIPO'].astype(str).str.strip().str.upper()
        df_classificacoes['COD_AFIRMACAO'] = df_classificacoes['COD_AFIRMACAO'].astype(str).str.strip()
        df_classificacoes['DIMENSAO_SAUDE_EMOCIONAL'] = (
            df_classificacoes['DIMENSAO_SAUDE_EMOCIONAL'].astype(str).str.strip()
            .replace({'Equilíbrio Vida- Trabalho': 'Equilíbrio Vida-Trabalho'})
        )
        st.success("✅ **TABELA_SAUDE_EMOCIONAL.csv carregada com sucesso!**")
        st.info(f"📊 Total de linhas no CSV: {len(df_classificacoes)}")
        classificacoes = {}
        for _, row in df_classificacoes.iterrows():
            tipo = str(row['TIPO']).upper().strip()
            codigo = str(row['COD_AFIRMACAO']).strip()
            dimensao = row['DIMENSAO_SAUDE_EMOCIONAL']
            if tipo.startswith('ARQ'):
                tipo_codigo = f"arq_{codigo}"
            elif tipo.startswith('MICRO'):
                tipo_codigo = f"micro_{codigo}"
            else:
                tipo_codigo = codigo
            classificacoes[tipo_codigo] = dimensao
            if codigo not in classificacoes:
                classificacoes[codigo] = dimensao
        contagem_dim = df_classificacoes['DIMENSAO_SAUDE_EMOCIONAL'].value_counts().sort_index()
        st.info("📋 **Distribuição por dimensão (TABELA_SAUDE_EMOCIONAL):**")
        for dim, qtd in contagem_dim.items():
            st.write(f"  - {dim}: {qtd} afirmações")
        st.info(f"🔑 **Total de chaves no dicionário:** {len(classificacoes)}")
        return classificacoes
    except Exception as e:
        st.error(f"❌ **ERRO ao carregar classificações:** {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return {}

# ==================== FUNÇÕES ARQUÉTIPOS ====================

@st.cache_data(ttl=3600)
def carregar_matriz_arquetipos():
    try:
        matriz = pd.read_excel('TABELA_GERAL_ARQUETIPOS_COM_CHAVE.xlsx')
        return matriz
    except Exception as e:
        st.error(f"❌ Erro ao carregar matriz de arquétipos: {str(e)}")
        return None

def calcular_arquetipos_respondente(respostas, matriz):
    """Calcula percentuais de arquétipos para um respondente individual - busca na tabela"""
    arquétipos = ['Imperativo', 'Resoluto', 'Cuidativo', 'Consultivo', 'Prescritivo', 'Formador']
    pontos_por_arquétipo = {arq: 0 for arq in arquétipos}
    pontos_maximos_por_arquétipo = {arq: 0 for arq in arquétipos}
    for questao, estrelas in respostas.items():
        if questao.startswith('Q'):
            estrelas_int = int(estrelas)
            for arquétipo in arquétipos:
                chave = f"{arquétipo}{estrelas_int}{questao}"
                linha = matriz[matriz['CHAVE'] == chave]
                if not linha.empty:
                    pontos_por_arquétipo[arquétipo] += linha['PONTOS_OBTIDOS'].iloc[0]
                    pontos_maximos_por_arquétipo[arquétipo] += linha['PONTOS_MAXIMOS'].iloc[0]
    arquétipos_percentuais = {}
    for arquétipo in arquétipos:
        total = pontos_por_arquétipo[arquétipo]
        maximos = pontos_maximos_por_arquétipo[arquétipo]
        arquétipos_percentuais[arquétipo] = (total / maximos) * 100 if maximos > 0 else 0
    return arquétipos_percentuais

# ==================== FUNÇÕES MICROAMBIENTE ====================

@st.cache_data(ttl=3600)
def carregar_matrizes_microambiente():
    try:
        matriz = pd.read_excel('TABELA_GERAL_MICROAMBIENTE_COM_CHAVE.xlsx')
        pontos_max_dimensao = pd.read_excel('pontos_maximos_dimensao_microambiente.xlsx')
        pontos_max_subdimensao = pd.read_excel('pontos_maximos_subdimensao_microambiente.xlsx')
        return matriz, pontos_max_dimensao, pontos_max_subdimensao
    except Exception as e:
        st.error(f"❌ Erro ao carregar matrizes de microambiente: {str(e)}")
        return None, None, None

def calcular_microambiente_respondente(respostas, matriz, pontos_max_dimensao, pontos_max_subdimensao):
    """Calcula percentuais de microambiente para um respondente individual - busca na tabela"""
    MAPEAMENTO_QUESTOES = {
        'Q01':'Q01','Q02':'Q12','Q03':'Q23','Q04':'Q34','Q05':'Q44','Q06':'Q45',
        'Q07':'Q46','Q08':'Q47','Q09':'Q48','Q10':'Q02','Q11':'Q03','Q12':'Q04',
        'Q13':'Q05','Q14':'Q06','Q15':'Q07','Q16':'Q08','Q17':'Q09','Q18':'Q10',
        'Q19':'Q11','Q20':'Q13','Q21':'Q14','Q22':'Q15','Q23':'Q16','Q24':'Q17',
        'Q25':'Q18','Q26':'Q19','Q27':'Q20','Q28':'Q21','Q29':'Q22','Q30':'Q24',
        'Q31':'Q25','Q32':'Q26','Q33':'Q27','Q34':'Q28','Q35':'Q29','Q36':'Q30',
        'Q37':'Q31','Q38':'Q32','Q39':'Q33','Q40':'Q35','Q41':'Q36','Q42':'Q37',
        'Q43':'Q38','Q44':'Q39','Q45':'Q40','Q46':'Q41','Q47':'Q42','Q48':'Q43'
    }
    dimensoes = ['Adaptabilidade', 'Colaboração Mútua', 'Nitidez', 'Performance', 'Reconhecimento', 'Responsabilidade']
    subdimensoes = [
        'Criação', 'Simplificação de Processos', 'Credibilidade Recíproca', 'Dedicação', 'Parceria',
        'Satisfação em Fazer Parte', 'Obrigações e Deveres', 'Propósito e Objetivo', 'Aprimoramento',
        'Qualidade Superior', 'Celebração', 'Performance', 'Liberdade de Ação', 'Responsabilização'
    ]
    respostas_real = {}
    respostas_ideal = {}
    for questao, estrelas in respostas.items():
        if questao.startswith('Q'):
            if questao.endswith('C'):
                respostas_real[questao[:-1]] = int(estrelas)
            elif questao.endswith('k'):
                respostas_ideal[questao[:-1]] = int(estrelas)
    pontos_por_dimensao_real = {dim: 0 for dim in dimensoes}
    pontos_por_subdimensao_real = {sub: 0 for sub in subdimensoes}
    pontos_por_dimensao_ideal = {dim: 0 for dim in dimensoes}
    pontos_por_subdimensao_ideal = {sub: 0 for sub in subdimensoes}
    for questao in respostas_real:
        if questao in respostas_ideal:
            estrelas_real = respostas_real[questao]
            estrelas_ideal = respostas_ideal[questao]
            questao_mapeada = MAPEAMENTO_QUESTOES.get(questao, questao)
            chave_transformada = f"{questao_mapeada}_I{estrelas_ideal}_R{estrelas_real}"
            linha = matriz[matriz['CHAVE'] == chave_transformada]
            if not linha.empty:
                dimensao = linha['DIMENSAO'].iloc[0]
                subdimensao = linha['SUBDIMENSAO'].iloc[0]
                pontos_por_dimensao_real[dimensao] += linha['PONTUACAO_REAL'].iloc[0]
                pontos_por_dimensao_ideal[dimensao] += linha['PONTUACAO_IDEAL'].iloc[0]
                pontos_por_subdimensao_real[subdimensao] += linha['PONTUACAO_REAL'].iloc[0]
                pontos_por_subdimensao_ideal[subdimensao] += linha['PONTUACAO_IDEAL'].iloc[0]
    dimensoes_percentuais_real = {}
    dimensoes_percentuais_ideal = {}
    for dimensao in dimensoes:
        pontos_maximos = pontos_max_dimensao[pontos_max_dimensao['DIMENSAO'] == dimensao]['PONTOS_MAXIMOS_DIMENSAO'].iloc[0]
        dimensoes_percentuais_real[dimensao] = (pontos_por_dimensao_real[dimensao] / pontos_maximos) * 100 if pontos_maximos > 0 else 0
        dimensoes_percentuais_ideal[dimensao] = (pontos_por_dimensao_ideal[dimensao] / pontos_maximos) * 100 if pontos_maximos > 0 else 0
    subdimensoes_percentuais_real = {}
    subdimensoes_percentuais_ideal = {}
    for subdimensao in subdimensoes:
        pontos_maximos = pontos_max_subdimensao[pontos_max_subdimensao['SUBDIMENSAO'] == subdimensao]['PONTOS_MAXIMOS_SUBDIMENSAO'].iloc[0]
        subdimensoes_percentuais_real[subdimensao] = (pontos_por_subdimensao_real[subdimensao] / pontos_maximos) * 100 if pontos_maximos > 0 else 0
        subdimensoes_percentuais_ideal[subdimensao] = (pontos_por_subdimensao_ideal[subdimensao] / pontos_maximos) * 100 if pontos_maximos > 0 else 0
    return (dimensoes_percentuais_real, dimensoes_percentuais_ideal,
            subdimensoes_percentuais_real, subdimensoes_percentuais_ideal)


# ==================== FUNÇÕES COMPARTILHADAS ====================

# Mapeamentos globais FORM <-> MATRIZ
_MAP_FORM_TO_MATRIZ = {
    'Q01':'Q01','Q02':'Q12','Q03':'Q23','Q04':'Q34','Q05':'Q44','Q06':'Q45',
    'Q07':'Q46','Q08':'Q47','Q09':'Q48','Q10':'Q02','Q11':'Q03','Q12':'Q04',
    'Q13':'Q05','Q14':'Q06','Q15':'Q07','Q16':'Q08','Q17':'Q09','Q18':'Q10',
    'Q19':'Q11','Q20':'Q13','Q21':'Q14','Q22':'Q15','Q23':'Q16','Q24':'Q17',
    'Q25':'Q18','Q26':'Q19','Q27':'Q20','Q28':'Q21','Q29':'Q22','Q30':'Q24',
    'Q31':'Q25','Q32':'Q26','Q33':'Q27','Q34':'Q28','Q35':'Q29','Q36':'Q30',
    'Q37':'Q31','Q38':'Q32','Q39':'Q33','Q40':'Q35','Q41':'Q36','Q42':'Q37',
    'Q43':'Q38','Q44':'Q39','Q45':'Q40','Q46':'Q41','Q47':'Q42','Q48':'Q43'
}
_MAP_MATRIZ_TO_FORM = {v: k for k, v in _MAP_FORM_TO_MATRIZ.items()}


def calcular_real_ideal_gap_por_questao(df_micro_filtrado, matriz_micro, codigo_matriz):
    """
    ✅ LÓGICA CORRETA: busca na tabela para cada respondente individualmente,
    depois faz média dos percentuais obtidos.
    codigo_matriz: código canônico da MATRIZ (ex: 'Q45')
    """
    codigo_form = _MAP_MATRIZ_TO_FORM.get(codigo_matriz, codigo_matriz)

    soma_real = 0.0
    soma_ideal = 0.0
    count = 0

    for _, resp in df_micro_filtrado.iterrows():
        respostas = resp.get('respostas', {})
        if not isinstance(respostas, dict):
            continue
        qR = f"{codigo_form}C"
        qI = f"{codigo_form}k"
        if qR in respostas and qI in respostas:
            try:
                r = int(respostas[qR])
                i = int(respostas[qI])
            except:
                continue
            chave = f"{codigo_matriz}_I{i}_R{r}"
            linha = matriz_micro[matriz_micro['CHAVE'] == chave]
            if not linha.empty:
                soma_real += float(linha['PONTUACAO_REAL'].iloc[0])
                soma_ideal += float(linha['PONTUACAO_IDEAL'].iloc[0])
                count += 1

    if count == 0:
        return None, None, None

    real_pct = round(soma_real / count, 2)
    ideal_pct = round(soma_ideal / count, 2)
    gap = round(ideal_pct - real_pct, 2)
    return real_pct, ideal_pct, gap


def calcular_tendencia_arquetipos_por_questao(df_arq_filtrado, matriz_arq, codigo_questao, arquétipo):
    """
    ✅ LÓGICA CORRETA: busca na tabela para cada respondente individualmente,
    depois faz média dos percentuais de tendência obtidos.
    """
    percentuais_individuais = []
    soma_notas = 0
    count_notas = 0

    for _, respondente in df_arq_filtrado.iterrows():
        if 'respostas' in respondente and codigo_questao in respondente['respostas']:
            estrelas = int(respondente['respostas'][codigo_questao])
            chave = f"{arquétipo}{estrelas}{codigo_questao}"
            linha = matriz_arq[matriz_arq['CHAVE'] == chave]
            if not linha.empty:
                pct = float(linha['% Tendência'].iloc[0]) * 100
                percentuais_individuais.append(pct)
                soma_notas += estrelas
                count_notas += 1

    if not percentuais_individuais:
        return None, None, None

    percentual_medio = round(sum(percentuais_individuais) / len(percentuais_individuais), 2)
    media_arredondada = round(soma_notas / count_notas)
    chave_tendencia = f"{arquétipo}{media_arredondada}{codigo_questao}"
    linha_tend = matriz_arq[matriz_arq['CHAVE'] == chave_tendencia]
    tendencia_info = linha_tend['Tendência'].iloc[0] if not linha_tend.empty else 'N/A'

    return percentual_medio, tendencia_info, len(percentuais_individuais)


# ==================== PROCESSAR DADOS ====================

def processar_dados_arquetipos(consolidado_arq, matriz):
    respondentes_processados = []

    def contexto_resposta(item, resposta):
        return {
            'holding': primeiro_valido(resposta.get('holding'), item.get('holding'), ''),
            'holding_id': primeiro_valido(resposta.get('holding_id'), item.get('holding_id'), ''),
            'empresa_id': primeiro_valido(resposta.get('empresa_id'), item.get('empresa_id'), ''),
            'filial_id': primeiro_valido(resposta.get('filial_id'), item.get('filial_id'), ''),
            'company_name': primeiro_valido(resposta.get('company_name'), item.get('company_name'), ''),
            'branch_name': primeiro_valido(resposta.get('branch_name'), item.get('branch_name'), ''),
        }

    for item in consolidado_arq:
        if isinstance(item, dict) and 'dados_json' in item:
            dados = item['dados_json']
            if 'autoavaliacao' in dados and 'respostas' in dados['autoavaliacao']:
                auto = dados['autoavaliacao']
                arquétipos_auto = calcular_arquetipos_respondente(auto['respostas'], matriz)
                respondentes_processados.append({
                    'empresa': primeiro_valido(auto.get('empresa'), item.get('empresa'), 'N/A'),
                    'codrodada': primeiro_valido(auto.get('codrodada'), item.get('codrodada'), 'N/A'),
                    'emailLider': primeiro_valido(auto.get('emailLider'), item.get('emaillider'), 'N/A'),
                    'nome': auto.get('nome', 'N/A'),
                    'email': auto.get('email', 'N/A'),
                    'sexo': auto.get('sexo', 'N/A'),
                    'etnia': auto.get('etnia', 'N/A'),
                    'estado': auto.get('estado', 'N/A'),
                    'cidade': auto.get('cidade', 'N/A'),
                    'cargo': auto.get('cargo', 'N/A'),
                    'area': auto.get('area', 'N/A'),
                    'departamento': auto.get('departamento', 'N/A'),
                    'tipo': 'Autoavaliação',
                    'arquétipos': arquétipos_auto,
                    'respostas': auto['respostas'],
                    **contexto_resposta(item, auto)
                })
            if 'avaliacoesEquipe' in dados:
                for membro in dados['avaliacoesEquipe']:
                    if 'respostas' in membro:
                        arquétipos_equipe = calcular_arquetipos_respondente(membro['respostas'], matriz)
                        respondentes_processados.append({
                            'empresa': primeiro_valido(membro.get('empresa'), item.get('empresa'), 'N/A'),
                            'codrodada': primeiro_valido(membro.get('codrodada'), item.get('codrodada'), 'N/A'),
                            'emailLider': primeiro_valido(membro.get('emailLider'), item.get('emaillider'), 'N/A'),
                            'nome': membro.get('nome', 'N/A'),
                            'email': membro.get('email', 'N/A'),
                            'sexo': membro.get('sexo', 'N/A'),
                            'etnia': membro.get('etnia', 'N/A'),
                            'estado': membro.get('estado', 'N/A'),
                            'cidade': membro.get('cidade', 'N/A'),
                            'cargo': membro.get('cargo', 'N/A'),
                            'area': membro.get('area', 'N/A'),
                            'departamento': membro.get('departamento', 'N/A'),
                            'tipo': 'Avaliação Equipe',
                            'arquétipos': arquétipos_equipe,
                            'respostas': membro['respostas'],
                            **contexto_resposta(item, membro)
                        })
    return pd.DataFrame(respondentes_processados)


def processar_dados_microambiente(consolidado_micro, matriz, pontos_max_dimensao, pontos_max_subdimensao):
    respondentes_processados = []

    def contexto_resposta(item, resposta):
        return {
            'holding': primeiro_valido(resposta.get('holding'), item.get('holding'), ''),
            'holding_id': primeiro_valido(resposta.get('holding_id'), item.get('holding_id'), ''),
            'empresa_id': primeiro_valido(resposta.get('empresa_id'), item.get('empresa_id'), ''),
            'filial_id': primeiro_valido(resposta.get('filial_id'), item.get('filial_id'), ''),
            'company_name': primeiro_valido(resposta.get('company_name'), item.get('company_name'), ''),
            'branch_name': primeiro_valido(resposta.get('branch_name'), item.get('branch_name'), ''),
        }

    for item in consolidado_micro:
        if isinstance(item, dict) and 'dados_json' in item:
            dados = item['dados_json']
            if 'autoavaliacao' in dados:
                auto = dados['autoavaliacao']
                dimensoes_real, dimensoes_ideal, subdimensoes_real, subdimensoes_ideal = calcular_microambiente_respondente(auto, matriz, pontos_max_dimensao, pontos_max_subdimensao)
                respondentes_processados.append({
                    'empresa': primeiro_valido(auto.get('empresa'), item.get('empresa'), ''),
                    'codrodada': primeiro_valido(auto.get('codrodada'), item.get('codrodada'), ''),
                    'emailLider': primeiro_valido(auto.get('emailLider'), item.get('emaillider'), ''),
                    'nome': auto.get('nome', ''),
                    'email': auto.get('email', ''),
                    'sexo': auto.get('sexo', ''),
                    'etnia': auto.get('etnia', ''),
                    'estado': auto.get('estado', ''),
                    'cidade': auto.get('cidade', ''),
                    'cargo': auto.get('cargo', ''),
                    'area': auto.get('area', ''),
                    'departamento': auto.get('departamento', ''),
                    'tipo': 'Autoavaliação',
                    'dimensoes_real': dimensoes_real,
                    'dimensoes_ideal': dimensoes_ideal,
                    'subdimensoes_real': subdimensoes_real,
                    'subdimensoes_ideal': subdimensoes_ideal,
                    'respostas': auto,
                    **contexto_resposta(item, auto)
                })
            if 'avaliacoesEquipe' in dados:
                for membro in dados['avaliacoesEquipe']:
                    dimensoes_real, dimensoes_ideal, subdimensoes_real, subdimensoes_ideal = calcular_microambiente_respondente(membro, matriz, pontos_max_dimensao, pontos_max_subdimensao)
                    respondentes_processados.append({
                        'empresa': primeiro_valido(membro.get('empresa'), item.get('empresa'), ''),
                        'codrodada': primeiro_valido(membro.get('codrodada'), item.get('codrodada'), ''),
                        'emailLider': primeiro_valido(membro.get('emailLider'), item.get('emaillider'), ''),
                        'nome': membro.get('nome', ''),
                        'email': membro.get('email', ''),
                        'sexo': membro.get('sexo', ''),
                        'etnia': membro.get('etnia', ''),
                        'estado': membro.get('estado', ''),
                        'cidade': membro.get('cidade', ''),
                        'departamento': membro.get('departamento', ''),
                        'tipo': 'Avaliação Equipe',
                        'dimensoes_real': dimensoes_real,
                        'dimensoes_ideal': dimensoes_ideal,
                        'subdimensoes_real': subdimensoes_real,
                        'subdimensoes_ideal': subdimensoes_ideal,
                        'respostas': membro,
                        **contexto_resposta(item, membro)
                    })
    return pd.DataFrame(respondentes_processados)


# ==================== CALCULAR MÉDIAS COM FILTROS ====================

def aplicar_filtro_seguro_dashboard(df, coluna, valor):
    if df is None or df.empty or coluna not in df.columns:
        return df
    texto = str(valor or "").strip()
    if not texto or texto.lower() in {"todos", "todas"}:
        return df
    serie = df[coluna].fillna("").astype(str).str.strip()
    if not serie.any():
        return df
    candidato = df[serie.str.lower() == texto.lower()]
    return candidato if not candidato.empty else df


def calcular_medias_arquetipos(df_respondentes, filtros):
    df_filtrado = df_respondentes.copy()
    for coluna, chave in [
        ("empresa", "empresa"),
        ("codrodada", "codrodada"),
        ("emailLider", "emaillider"),
        ("estado", "estado"),
        ("sexo", "sexo"),
        ("etnia", "etnia"),
        ("departamento", "departamento"),
        ("cargo", "cargo"),
        ("area", "area"),
        ("holding", "holding"),
    ]:
        if chave in filtros:
            df_filtrado = aplicar_filtro_seguro_dashboard(df_filtrado, coluna, filtros.get(chave))
    df_auto = df_filtrado[df_filtrado['tipo'] == 'Autoavaliação']
    df_equipe = df_filtrado[df_filtrado['tipo'] == 'Avaliação Equipe']
    arquétipos = ['Imperativo', 'Resoluto', 'Cuidativo', 'Consultivo', 'Prescritivo', 'Formador']
    medias_auto = []
    for arq in arquétipos:
        valores = [row['arquétipos'][arq] for _, row in df_auto.iterrows() if 'arquétipos' in row and isinstance(row['arquétipos'], dict) and arq in row['arquétipos']]
        medias_auto.append(np.mean(valores) if valores else 0)
    medias_equipe = []
    for arq in arquétipos:
        valores = [row['arquétipos'][arq] for _, row in df_equipe.iterrows() if 'arquétipos' in row and isinstance(row['arquétipos'], dict) and arq in row['arquétipos']]
        medias_equipe.append(np.mean(valores) if valores else 0)
    return arquétipos, medias_auto, medias_equipe, df_filtrado


def calcular_medias_microambiente(df_respondentes, filtros):
    df_filtrado = df_respondentes.copy()
    for coluna, chave in [
        ("empresa", "empresa"),
        ("codrodada", "codrodada"),
        ("emailLider", "emaillider"),
        ("estado", "estado"),
        ("sexo", "sexo"),
        ("etnia", "etnia"),
        ("departamento", "departamento"),
        ("cargo", "cargo"),
        ("area", "area"),
        ("holding", "holding"),
    ]:
        if chave in filtros:
            df_filtrado = aplicar_filtro_seguro_dashboard(df_filtrado, coluna, filtros.get(chave))
    df_auto = df_filtrado[df_filtrado['tipo'] == 'Autoavaliação']
    df_equipe = df_filtrado[df_filtrado['tipo'] == 'Avaliação Equipe']
    dimensoes = ['Adaptabilidade', 'Colaboração Mútua', 'Nitidez', 'Performance', 'Reconhecimento', 'Responsabilidade']
    subdimensoes = [
        'Criação', 'Simplificação de Processos', 'Credibilidade Recíproca', 'Dedicação', 'Parceria',
        'Satisfação em Fazer Parte', 'Obrigações e Deveres', 'Propósito e Objetivo', 'Aprimoramento',
        'Qualidade Superior', 'Celebração', 'Performance', 'Liberdade de Ação', 'Responsabilização'
    ]
    def media_dim(df, col, dim):
        valores = [row[col][dim] for _, row in df.iterrows() if col in row and isinstance(row[col], dict) and dim in row[col]]
        return np.mean(valores) if valores else 0
    medias_real = [media_dim(df_auto, 'dimensoes_real', d) for d in dimensoes]
    medias_ideal = [media_dim(df_auto, 'dimensoes_ideal', d) for d in dimensoes]
    medias_equipe_real = [media_dim(df_equipe, 'dimensoes_real', d) for d in dimensoes]
    medias_equipe_ideal = [media_dim(df_equipe, 'dimensoes_ideal', d) for d in dimensoes]
    medias_subdimensoes_equipe_real = [media_dim(df_equipe, 'subdimensoes_real', s) for s in subdimensoes]
    medias_subdimensoes_equipe_ideal = [media_dim(df_equipe, 'subdimensoes_ideal', s) for s in subdimensoes]
    return dimensoes, medias_real, medias_ideal, medias_equipe_real, medias_equipe_ideal, medias_subdimensoes_equipe_real, medias_subdimensoes_equipe_ideal, df_filtrado


# ==================== FUNÇÕES DE GRÁFICOS ====================

def gerar_grafico_arquetipos(medias_auto, medias_equipe, arquétipos, titulo, tipo_visualizacao):
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Autoavaliação', x=arquétipos, y=medias_auto, marker_color='#1f77b4',
        text=[f"{v:.1f}%" for v in medias_auto], textposition='auto',
        hovertemplate='<b>%{x}</b><br>Autoavaliação: %{y:.1f}%<extra></extra>'))
    fig.add_trace(go.Bar(name='Média da Equipe', x=arquétipos, y=medias_equipe, marker_color='#ff7f0e',
        text=[f"{v:.1f}%" for v in medias_equipe], textposition='auto',
        hovertemplate='<b>%{x}</b><br>Média da Equipe: %{y:.1f}%<extra></extra>'))
    fig.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Suporte (50%)", annotation_position="right", line_width=2)
    fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="Dominante (60%)", annotation_position="right", line_width=2)
    fig.update_layout(
        title=f"📊 {titulo}", xaxis_title="Arquétipos", yaxis_title="Pontuação (%)",
        yaxis=dict(range=[0, 100]), barmode='group',
        height=600 if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique" else 500,
        hovermode='closest', showlegend=True,
        clickmode='event+select' if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique" else 'event'
    )
    return fig


def gerar_grafico_microambiente_linha(medias_real, medias_ideal, dimensoes, titulo):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dimensoes, y=medias_real, mode='lines+markers+text', name='Como é (Real)',
        line=dict(color='orange', width=3), marker=dict(size=8),
        text=[f"{v:.1f}%" for v in medias_real], textposition='top center'))
    fig.add_trace(go.Scatter(x=dimensoes, y=medias_ideal, mode='lines+markers+text', name='Como deveria ser (Ideal)',
        line=dict(color='darkblue', width=3), marker=dict(size=8),
        text=[f"{v:.1f}%" for v in medias_ideal], textposition='bottom center'))
    fig.update_layout(title=f"   {titulo}", xaxis_title="Dimensões", yaxis_title="Pontuação (%)",
        yaxis=dict(range=[0, 100]), height=500)
    return fig


# ==================== DRILL-DOWN ====================

def gerar_drill_down_arquetipos(arquétipo_clicado, df_respondentes_filtrado, matriz):
    """✅ LÓGICA CORRETA: busca na tabela individualmente para cada respondente"""
    questoes_impacto = matriz[
        (matriz['ARQUETIPO'] == arquétipo_clicado) &
        (matriz['PONTOS_MAXIMOS'] == 200)
    ]['COD_AFIRMACAO'].unique().tolist()

    if not questoes_impacto:
        return None

    questoes_detalhadas = []
    for questao in questoes_impacto:
        linha_questao = matriz[matriz['COD_AFIRMACAO'] == questao].iloc[0]
        afirmacao = linha_questao['AFIRMACAO']

        # ✅ Busca na tabela individualmente para cada respondente
        percentual_medio, tendencia_info, n_respostas = calcular_tendencia_arquetipos_por_questao(
            df_respondentes_filtrado, matriz, questao, arquétipo_clicado
        )

        if percentual_medio is not None:
            if 'DESFAVORÁVEL' in tendencia_info:
                valor_grafico = -percentual_medio
            else:
                valor_grafico = percentual_medio

            # Média de estrelas apenas para exibição
            estrelas_lista = []
            for _, respondente in df_respondentes_filtrado.iterrows():
                if 'respostas' in respondente and questao in respondente['respostas']:
                    estrelas_lista.append(int(respondente['respostas'][questao]))
            media_estrelas = np.mean(estrelas_lista) if estrelas_lista else 0

            questoes_detalhadas.append({
                'questao': questao,
                'afirmacao': afirmacao,
                'media_estrelas': media_estrelas,
                'media_arredondada': round(media_estrelas),
                'tendencia': percentual_medio,
                'tendencia_info': tendencia_info,
                'valor_grafico': valor_grafico,
                'n_respostas': n_respostas
            })

    questoes_detalhadas.sort(key=lambda x: x['tendencia'], reverse=True)
    return questoes_detalhadas


def gerar_drill_down_microambiente(dimensao_clicada, df_respondentes_filtrado, matriz, tipo_analise):
    """✅ LÓGICA CORRETA: busca na tabela individualmente para cada respondente"""
    if tipo_analise == "Média da Equipe":
        df_dados = df_respondentes_filtrado[df_respondentes_filtrado['tipo'] == 'Avaliação Equipe']
    elif tipo_analise == "Autoavaliação":
        df_dados = df_respondentes_filtrado[df_respondentes_filtrado['tipo'] == 'Autoavaliação']
    else:
        df_dados = df_respondentes_filtrado

    questoes_detalhadas = []
    linhas_dim = matriz[matriz['DIMENSAO'] == dimensao_clicada][['COD', 'AFIRMACAO', 'SUBDIMENSAO']].drop_duplicates()

    for _, row in linhas_dim.iterrows():
        codigo_matriz = row['COD']
        afirmacao = row['AFIRMACAO']
        subdim = row['SUBDIMENSAO']
        codigo_form = _MAP_MATRIZ_TO_FORM.get(codigo_matriz, codigo_matriz)

        # ✅ Busca na tabela individualmente
        real_pct, ideal_pct, gap = calcular_real_ideal_gap_por_questao(df_dados, matriz, codigo_matriz)
        if real_pct is None:
            continue

        questoes_detalhadas.append({
            'questao': codigo_form,
            'afirmacao': afirmacao,
            'dimensao': dimensao_clicada,
            'subdimensao': subdim,
            'media_real': real_pct,
            'media_ideal': ideal_pct,
            'pontuacao_real': real_pct,
            'pontuacao_ideal': ideal_pct,
            'gap': gap,
            'n_respostas': None
        })

    questoes_detalhadas.sort(key=lambda x: x['gap'], reverse=True)
    return questoes_detalhadas


# ==================== BUSCAR DADOS ====================

def adicionar_holding_ao_dataframe(df, contexto_por_chave):
    holdings = []
    holding_ids = []
    empresa_ids = []
    filial_ids = []
    company_names = []
    branch_names = []
    for _, row in df.iterrows():
        email = str(row.get('email', '')).lower()
        email_lider = str(row.get('emailLider', '')).lower()
        empresa = str(row.get('empresa', '')).lower()
        contexto = (
            contexto_por_chave.get(email)
            or contexto_por_chave.get(email_lider)
            or contexto_por_chave.get(empresa)
            or {}
        )
        # O contexto historico da resposta deve prevalecer sobre o cadastro
        # atual do respondente. Um profissional pode mudar de empresa/holding
        # depois de responder a rodada sem que a resposta mude de contexto.
        holding = primeiro_valido(row.get('holding'))
        if holding:
            holding = str(holding).upper().strip()
        if not holding:
            codrodada = str(row.get('codrodada', '')).lower()
            if 'leven' in codrodada:
                holding = 'LEVEN'
            elif empresa in ['astro34', 'spectral_v', 'spectral_a', 'spectral_sales', 'fastco', 'futurex'] or \
               any(x in empresa for x in ['astro34', 'spectral', 'fastco', 'futurex']):
                holding = 'PROSPERA'
            else:
                holding = primeiro_valido(contexto.get('holding'))
                holding = str(holding).upper().strip() if holding else (empresa.upper() if empresa else 'N/A')
        holdings.append(str(holding).upper().strip() if holding else 'N/A')
        holding_ids.append(primeiro_valido(row.get('holding_id'), contexto.get('holding_id'), ''))
        empresa_ids.append(primeiro_valido(row.get('empresa_id'), contexto.get('empresa_id'), ''))
        filial_ids.append(primeiro_valido(row.get('filial_id'), contexto.get('filial_id'), ''))
        company_names.append(primeiro_valido(row.get('company_name'), contexto.get('company_name'), ''))
        branch_names.append(primeiro_valido(row.get('branch_name'), contexto.get('branch_name'), ''))
    df['holding'] = holdings
    df['holding_id'] = holding_ids
    df['empresa_id'] = empresa_ids
    df['filial_id'] = filial_ids
    df['company_name'] = company_names
    df['branch_name'] = branch_names
    return df


@st.cache_data(ttl=300)
def fetch_data(ctx_key=(), filtro_key=()):
    try:
        supabase = init_supabase()
        ctx = contexto_from_cache_key(ctx_key)
        filtros_consulta = filtros_consulta_from_cache_key(filtro_key)
        consolidado_arq, consolidado_micro = consultar_consolidados_com_fallback(
            supabase,
            ctx,
            filtros_consulta,
        )
        return consolidado_arq, consolidado_micro
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {str(e)}")
        return [], []


# ==================== INTERFACE PRINCIPAL ====================

st.title("🎯 LeaderTrack Dashboard")
st.markdown("---")

ctx = contexto_url()
filtros_preconsulta = filtros_preconsulta_dashboard(ctx)

with st.spinner("Carregando matrizes..."):
    matriz_arq = carregar_matriz_arquetipos()
    matriz_micro, pontos_max_dimensao, pontos_max_subdimensao = carregar_matrizes_microambiente()

if matriz_arq is not None and matriz_micro is not None:
    with st.spinner("Carregando dados dos respondentes..."):
        consolidado_arq, consolidado_micro = fetch_data(
            contexto_cache_key(ctx),
            filtro_consulta_cache_key(filtros_preconsulta),
        )

    if not (consolidado_arq and consolidado_micro):
        qtd_arq = len(consolidado_arq or [])
        qtd_micro = len(consolidado_micro or [])
        st.error(
            "Não encontrei dados suficientes para montar o dashboard com o contexto/filtro atual."
        )
        st.caption(
            f"Registros encontrados: Arquétipos={qtd_arq}; Microambiente={qtd_micro}. "
            "Abra pelo portal The HR Key com o contexto selecionado ou limpe os filtros do menu lateral."
        )
        st.stop()

    if consolidado_arq and consolidado_micro:
        st.success("✅ Conectado ao Supabase!")

        with st.spinner("Carregando dados de holding..."):
            try:
                supabase = init_supabase()
                employees_rows = []
                try:
                    employees_rows = executar_query_com_fallback(
                        supabase,
                        'employees',
                        'email,emailLider,holding,holding_id,empresa,empresa_id,company_name,filial_id,branch_name',
                        ctx,
                    )
                except:
                    try:
                        employees_rows = supabase.table('employees').select('email, holding, empresa').execute().data
                    except:
                        try:
                            employees_rows = supabase.table('employees').select('holding').execute().data
                        except:
                            employees_rows = supabase.table('employees').select('*').execute().data
                contexto_por_chave = {}
                if employees_rows:
                    for emp in employees_rows:
                        email = emp.get('email', '').lower() if emp.get('email') else ''
                        email_lider = emp.get('emailLider', '').lower() if emp.get('emailLider') else ''
                        holding = str(emp.get('holding', 'N/A')).upper().strip()
                        empresa = emp.get('empresa', '')
                        contexto_emp = {
                            'holding': holding,
                            'holding_id': emp.get('holding_id', ''),
                            'empresa_id': emp.get('empresa_id', ''),
                            'company_name': emp.get('company_name', ''),
                            'filial_id': emp.get('filial_id', ''),
                            'branch_name': emp.get('branch_name', ''),
                        }
                        if email:
                            contexto_por_chave[email] = contexto_emp
                        if email_lider:
                            contexto_por_chave[email_lider] = contexto_emp
                        if empresa:
                            empresa_lower = empresa.lower()
                            if empresa_lower not in contexto_por_chave:
                                contexto_por_chave[empresa_lower] = contexto_emp
            except Exception as e:
                st.warning(f"⚠️ Aviso: Não foi possível carregar dados de holding: {str(e)}")
                contexto_por_chave = {}

        with st.spinner("Calculando arquétipos individuais..."):
            df_arquetipos = processar_dados_arquetipos(consolidado_arq, matriz_arq)
            df_arquetipos = adicionar_holding_ao_dataframe(df_arquetipos, contexto_por_chave)

        with st.spinner("Calculando microambiente individual..."):
            df_microambiente = processar_dados_microambiente(consolidado_micro, matriz_micro, pontos_max_dimensao, pontos_max_subdimensao)
            df_microambiente = adicionar_holding_ao_dataframe(df_microambiente, contexto_por_chave)

        # Normalizar campos
        for col in ['empresa', 'codrodada', 'emailLider', 'estado', 'sexo', 'etnia', 'departamento', 'cargo']:
            df_arquetipos[col] = df_arquetipos[col].astype(str).str.lower()
            df_microambiente[col] = df_microambiente[col].astype(str).str.lower()
        if 'holding' in df_arquetipos.columns:
            df_arquetipos['holding'] = df_arquetipos['holding'].astype(str).str.upper()
        if 'holding' in df_microambiente.columns:
            df_microambiente['holding'] = df_microambiente['holding'].astype(str).str.upper()


        # ==================== CONTEXTO RECEBIDO DO WORDPRESS ====================
        if ctx.get("nivel_contexto"):
            st.session_state["hrkey_contexto"] = ctx
            persistir_contexto_no_navegador(ctx)
            corrigir_menu_streamlit_com_contexto(ctx)

            df_arquetipos = filtrar_leadertrack_por_contexto(df_arquetipos, ctx)
            df_microambiente = filtrar_leadertrack_por_contexto(df_microambiente, ctx)

            contexto_label = (
                ctx.get("contexto_nome")
                or ctx.get("filial_nome")
                or ctx.get("empresa_nome")
                or ctx.get("holding_nome")
                or "—"
            )

            st.info(
                f"Contexto aplicado: {str(ctx.get('nivel_contexto')).upper()} · {contexto_label}"
            )        

 

        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Arquétipos", len(df_arquetipos))
        with col2:
            st.metric("🏢 Total Microambiente", len(df_microambiente))
        with col3:
            st.metric("👤 Autoavaliações", len(df_arquetipos[df_arquetipos['tipo'] == 'Autoavaliação']))
        with col4:
            st.metric("Última Atualização", datetime.now().strftime("%H:%M"))

        # FILTROS
        st.sidebar.header("🎛️ Filtros Globais")
        st.sidebar.subheader("Filtros Principais")
        
        filtros_url = filtros_url_dashboard()
        
        def encontrar_index_opcao(opcoes, valor_url, default_index=0):
            """
            Procura uma opção ignorando maiúsculas/minúsculas.
            Se não encontrar, mantém o índice padrão.
            """
            if not valor_url:
                return default_index
        
            valor_url_norm = str(valor_url).strip().lower()
        
            for idx, opt in enumerate(opcoes):
                if str(opt).strip().lower() == valor_url_norm:
                    return idx
        
            return default_index
        
        
        # =========================
        # HOLDING
        # =========================
        holdings_arq = set(df_arquetipos['holding'].dropna().unique()) if 'holding' in df_arquetipos.columns else set()
        holdings_micro = set(df_microambiente['holding'].dropna().unique()) if 'holding' in df_microambiente.columns else set()
        
        todas_holdings = [
            h for h in sorted([str(h) for h in holdings_arq.union(holdings_micro)])
            if h and str(h).strip() and str(h).upper() != 'N/A'
        ]
        
        holdings = ["Todas"] + todas_holdings
        holding_preconsulta = filtros_preconsulta.get("holding")
        if holding_preconsulta and holding_preconsulta != "Todas" and holding_preconsulta not in holdings:
            holdings.append(holding_preconsulta)
        
        holding_default_index = 0
        if filtros_url.get("holding_nome"):
            holding_default_index = encontrar_index_opcao(holdings, filtros_url.get("holding_nome"), 0)
        
        holding_selecionada = st.sidebar.selectbox(
            "🏢 Holding",
            holdings,
            index=holding_default_index,
            key="filtro_holding",
        ) if len(holdings) > 1 else "Todas"
        
        
        # =========================
        # EMPRESA
        # =========================
        todas_empresas = sorted([
            str(e)
            for e in set(df_arquetipos['empresa'].unique()).union(set(df_microambiente['empresa'].unique()))
        ])
        
        empresa_options = ["Todas"] + todas_empresas
        empresa_preconsulta = filtros_preconsulta.get("empresa")
        if empresa_preconsulta and empresa_preconsulta != "Todas" and empresa_preconsulta not in empresa_options:
            empresa_options.append(empresa_preconsulta)
        empresa_default_index = 0
        
        nivel_contexto_url = str(filtros_url.get("nivel_contexto") or "").strip().lower()
        
        """
        Regra:
        - Se o contexto vindo da URL for HOLDING, a empresa deve ficar em "Todas".
          Assim o dashboard consolida todas as empresas daquela holding.
        - Se o contexto for EMPRESA, aí sim aplicamos a empresa da URL.
        """
        
        if nivel_contexto_url != "holding":
            if filtros_url.get("company"):
                empresa_default_index = encontrar_index_opcao(empresa_options, filtros_url.get("company"), 0)
            elif filtros_url.get("empresa_nome"):
                empresa_default_index = encontrar_index_opcao(empresa_options, filtros_url.get("empresa_nome"), 0)
        
        empresa_selecionada = st.sidebar.selectbox(
            "Empresa",
            empresa_options,
            index=empresa_default_index,
            key="filtro_empresa",
        )
        
        
        # =========================
        # CÓDIGO DA RODADA
        # =========================
        todas_codrodadas = sorted([
            str(c)
            for c in set(df_arquetipos['codrodada'].unique()).union(set(df_microambiente['codrodada'].unique()))
        ])
        
        codrodada_options = ["Todas"] + todas_codrodadas
        codrodada_preconsulta = filtros_preconsulta.get("codrodada")
        if codrodada_preconsulta and codrodada_preconsulta != "Todas" and codrodada_preconsulta not in codrodada_options:
            codrodada_options.append(codrodada_preconsulta)
        codrodada_default_index = 0
        
        if filtros_url.get("codrodada"):
            codrodada_default_index = encontrar_index_opcao(codrodada_options, filtros_url.get("codrodada"), 0)
        
        codrodada_selecionada = st.sidebar.selectbox(
            "Código da Rodada",
            codrodada_options,
            index=codrodada_default_index,
            key="filtro_codrodada",
        )
        
        
        # =========================
        # EMAIL DO LÍDER
        # =========================
        todos_emailliders = sorted([
            str(e).strip().lower()
            for e in set(df_arquetipos['emailLider'].unique()).union(set(df_microambiente['emailLider'].unique()))
            if str(e).strip()
        ])
        
        emaillider_url = filtros_url.get("emaillider")
        pode_administrar_url = filtros_url.get("pode_administrar") == "true"
        
        if emaillider_url and not pode_administrar_url:
            """
            Usuário comum:
            se a URL veio com emaillider, o dashboard fica travado nesse líder.
            Não mostra 'Todos' e não permite escolher outros líderes.
            """
            emaillider_options = [emaillider_url]
            emaillider_default_index = 0
        
        elif emaillider_url and pode_administrar_url:
            """
            Admin/RH/Master:
            pode continuar vendo todos, mas se a URL trouxe um líder específico,
            o dashboard já abre selecionado nele.
            """
            emaillider_options = ["Todos"] + todos_emailliders
        
            if emaillider_url not in emaillider_options:
                emaillider_options.append(emaillider_url)
        
            emaillider_default_index = encontrar_index_opcao(emaillider_options, emaillider_url, 0)
        
        else:
            """
            Sem líder específico na URL:
            mantém comportamento padrão.
            """
            emaillider_options = ["Todos"] + todos_emailliders
            emaillider_default_index = 0

        emaillider_preconsulta = filtros_preconsulta.get("emaillider")
        if emaillider_preconsulta and emaillider_preconsulta != "Todos" and emaillider_preconsulta not in emaillider_options:
            emaillider_options.append(emaillider_preconsulta)
        
        emaillider_selecionado = st.sidebar.selectbox(
            "👤 Email do Líder",
            emaillider_options,
            index=emaillider_default_index,
            key="filtro_emaillider",
        )
        
        
        # =========================
        # ESTADO
        # =========================
        todos_estados = sorted([
            str(e)
            for e in set(df_arquetipos['estado'].unique()).union(set(df_microambiente['estado'].unique()))
        ])
        
        estado_selecionado = st.sidebar.selectbox(
            "🗺️ Estado",
            ["Todos"] + todos_estados,
            key="filtro_estado",
        )
        
        
        # =========================
        # GÊNERO
        # =========================
        todos_generos = sorted([
            str(g)
            for g in set(df_arquetipos['sexo'].unique()).union(set(df_microambiente['sexo'].unique()))
        ])
        
        genero_selecionado = st.sidebar.selectbox(
            "⚧ Gênero",
            ["Todos"] + todos_generos,
            key="filtro_genero",
        )
        
        
        # =========================
        # ETNIA
        # =========================
        todas_etnias = sorted([
            str(e)
            for e in set(df_arquetipos['etnia'].unique()).union(set(df_microambiente['etnia'].unique()))
        ])
        
        etnia_selecionada = st.sidebar.selectbox(
            "Etnia",
            ["Todas"] + todas_etnias,
            key="filtro_etnia",
        )
        
        
        # =========================
        # DEPARTAMENTO
        # =========================
        todos_departamentos = sorted([
            str(d)
            for d in set(df_arquetipos['departamento'].unique()).union(set(df_microambiente['departamento'].unique()))
        ])
        
        departamento_selecionado = st.sidebar.selectbox(
            "🏢 Departamento",
            ["Todos"] + todos_departamentos,
            key="filtro_departamento",
        )
        
        
        # =========================
        # CARGO
        # =========================
        todos_cargos = sorted([
            str(c)
            for c in set(df_arquetipos['cargo'].unique()).union(set(df_microambiente['cargo'].unique()))
        ])
        
        cargo_selecionado = st.sidebar.selectbox(
            "💼 Cargo",
            ["Todos"] + todos_cargos,
            key="filtro_cargo",
        )
        
        
        # =========================
        # DICIONÁRIO FINAL DE FILTROS
        # =========================
        filtros = {
            'empresa': empresa_selecionada.lower() if empresa_selecionada != "Todas" else empresa_selecionada,
            'codrodada': codrodada_selecionada.lower() if codrodada_selecionada != "Todas" else codrodada_selecionada,
            'emaillider': emaillider_selecionado.lower() if emaillider_selecionado != "Todos" else emaillider_selecionado,
            'estado': estado_selecionado.lower() if estado_selecionado != "Todos" else estado_selecionado,
            'sexo': genero_selecionado.lower() if genero_selecionado != "Todos" else genero_selecionado,
            'etnia': etnia_selecionada.lower() if etnia_selecionada != "Todas" else etnia_selecionada,
            'departamento': departamento_selecionado.lower() if departamento_selecionado != "Todos" else departamento_selecionado,
            'cargo': cargo_selecionado.lower() if cargo_selecionado != "Todos" else cargo_selecionado,
            'holding': holding_selecionada.upper() if holding_selecionada != "Todas" else holding_selecionada,
        }
        tab1, tab2, tab3, tab4 = st.tabs([
            "📊 Arquétipos",
            "🏢 Microambiente",
            "💚 Saúde Emocional",
            "🏛️ Parecer Corporativo",
        ])

        # ==================== TAB ARQUÉTIPOS ====================
        with tab1:
            st.header("📊 Análise de Arquétipos de Liderança")
            arquétipos, medias_auto, medias_equipe, df_filtrado_arq = calcular_medias_arquetipos(df_arquetipos, filtros)
            if arquétipos:
                titulo_parts = [f"{k}: {v}" for k, v in filtros.items() if v not in ["Todas", "Todos"]]
                titulo = " | ".join(titulo_parts) if titulo_parts else "Média Geral de Todos os Respondentes"
                st.markdown("**🎨 Escolha o tipo de visualização:**")
                tipo_visualizacao = st.radio("Tipo de Gráfico:", ["📊 Gráfico com Rótulos e Clique", "📈 Gráfico Simples"], horizontal=True, key="arquetipos")
                fig = gerar_grafico_arquetipos(medias_auto, medias_equipe, arquétipos, titulo, tipo_visualizacao)
                st.plotly_chart(fig, use_container_width=True)

                if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique":
                    st.info("💡 **Dica:** Selecione um arquétipo abaixo para ver as questões detalhadas!")
                    st.subheader("🔍 Drill-Down por Arquétipo")
                    arquétipo_selecionado = st.selectbox("Selecione um arquétipo:", arquétipos, index=None, placeholder="Escolha um arquétipo...", key="arquetipo_select")
                    if arquétipo_selecionado:
                        st.markdown(f"### 📋 Questões que Impactam: **{arquétipo_selecionado}**")
                        
                        df_equipe_arq = df_filtrado_arq[df_filtrado_arq['tipo'] == 'Avaliação Equipe']
                        questoes_detalhadas = gerar_drill_down_arquetipos(arquétipo_selecionado, df_equipe_arq, matriz_arq)
                        
                        if questoes_detalhadas:
                            questoes = [q['questao'] for q in questoes_detalhadas]
                            valores_grafico = [q['valor_grafico'] for q in questoes_detalhadas]
                            cores_barras = []
                            for q in questoes_detalhadas:
                                t = q['tendencia_info']
                                if t == 'MUITO DESFAVORÁVEL': cores_barras.append('rgba(255, 0, 0, 0.8)')
                                elif t == 'POUCO DESFAVORÁVEL': cores_barras.append('rgba(255, 255, 0, 0.7)')
                                elif t == 'DESFAVORÁVEL': cores_barras.append('rgba(255, 165, 0, 0.7)')
                                elif t == 'FAVORÁVEL': cores_barras.append('rgba(0, 255, 0, 0.3)')
                                elif t == 'MUITO FAVORÁVEL': cores_barras.append('rgba(0, 128, 0, 0.5)')
                                elif t == 'POUCO FAVORÁVEL': cores_barras.append('rgba(0, 128, 0, 0.4)')
                                else: cores_barras.append('rgba(128, 128, 128, 0.5)')
                            fig_questoes = go.Figure()
                            fig_questoes.add_trace(go.Bar(x=questoes, y=valores_grafico, marker_color=cores_barras,
                                text=[f"{v:.1f}%" for v in valores_grafico], textposition='auto',
                                hovertemplate='<b>%{x}</b><br>% Tendência: %{y:.1f}%<br>Média: %{customdata:.1f} estrelas<extra></extra>',
                                customdata=[q['media_estrelas'] for q in questoes_detalhadas]))
                            fig_questoes.update_layout(title=f"📊 % Tendência das Questões - {arquétipo_selecionado}",
                                xaxis_title="Questões", yaxis_title="% Tendência", yaxis=dict(range=[-100, 100]), height=400)
                            st.plotly_chart(fig_questoes, use_container_width=True)
                            st.subheader("📋 Detalhamento das Questões")
                            df_questoes = pd.DataFrame(questoes_detalhadas)
                            df_questoes['Tendência'] = df_questoes['tendencia_info']
                            df_questoes['% Tendência'] = df_questoes['tendencia'].apply(lambda x: f"{x:.1f}%")
                            df_questoes['Questão'] = df_questoes['questao']
                            df_questoes['Afirmação'] = df_questoes['afirmacao']
                            df_questoes['Média Estrelas'] = df_questoes['media_estrelas'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Média Arredondada'] = df_questoes['media_arredondada']
                            df_questoes['Nº Respostas'] = df_questoes['n_respostas']
                            def color_tendencia(val):
                                val_str = str(val).strip()
                                if val_str == 'POUCO DESFAVORÁVEL': return 'background-color: rgba(255, 255, 0, 0.4)'
                                elif val_str == 'DESFAVORÁVEL': return 'background-color: rgba(255, 165, 0, 0.5)'
                                elif val_str == 'MUITO DESFAVORÁVEL': return 'background-color: rgba(255, 0, 0, 0.8)'
                                elif val_str == 'MUITO FAVORÁVEL': return 'background-color: rgba(0, 255, 0, 0.1)'
                                elif val_str == 'FAVORÁVEL': return 'background-color: rgba(0, 255, 0, 0.2)'
                                elif val_str == 'POUCO FAVORÁVEL': return 'background-color: rgba(0, 128, 0, 0.3)'
                                else: return 'background-color: rgba(200, 200, 200, 0.1)'
                            df_questoes_styled = df_questoes[['Questão', 'Afirmação', '% Tendência', 'Tendência', 'Média Estrelas', 'Média Arredondada', 'Nº Respostas']].style.map(color_tendencia, subset=['Tendência'])
                            st.dataframe(df_questoes_styled, use_container_width=True, hide_index=True)
                            st.info(f"**📊 Informações:** {len(df_filtrado_arq)} respondentes filtrados. % Tendência calculado individualmente por respondente.")
                        else:
                            st.warning(f"⚠️ Nenhuma questão de impacto encontrada para {arquétipo_selecionado}")

                col1, col2, col3 = st.columns(3)
                with col1: st.info(f"**📊 Respondentes Analisados:** {len(df_filtrado_arq)}")
                with col2: st.info(f"**👥 Total de Avaliações:** {len(df_filtrado_arq)}")
                with col3: st.info(f"**📈 Arquétipos Analisados:** {len(arquétipos)}")
                st.subheader("📋 Tabela de Médias")
                df_medias = pd.DataFrame({'Arquétipo': arquétipos, 'Autoavaliação (%)': [f"{v:.1f}%" for v in medias_auto], 'Média Equipe (%)': [f"{v:.1f}%" for v in medias_equipe]})
                st.dataframe(df_medias, use_container_width=True)
            else:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")

        # ==================== TAB MICROAMBIENTE ====================
        with tab2:
            st.header("🏢 Análise de Microambiente de Equipes")
            dimensoes, medias_real, medias_ideal, medias_equipe_real, medias_equipe_ideal, medias_subdimensoes_equipe_real, medias_subdimensoes_equipe_ideal, df_filtrado_micro = calcular_medias_microambiente(df_microambiente, filtros)
            if dimensoes:
                titulo_parts = [f"{k}: {v}" for k, v in filtros.items() if v not in ["Todas", "Todos"]]
                titulo = " | ".join(titulo_parts) if titulo_parts else "Média Geral de Todos os Respondentes"
                st.markdown("**🎯 Escolha o tipo de análise:**")
                tipo_analise = st.radio("Tipo de Análise:", ["Autoavaliação", "Média da Equipe", "Comparativo (Auto vs Equipe)"], horizontal=True, key="tipo_analise_micro")
                if tipo_analise == "Autoavaliação":
                    medias_real_final, medias_ideal_final, titulo_analise = medias_real, medias_ideal, "Autoavaliação"
                elif tipo_analise == "Média da Equipe":
                    medias_real_final, medias_ideal_final, titulo_analise = medias_equipe_real, medias_equipe_ideal, "Média da Equipe"
                else:
                    medias_real_final, medias_ideal_final, titulo_analise = medias_real, medias_ideal, "Comparativo"
                st.markdown("**🎨 Escolha o tipo de visualização:**")
                tipo_visualizacao = st.radio("Tipo de Gráfico:", ["📊 Gráfico com Rótulos e Clique", "📈 Gráfico Simples"], horizontal=True, key="microambiente")
                fig = gerar_grafico_microambiente_linha(medias_real_final, medias_ideal_final, dimensoes, f"{titulo} - {titulo_analise}")
                st.plotly_chart(fig, use_container_width=True, key=f"grafico_dimensoes_{tipo_analise}")
                st.subheader("📊 Análise por Subdimensões")
                df_auto = df_filtrado_micro[df_filtrado_micro['tipo'] == 'Autoavaliação']
                df_equipe = df_filtrado_micro[df_filtrado_micro['tipo'] == 'Avaliação Equipe']
                subdimensoes = ['Criação', 'Simplificação de Processos', 'Credibilidade Recíproca', 'Dedicação', 'Parceria',
                    'Satisfação em Fazer Parte', 'Obrigações e Deveres', 'Propósito e Objetivo', 'Aprimoramento',
                    'Qualidade Superior', 'Celebração', 'Performance', 'Liberdade de Ação', 'Responsabilização']
                df_sub = df_auto if tipo_analise == "Autoavaliação" else df_equipe
                col_real = 'subdimensoes_real'
                col_ideal = 'subdimensoes_ideal'
                medias_sub_real = [np.mean([r[col_real][s] for _, r in df_sub.iterrows() if col_real in r and isinstance(r[col_real], dict) and s in r[col_real]]) if any(col_real in r and isinstance(r[col_real], dict) and s in r[col_real] for _, r in df_sub.iterrows()) else 0 for s in subdimensoes]
                medias_sub_ideal = [np.mean([r[col_ideal][s] for _, r in df_sub.iterrows() if col_ideal in r and isinstance(r[col_ideal], dict) and s in r[col_ideal]]) if any(col_ideal in r and isinstance(r[col_ideal], dict) and s in r[col_ideal] for _, r in df_sub.iterrows()) else 0 for s in subdimensoes]
                fig_sub = go.Figure()
                fig_sub.add_trace(go.Scatter(x=subdimensoes, y=medias_sub_real, mode='lines+markers+text', name='Como é (Real)',
                    line=dict(color='orange', width=3), marker=dict(size=8), text=[f"{v:.1f}%" for v in medias_sub_real], textposition='top center'))
                fig_sub.add_trace(go.Scatter(x=subdimensoes, y=medias_sub_ideal, mode='lines+markers+text', name='Como deveria ser (Ideal)',
                    line=dict(color='darkblue', width=3), marker=dict(size=8), text=[f"{v:.1f}%" for v in medias_sub_ideal], textposition='bottom center'))
                fig_sub.update_layout(title=f"📊 Microambiente por Subdimensões - {titulo_analise}", xaxis_title="Subdimensões", yaxis_title="Pontuação (%)", yaxis=dict(range=[0, 100]), height=500)
                st.plotly_chart(fig_sub, use_container_width=True)
                if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique":
                    st.subheader("🔍 Drill-Down por Dimensão")
                    dimensao_selecionada = st.selectbox("Selecione uma dimensão:", dimensoes, index=None, placeholder="Escolha uma dimensão...", key="dimensao_select_micro")
                    if dimensao_selecionada:
                        st.markdown(f"### 📋 Questões que Impactam: **{dimensao_selecionada}**")
                        questoes_detalhadas = gerar_drill_down_microambiente(dimensao_selecionada, df_filtrado_micro, matriz_micro, tipo_analise)
                        if questoes_detalhadas:
                            questoes = [q['questao'] for q in questoes_detalhadas]
                            gaps = [q['gap'] for q in questoes_detalhadas]
                            cores_gaps = []
                            for gap in gaps:
                                if gap > 80: cores_gaps.append('rgba(255, 0, 0, 0.8)')
                                elif gap > 60: cores_gaps.append('rgba(255, 100, 0, 0.8)')
                                elif gap > 40: cores_gaps.append('rgba(255, 165, 0, 0.7)')
                                elif gap > 20: cores_gaps.append('rgba(255, 255, 0, 0.6)')
                                elif gap > 0: cores_gaps.append('rgba(144, 238, 144, 0.6)')
                                else: cores_gaps.append('rgba(0, 255, 0, 0.5)')
                            fig_questoes = go.Figure()
                            fig_questoes.add_trace(go.Bar(x=questoes, y=gaps, marker_color=cores_gaps,
                                text=[f"{v:.1f}" for v in gaps], textposition='auto',
                                hovertemplate='<b>%{x}</b><br>Gap: %{y:.1f}<br>Real: %{customdata[0]:.1f} | Ideal: %{customdata[1]:.1f}<extra></extra>',
                                customdata=[[q['pontuacao_real'], q['pontuacao_ideal']] for q in questoes_detalhadas]))
                            fig_questoes.update_layout(title=f"Gap das Questões - {dimensao_selecionada}", xaxis_title="Questões", yaxis_title="Gap (Ideal - Real)", height=400)
                            st.plotly_chart(fig_questoes, use_container_width=True)
                            st.subheader("📋 Detalhamento das Questões")
                            df_questoes = pd.DataFrame(questoes_detalhadas)
                            df_questoes['Questão'] = df_questoes['questao']
                            df_questoes['Afirmação'] = df_questoes['afirmacao']
                            df_questoes['Dimensão'] = df_questoes['dimensao']
                            df_questoes['Subdimensão'] = df_questoes['subdimensao']
                            df_questoes['Real (%)'] = df_questoes['media_real'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Ideal (%)'] = df_questoes['media_ideal'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Gap'] = df_questoes['gap'].apply(lambda x: f"{x:.1f}")
                            df_questoes = df_questoes.sort_values(['Dimensão', 'Subdimensão'])
                            def color_gap(val):
                                try:
                                    gap_val = float(val)
                                    if gap_val > 80: return 'background-color: rgba(255, 0, 0, 0.8)'
                                    elif gap_val > 60: return 'background-color: rgba(255, 100, 0, 0.8)'
                                    elif gap_val > 40: return 'background-color: rgba(255, 165, 0, 0.7)'
                                    elif gap_val > 20: return 'background-color: rgba(255, 255, 0, 0.6)'
                                    elif gap_val > 0: return 'background-color: rgba(144, 238, 144, 0.6)'
                                    else: return 'background-color: rgba(0, 255, 0, 0.5)'
                                except: return 'background-color: transparent'
                            df_questoes_styled = df_questoes[['Questão', 'Afirmação', 'Dimensão', 'Subdimensão', 'Real (%)', 'Ideal (%)', 'Gap']].style.map(color_gap, subset=['Gap'])
                            st.dataframe(df_questoes_styled, use_container_width=True, hide_index=True)
                            st.info(f"**📊 Informações:** {len(df_filtrado_micro)} respondentes filtrados. Real/Ideal/Gap calculados individualmente por respondente.")
                        else:
                            st.warning(f"⚠️ Nenhuma questão encontrada para {dimensao_selecionada}")
                col1, col2, col3 = st.columns(3)
                with col1: st.info(f"**📊 Respondentes Analisados:** {len(df_filtrado_micro)}")
                with col2: st.info(f"**👥 Total de Avaliações:** {len(df_filtrado_micro)}")
                with col3: st.info(f"**📈 Dimensões Analisadas:** {len(dimensoes)}")
                st.subheader("📋 Tabela de Médias")
                df_medias = pd.DataFrame({'Dimensão': dimensoes, f'{titulo_analise} (Real) (%)': [f"{v:.1f}%" for v in medias_real_final], f'{titulo_analise} (Ideal) (%)': [f"{v:.1f}%" for v in medias_ideal_final]})
                st.dataframe(df_medias, use_container_width=True)
            else:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")

        # ==================== TAB SAÚDE EMOCIONAL ====================
        with tab3:
            st.header("💚 Análise de Saúde Emocional + Compliance NR-1")
            st.markdown("**🔍 Analisando afirmações existentes relacionadas à saúde emocional...**")

            with st.spinner("Identificando afirmações de saúde emocional..."):
                afirmacoes_saude_emocional, df_arq_filtrado, df_micro_filtrado = analisar_afirmacoes_saude_emocional(
                    matriz_arq, matriz_micro, df_arquetipos, df_microambiente, filtros)
                compliance_nr1 = mapear_compliance_nr1(afirmacoes_saude_emocional)

            if afirmacoes_saude_emocional:
                col1, col2, col3, col4 = st.columns(4)
                with col1: st.metric("🧠 Arquétipos SE", len([a for a in afirmacoes_saude_emocional if a['tipo'] == 'Arquétipo']))
                with col2: st.metric("Microambiente SE", len([a for a in afirmacoes_saude_emocional if a['tipo'] == 'Microambiente']))
                with col3: st.metric("💚 Total SE", len(afirmacoes_saude_emocional))
                with col4:
                    import os
                    arquivo_csv = 'TABELA_SAUDE_EMOCIONAL.csv'
                    if os.path.exists(arquivo_csv):
                        df_csv_temp = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig')
                        total_csv = len(df_csv_temp)
                        percentual = (len(afirmacoes_saude_emocional) / total_csv) * 100 if total_csv > 0 else 0
                        st.metric(f"📊 % das {total_csv} Afirmações (CSV)", f"{percentual:.1f}%")
                    else:
                        st.metric("📊 Total de Afirmações", len(afirmacoes_saude_emocional))
                st.divider()

            # ==================== GRÁFICO COMPLIANCE NR-1 ====================
            st.subheader("📊 Compliance NR-1 + Adendo Saúde Mental - Valores das Questões")

            categoria_valores = {
                'Prevenção de Estresse': [],
                'Ambiente Psicológico Seguro': [],
                'Suporte Emocional': [],
                'Comunicação Positiva': [],
                'Equilíbrio Vida-Trabalho': []
            }

            MAPEAMENTO_QUESTOES_SE = {
                'Q01':'Q01','Q02':'Q12','Q03':'Q23','Q04':'Q34','Q05':'Q44','Q06':'Q45',
                'Q07':'Q46','Q08':'Q47','Q09':'Q48','Q10':'Q02','Q11':'Q03','Q12':'Q04',
                'Q13':'Q05','Q14':'Q06','Q15':'Q07','Q16':'Q08','Q17':'Q09','Q18':'Q10',
                'Q19':'Q11','Q20':'Q13','Q21':'Q14','Q22':'Q15','Q23':'Q16','Q24':'Q17',
                'Q25':'Q18','Q26':'Q19','Q27':'Q20','Q28':'Q21','Q29':'Q22','Q30':'Q24',
                'Q31':'Q25','Q32':'Q26','Q33':'Q27','Q34':'Q28','Q35':'Q29','Q36':'Q30',
                'Q37':'Q31','Q38':'Q32','Q39':'Q33','Q40':'Q35','Q41':'Q36','Q42':'Q37',
                'Q43':'Q38','Q44':'Q39','Q45':'Q40','Q46':'Q41','Q47':'Q42','Q48':'Q43'
            }
            REVERSO_FORM_SE = {can: form for form, can in MAPEAMENTO_QUESTOES_SE.items()}

            for af in afirmacoes_saude_emocional:
                codigo = af['chave']
                categoria = af.get('dimensao_saude_emocional', 'Suporte Emocional')
                if categoria not in categoria_valores:
                    categoria = 'Suporte Emocional'

                if af['tipo'] == 'Arquétipo':
                    arquétipo = af['dimensao']
                    # ✅ LÓGICA CORRETA: busca individualmente na tabela
                    percentual_medio, tendencia_info, _ = calcular_tendencia_arquetipos_por_questao(
                        df_arq_filtrado[df_arq_filtrado['tipo'] == 'Avaliação Equipe'], matriz_arq, codigo, arquétipo
                    )
                    if percentual_medio is not None and tendencia_info:
                        if 'DESFAVORÁVEL' in tendencia_info:
                            valor = max(0, 100 - percentual_medio)
                        else:
                            valor = percentual_medio
                        categoria_valores[categoria].append(valor)

                else:  # Microambiente
                    codigo_canonico = af['chave']
                    # ✅ LÓGICA CORRETA: busca individualmente na tabela
                    real_pct, ideal_pct, gap = calcular_real_ideal_gap_por_questao(
                        df_micro_filtrado, matriz_micro, codigo_canonico
                    )
                    if real_pct is not None and gap is not None:
                        valor = max(0.0, 100.0 - gap)
                        categoria_valores[categoria].append(valor)

            categoria_medias = {}
            for categoria, valores in categoria_valores.items():
                categoria_medias[categoria] = np.mean(valores) if valores else 0

            cores_compliance = []
            for valor in categoria_medias.values():
                if valor >= 80: cores_compliance.append('rgba(0, 128, 0, 0.9)')
                elif valor >= 75: cores_compliance.append('rgba(46, 204, 113, 0.9)')
                elif valor >= 70: cores_compliance.append('rgba(144, 238, 144, 0.9)')
                elif valor >= 60: cores_compliance.append('rgba(255, 215, 0, 0.9)')
                else: cores_compliance.append('rgba(255, 99, 71, 0.9)')

            fig_compliance = go.Figure()
            fig_compliance.add_trace(go.Bar(
                y=list(categoria_medias.keys()), x=list(categoria_medias.values()),
                orientation='h', marker_color=cores_compliance,
                text=[f"{v:.1f}%" for v in categoria_medias.values()], textposition='auto',
                hovertemplate='<b>%{y}</b><br>Score Médio: %{x:.1f}%<br>Questões: %{customdata}<extra></extra>',
                customdata=[len(categoria_valores[k]) for k in categoria_medias.keys()]
            ))
            fig_compliance.update_layout(title="📊 Score Médio por Categoria NR-1",
                xaxis_title="Score Médio (%)", yaxis_title="Categorias de Compliance",
                xaxis=dict(range=[0, 100]), height=400, showlegend=False)
            st.plotly_chart(fig_compliance, use_container_width=True)
            st.divider()

            # ==================== IMPORTAR RECLASSIFICAÇÕES ====================
            st.subheader("📤 Importar Reclassificações de Afirmações")
            uploaded_file = st.file_uploader("Escolha o arquivo CSV com as reclassificações", type=['csv'], key="upload_reclassificacoes")
            reclassificacoes = {}
            novas_afirmacoes = []
            if uploaded_file is not None:
                try:
                    df_reclass = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                    df_reclass.columns = df_reclass.columns.str.strip()
                    colunas_necessarias = ['COD', 'STATUS', 'DE', 'PARA', 'Tipo', 'Código']
                    colunas_encontradas = [col for col in colunas_necessarias if col in df_reclass.columns]
                    if len(colunas_encontradas) >= 4:
                        st.success(f"✅ Arquivo carregado! {len(df_reclass)} linhas processadas.")
                        for _, row in df_reclass.iterrows():
                            cod = str(row.get('COD', '')).strip()
                            status = str(row.get('STATUS', '')).strip()
                            de = str(row.get('DE', '')).strip() if pd.notna(row.get('DE')) else ''
                            para = str(row.get('PARA', '')).strip() if pd.notna(row.get('PARA')) else ''
                            tipo = str(row.get('Tipo', '')).strip()
                            codigo_original = str(row.get('Código', '')).strip()
                            coluna_afirmacao = next((col for col in df_reclass.columns if col not in colunas_necessarias and pd.notna(row.get(col))), None)
                            afirmacao_texto = str(row.get(coluna_afirmacao, '')).strip() if coluna_afirmacao else ''
                            if para and para.upper() != 'NAN' and para != '':
                                if cod.startswith('a') or cod.startswith('m'):
                                    novas_afirmacoes.append({'cod': cod, 'codigo_original': codigo_original or cod, 'tipo': tipo, 'afirmacao': afirmacao_texto, 'dimensao': para, 'status': status})
                                else:
                                    codigo_chave = str(codigo_original).strip() if codigo_original and str(codigo_original).strip() != '' else str(cod).strip()
                                    reclassificacoes[codigo_chave] = {'de': de, 'para': para, 'tipo': tipo, 'cod': cod}
                                    if cod != codigo_chave and codigo_original:
                                        reclassificacoes[str(cod).strip()] = {'de': de, 'para': para, 'tipo': tipo, 'cod': cod}
                        st.info(f"📊 Processadas: {len(reclassificacoes)} reclassificações e {len(novas_afirmacoes)} novas afirmações")
                    else:
                        st.error(f"❌ Colunas necessárias não encontradas. Encontradas: {', '.join(df_reclass.columns.tolist())}")
                except Exception as e:
                    st.error(f"❌ Erro ao processar arquivo: {str(e)}")

            st.info(f"✅ **Afirmações do CSV incluídas!** Total: {len(afirmacoes_saude_emocional)} afirmações")
            st.divider()

            # ==================== MAPEAMENTO POR DIMENSÃO ====================
            st.subheader("📋 Mapeamento Completo: Afirmações por Dimensão de Saúde Emocional")
            mapeamento_por_dimensao = {
                'Prevenção de Estresse': {'arquetipos': [], 'microambiente': []},
                'Ambiente Psicológico Seguro': {'arquetipos': [], 'microambiente': []},
                'Suporte Emocional': {'arquetipos': [], 'microambiente': []},
                'Comunicação Positiva': {'arquetipos': [], 'microambiente': []},
                'Equilíbrio Vida-Trabalho': {'arquetipos': [], 'microambiente': []}
            }
            dimensoes_normalizadas = {
                'Prevenção de Estresse': 'Prevenção de Estresse', 'Prevencao de Estresse': 'Prevenção de Estresse',
                'Ambiente Psicológico Seguro': 'Ambiente Psicológico Seguro', 'Ambiente Psicologico Seguro': 'Ambiente Psicológico Seguro',
                'Suporte Emocional': 'Suporte Emocional', 'Comunicação Positiva': 'Comunicação Positiva',
                'Comunicacao Positiva': 'Comunicação Positiva', 'Equilíbrio Vida-Trabalho': 'Equilíbrio Vida-Trabalho',
                'Equilibrio Vida-Trabalho': 'Equilíbrio Vida-Trabalho', 'Equilíbrio Vida- Trabalho': 'Equilíbrio Vida-Trabalho',
                'Equilibrio Vida- Trabalho': 'Equilíbrio Vida-Trabalho'
            }
            classificacoes = carregar_classificacoes_saude_emocional()
            codigos_processados_map = set()
            for af in afirmacoes_saude_emocional:
                codigo_af = str(af['chave']).strip()
                tipo_af = af.get('tipo', '').strip()
                codigo_key = f"arq_{codigo_af}" if 'Arquétipo' in tipo_af or 'Arquetipo' in tipo_af else f"micro_{codigo_af}" if 'Microambiente' in tipo_af or 'Micro' in tipo_af else codigo_af
                if codigo_key in codigos_processados_map:
                    continue
                codigos_processados_map.add(codigo_key)
                categoria_atribuida = af.get('dimensao_saude_emocional') or classificacoes.get(codigo_key) or classificacoes.get(codigo_af)
                if not categoria_atribuida and reclassificacoes:
                    r = reclassificacoes.get(codigo_key) or reclassificacoes.get(codigo_af)
                    if r: categoria_atribuida = r.get('para')
                if not categoria_atribuida:
                    categoria_atribuida = 'Suporte Emocional'
                categoria_atribuida = dimensoes_normalizadas.get(categoria_atribuida, categoria_atribuida)
                if categoria_atribuida not in mapeamento_por_dimensao:
                    categoria_atribuida = 'Suporte Emocional'
                if af['tipo'] == 'Arquétipo':
                    mapeamento_por_dimensao[categoria_atribuida]['arquetipos'].append({'codigo': af['chave'], 'afirmacao': af['afirmacao'], 'dimensao': af['dimensao']})
                else:
                    mapeamento_por_dimensao[categoria_atribuida]['microambiente'].append({'codigo': af['chave'], 'afirmacao': af['afirmacao'], 'dimensao': af['dimensao'], 'subdimensao': af['subdimensao']})

            dados_exportacao = []
            total_mapeamento = sum(len(d['arquetipos']) + len(d['microambiente']) for d in mapeamento_por_dimensao.values())
            for dimensao, dados in mapeamento_por_dimensao.items():
                total_arq = len(dados['arquetipos'])
                total_micro = len(dados['microambiente'])
                total_geral = total_arq + total_micro
                if total_geral > 0:
                    with st.expander(f"📁 **{dimensao}** ({total_geral} afirmações: {total_arq} arquétipos + {total_micro} microambiente)", expanded=False):
                        if dados['arquetipos']:
                            st.markdown(f"### 🧠 Arquétipos ({total_arq} afirmações)")
                            df_arq = pd.DataFrame(dados['arquetipos'])
                            df_arq.columns = ['Código', 'Afirmação', 'Arquétipo']
                            st.dataframe(df_arq, use_container_width=True, hide_index=True)
                            for _, row in df_arq.iterrows():
                                dados_exportacao.append({'Dimensão Saúde Emocional': dimensao, 'Tipo': 'Arquétipo', 'Código': row['Código'], 'Afirmação': row['Afirmação'], 'Arquétipo/Dimensão': row['Arquétipo'], 'Subdimensão': 'N/A'})
                        if dados['microambiente']:
                            st.markdown(f"### 🏢 Microambiente ({total_micro} afirmações)")
                            df_micro = pd.DataFrame(dados['microambiente'])
                            df_micro.columns = ['Código', 'Afirmação', 'Dimensão', 'Subdimensão']
                            st.dataframe(df_micro, use_container_width=True, hide_index=True)
                            for _, row in df_micro.iterrows():
                                dados_exportacao.append({'Dimensão Saúde Emocional': dimensao, 'Tipo': 'Microambiente', 'Código': row['Código'], 'Afirmação': row['Afirmação'], 'Arquétipo/Dimensão': row['Dimensão'], 'Subdimensão': row['Subdimensão']})
                else:
                    with st.expander(f"📁 **{dimensao}** (0 afirmações)", expanded=False):
                        st.info("ℹ️ Nenhuma afirmação classificada nesta dimensão ainda.")

            if dados_exportacao:
                df_export = pd.DataFrame(dados_exportacao)
                st.download_button(label="📥 Download CSV - Mapeamento Completo por Dimensão", data=df_export.to_csv(index=False, encoding='utf-8-sig'), file_name="mapeamento_saude_emocional_por_dimensao.csv", mime="text/csv", key="download_mapeamento")
            st.markdown(f"**📊 Total de afirmações no mapeamento: {total_mapeamento}**")
            st.divider()

            # ==================== AFIRMAÇÕES NÃO SE ====================
            st.subheader("📝 Afirmações que NÃO estão em Saúde Emocional")
            codigos_se_arq = set(str(af['chave']).strip() for af in afirmacoes_saude_emocional if af['tipo'] == 'Arquétipo')
            codigos_se_micro = set(str(af['chave']).strip() for af in afirmacoes_saude_emocional if af['tipo'] == 'Microambiente')
            todas_afirmacoes_arq = matriz_arq[['COD_AFIRMACAO', 'AFIRMACAO', 'ARQUETIPO']].drop_duplicates(subset=['COD_AFIRMACAO'])
            todas_afirmacoes_micro = matriz_micro[['COD', 'AFIRMACAO', 'DIMENSAO', 'SUBDIMENSAO']].drop_duplicates(subset=['COD'])
            afirmacoes_nao_se_arq = [{'codigo_original': str(row['COD_AFIRMACAO']).strip(), 'afirmacao': row['AFIRMACAO'], 'arquetipo': row['ARQUETIPO']} for _, row in todas_afirmacoes_arq.iterrows() if str(row['COD_AFIRMACAO']).strip() not in codigos_se_arq]
            afirmacoes_nao_se_micro = [{'codigo_original': str(row['COD']).strip(), 'afirmacao': row['AFIRMACAO'], 'dimensao': row['DIMENSAO'], 'subdimensao': row['SUBDIMENSAO']} for _, row in todas_afirmacoes_micro.iterrows() if str(row['COD']).strip() not in codigos_se_micro]

            total_arq_unicos = len(todas_afirmacoes_arq)
            total_micro_unicos = len(todas_afirmacoes_micro)
            total_geral_esperado = total_arq_unicos + total_micro_unicos
            total_se = len(codigos_se_arq) + len(codigos_se_micro)
            total_nao_se = len(afirmacoes_nao_se_arq) + len(afirmacoes_nao_se_micro)

            st.markdown(f"**📊 Verificação:** Total esperado: {total_geral_esperado} | SE: {total_se} | Não-SE: {total_nao_se} | Soma: {total_se + total_nao_se}")
            col1, col2 = st.columns(2)
            with col1: st.metric("🧠 Arquétipos não-SE", len(afirmacoes_nao_se_arq))
            with col2: st.metric("🏢 Microambiente não-SE", len(afirmacoes_nao_se_micro))

            afirmacoes_com_codigo = []
            for idx, af in enumerate(afirmacoes_nao_se_arq, 1):
                afirmacoes_com_codigo.append({'codigo': f"a{idx:02d}", 'codigo_original': af['codigo_original'], 'tipo': 'Arquétipo', 'afirmacao': af['afirmacao'], 'dimensao': af['arquetipo'], 'subdimensao': 'N/A'})
            for idx, af in enumerate(afirmacoes_nao_se_micro, 1):
                afirmacoes_com_codigo.append({'codigo': f"m{idx:02d}", 'codigo_original': af['codigo_original'], 'tipo': 'Microambiente', 'afirmacao': af['afirmacao'], 'dimensao': af['dimensao'], 'subdimensao': af['subdimensao']})

            if afirmacoes_com_codigo:
                df_nao_se = pd.DataFrame(afirmacoes_com_codigo)
                df_nao_se.columns = ['Código', 'Código Original', 'Tipo', 'Afirmação', 'Dimensão/Arquétipo', 'Subdimensão']
                st.dataframe(df_nao_se, use_container_width=True, hide_index=True)
                st.download_button(label="📥 Download CSV - Afirmações NÃO em Saúde Emocional", data=df_nao_se.to_csv(index=False, encoding='utf-8-sig'), file_name="afirmacoes_nao_saude_emocional.csv", mime="text/csv", key="download_nao_se")
            else:
                st.success("✅ Todas as afirmações já estão classificadas em Saúde Emocional!")
            st.divider()

            # ==================== DRILL-DOWN POR CATEGORIA ====================
            st.subheader("🔍 Drill-Down por Categoria de Compliance")
            col1, col2 = st.columns([2, 1])
            with col1:
                categoria_selecionada = st.selectbox("Selecione uma categoria:",
                    ["Todas", "Prevenção de Estresse", "Ambiente Psicológico Seguro", "Suporte Emocional", "Comunicação Positiva", "Equilíbrio Vida-Trabalho"],
                    index=None, placeholder="Escolha uma categoria...", key="categoria_compliance_select")
            with col2:
                st.markdown("**💡 Dica:** Selecione uma categoria para ver as questões detalhadas!")

            if categoria_selecionada and categoria_selecionada != "Todas":
                afirmacoes_saude_emocional_filtradas = [af for af in afirmacoes_saude_emocional if af.get('dimensao_saude_emocional') == categoria_selecionada]
                if afirmacoes_saude_emocional_filtradas:
                    st.success(f"✅ **Filtro aplicado:** {len(afirmacoes_saude_emocional_filtradas)} questões da categoria '{categoria_selecionada}'")
                else:
                    afirmacoes_saude_emocional_filtradas = afirmacoes_saude_emocional
                    st.warning(f"⚠️ Nenhuma questão encontrada para '{categoria_selecionada}'. Mostrando todas.")
            else:
                afirmacoes_saude_emocional_filtradas = afirmacoes_saude_emocional

            afirmacoes_arq = [a for a in afirmacoes_saude_emocional_filtradas if a['tipo'] == 'Arquétipo']
            afirmacoes_micro = [a for a in afirmacoes_saude_emocional_filtradas if a['tipo'] == 'Microambiente']

            if categoria_selecionada and categoria_selecionada != "Todas":
                st.markdown(f"### 📋 Questões da Categoria: **{categoria_selecionada}**")
                afirmacoes_categoria = [af for af in afirmacoes_saude_emocional_filtradas if af.get('dimensao_saude_emocional') == categoria_selecionada]
                if afirmacoes_categoria:
                    st.success(f"✅ Encontradas {len(afirmacoes_categoria)} questões na categoria {categoria_selecionada}")
                    for i, af in enumerate(afirmacoes_categoria, 1):
                        with st.expander(f"Questão {i}: {af['afirmacao'][:100]}..."):
                            st.markdown(f"**Tipo:** {af['tipo']}")
                            st.markdown(f"**Dimensão:** {af['dimensao']}")
                            if af['subdimensao'] != 'N/A':
                                st.markdown(f"**Subdimensão:** {af['subdimensao']}")
                            st.markdown(f"**Afirmação completa:** {af['afirmacao']}")
                            st.divider()
                            st.markdown("**📊 Dados da Questão:**")
                            if af['tipo'] == 'Arquétipo':
                                codigo = af['chave']
                                arquétipo = af['dimensao']
                                # ✅ LÓGICA CORRETA
                                percentual_medio, tendencia_info, n_resp = calcular_tendencia_arquetipos_por_questao(
                                    df_arq_filtrado[df_arq_filtrado['tipo'] == 'Avaliação Equipe'], matriz_arq, codigo, arquétipo)
                                if percentual_medio is not None:
                                    # Média de estrelas para exibição
                                    estrelas_lista = [int(resp['respostas'][codigo]) for _, resp in df_arq_filtrado.iterrows() if 'respostas' in resp and codigo in resp['respostas']]
                                    media_estrelas = np.mean(estrelas_lista) if estrelas_lista else 0
                                    col1, col2, col3 = st.columns(3)
                                    with col1: st.metric("⭐ Média Estrelas", f"{media_estrelas:.1f}")
                                    with col2: st.metric("% Tendência", f"{percentual_medio:.1f}%")
                                    with col3: st.metric("Nº Respostas", n_resp)
                                    st.info(f"**Tendência:** {tendencia_info}")
                                else:
                                    st.warning("⚠️ Nenhuma resposta encontrada para esta questão")
                            else:
                                codigo_canonico = af['chave']
                                # ✅ LÓGICA CORRETA
                                real_pct, ideal_pct, gap = calcular_real_ideal_gap_por_questao(
                                    df_micro_filtrado, matriz_micro, codigo_canonico)
                                if real_pct is not None:
                                    col1, col2, col3, col4 = st.columns(4)
                                    with col1: st.metric("⭐ Real (%)", f"{real_pct:.1f}%")
                                    with col2: st.metric("⭐ Ideal (%)", f"{ideal_pct:.1f}%")
                                    with col3: st.metric("Gap", f"{gap:.1f}%")
                                    with col4: st.metric("Nº Respostas", "—")
                                    if gap > 40: st.error(f"**Gap Alto:** {gap:.1f}%")
                                    elif gap > 20: st.warning(f"🟠 **Gap Moderado:** {gap:.1f}%")
                                    else: st.success(f"✅ **Gap Mínimo:** {gap:.1f}%")
                                else:
                                    st.warning("⚠️ Dados insuficientes para calcular gap")
                else:
                    st.warning(f"⚠️ Nenhuma questão encontrada na categoria {categoria_selecionada}.")

            # ==================== GRÁFICO MICROAMBIENTE SE ====================
            st.subheader("🏢 Microambiente: Como é vs Como deveria ser vs Gap")
            afirmacoes_micro = [a for a in afirmacoes_saude_emocional_filtradas if a['tipo'] == 'Microambiente']
            if afirmacoes_micro:
                def _wrap_affirmacao(txt, max_chars=58, max_lines=3):
                    palavras = str(txt).split()
                    linhas, atual = [], ""
                    for p in palavras:
                        if len(atual) + len(p) + 1 <= max_chars:
                            atual = (atual + " " + p).strip()
                        else:
                            linhas.append(atual)
                            atual = p
                            if len(linhas) == max_lines - 1:
                                break
                    if atual:
                        linhas.append(atual)
                    return "<br>".join(linhas)

                questoes_micro = []
                medias_real_se = []
                medias_ideal_se = []
                gaps_se = []

                for af in afirmacoes_micro:
                    # ✅ LÓGICA CORRETA: busca individualmente na tabela
                    real_pct, ideal_pct, gap = calcular_real_ideal_gap_por_questao(
                        df_micro_filtrado, matriz_micro, af['chave'])
                    if real_pct is None:
                        continue
                    questoes_micro.append(_wrap_affirmacao(af['afirmacao']))
                    medias_real_se.append(real_pct)
                    medias_ideal_se.append(ideal_pct)
                    gaps_se.append(gap)

                if questoes_micro:
                    fig_micro = go.Figure()
                    fig_micro.add_trace(go.Bar(name='Como é (Real)', x=questoes_micro, y=medias_real_se, marker_color='rgba(255, 165, 0, 0.7)', text=[f"{v:.1f}%" for v in medias_real_se], textposition='auto'))
                    fig_micro.add_trace(go.Bar(name='Como deveria ser (Ideal)', x=questoes_micro, y=medias_ideal_se, marker_color='rgba(0, 128, 0, 0.7)', text=[f"{v:.1f}%" for v in medias_ideal_se], textposition='auto'))
                    fig_micro.add_trace(go.Bar(name='Gap (Ideal - Real)', x=questoes_micro, y=gaps_se, marker_color='rgba(138, 43, 226, 0.7)', text=[f"{v:.1f}" for v in gaps_se], textposition='auto'))
                    fig_micro.update_layout(title="🏢 Questões de Microambiente - Real vs Ideal vs Gap", xaxis_title="Questões", yaxis_title="Percentual (%) / Gap", barmode='group', height=600, xaxis_tickangle=-45)
                    st.plotly_chart(fig_micro, use_container_width=True)

            st.divider()

            # ==================== SCORE FINAL ====================
            st.subheader("🌡️ Score Final de Saúde Emocional")
            if categoria_selecionada and categoria_selecionada != "Todas" and categoria_selecionada in categoria_medias:
                score_final = categoria_medias[categoria_selecionada]
            else:
                valores_categorias = [v for v in categoria_medias.values() if v > 0]
                score_final = np.mean(valores_categorias) if valores_categorias else 0

            # Score Arquétipos (referência) - ✅ LÓGICA CORRETA
            score_arquetipos = 0
            if afirmacoes_arq:
                tendencias_gerais = []
                for af in afirmacoes_arq:
                    codigo = af['chave']
                    arquétipo = af['dimensao']
                    percentual_medio, tendencia_info, _ = calcular_tendencia_arquetipos_por_questao(
                        df_arq_filtrado[df_arq_filtrado['tipo'] == 'Avaliação Equipe'], matriz_arq, codigo, arquétipo)
                    if percentual_medio is not None and tendencia_info:
                        if 'DESFAVORÁVEL' in tendencia_info:
                            score = max(0, 100 - percentual_medio)
                        else:
                            score = percentual_medio
                        tendencias_gerais.append(score)
                if tendencias_gerais:
                    score_arquetipos = np.mean(tendencias_gerais)

            # Score Microambiente (referência) - ✅ LÓGICA CORRETA
            score_microambiente = 0
            if afirmacoes_micro and gaps_se:
                gap_medio = np.mean(gaps_se)
                score_microambiente = max(0, 100 - gap_medio)

            if score_final >= 95: interpretacao, cor_score = "EXCELENTE - acima de 95%", "green"
            elif score_final >= 85: interpretacao, cor_score = "ÓTIMO - entre 85% e 94,99%", "darkgreen"
            elif score_final >= 75: interpretacao, cor_score = "BOM - entre 75% e 84,99%", "orange"
            elif score_final >= 65: interpretacao, cor_score = "REGULAR - entre 65% e 74,99%", "darkorange"
            else: interpretacao, cor_score = "NÃO ADEQUADO - abaixo de 65%", "red"

            col1, col2 = st.columns([1, 2])
            with col1:
                st.markdown(f"""<div style="text-align: center; padding: 20px; border: 3px solid {cor_score}; border-radius: 10px;">
                    <h2 style="color: {cor_score}; margin: 0;">{score_final:.1f}%</h2>
                    <p style="margin: 5px 0; font-size: 18px;">Score Final</p>
                    <p style="margin: 5px 0; font-size: 14px;">Saúde Emocional</p></div>""", unsafe_allow_html=True)
            with col2:
                st.markdown(f"""<div style="padding: 20px; background-color: rgba(0,0,0,0.05); border-radius: 10px;">
                    <h3>📊 Como o Score é Calculado</h3>
                    <p><strong>{interpretacao}</strong></p>
                    <p><strong>🧠 Score Arquétipos:</strong> {score_arquetipos:.1f}% (referência)</p>
                    <p><strong>🏢 Score Microambiente:</strong> {score_microambiente:.1f}% (referência)</p>
                    <p><strong>💚 Score Final:</strong> {'Score da categoria filtrada' if categoria_selecionada and categoria_selecionada != 'Todas' else 'Média das 5 categorias do gráfico de Compliance'}</p>
                    <p><strong>🎯 Interpretação:</strong> Quanto maior o score, melhor a saúde emocional proporcionada pelo líder</p>
                    <hr><h4>Legenda dos Níveis</h4>
                    <table style="width:100%; font-size: 13px; border-collapse: collapse;">
                    <tr><th style="text-align:left; padding: 4px; border-bottom: 1px solid #ccc;">Faixa</th><th style="text-align:left; padding: 4px; border-bottom: 1px solid #ccc;">Nível</th><th style="text-align:left; padding: 4px; border-bottom: 1px solid #ccc;">Descrição</th></tr>
                    <tr><td style="padding: 4px;">≥ 95%</td><td style="padding: 4px;">Excelente</td><td style="padding: 4px;">Ambiente de referência, com padrão consistente de excelência</td></tr>
                    <tr><td style="padding: 4px;">85% a 94,99%</td><td style="padding: 4px;">Ótimo</td><td style="padding: 4px;">Ambiente saudável e forte, com poucas oportunidades de ajuste</td></tr>
                    <tr><td style="padding: 4px;">75% a 84,99%</td><td style="padding: 4px;">Bom</td><td style="padding: 4px;">Ambiente adequado, com pontos relevantes a desenvolver</td></tr>
                    <tr><td style="padding: 4px;">65% a 74,99%</td><td style="padding: 4px;">Regular</td><td style="padding: 4px;">Ambiente em atenção, requer melhorias acompanhadas</td></tr>
                    <tr><td style="padding: 4px;">&lt; 65%</td><td style="padding: 4px;">Não Adequado</td><td style="padding: 4px;">Ambiente requer intervenção e plano de ação (PDI)</td></tr>
                    </table></div>""", unsafe_allow_html=True)

            st.divider()

            # ==================== TABELAS DETALHADAS ====================
            st.subheader("📋 Análise Detalhada por Tipo")

            # TABELA ARQUÉTIPOS
            if afirmacoes_arq:
                st.markdown("** Questões de Arquétipos - Saúde Emocional**")
                df_arq_detalhado = pd.DataFrame(afirmacoes_arq)
                tendencias_arq = []
                percentuais_arq = []
                for _, row in df_arq_detalhado.iterrows():
                    codigo = row['chave']
                    arquétipo = row['dimensao']
                    # ✅ LÓGICA CORRETA: busca individualmente na tabela
                    percentual_medio, tendencia_info, _ = calcular_tendencia_arquetipos_por_questao(
                        df_arq_filtrado[df_arq_filtrado['tipo'] == 'Avaliação Equipe'], matriz_arq, codigo, arquétipo)
                    if percentual_medio is not None:
                        tendencias_arq.append(tendencia_info)
                        percentuais_arq.append(f"{percentual_medio:.1f}%")
                    else:
                        tendencias_arq.append("N/A")
                        percentuais_arq.append("N/A")
                df_arq_detalhado['% Tendência'] = percentuais_arq
                df_arq_detalhado['Tendência'] = tendencias_arq
                def color_tendencia_arq(val):
                    val_str = str(val).strip()
                    if val_str == 'MUITO FAVORÁVEL': return 'background-color: rgba(173, 216, 230, 0.8)'
                    elif val_str == 'FAVORÁVEL': return 'background-color: rgba(0, 128, 0, 0.8)'
                    elif val_str == 'POUCO FAVORÁVEL': return 'background-color: rgba(144, 238, 144, 0.8)'
                    elif val_str == 'POUCO DESFAVORÁVEL': return 'background-color: rgba(255, 255, 0, 0.7)'
                    elif val_str == 'DESFAVORÁVEL': return 'background-color: rgba(255, 165, 0, 0.7)'
                    elif val_str == 'MUITO DESFAVORÁVEL': return 'background-color: rgba(255, 0, 0, 0.8)'
                    else: return 'background-color: rgba(200, 200, 200, 0.3)'
                df_arq_exibir = df_arq_detalhado[['chave', 'afirmacao', 'dimensao', '% Tendência', 'Tendência']].copy()
                df_arq_exibir.columns = ['Questão', 'Afirmação', 'Arquétipo', '% Tendência', 'Tendência']
                st.dataframe(df_arq_exibir.style.map(color_tendencia_arq, subset=['Tendência']), use_container_width=True)
                st.download_button(label="📥 Download CSV - Arquétipos SE", data=df_arq_exibir.to_csv(index=False), file_name="saude_emocional_arquetipos.csv", mime="text/csv")

            st.divider()

            # TABELA MICROAMBIENTE
            afirmacoes_micro_final = [a for a in afirmacoes_saude_emocional_filtradas if a['tipo'] == 'Microambiente']
            if afirmacoes_micro_final:
                st.markdown("**🏢 Questões de Microambiente - Saúde Emocional**")
                df_micro_detalhado = pd.DataFrame(afirmacoes_micro_final)
                reais_micro = []
                ideais_micro = []
                gaps_micro = []
                for _, row in df_micro_detalhado.iterrows():
                    # ✅ LÓGICA CORRETA: busca individualmente na tabela
                    real_pct, ideal_pct, gap = calcular_real_ideal_gap_por_questao(
                        df_micro_filtrado, matriz_micro, row['chave'])
                    if real_pct is not None:
                        reais_micro.append(f"{real_pct:.1f}%")
                        ideais_micro.append(f"{ideal_pct:.1f}%")
                        gaps_micro.append(f"{gap:.1f}")
                    else:
                        reais_micro.append("N/A")
                        ideais_micro.append("N/A")
                        gaps_micro.append("N/A")
                df_micro_detalhado['Real'] = reais_micro
                df_micro_detalhado['Ideal'] = ideais_micro
                df_micro_detalhado['Gap'] = gaps_micro
                def color_gap_micro(val):
                    try:
                        gap_val = float(val)
                        if gap_val > 80: return 'background-color: rgba(255, 0, 0, 0.8)'
                        elif gap_val > 60: return 'background-color: rgba(255, 100, 0, 0.8)'
                        elif gap_val > 40: return 'background-color: rgba(255, 165, 0, 0.7)'
                        elif gap_val > 20: return 'background-color: rgba(255, 255, 0, 0.6)'
                        elif gap_val > 0: return 'background-color: rgba(144, 238, 144, 0.6)'
                        else: return 'background-color: rgba(0, 255, 0, 0.5)'
                    except: return 'background-color: transparent'
                df_micro_exibir = df_micro_detalhado[['chave', 'afirmacao', 'dimensao', 'subdimensao', 'Real', 'Ideal', 'Gap']].copy()
                df_micro_exibir.columns = ['Questão', 'Afirmação', 'Dimensão', 'Subdimensão', 'Real (%)', 'Ideal (%)', 'Gap']
                st.dataframe(df_micro_exibir.style.map(color_gap_micro, subset=['Gap']), use_container_width=True)
                st.download_button(label="📥 Download CSV - Microambiente SE", data=df_micro_exibir.to_csv(index=False), file_name="saude_emocional_microambiente.csv", mime="text/csv")

        # ==================== TAB PARECER CORPORATIVO ====================
        with tab4:
            st.header("🏛️ Parecer Corporativo LeaderTrack")
            st.warning(
                "Saúde emocional é exibida aqui somente em nível organizacional/agregado "
                "para RH, CEO, diretoria ou gestão autorizada. Não use este bloco como "
                "devolutiva individual para líder."
            )

            col_cfg1, col_cfg2, col_cfg3 = st.columns(3)
            with col_cfg1:
                amostra_minima_org = st.number_input(
                    "Amostra mínima",
                    min_value=3,
                    max_value=30,
                    value=5,
                    step=1,
                    help="Recortes abaixo deste número são omitidos para proteger pessoas e evitar conclusão frágil.",
                )
            with col_cfg2:
                diferenca_relevante_org = st.number_input(
                    "Diferença relevante",
                    min_value=3.0,
                    max_value=20.0,
                    value=5.0,
                    step=0.5,
                    help="Diferença mínima em pontos para virar achado.",
                )
            with col_cfg3:
                gerar_com_ia_org = st.checkbox("Gerar texto com IA", value=True)

            if st.button("Gerar parecer corporativo", type="primary", key="btn_parecer_corporativo"):
                rules_org = OrganizationalRules(
                    min_sample=int(amostra_minima_org),
                    relevant_delta_points=float(diferenca_relevante_org),
                )
                with st.spinner("Montando pacote analítico organizacional..."):
                    pacote_org = gerar_pacote_organizacional(
                        matriz_arq=matriz_arq,
                        matriz_micro=matriz_micro,
                        df_arquetipos=df_arquetipos,
                        df_microambiente=df_microambiente,
                        filtros=filtros,
                        contexto=ctx,
                        rules=rules_org,
                    )
                    st.session_state["parecer_corporativo_pacote"] = pacote_org

                amostra_org = pacote_org.get("amostra") or {}
                respondentes_org = int(amostra_org.get("respondentes") or 0)
                if respondentes_org < int(amostra_minima_org):
                    st.error(
                        "Amostra insuficiente para gerar parecer corporativo com segurança. "
                        f"Foram encontrados {respondentes_org} respondentes no recorte atual."
                    )
                    st.stop()

                with st.spinner("Enviando pacote ao Leadertrackbot..."):
                    pacote_para_bot = (
                        pacote_organizacional_para_ia(pacote_org)
                        if gerar_com_ia_org
                        else pacote_org
                    )
                    resposta_org, erro_org = chamar_parecer_organizacional(
                        pacote_para_bot,
                        gerar_com_ia=gerar_com_ia_org,
                    )

                if erro_org:
                    st.error(erro_org)
                else:
                    st.session_state["parecer_corporativo_resposta"] = resposta_org
                    st.success("Parecer corporativo gerado.")
                    if gerar_com_ia_org:
                        st.caption(
                            "IA recebeu um pacote analítico resumido e priorizado; "
                            "o pacote completo segue disponível abaixo para auditoria."
                        )

            pacote_salvo = st.session_state.get("parecer_corporativo_pacote")
            if isinstance(pacote_salvo, dict):
                amostra_salva = pacote_salvo.get("amostra") or {}
                saude_salva = pacote_salvo.get("saude_emocional") or {}
                achados_salvos = pacote_salvo.get("achados_relevantes") or []

                col_m1, col_m2, col_m3 = st.columns(3)
                with col_m1:
                    st.metric("Respondentes", amostra_salva.get("respondentes", 0))
                with col_m2:
                    st.metric("Líderes", amostra_salva.get("lideres", 0))
                with col_m3:
                    score_se = saude_salva.get("score_final")
                    st.metric("Saúde Emocional", "—" if score_se is None else f"{float(score_se):.1f}%")

                exibir_entrega_executiva_organizacional(
                    pacote_salvo,
                    matriz_arq,
                    matriz_micro,
                    df_arquetipos,
                    df_microambiente,
                    filtros,
                )

                exibir_visao_visual_parecer_organizacional(pacote_salvo)

                if achados_salvos:
                    st.subheader("Achados detectados pelo motor")
                    df_achados_org = pd.DataFrame(achados_salvos)
                    colunas_achados = [
                        col for col in [
                            "tipo",
                            "campo",
                            "rotulo",
                            "valor",
                            "n",
                            "dimensao",
                            "score",
                            "media_contexto",
                            "delta",
                            "real",
                            "ideal",
                            "gap",
                            "severidade",
                            "mensagem_base",
                        ] if col in df_achados_org.columns
                    ]
                    st.dataframe(df_achados_org[colunas_achados], use_container_width=True, hide_index=True)
                else:
                    st.info("Nenhum achado relevante detectado com os critérios atuais.")

                st.download_button(
                    "Baixar pacote analítico JSON",
                    data=json.dumps(pacote_salvo, ensure_ascii=False, indent=2, default=str),
                    file_name="pacote_analitico_parecer_corporativo_leadertrack.json",
                    mime="application/json",
                    key="download_pacote_parecer_corporativo",
                )

            resposta_salva = st.session_state.get("parecer_corporativo_resposta")
            if isinstance(resposta_salva, dict):
                enviar_parecer_organizacional_para_wordpress(resposta_salva, pacote_salvo)
                st.divider()
                st.subheader("Parecer gerado pelo Leadertrackbot")
                exibir_resposta_parecer_organizacional(resposta_salva)

        if not afirmacoes_saude_emocional:
            st.warning("⚠️ Nenhuma afirmação relacionada à saúde emocional foi identificada.")
