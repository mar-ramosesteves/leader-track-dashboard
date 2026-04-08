import streamlit as st
import streamlit.components.v1 as components
from supabase import create_client
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import json

st.set_page_config(page_title="📊 Visão Executiva", page_icon="📊", layout="wide")

SUPABASE_URL = "https://xmsjjknpnowsswwrbvpc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtc2pqa25wbm93c3N3d3JidnBjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MDg0NDUsImV4cCI6MjA2ODA4NDQ0NX0.OexXJX7lK_DefGb72VDWGLDcUXamoQIgYOv5Zo_e9L4"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

@st.cache_data(ttl=3600)
def carregar_matriz_arquetipos():
    try:
        return pd.read_excel('TABELA_GERAL_ARQUETIPOS_COM_CHAVE.xlsx')
    except:
        return None

@st.cache_data(ttl=3600)
def carregar_matriz_microambiente():
    try:
        return pd.read_excel('TABELA_GERAL_MICROAMBIENTE_COM_CHAVE.xlsx')
    except:
        return None

@st.cache_data(ttl=300)
def carregar_dados_supabase():
    supabase = init_supabase()
    try:
        arq = supabase.table('consolidado_arquetipos').select('*').execute().data
        micro = supabase.table('consolidado_microambiente').select('*').execute().data
        employees = supabase.table('employees').select(
            'id,nome,email,emailLider,manager_name,empresa,holding,company_name,'
            'department_name,cargo,nivel,genero,etnia,employment_status'
        ).execute().data
        ninebox = supabase.table('v_ninebox_items').select('*').execute().data
        evaluations = supabase.table('evaluations').select(
            'employee_id,evaluation_year,round_code,final_rating,performance_rating,'
            'potential_rating,nine_box_position,institucional_avg,funcional_avg,'
            'individual_avg,metas_avg'
        ).execute().data
        return arq, micro, employees, ninebox, evaluations
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return [], [], [], [], []

# ==================== LABELS ====================
NINEBOX_LABELS = {
    1:"🌟 Alto Pot × Alto Des", 2:"⬆️ Alto Pot × Méd Des", 3:"💎 Alto Pot × Bx Des",
    4:"🚀 Méd Pot × Alto Des",  5:"✅ Méd Pot × Méd Des",  6:"⚠️ Méd Pot × Bx Des",
    7:"💪 Bx Pot × Alto Des",   8:"📈 Bx Pot × Méd Des",   9:"🔴 Bx Pot × Bx Des"
}
NINEBOX_CORES = {
    1:"rgba(0,128,0,0.7)",   2:"rgba(0,200,0,0.5)",    3:"rgba(144,238,144,0.5)",
    4:"rgba(0,0,255,0.4)",   5:"rgba(255,255,0,0.5)",  6:"rgba(255,165,0,0.5)",
    7:"rgba(255,200,0,0.4)", 8:"rgba(255,100,0,0.5)",  9:"rgba(255,0,0,0.7)"
}


def gerar_tabela_html(df):
    """
    Gera tabela HTML com:
    - Cabeçalhos agrupados por seção
    - Coluna Nome congelada (sticky)
    - Cores por valores
    """

    def cor_gap(val):
        try:
            v = float(val)
            if v > 30: return "#fca5a5"
            elif v > 20: return "#fdba74"
            elif v > 10: return "#fef08a"
            else: return "#bbf7d0"
        except: return "transparent"

    def cor_termo(val):
        v = str(val)
        if 'ALTO ESTÍM' in v: return "#86efac"
        elif 'ESTÍMULO' in v: return "#bbf7d0"
        elif 'NEUTRO' in v: return "#fef08a"
        elif 'BAIXO' in v: return "#fdba74"
        elif 'DESMOTIV' in v: return "#fca5a5"
        return "transparent"

    def cor_rating(val):
        try:
            v = float(val)
            if v <= 1.5: return "#86efac"
            elif v <= 2.5: return "#bbf7d0"
            elif v <= 3.5: return "#fef08a"
            elif v <= 4.5: return "#fdba74"
            else: return "#fca5a5"
        except: return "transparent"

    def cor_ninebox(val):
        cores = {
            1:"#6ee7b7", 2:"#a7f3d0", 3:"#d1fae5",
            4:"#93c5fd", 5:"#fde68a", 6:"#fecaca",
            7:"#fef08a", 8:"#fed7aa", 9:"#fca5a5"
        }
        try: return cores.get(int(val), "transparent")
        except: return "transparent"

    # Grupos de colunas
    grupos = [
        {
            "titulo": "👤 Identificação",
            "bg": "#1e3a5f",
            "colunas": ["Nome", "Cargo", "Empresa", "Holding", "Dept", "Status", "Rodada LT"]
        },
        {
            "titulo": "🎯 Arquétipos de Gestão",
            "bg": "#1e40af",
            "colunas": ["Dominantes", "Suporte", "Arq #1", "Arq #2", "Arq #3", "N Resp Arq"]
        },
        {
            "titulo": "🏢 Microambiente de Equipes",
            "bg": "#065f46",
            "colunas": ["Gap Geral%", "Gaps >20%", "Termômetro", "N Resp Micro",
                        "Gap Adapt.", "Gap Colab.", "Gap Nitidez", "Gap Perf.", "Gap Reconh.", "Gap Resp."]
        },
        {
            "titulo": "⭐ Avaliação de Desempenho",
            "bg": "#7c2d12",
            "colunas": ["Round Aval.", "Rating Final", "Classif.", "Instit.", "Funcional", "Individual", "Metas"]
        },
        {
            "titulo": "🎲 9Box",
            "bg": "#4c1d95",
            "colunas": ["Desempenho", "Potencial", "9Box Pos", "9Box Label"]
        },
    ]

    # Filtrar apenas colunas existentes no df
    cols_disponiveis = list(df.columns)
    grupos_filtrados = []
    for g in grupos:
        cols = [c for c in g["colunas"] if c in cols_disponiveis]
        if cols:
            grupos_filtrados.append({**g, "colunas": cols})

    # Colunas na ordem correta
    todas_cols = []
    for g in grupos_filtrados:
        todas_cols.extend(g["colunas"])

    # CSS
    css = """
    <style>
    .exec-table-wrap {
        overflow-x: auto;
        max-height: 500px;
        overflow-y: auto;
        border: 1px solid #e5e7eb;
        border-radius: 10px;
        font-family: system-ui, -apple-system, sans-serif;
        font-size: 12px;
    }
    .exec-table {
        border-collapse: collapse;
        width: max-content;
        min-width: 100%;
    }
    .exec-table th, .exec-table td {
        padding: 7px 10px;
        white-space: nowrap;
        border: 1px solid #e5e7eb;
        text-align: left;
        vertical-align: middle;
    }
    /* Cabeçalho grupo */
    .exec-table .th-group {
        color: white;
        font-weight: 700;
        font-size: 11px;
        text-align: center;
        letter-spacing: 0.5px;
        padding: 8px 10px;
        position: sticky;
        top: 0;
        z-index: 3;
    }
    /* Cabeçalho coluna */
    .exec-table .th-col {
        background: #f1f5f9;
        font-weight: 600;
        font-size: 11px;
        color: #374151;
        position: sticky;
        top: 33px;
        z-index: 2;
    }
    /* Linhas alternadas */
    .exec-table tbody tr:nth-child(even) td {
        background: #f8fafc;
    }
    .exec-table tbody tr:hover td {
        background: #e0f2fe !important;
    }
    /* Coluna Nome congelada */
    .exec-table td.frozen,
    .exec-table th.frozen {
        position: sticky;
        left: 0;
        z-index: 4;
        box-shadow: 2px 0 4px rgba(0,0,0,0.08);
    }
    .exec-table th.frozen {
        z-index: 5;
    }
    .exec-table td.frozen {
        background: #fff;
        font-weight: 600;
    }
    .exec-table tbody tr:nth-child(even) td.frozen {
        background: #f8fafc;
    }
    .exec-table tbody tr:hover td.frozen {
        background: #e0f2fe !important;
    }
    </style>
    """

    html = css + '<div class="exec-table-wrap"><table class="exec-table">'

    # ── Linha 1: cabeçalhos de grupo ──
    html += "<thead><tr>"
    for g in grupos_filtrados:
        n_cols = len(g["colunas"])
        frozen = 'class="th-group frozen"' if g["colunas"][0] == "Nome" else 'class="th-group"'
        html += f'<th {frozen} colspan="{n_cols}" style="background:{g["bg"]}">{g["titulo"]}</th>'
    html += "</tr>"

    # ── Linha 2: nomes das colunas ──
    html += "<tr>"
    for i, col in enumerate(todas_cols):
        frozen = ' frozen' if col == "Nome" else ""
        html += f'<th class="th-col{frozen}">{col}</th>'
    html += "</tr></thead>"

    # ── Dados ──
    html += "<tbody>"
    for _, row in df.iterrows():
        html += "<tr>"
        for col in todas_cols:
            val = row.get(col, "—")
            val_str = str(val) if val != "" else "—"

            # Cor de fundo baseada no tipo de coluna
            bg = "transparent"
            if col in ["Gap Geral%", "Gap Adapt.", "Gap Colab.", "Gap Nitidez", "Gap Perf.", "Gap Reconh.", "Gap Resp."]:
                bg = cor_gap(val)
            elif col == "Termômetro":
                bg = cor_termo(val)
            elif col == "Rating Final":
                bg = cor_rating(val)
            elif col == "9Box Pos":
                bg = cor_ninebox(val)

            frozen = ' class="frozen"' if col == "Nome" else ""
            style = f'style="background:{bg}"' if bg != "transparent" else ""

            html += f'<td{frozen} {style}>{val_str}</td>'
        html += "</tr>"

    html += "</tbody></table></div>"
    return html


def calcular_ninebox(performance_rating, potential_rating):
    """
    Lógica idêntica à página WordPress:
    - Arredondamento natural (6.8→7, 5.4→5)
    - Bands: 1-3=baixo, 4-6=médio, 7-9=alto
    """
    def to_int(v):
        try:
            n = round(float(v))
            return max(1, min(9, n))
        except:
            return None
    def band(n):
        if n <= 3: return 0
        if n <= 6: return 1
        return 2
    perf = to_int(performance_rating)
    pot  = to_int(potential_rating)
    if perf is None or pot is None:
        return None
    row = 2 - band(pot)
    col = 2 - band(perf)
    return row * 3 + col + 1

def rating_label(rating):
    try:
        v = float(rating)
        if v <= 1.5: return "⭐ Excelente"
        elif v <= 2.5: return "✅ Bom"
        elif v <= 3.5: return "🟡 Regular"
        elif v <= 4.5: return "🟠 Abaixo"
        else: return "🔴 Insuficiente"
    except: return "—"

def classificar_termometro(qtd_gaps):
    if qtd_gaps is None: return "—", ""
    if qtd_gaps <= 3: return "ALTO ESTÍMULO", "🟢"
    elif qtd_gaps <= 6: return "ESTÍMULO", "🟩"
    elif qtd_gaps <= 9: return "NEUTRO", "🟡"
    elif qtd_gaps <= 12: return "BAIXO ESTÍMULO", "🟠"
    else: return "DESMOTIVAÇÃO", "🔴"

def fmt(val, decimais=1):
    try:
        v = round(float(val), decimais)
        return v
    except: return "—"

def fmt_str(val, decimais=1):
    """Formata para exibição com arredondamento natural"""
    try:
        v = round(float(val), decimais)
        return f"{v:.{decimais}f}"
    except: return "—"

# ==================== CÁLCULOS ====================

def calcular_arquetipos_lider(consolidado_arq, matriz):
    arquetipos_lista = ['Imperativo','Resoluto','Cuidativo','Consultivo','Prescritivo','Formador']
    resultados = {}
    for item in consolidado_arq:
        if not isinstance(item, dict) or 'dados_json' not in item:
            continue
        dados = item['dados_json']
        email_lider = item.get('emaillider','').lower().strip()
        codrodada = item.get('codrodada','')
        equipe = dados.get('avaliacoesEquipe', [])
        if not equipe:
            continue
        soma = {a: 0 for a in arquetipos_lista}
        maximo = {a: 0 for a in arquetipos_lista}
        for membro in equipe:
            respostas = membro.get('respostas', {})
            for q, estrelas in respostas.items():
                if not q.startswith('Q'):
                    continue
                try:
                    nota = int(estrelas)
                except:
                    continue
                for arq in arquetipos_lista:
                    chave = f"{arq}{nota}{q}"
                    linha = matriz[matriz['CHAVE'] == chave]
                    if not linha.empty:
                        soma[arq] += linha['PONTOS_OBTIDOS'].iloc[0]
                        maximo[arq] += linha['PONTOS_MAXIMOS'].iloc[0]
        percentuais = {a: round((soma[a]/maximo[a])*100,1) if maximo[a]>0 else 0 for a in arquetipos_lista}
        dominantes = [a for a,p in percentuais.items() if p >= 60]
        suporte = [a for a,p in percentuais.items() if 50 <= p < 60]
        # Chave única por email+rodada
        key = f"{email_lider}|{codrodada}"
        if key not in resultados:
            resultados[key] = {
                'emaillider': email_lider, 'codrodada': codrodada,
                'percentuais': percentuais, 'dominantes': dominantes,
                'suporte': suporte, 'n_respondentes': len(equipe)
            }
    return resultados


def calcular_gaps_microambiente(consolidado_micro, matriz_micro):
    MAPEAMENTO = {
        'Q01':'Q01','Q02':'Q12','Q03':'Q23','Q04':'Q34','Q05':'Q44','Q06':'Q45',
        'Q07':'Q46','Q08':'Q47','Q09':'Q48','Q10':'Q02','Q11':'Q03','Q12':'Q04',
        'Q13':'Q05','Q14':'Q06','Q15':'Q07','Q16':'Q08','Q17':'Q09','Q18':'Q10',
        'Q19':'Q11','Q20':'Q13','Q21':'Q14','Q22':'Q15','Q23':'Q16','Q24':'Q17',
        'Q25':'Q18','Q26':'Q19','Q27':'Q20','Q28':'Q21','Q29':'Q22','Q30':'Q24',
        'Q31':'Q25','Q32':'Q26','Q33':'Q27','Q34':'Q28','Q35':'Q29','Q36':'Q30',
        'Q37':'Q31','Q38':'Q32','Q39':'Q33','Q40':'Q35','Q41':'Q36','Q42':'Q37',
        'Q43':'Q38','Q44':'Q39','Q45':'Q40','Q46':'Q41','Q47':'Q42','Q48':'Q43'
    }
    REVERSO = {v: k for k, v in MAPEAMENTO.items()}
    resultados = {}
    for item in consolidado_micro:
        if not isinstance(item, dict) or 'dados_json' not in item:
            continue
        dados = item['dados_json']
        email_lider = item.get('emaillider','').lower().strip()
        codrodada = item.get('codrodada','')
        equipe = dados.get('avaliacoesEquipe', [])
        if not equipe:
            continue
        gaps_por_questao = {}
        for q_can in matriz_micro['COD'].unique():
            q_form = REVERSO.get(q_can, q_can)
            soma_real = soma_ideal = count = 0
            for av in equipe:
                qR, qI = f"{q_form}C", f"{q_form}k"
                if qR in av and qI in av:
                    try:
                        r, i = int(av[qR]), int(av[qI])
                    except:
                        continue
                    chave = f"{q_can}_I{i}_R{r}"
                    linha = matriz_micro[matriz_micro['CHAVE'] == chave]
                    if not linha.empty:
                        soma_real += float(linha['PONTUACAO_REAL'].iloc[0])
                        soma_ideal += float(linha['PONTUACAO_IDEAL'].iloc[0])
                        count += 1
            if count > 0:
                real_pct = round(soma_real/count, 2)
                ideal_pct = round(soma_ideal/count, 2)
                gap = round(ideal_pct - real_pct, 2)
                linhas_q = matriz_micro[matriz_micro['COD'] == q_can]
                if not linhas_q.empty:
                    gaps_por_questao[q_can] = {
                        'real': real_pct, 'ideal': ideal_pct, 'gap': gap,
                        'dimensao': linhas_q.iloc[0]['DIMENSAO'],
                        'subdimensao': linhas_q.iloc[0]['SUBDIMENSAO'],
                        'afirmacao': linhas_q.iloc[0]['AFIRMACAO']
                    }
        if not gaps_por_questao:
            continue
        gaps_dim, gaps_subdim = {}, {}
        afirmacoes_gap_critico, afirmacoes_ideal_baixo = [], []
        for q, d in gaps_por_questao.items():
            gaps_dim.setdefault(d['dimensao'], []).append(d['gap'])
            gaps_subdim.setdefault(d['subdimensao'], []).append(d['gap'])
            if abs(d['gap']) > 20:
                afirmacoes_gap_critico.append({**d, 'questao': q})
            if d['ideal'] < 80:
                afirmacoes_ideal_baixo.append({**d, 'questao': q})
        key = f"{email_lider}|{codrodada}"
        if key not in resultados:
            resultados[key] = {
                'emaillider': email_lider, 'codrodada': codrodada,
                'gap_geral': round(np.mean([d['gap'] for d in gaps_por_questao.values()]),1),
                'qtd_gaps_criticos': len(afirmacoes_gap_critico),
                'gap_por_dimensao': {d: round(np.mean(v),1) for d,v in gaps_dim.items()},
                'gap_por_subdimensao': {s: round(np.mean(v),1) for s,v in gaps_subdim.items()},
                'afirmacoes_gap_critico': afirmacoes_gap_critico,
                'afirmacoes_ideal_baixo': afirmacoes_ideal_baixo,
                'n_respondentes': len(equipe)
            }
    return resultados


# ==================== INTERFACE ====================
st.title("📊 Visão Executiva Consolidada")
st.markdown("**Análise completa de todos os líderes em uma única página**")
st.markdown("---")

with st.spinner("Carregando dados..."):
    matriz_arq = carregar_matriz_arquetipos()
    matriz_micro = carregar_matriz_microambiente()
    consolidado_arq, consolidado_micro, employees, ninebox, evaluations = carregar_dados_supabase()

with st.spinner("Calculando indicadores..."):
    dados_arq = calcular_arquetipos_lider(consolidado_arq, matriz_arq)
    dados_micro = calcular_gaps_microambiente(consolidado_micro, matriz_micro)

df_emp = pd.DataFrame(employees) if employees else pd.DataFrame()
df_ninebox = pd.DataFrame(ninebox) if ninebox else pd.DataFrame()
df_eval = pd.DataFrame(evaluations) if evaluations else pd.DataFrame()

# ── Identificar líderes ──────────────────────────────
# 1) Líderes do LeaderTrack (email aparece nos consolidados)
lideres_lt = set()
for v in {**dados_arq, **dados_micro}.values():
    lideres_lt.add(v['emaillider'])

# 2) Líderes da tabela employees: nome aparece em manager_name de outros
# Mapeamento nome → email
nome_to_email = {}
if not df_emp.empty and 'nome' in df_emp.columns and 'email' in df_emp.columns:
    for _, row in df_emp.iterrows():
        if row.get('nome') and row.get('email'):
            nome_to_email[str(row['nome']).strip().upper()] = str(row['email']).lower().strip()

# Quem aparece como manager_name (exceto "GOD")
lideres_manager = set()
if not df_emp.empty and 'manager_name' in df_emp.columns:
    for mgr in df_emp['manager_name'].dropna().unique():
        mgr_upper = str(mgr).strip().upper()
        if mgr_upper != 'GOD' and mgr_upper in nome_to_email:
            lideres_manager.add(nome_to_email[mgr_upper])

# União de todos os líderes
todos_lideres_emails = lideres_lt.union(lideres_manager)

# ==================== FILTROS ====================
st.sidebar.header("🎛️ Filtros")

# Employment Status
status_opcoes = ["Todos"]
if not df_emp.empty and 'employment_status' in df_emp.columns:
    status_vals = sorted(df_emp['employment_status'].dropna().unique().tolist())
    status_opcoes += status_vals
status_sel = st.sidebar.selectbox("👔 Status", status_opcoes, index=status_opcoes.index("ATIVO") if "ATIVO" in status_opcoes else 0)

# Holding
holdings = ["Todas"]
if not df_emp.empty and 'holding' in df_emp.columns:
    holdings += sorted([str(h).upper() for h in df_emp['holding'].dropna().unique() if h])
holding_sel = st.sidebar.selectbox("🏢 Holding", holdings)

# Empresa
empresas_list = ["Todas"]
if not df_emp.empty and 'empresa' in df_emp.columns:
    empresas_list += sorted([str(e) for e in df_emp['empresa'].dropna().unique() if e])
empresa_sel = st.sidebar.selectbox("🏭 Empresa", empresas_list)

# Rodada LeaderTrack
rodadas_lt = sorted(set(v['codrodada'] for v in {**dados_arq, **dados_micro}.values()))
rodada_lt_sel = st.sidebar.selectbox("📅 Rodada LeaderTrack", ["Todas"] + rodadas_lt)

# Round Avaliação
rounds_disp = ["Todos"]
if not df_eval.empty and 'round_code' in df_eval.columns:
    rounds_disp += sorted(df_eval['round_code'].dropna().unique().tolist(), reverse=True)
round_eval_sel = st.sidebar.selectbox("📆 Round Avaliação", rounds_disp)

# Líder
lider_sel = st.sidebar.multiselect("👤 Líder(es)", sorted(todos_lideres_emails))

# ==================== MONTAR TABELA ÚNICA ====================
linhas = []

for email in todos_lideres_emails:
    # Filtro de líder
    if lider_sel and email not in lider_sel:
        continue

    # Dados do employee
    emp = {}
    if not df_emp.empty and 'email' in df_emp.columns:
        emp_rows = df_emp[df_emp['email'].str.lower().str.strip() == email]
        if not emp_rows.empty:
            emp = emp_rows.iloc[0].to_dict()

    # Filtro status
    emp_status = str(emp.get('employment_status','')).strip().upper() if emp else ''
    if status_sel != "Todos" and emp_status != status_sel:
        continue

    # Filtros holding e empresa
    emp_holding = str(emp.get('holding','')).upper().strip() if emp else ''
    emp_empresa = str(emp.get('empresa','')).lower().strip() if emp else ''
    if holding_sel != "Todas" and emp_holding != holding_sel.upper():
        continue
    if empresa_sel != "Todas" and emp_empresa != empresa_sel.lower():
        continue

    # Buscar dados LeaderTrack (pode ter múltiplas rodadas)
    keys_lider = [k for k in {**dados_arq, **dados_micro}.keys() if k.startswith(f"{email}|")]

    # Se filtro de rodada, filtrar
    if rodada_lt_sel != "Todas":
        keys_lider = [k for k in keys_lider if k.endswith(f"|{rodada_lt_sel}")]

    # Se não tem dados LeaderTrack, ainda inclui com dados vazios
    if not keys_lider:
        keys_lider = [f"{email}|—"]

    for key in keys_lider:
        rodada = key.split('|')[1] if '|' in key else '—'
        arq = dados_arq.get(key, {})
        micro = dados_micro.get(key, {})

        # Arquétipos
        pcts = arq.get('percentuais', {})
        dominantes = arq.get('dominantes', [])
        suporte_arq = arq.get('suporte', [])
        top_arq = sorted(pcts.items(), key=lambda x: -x[1]) if pcts else []

        # Microambiente
        gap_geral = micro.get('gap_geral')
        qtd_gaps = micro.get('qtd_gaps_criticos')
        gap_dim = micro.get('gap_por_dimensao', {})
        termo_label, termo_emoji = classificar_termometro(qtd_gaps)

        # Dados de avaliação
        emp_id = emp.get('id') if emp else None
        eval_data = {}
        ninebox_data = {}
        if emp_id:
            if not df_eval.empty and 'employee_id' in df_eval.columns:
                evals = df_eval[df_eval['employee_id'] == emp_id]
                if round_eval_sel != "Todos" and 'round_code' in evals.columns:
                    evals = evals[evals['round_code'] == round_eval_sel]
                if not evals.empty:
                    eval_data = evals.sort_values('evaluation_year', ascending=False).iloc[0].to_dict()
            if not df_ninebox.empty and 'employee_id' in df_ninebox.columns:
                nb = df_ninebox[df_ninebox['employee_id'] == emp_id]
                if round_eval_sel != "Todos" and 'round_code' in nb.columns:
                    nb = nb[nb['round_code'] == round_eval_sel]
                if not nb.empty:
                    ninebox_data = nb.iloc[0].to_dict()

        final_rating = ninebox_data.get('final_rating') or eval_data.get('final_rating')
        perf_rating  = ninebox_data.get('performance_rating') or eval_data.get('performance_rating')
        pot_rating   = ninebox_data.get('potential_rating') or eval_data.get('potential_rating')
        # Recalcular 9Box pela lógica correta (idêntica ao WordPress)
        nb_pos = calcular_ninebox(perf_rating, pot_rating)
        round_aval   = ninebox_data.get('round_code') or eval_data.get('round_code','—')

        linhas.append({
            # ── Identificação ──
            'Nome':        emp.get('nome','—') if emp else email,
            'Email':       email,
            'Cargo':       emp.get('cargo','—') if emp else '—',
            'Empresa':     emp.get('empresa','—') if emp else '—',
            'Holding':     emp.get('holding','—') if emp else '—',
            'Dept':        emp.get('department_name','—') if emp else '—',
            'Status':      emp_status or '—',
            # ── LeaderTrack - Arquétipos ──
            'Rodada LT':   rodada,
            'Dominantes':  ', '.join(dominantes) if dominantes else ('—' if pcts else 'Sem dados'),
            'Suporte':     ', '.join(suporte_arq) if suporte_arq else '—',
            'Arq #1':      f"{top_arq[0][0]} ({top_arq[0][1]:.0f}%)" if len(top_arq)>0 else '—',
            'Arq #2':      f"{top_arq[1][0]} ({top_arq[1][1]:.0f}%)" if len(top_arq)>1 else '—',
            'Arq #3':      f"{top_arq[2][0]} ({top_arq[2][1]:.0f}%)" if len(top_arq)>2 else '—',
            'N Resp Arq':  arq.get('n_respondentes', '—') if arq else '—',
            # ── LeaderTrack - Microambiente ──
            'Gap Geral%':  fmt(gap_geral) if gap_geral is not None else '—',
            'Gaps >20%':   qtd_gaps if qtd_gaps is not None else '—',
            'Termômetro':  f"{termo_emoji} {termo_label}" if micro else '—',
            'N Resp Micro':micro.get('n_respondentes','—') if micro else '—',
            # Gaps por dimensão
            'Gap Adapt.':  fmt(gap_dim.get('Adaptabilidade')) if gap_dim else '—',
            'Gap Colab.':  fmt(gap_dim.get('Colaboração Mútua')) if gap_dim else '—',
            'Gap Nitidez': fmt(gap_dim.get('Nitidez')) if gap_dim else '—',
            'Gap Perf.':   fmt(gap_dim.get('Performance')) if gap_dim else '—',
            'Gap Reconh.': fmt(gap_dim.get('Reconhecimento')) if gap_dim else '—',
            'Gap Resp.':   fmt(gap_dim.get('Responsabilidade')) if gap_dim else '—',
            # ── Avaliação de Desempenho ──
            'Round Aval.': round_aval,
            'Rating Final':fmt(final_rating, 2) if final_rating else '—',
            'Classif.':    rating_label(final_rating) if final_rating else '—',
            'Desempenho':  fmt(perf_rating, 2) if perf_rating else '—',
            'Potencial':   fmt(pot_rating, 2) if pot_rating else '—',
            'Instit.':     fmt(eval_data.get('institucional_avg'), 2) if eval_data.get('institucional_avg') else '—',
            'Funcional':   fmt(eval_data.get('funcional_avg'), 2) if eval_data.get('funcional_avg') else '—',
            'Individual':  fmt(eval_data.get('individual_avg'), 2) if eval_data.get('individual_avg') else '—',
            'Metas':       fmt(eval_data.get('metas_avg'), 2) if eval_data.get('metas_avg') else '—',
            # ── 9Box ──
            '9Box Pos':    int(nb_pos) if nb_pos else '—',
            '9Box Label':  NINEBOX_LABELS.get(int(nb_pos),'—') if nb_pos else '—',
            # Referências internas
            '_micro': micro,
            '_arq':   arq,
            '_emp_id': emp_id,
        })

df = pd.DataFrame(linhas)

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
    st.stop()

# Remove duplicatas (mesmo líder em múltiplas rodadas se filtro = Todas)
# Mantém todas as linhas — cada rodada é uma linha separada

# ==================== MÉTRICAS ====================
c1,c2,c3,c4,c5,c6 = st.columns(6)
with c1: st.metric("👥 Líderes", len(df['Email'].unique()))
with c2:
    gaps_num = pd.to_numeric(df['Gap Geral%'].replace('—',np.nan), errors='coerce')
    st.metric("Gap Médio", f"{gaps_num.mean():.1f}%" if not gaps_num.isna().all() else "—")
with c3:
    qtds_num = pd.to_numeric(df['Gaps >20%'].replace('—',np.nan), errors='coerce')
    st.metric("Média Gaps Críticos", f"{qtds_num.mean():.1f}" if not qtds_num.isna().all() else "—")
with c4:
    ratings_num = pd.to_numeric(df['Rating Final'].replace('—',np.nan), errors='coerce')
    st.metric("Rating Médio", f"{ratings_num.mean():.2f}" if not ratings_num.isna().all() else "—")
with c5:
    st.metric("🔴 Desmotivação", len(df[df['Termômetro'].str.contains('DESMOTIV',na=False)]))
with c6:
    st.metric("🟢 Alto Estímulo", len(df[df['Termômetro'].str.contains('ALTO ESTÍM',na=False)]))

st.markdown("---")

# ==================== TABELA ÚNICA COMPLETA ====================
st.subheader("📋 Tabela Consolidada — Uma linha por Líder")

cols_exibir = [c for c in df.columns if not c.startswith('_')]
df_show = df[cols_exibir].copy()

# Tabela HTML com cabeçalhos agrupados e Nome congelado
tabela_html = gerar_tabela_html(df_show)
components.html(tabela_html, height=540, scrolling=True)

# Download
csv = df_show.to_csv(index=False, encoding='utf-8-sig')
st.download_button("📥 Download CSV Completo", data=csv, file_name="visao_executiva.csv", mime="text/csv")

# ==================== GRÁFICOS COMPARATIVOS ====================
st.markdown("---")
st.subheader("📊 Comparativos entre Líderes")

tab_arq, tab_micro, tab_eval, tab_9box = st.tabs([
    "🎯 Arquétipos", "🏢 Microambiente", "⭐ Avaliação", "🎲 9Box"
])

with tab_arq:
    arquetipos_lista = ['Imperativo','Resoluto','Cuidativo','Consultivo','Prescritivo','Formador']
    df_com_arq = df[df['Arq #1'] != '—'].copy()
    if not df_com_arq.empty:
        nomes_c = [n[:20] for n in df_com_arq['Nome']]
        vals = {a: [] for a in arquetipos_lista}
        for _, row in df_com_arq.iterrows():
            pcts = row['_arq'].get('percentuais', {})
            for arq in arquetipos_lista:
                vals[arq].append(pcts.get(arq, 0))
        fig = go.Figure()
        cores_arq = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b']
        for i, arq in enumerate(arquetipos_lista):
            fig.add_trace(go.Bar(name=arq, x=nomes_c, y=vals[arq], marker_color=cores_arq[i]))
        fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="Dominante (60%)")
        fig.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Suporte (50%)")
        fig.update_layout(barmode='group', title="Arquétipos por Líder", yaxis=dict(range=[0,100]), height=500)
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("ℹ️ Sem dados de arquétipos para os filtros selecionados.")

with tab_micro:
    df_com_micro = df[df['Gap Geral%'] != '—'].copy()
    if not df_com_micro.empty:
        nomes_m = [n[:20] for n in df_com_micro['Nome']]
        gaps_g = pd.to_numeric(df_com_micro['Gap Geral%'], errors='coerce').tolist()
        qtds_c = pd.to_numeric(df_com_micro['Gaps >20%'].replace('—',np.nan), errors='coerce').fillna(0).astype(int).tolist()
        col1, col2 = st.columns(2)
        with col1:
            fig2 = go.Figure(go.Bar(x=nomes_m, y=gaps_g,
                marker_color=['rgba(255,0,0,0.7)' if v>20 else 'rgba(255,165,0,0.7)' if v>10 else 'rgba(0,128,0,0.7)' for v in gaps_g],
                text=[f"{v:.1f}%" for v in gaps_g], textposition='auto'))
            fig2.update_layout(title="Gap Geral por Líder", height=400)
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            fig3 = go.Figure(go.Bar(x=nomes_m, y=qtds_c,
                marker_color=['rgba(255,0,0,0.7)' if v>12 else 'rgba(255,165,0,0.7)' if v>6 else 'rgba(0,128,0,0.7)' for v in qtds_c],
                text=[str(v) for v in qtds_c], textposition='auto'))
            fig3.update_layout(title="Gaps Críticos (>20%) por Líder", height=400)
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("ℹ️ Sem dados de microambiente para os filtros selecionados.")

with tab_eval:
    df_com_eval = df[df['Rating Final'] != '—'].copy()
    if not df_com_eval.empty:
        nomes_r = [n[:20] for n in df_com_eval['Nome']]
        ratings_r = pd.to_numeric(df_com_eval['Rating Final'], errors='coerce').tolist()
        fig4 = go.Figure(go.Bar(x=nomes_r, y=ratings_r,
            marker_color=['rgba(0,128,0,0.7)' if v<=1.5 else 'rgba(144,238,144,0.7)' if v<=2.5 else 'rgba(255,255,0,0.7)' if v<=3.5 else 'rgba(255,165,0,0.7)' if v<=4.5 else 'rgba(255,0,0,0.7)' for v in ratings_r],
            text=[f"{v:.2f}" for v in ratings_r], textposition='auto'))
        fig4.add_hline(y=2.5, line_dash="dash", line_color="gray", annotation_text="Bom/Regular")
        fig4.update_layout(title="Rating Final por Líder (1=Excelente → 5=Insuficiente)",
            yaxis=dict(range=[0,5.5]), height=400)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("ℹ️ Sem dados de avaliação para o round selecionado.")

with tab_9box:
    df_com_9b = df[df['9Box Pos'] != '—'].copy()
    if not df_com_9b.empty:
        # Matriz visual
        st.markdown("**Distribuição 9Box:**")
        posicoes_grid = [[1,2,3],[4,5,6],[7,8,9]]
        for row_pos in posicoes_grid:
            cols_9b = st.columns(3)
            for col_idx, pos in enumerate(row_pos):
                nomes_pos = df_com_9b[df_com_9b['9Box Pos'] == pos]['Nome'].tolist()
                qtd = len(nomes_pos)
                label = NINEBOX_LABELS.get(pos,'—')
                cor = NINEBOX_CORES.get(pos,'rgba(200,200,200,0.3)')
                with cols_9b[col_idx]:
                    nomes_str = '<br>'.join([n[:25] for n in nomes_pos]) if nomes_pos else '—'
                    st.markdown(f"""
                    <div style="padding:10px;border-radius:8px;background:{cor};margin:3px;min-height:90px;">
                        <b style="font-size:11px;">{label}</b><br>
                        <span style="font-size:22px;font-weight:bold;">{qtd}</span><br>
                        <span style="font-size:10px;">{nomes_str}</span>
                    </div>""", unsafe_allow_html=True)
    else:
        st.info("ℹ️ Sem dados de 9Box para o round selecionado.")

# ==================== DRILL-DOWN POR LÍDER ====================
st.markdown("---")
st.subheader("🔍 Detalhamento por Líder")

opcoes_drill = ["—"] + sorted(df['Nome'].unique().tolist())
lider_detail = st.selectbox("Selecione um líder para detalhes:", opcoes_drill)

if lider_detail != "—":
    rows_lider = df[df['Nome'] == lider_detail]
    row = rows_lider.iloc[0]
    micro_data = row['_micro']
    arq_data = row['_arq']

    st.markdown(f"### 👤 {row['Nome']}  |  {row['Cargo']}  |  {row['Empresa']} / {row['Holding']}")

    t1,t2,t3,t4,t5 = st.tabs(["🎯 Arquétipos","🏢 Microambiente","⚠️ Gaps Críticos","⭐ Avaliação","🎲 9Box"])

    with t1:
        pcts = arq_data.get('percentuais',{})
        if pcts:
            arq_ord = sorted(pcts.items(), key=lambda x: -x[1])
            cores = ['rgba(0,128,0,0.8)' if v>=60 else 'rgba(255,165,0,0.8)' if v>=50 else 'rgba(200,200,200,0.6)' for _,v in arq_ord]
            fig = go.Figure(go.Bar(
                x=[a for a,v in arq_ord], y=[v for a,v in arq_ord],
                marker_color=cores, text=[f"{v:.1f}%" for _,v in arq_ord], textposition='auto'))
            fig.add_hline(y=60, line_dash="dash", line_color="green", annotation_text="Dominante (60%)")
            fig.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Suporte (50%)")
            fig.update_layout(title="Arquétipos — Média da Equipe", yaxis=dict(range=[0,100]), height=400)
            st.plotly_chart(fig, use_container_width=True)
            c1,c2 = st.columns(2)
            with c1: st.success(f"**Dominantes (≥60%):** {', '.join(arq_data.get('dominantes',[])) or 'Nenhum'}")
            with c2: st.warning(f"**Suporte (50-59%):** {', '.join(arq_data.get('suporte',[])) or 'Nenhum'}")
        else:
            st.info("ℹ️ Sem dados de arquétipos LeaderTrack para este líder.")

    with t2:
        gd = micro_data.get('gap_por_dimensao',{})
        gs = micro_data.get('gap_por_subdimensao',{})
        if gd:
            c1,c2 = st.columns(2)
            with c1:
                fig2 = go.Figure(go.Bar(
                    x=list(gd.values()), y=list(gd.keys()), orientation='h',
                    marker_color=['rgba(255,0,0,0.7)' if v>20 else 'rgba(255,165,0,0.7)' if v>10 else 'rgba(0,128,0,0.7)' for v in gd.values()],
                    text=[f"{v:.1f}%" for v in gd.values()], textposition='auto'))
                fig2.update_layout(title="Gap por Dimensão", height=350)
                st.plotly_chart(fig2, use_container_width=True)
            with c2:
                fig3 = go.Figure(go.Bar(
                    x=list(gs.values()), y=list(gs.keys()), orientation='h',
                    marker_color=['rgba(255,0,0,0.7)' if v>20 else 'rgba(255,165,0,0.7)' if v>10 else 'rgba(0,128,0,0.7)' for v in gs.values()],
                    text=[f"{v:.1f}%" for v in gs.values()], textposition='auto'))
                fig3.update_layout(title="Gap por Subdimensão", height=350)
                st.plotly_chart(fig3, use_container_width=True)
            c1,c2,c3 = st.columns(3)
            with c1: st.metric("Gap Geral", f"{micro_data.get('gap_geral',0):.1f}%")
            with c2: st.metric("Gaps Críticos (>20%)", micro_data.get('qtd_gaps_criticos',0))
            with c3: st.metric("Termômetro", row['Termômetro'])
        else:
            st.info("ℹ️ Sem dados de microambiente LeaderTrack para este líder.")

    with t3:
        gc = micro_data.get('afirmacoes_gap_critico',[])
        ib = micro_data.get('afirmacoes_ideal_baixo',[])
        c1,c2 = st.columns(2)
        with c1:
            st.markdown(f"#### ⚠️ Gap > 20% ({len(gc)})")
            if gc:
                df_gc = pd.DataFrame(gc)[['questao','afirmacao','dimensao','subdimensao','real','ideal','gap']]
                df_gc.columns = ['Q','Afirmação','Dimensão','Subdim.','Real%','Ideal%','Gap']
                st.dataframe(df_gc.sort_values('Gap',ascending=False), use_container_width=True, hide_index=True)
            else:
                st.success("✅ Nenhum gap crítico!")
        with c2:
            st.markdown(f"#### 📉 Ideal < 80% ({len(ib)})")
            if ib:
                df_ib = pd.DataFrame(ib)[['questao','afirmacao','dimensao','real','ideal','gap']]
                df_ib.columns = ['Q','Afirmação','Dimensão','Real%','Ideal%','Gap']
                st.dataframe(df_ib.sort_values('Ideal%'), use_container_width=True, hide_index=True)
            else:
                st.success("✅ Todos os ideais acima de 80%!")

    with t4:
        if row['Rating Final'] != '—':
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("Rating Final", row['Rating Final'])
            with c2: st.metric("Classificação", row['Classif.'])
            with c3: st.metric("Desempenho", row['Desempenho'])
            with c4: st.metric("Potencial", row['Potencial'])
            st.markdown("**Médias por Dimensão:**")
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("Institucional", row['Instit.'])
            with c2: st.metric("Funcional", row['Funcional'])
            with c3: st.metric("Individual", row['Individual'])
            with c4: st.metric("Metas", row['Metas'])
        else:
            st.info("ℹ️ Sem dados de avaliação para este líder no round selecionado.")

    with t5:
        if row['9Box Label'] != '—':
            c1,c2,c3 = st.columns(3)
            with c1: st.metric("Posição 9Box", row['9Box Pos'])
            with c2: st.metric("Quadrante", row['9Box Label'])
            with c3: st.metric("Round", row['Round Aval.'])
        else:
            st.info("ℹ️ Sem dados de 9Box para este líder no round selecionado.")

st.markdown("---")
st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
