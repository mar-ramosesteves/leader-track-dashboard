import streamlit as st
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
def carregar_dados():
    supabase = init_supabase()
    try:
        arq = supabase.table('consolidado_arquetipos').select('*').execute().data
        micro = supabase.table('consolidado_microambiente').select('*').execute().data
        
        # Buscar apenas líderes: emails que aparecem no campo emailLider de outros registros
        employees = supabase.table('employees').select(
            'id,nome,email,emailLider,empresa,holding,company_name,department_name,cargo,genero,etnia'
        ).execute().data
        
        # View 9box
        ninebox = supabase.table('v_ninebox_items').select('*').execute().data
        
        # Evaluations com todas as colunas necessárias
        evaluations = supabase.table('evaluations').select(
            'employee_id,evaluation_year,round_code,final_rating,performance_rating,potential_rating,nine_box_position,institucional_avg,funcional_avg,individual_avg,metas_avg,dimension_averages'
        ).execute().data

        return arq, micro, employees, ninebox, evaluations
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return [], [], [], [], []

# ==================== LABELS ====================
NINEBOX_LABELS = {
    1: "🌟 Alto Pot × Alto Des",
    2: "⬆️ Alto Pot × Méd Des",
    3: "💎 Alto Pot × Bx Des",
    4: "🚀 Méd Pot × Alto Des",
    5: "✅ Méd Pot × Méd Des",
    6: "⚠️ Méd Pot × Bx Des",
    7: "💪 Bx Pot × Alto Des",
    8: "📈 Bx Pot × Méd Des",
    9: "🔴 Bx Pot × Bx Des"
}

NINEBOX_CORES = {
    1: "rgba(0,128,0,0.7)", 2: "rgba(0,200,0,0.5)", 3: "rgba(144,238,144,0.5)",
    4: "rgba(0,0,255,0.4)", 5: "rgba(255,255,0,0.5)", 6: "rgba(255,165,0,0.5)",
    7: "rgba(255,200,0,0.4)", 8: "rgba(255,100,0,0.5)", 9: "rgba(255,0,0,0.7)"
}

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
    if qtd_gaps <= 3: return "ALTO ESTÍMULO", "🟢"
    elif qtd_gaps <= 6: return "ESTÍMULO", "🟩"
    elif qtd_gaps <= 9: return "NEUTRO", "🟡"
    elif qtd_gaps <= 12: return "BAIXO ESTÍMULO", "🟠"
    else: return "DESMOTIVAÇÃO", "🔴"

# ==================== CÁLCULOS ====================

def calcular_arquetipos_lider(consolidado_arq, matriz):
    arquetipos_lista = ['Imperativo','Resoluto','Cuidativo','Consultivo','Prescritivo','Formador']
    resultados = {}
    for item in consolidado_arq:
        if not isinstance(item, dict) or 'dados_json' not in item:
            continue
        dados = item['dados_json']
        email_lider = item.get('emaillider','').lower()
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
        key = f"{email_lider}|{codrodada}"
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
        email_lider = item.get('emaillider','').lower()
        codrodada = item.get('codrodada','')
        equipe = dados.get('avaliacoesEquipe', [])
        if not equipe:
            continue
        gaps_por_questao = {}
        questoes_canonicas = matriz_micro['COD'].unique()
        for q_can in questoes_canonicas:
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
        gaps_dim = {}
        gaps_subdim = {}
        afirmacoes_gap_critico = []
        afirmacoes_ideal_baixo = []
        for q, d in gaps_por_questao.items():
            gaps_dim.setdefault(d['dimensao'], []).append(d['gap'])
            gaps_subdim.setdefault(d['subdimensao'], []).append(d['gap'])
            if abs(d['gap']) > 20:
                afirmacoes_gap_critico.append({**d, 'questao': q})
            if d['ideal'] < 80:
                afirmacoes_ideal_baixo.append({**d, 'questao': q})
        key = f"{email_lider}|{codrodada}"
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


# ==================== CARREGAR ====================
st.title("📊 Visão Executiva Consolidada")
st.markdown("**Análise completa de todos os líderes em uma única página**")
st.markdown("---")

with st.spinner("Carregando dados..."):
    matriz_arq = carregar_matriz_arquetipos()
    matriz_micro = carregar_matriz_microambiente()
    consolidado_arq, consolidado_micro, employees, ninebox, evaluations = carregar_dados()

with st.spinner("Calculando indicadores..."):
    dados_arq = calcular_arquetipos_lider(consolidado_arq, matriz_arq)
    dados_micro = calcular_gaps_microambiente(consolidado_micro, matriz_micro)

# DataFrames auxiliares
df_emp = pd.DataFrame(employees) if employees else pd.DataFrame()
df_ninebox = pd.DataFrame(ninebox) if ninebox else pd.DataFrame()
df_eval = pd.DataFrame(evaluations) if evaluations else pd.DataFrame()

# Identificar líderes: emails que aparecem como emailLider de outros
lideres_emails = set()
if not df_emp.empty and 'emailLider' in df_emp.columns:
    lideres_emails = set(df_emp['emailLider'].dropna().str.lower().unique())

# Também incluir líderes do LeaderTrack
lideres_arq = set(v['emaillider'] for v in dados_arq.values())
lideres_micro = set(v['emaillider'] for v in dados_micro.values())
lideres_emails = lideres_emails.union(lideres_arq).union(lideres_micro)

# Rounds disponíveis
rounds_disp = ["Todos"]
if not df_eval.empty and 'round_code' in df_eval.columns:
    rounds_disp += sorted(df_eval['round_code'].dropna().unique().tolist(), reverse=True)

# ==================== FILTROS ====================
st.sidebar.header("🎛️ Filtros")

holdings = ["Todas"]
empresas_list = ["Todas"]
if not df_emp.empty:
    if 'holding' in df_emp.columns:
        holdings += sorted([str(h).upper() for h in df_emp['holding'].dropna().unique() if h])
    if 'empresa' in df_emp.columns:
        empresas_list += sorted([str(e) for e in df_emp['empresa'].dropna().unique() if e])

holding_sel = st.sidebar.selectbox("🏢 Holding", holdings)
empresa_sel = st.sidebar.selectbox("🏭 Empresa", empresas_list)

rodadas_lt = sorted(set(v['codrodada'] for v in {**dados_arq, **dados_micro}.values()))
rodada_lt_sel = st.sidebar.selectbox("📅 Rodada LeaderTrack", ["Todas"] + rodadas_lt)

round_eval_sel = st.sidebar.selectbox("📆 Round Avaliação", rounds_disp)

lideres_sorted = sorted(lideres_emails)
lider_sel = st.sidebar.multiselect("👤 Líder(es)", lideres_sorted)

# ==================== MONTAR TABELA ====================
linhas = []
todos_lideres_keys = set(dados_arq.keys()).union(set(dados_micro.keys()))

for key in todos_lideres_keys:
    email = key.split('|')[0]
    rodada = key.split('|')[1] if '|' in key else ''

    # Filtrar rodada LeaderTrack
    if rodada_lt_sel != "Todas" and rodada != rodada_lt_sel:
        continue
    # Filtrar líder
    if lider_sel and email not in lider_sel:
        continue

    # Dados employee do líder
    emp = {}
    if not df_emp.empty and 'email' in df_emp.columns:
        emp_rows = df_emp[df_emp['email'].str.lower() == email]
        if not emp_rows.empty:
            emp = emp_rows.iloc[0].to_dict()

    # Filtros holding e empresa
    emp_holding = str(emp.get('holding','')).upper().strip() if emp else ''
    emp_empresa = str(emp.get('empresa','')).lower().strip() if emp else ''
    if holding_sel != "Todas" and emp_holding != holding_sel.upper():
        continue
    if empresa_sel != "Todas" and emp_empresa != empresa_sel.lower():
        continue

    arq = dados_arq.get(key, {})
    micro = dados_micro.get(key, {})

    # Dados de avaliação do líder (pela view v_ninebox_items ou evaluations)
    eval_data = {}
    ninebox_data = {}
    emp_id = emp.get('id') if emp else None
    if emp_id:
        # Buscar na evaluations
        if not df_eval.empty and 'employee_id' in df_eval.columns:
            evals = df_eval[df_eval['employee_id'] == emp_id]
            if round_eval_sel != "Todos" and 'round_code' in evals.columns:
                evals = evals[evals['round_code'] == round_eval_sel]
            if not evals.empty:
                eval_data = evals.iloc[-1].to_dict()
        # Buscar na v_ninebox_items
        if not df_ninebox.empty and 'employee_id' in df_ninebox.columns:
            nb = df_ninebox[df_ninebox['employee_id'] == emp_id]
            if round_eval_sel != "Todos" and 'round_code' in nb.columns:
                nb = nb[nb['round_code'] == round_eval_sel]
            if not nb.empty:
                ninebox_data = nb.iloc[-1].to_dict()

    # Arquétipos
    pcts = arq.get('percentuais', {})
    dominantes = arq.get('dominantes', [])
    suporte_arq = arq.get('suporte', [])
    top_arq = sorted(pcts.items(), key=lambda x: -x[1]) if pcts else []

    # Microambiente
    gap_geral = micro.get('gap_geral')
    qtd_gaps = micro.get('qtd_gaps_criticos')
    gap_dim = micro.get('gap_por_dimensao', {})
    termo_label, termo_emoji = classificar_termometro(qtd_gaps) if qtd_gaps is not None else ("—","")

    # Avaliação — usar ninebox_data se disponível, senão eval_data
    final_rating = ninebox_data.get('final_rating') or eval_data.get('final_rating')
    perf_rating = ninebox_data.get('performance_rating') or eval_data.get('performance_rating')
    pot_rating = ninebox_data.get('potential_rating') or eval_data.get('potential_rating')
    nb_pos = ninebox_data.get('nine_box_position') or eval_data.get('nine_box_position')
    inst_avg = eval_data.get('institucional_avg')
    func_avg = eval_data.get('funcional_avg')
    ind_avg = eval_data.get('individual_avg')
    metas_avg = eval_data.get('metas_avg')
    round_code_eval = ninebox_data.get('round_code') or eval_data.get('round_code','—')

    linhas.append({
        # Identificação
        'Email': email,
        'Nome': emp.get('nome','—') if emp else '—',
        'Cargo': emp.get('cargo','—') if emp else '—',
        'Empresa': emp.get('empresa','—') if emp else '—',
        'Holding': emp.get('holding','—') if emp else '—',
        'Rodada LT': rodada,
        'Round Aval.': round_code_eval,
        # LeaderTrack - Arquétipos
        'Dominantes': ', '.join(dominantes) if dominantes else 'Nenhum',
        'Suporte': ', '.join(suporte_arq) if suporte_arq else '—',
        'Arq #1': f"{top_arq[0][0]} ({top_arq[0][1]:.0f}%)" if len(top_arq)>0 else '—',
        'Arq #2': f"{top_arq[1][0]} ({top_arq[1][1]:.0f}%)" if len(top_arq)>1 else '—',
        'Arq #3': f"{top_arq[2][0]} ({top_arq[2][1]:.0f}%)" if len(top_arq)>2 else '—',
        'N Resp Arq': arq.get('n_respondentes',0),
        # LeaderTrack - Microambiente
        'Gap Geral (%)': gap_geral if gap_geral is not None else '—',
        'Qtd Gaps >20%': qtd_gaps if qtd_gaps is not None else '—',
        'Termômetro': f"{termo_emoji} {termo_label}" if micro else '—',
        'Gap Adaptab.': gap_dim.get('Adaptabilidade','—'),
        'Gap Colab.': gap_dim.get('Colaboração Mútua','—'),
        'Gap Nitidez': gap_dim.get('Nitidez','—'),
        'Gap Perf.': gap_dim.get('Performance','—'),
        'Gap Reconh.': gap_dim.get('Reconhecimento','—'),
        'Gap Resp.': gap_dim.get('Responsabilidade','—'),
        'N Resp Micro': micro.get('n_respondentes',0),
        # Avaliação de Desempenho
        'Rating Final': round(float(final_rating),2) if final_rating else '—',
        'Classificação': rating_label(final_rating) if final_rating else '—',
        'Desempenho': round(float(perf_rating),2) if perf_rating else '—',
        'Potencial': round(float(pot_rating),2) if pot_rating else '—',
        'Avg Instit.': round(float(inst_avg),2) if inst_avg else '—',
        'Avg Funcional': round(float(func_avg),2) if func_avg else '—',
        'Avg Individual': round(float(ind_avg),2) if ind_avg else '—',
        'Avg Metas': round(float(metas_avg),2) if metas_avg else '—',
        # 9Box
        '9Box Posição': int(nb_pos) if nb_pos else '—',
        '9Box Label': NINEBOX_LABELS.get(int(nb_pos),'—') if nb_pos else '—',
        # Referências internas
        '_micro': micro,
        '_arq': arq,
        '_emp_id': emp_id,
    })

df = pd.DataFrame(linhas)

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
    st.stop()

# ==================== MÉTRICAS GERAIS ====================
c1,c2,c3,c4,c5,c6 = st.columns(6)
with c1:
    st.metric("👥 Total Líderes", len(df))
with c2:
    gaps_num = pd.to_numeric(df['Gap Geral (%)'].replace('—',np.nan), errors='coerce')
    st.metric("Gap Médio Micro", f"{gaps_num.mean():.1f}%" if not gaps_num.isna().all() else "—")
with c3:
    qtds_num = pd.to_numeric(df['Qtd Gaps >20%'].replace('—',np.nan), errors='coerce')
    st.metric("Média Gaps Críticos", f"{qtds_num.mean():.1f}" if not qtds_num.isna().all() else "—")
with c4:
    ratings_num = pd.to_numeric(df['Rating Final'].replace('—',np.nan), errors='coerce')
    st.metric("Rating Médio", f"{ratings_num.mean():.2f}" if not ratings_num.isna().all() else "—")
with c5:
    st.metric("🔴 Desmotivação", len(df[df['Termômetro'].str.contains('DESMOTIV',na=False)]))
with c6:
    st.metric("🟢 Alto Estímulo", len(df[df['Termômetro'].str.contains('ALTO ESTÍM',na=False)]))

st.markdown("---")

# ==================== TABELA POR SEÇÃO ====================

def color_gap(val):
    try:
        v = float(val)
        if v > 30: return 'background-color: rgba(255,0,0,0.25)'
        elif v > 20: return 'background-color: rgba(255,165,0,0.25)'
        elif v > 10: return 'background-color: rgba(255,255,0,0.25)'
        else: return 'background-color: rgba(0,255,0,0.15)'
    except: return ''

def color_termo(val):
    val = str(val)
    if 'ALTO ESTÍM' in val: return 'background-color: rgba(0,128,0,0.3)'
    elif 'ESTÍMULO' in val: return 'background-color: rgba(144,238,144,0.3)'
    elif 'NEUTRO' in val: return 'background-color: rgba(255,255,0,0.3)'
    elif 'BAIXO' in val: return 'background-color: rgba(255,165,0,0.3)'
    elif 'DESMOTIV' in val: return 'background-color: rgba(255,0,0,0.3)'
    return ''

def color_rating(val):
    try:
        v = float(val)
        if v <= 1.5: return 'background-color: rgba(0,128,0,0.3)'
        elif v <= 2.5: return 'background-color: rgba(144,238,144,0.3)'
        elif v <= 3.5: return 'background-color: rgba(255,255,0,0.3)'
        elif v <= 4.5: return 'background-color: rgba(255,165,0,0.3)'
        else: return 'background-color: rgba(255,0,0,0.3)'
    except: return ''

def color_ninebox(val):
    try:
        pos = int(val)
        cor = NINEBOX_CORES.get(pos,'')
        return f'background-color: {cor}' if cor else ''
    except: return ''

# Colunas base
cols_base = ['Nome','Empresa','Holding','Rodada LT']

# ── SEÇÃO 1: LEADERTRACK ──────────────────────────────
st.subheader("🎯 LeaderTrack — Arquétipos de Gestão")
cols_arq = cols_base + ['Dominantes','Suporte','Arq #1','Arq #2','Arq #3','N Resp Arq']
df_arq_show = df[[c for c in cols_arq if c in df.columns]].copy()
st.dataframe(df_arq_show, use_container_width=True, hide_index=True, height=350)

st.subheader("🏢 LeaderTrack — Microambiente de Equipes")
cols_micro = cols_base + ['Gap Geral (%)','Qtd Gaps >20%','Termômetro',
    'Gap Adaptab.','Gap Colab.','Gap Nitidez','Gap Perf.','Gap Reconh.','Gap Resp.','N Resp Micro']
df_micro_show = df[[c for c in cols_micro if c in df.columns]].copy()
styled_micro = df_micro_show.style\
    .map(color_gap, subset=[c for c in ['Gap Geral (%)','Gap Adaptab.','Gap Colab.','Gap Nitidez','Gap Perf.','Gap Reconh.','Gap Resp.'] if c in df_micro_show.columns])\
    .map(color_termo, subset=['Termômetro'] if 'Termômetro' in df_micro_show.columns else [])
st.dataframe(styled_micro, use_container_width=True, hide_index=True, height=350)

# ── SEÇÃO 2: SAÚDE EMOCIONAL ─────────────────────────
st.subheader("💚 Saúde Emocional")
st.info("ℹ️ Os dados de Saúde Emocional são derivados dos Arquétipos e Microambiente acima. Acesse o Dashboard principal para ver o score detalhado por líder.")

# ── SEÇÃO 3: AVALIAÇÃO DE DESEMPENHO ──────────────────
st.subheader("⭐ Avaliação de Desempenho")
cols_eval = cols_base + ['Round Aval.','Rating Final','Classificação','Desempenho',
    'Potencial','Avg Instit.','Avg Funcional','Avg Individual','Avg Metas']
df_eval_show = df[[c for c in cols_eval if c in df.columns]].copy()
styled_eval = df_eval_show.style\
    .map(color_rating, subset=['Rating Final'] if 'Rating Final' in df_eval_show.columns else [])
st.dataframe(styled_eval, use_container_width=True, hide_index=True, height=350)

# ── SEÇÃO 4: 9BOX ─────────────────────────────────────
st.subheader("🎯 9Box")
cols_9box = cols_base + ['Round Aval.','9Box Posição','9Box Label','Desempenho','Potencial']
df_9box_show = df[[c for c in cols_9box if c in df.columns]].copy()
styled_9box = df_9box_show.style\
    .map(color_ninebox, subset=['9Box Posição'] if '9Box Posição' in df_9box_show.columns else [])
st.dataframe(styled_9box, use_container_width=True, hide_index=True, height=350)

# Visualização matriz 9box
if not df_9box_show.empty and '9Box Posição' in df.columns:
    st.markdown("**📊 Distribuição 9Box:**")
    dist = df[df['9Box Posição'] != '—']['9Box Posição'].value_counts().sort_index()
    if not dist.empty:
        cols_9b = st.columns(3)
        posicoes_grid = [[1,2,3],[4,5,6],[7,8,9]]
        for row_idx, row_pos in enumerate(posicoes_grid):
            for col_idx, pos in enumerate(row_pos):
                qtd = dist.get(pos, 0)
                nomes_pos = df[df['9Box Posição'] == pos]['Nome'].tolist()
                label = NINEBOX_LABELS.get(pos,'—')
                with cols_9b[col_idx]:
                    cor = NINEBOX_CORES.get(pos,'rgba(200,200,200,0.3)')
                    st.markdown(f"""
                    <div style="padding:10px; border-radius:8px; background:{cor}; margin:3px; min-height:80px;">
                        <b style="font-size:12px;">{label}</b><br>
                        <span style="font-size:18px; font-weight:bold;">{qtd}</span><br>
                        <span style="font-size:10px;">{', '.join(nomes_pos[:3])}{'...' if len(nomes_pos)>3 else ''}</span>
                    </div>
                    """, unsafe_allow_html=True)

# Download geral
st.markdown("---")
cols_export = [c for c in df.columns if not c.startswith('_')]
csv = df[cols_export].to_csv(index=False, encoding='utf-8-sig')
st.download_button("📥 Download Completo CSV", data=csv, file_name="visao_executiva_completa.csv", mime="text/csv")

# ==================== DRILL-DOWN POR LÍDER ====================
st.markdown("---")
st.subheader("🔍 Detalhamento por Líder")

nomes_lideres = ["—"] + sorted(df['Nome'].unique().tolist())
lider_detail = st.selectbox("Selecione um líder:", nomes_lideres)

if lider_detail != "—":
    row = df[df['Nome'] == lider_detail].iloc[0]
    micro_data = row['_micro']
    arq_data = row['_arq']
    emp_id = row['_emp_id']

    st.markdown(f"### 👤 {row['Nome']} — {row['Empresa']} / {row['Holding']}")

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🎯 Arquétipos", "🏢 Microambiente", "⚠️ Gaps Críticos", "⭐ Avaliação", "🎯 9Box"
    ])

    with tab1:
        pcts = arq_data.get('percentuais', {})
        if pcts:
            arq_ord = sorted(pcts.items(), key=lambda x: -x[1])
            cores = ['rgba(0,128,0,0.8)' if v>=60 else 'rgba(255,165,0,0.8)' if v>=50 else 'rgba(200,200,200,0.6)' for _,v in arq_ord]
            fig = go.Figure(go.Bar(
                x=[a for a,v in arq_ord], y=[v for a,v in arq_ord],
                marker_color=cores, text=[f"{v:.1f}%" for a,v in arq_ord], textposition='auto'))
            fig.add_hline(y=60, line_dash="dash", line_color="green", annotation_text="Dominante (60%)")
            fig.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Suporte (50%)")
            fig.update_layout(title="Arquétipos - Média da Equipe", yaxis=dict(range=[0,100]), height=400)
            st.plotly_chart(fig, use_container_width=True)
            col1,col2 = st.columns(2)
            with col1: st.success(f"**Dominantes:** {', '.join(arq_data.get('dominantes',[])) or 'Nenhum'}")
            with col2: st.warning(f"**Suporte:** {', '.join(arq_data.get('suporte',[])) or 'Nenhum'}")

    with tab2:
        gap_dim = micro_data.get('gap_por_dimensao', {})
        gap_subdim = micro_data.get('gap_por_subdimensao', {})
        if gap_dim:
            col1,col2 = st.columns(2)
            with col1:
                fig2 = go.Figure(go.Bar(
                    x=list(gap_dim.values()), y=list(gap_dim.keys()), orientation='h',
                    marker_color=['rgba(255,0,0,0.7)' if v>20 else 'rgba(255,165,0,0.7)' if v>10 else 'rgba(0,128,0,0.7)' for v in gap_dim.values()],
                    text=[f"{v:.1f}%" for v in gap_dim.values()], textposition='auto'))
                fig2.update_layout(title="Gap por Dimensão", height=350)
                st.plotly_chart(fig2, use_container_width=True)
            with col2:
                fig3 = go.Figure(go.Bar(
                    x=list(gap_subdim.values()), y=list(gap_subdim.keys()), orientation='h',
                    marker_color=['rgba(255,0,0,0.7)' if v>20 else 'rgba(255,165,0,0.7)' if v>10 else 'rgba(0,128,0,0.7)' for v in gap_subdim.values()],
                    text=[f"{v:.1f}%" for v in gap_subdim.values()], textposition='auto'))
                fig3.update_layout(title="Gap por Subdimensão", height=350)
                st.plotly_chart(fig3, use_container_width=True)
            col1,col2,col3 = st.columns(3)
            with col1: st.metric("Gap Geral", f"{micro_data.get('gap_geral',0):.1f}%")
            with col2: st.metric("Gaps Críticos (>20%)", micro_data.get('qtd_gaps_criticos',0))
            with col3: st.metric("Termômetro", row['Termômetro'])

    with tab3:
        gc = micro_data.get('afirmacoes_gap_critico', [])
        ib = micro_data.get('afirmacoes_ideal_baixo', [])
        col1,col2 = st.columns(2)
        with col1:
            st.markdown(f"#### ⚠️ Gap > 20% ({len(gc)} afirmações)")
            if gc:
                df_gc = pd.DataFrame(gc)[['questao','afirmacao','dimensao','subdimensao','real','ideal','gap']]
                df_gc.columns = ['Q','Afirmação','Dimensão','Subdimensão','Real%','Ideal%','Gap']
                st.dataframe(df_gc.sort_values('Gap',ascending=False), use_container_width=True, hide_index=True)
            else:
                st.success("✅ Nenhum gap crítico!")
        with col2:
            st.markdown(f"#### 📉 Ideal < 80% ({len(ib)} afirmações)")
            if ib:
                df_ib = pd.DataFrame(ib)[['questao','afirmacao','dimensao','real','ideal','gap']]
                df_ib.columns = ['Q','Afirmação','Dimensão','Real%','Ideal%','Gap']
                st.dataframe(df_ib.sort_values('Ideal%'), use_container_width=True, hide_index=True)
            else:
                st.success("✅ Todos os ideais acima de 80%!")

    with tab4:
        if row['Rating Final'] != '—':
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("Rating Final", row['Rating Final'])
            with c2: st.metric("Classificação", row['Classificação'])
            with c3: st.metric("Desempenho", row['Desempenho'])
            with c4: st.metric("Potencial", row['Potencial'])
            st.markdown("**Médias por Dimensão:**")
            c1,c2,c3,c4 = st.columns(4)
            with c1: st.metric("Institucional", row['Avg Instit.'])
            with c2: st.metric("Funcional", row['Avg Funcional'])
            with c3: st.metric("Individual", row['Avg Individual'])
            with c4: st.metric("Metas", row['Avg Metas'])
        else:
            st.info("ℹ️ Sem dados de avaliação para este líder.")

    with tab5:
        if row['9Box Label'] != '—':
            c1,c2,c3 = st.columns(3)
            with c1: st.metric("Posição 9Box", row['9Box Posição'])
            with c2: st.metric("Label", row['9Box Label'])
            with c3: st.metric("Round", row['Round Aval.'])
        else:
            st.info("ℹ️ Sem dados de 9Box para este líder.")

# ==================== GRÁFICOS COMPARATIVOS ====================
st.markdown("---")
st.subheader("📊 Comparativos entre Líderes")

tab_c1, tab_c2, tab_c3, tab_c4 = st.tabs([
    "🎯 Arquétipos", "🏢 Microambiente", "⭐ Avaliação", "🎯 9Box"
])

with tab_c1:
    arquetipos_lista = ['Imperativo','Resoluto','Cuidativo','Consultivo','Prescritivo','Formador']
    nomes_c, vals = [], {a:[] for a in arquetipos_lista}
    for _,row in df.iterrows():
        pcts = row['_arq'].get('percentuais',{})
        if pcts:
            nomes_c.append(row['Nome'][:18] if row['Nome']!='—' else row['Email'][:18])
            for arq in arquetipos_lista:
                vals[arq].append(pcts.get(arq,0))
    if nomes_c:
        fig = go.Figure()
        cores_arq = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b']
        for i,arq in enumerate(arquetipos_lista):
            fig.add_trace(go.Bar(name=arq, x=nomes_c, y=vals[arq], marker_color=cores_arq[i]))
        fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="Dominante")
        fig.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Suporte")
        fig.update_layout(barmode='group', title="Arquétipos por Líder", yaxis=dict(range=[0,100]), height=500)
        st.plotly_chart(fig, use_container_width=True)

with tab_c2:
    nomes_m, gaps_g, qtds_c = [], [], []
    for _,row in df.iterrows():
        if row['Gap Geral (%)'] != '—':
            nomes_m.append(row['Nome'][:18] if row['Nome']!='—' else row['Email'][:18])
            gaps_g.append(float(row['Gap Geral (%)']))
            qtds_c.append(int(row['Qtd Gaps >20%']) if row['Qtd Gaps >20%']!='—' else 0)
    if nomes_m:
        col1,col2 = st.columns(2)
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
            fig3.update_layout(title="Gaps Críticos por Líder", height=400)
            st.plotly_chart(fig3, use_container_width=True)

with tab_c3:
    nomes_r, ratings_r = [], []
    for _,row in df.iterrows():
        if row['Rating Final'] != '—':
            nomes_r.append(row['Nome'][:18] if row['Nome']!='—' else row['Email'][:18])
            ratings_r.append(float(row['Rating Final']))
    if nomes_r:
        fig4 = go.Figure(go.Bar(x=nomes_r, y=ratings_r,
            marker_color=['rgba(0,128,0,0.7)' if v<=1.5 else 'rgba(144,238,144,0.7)' if v<=2.5 else 'rgba(255,255,0,0.7)' if v<=3.5 else 'rgba(255,165,0,0.7)' if v<=4.5 else 'rgba(255,0,0,0.7)' for v in ratings_r],
            text=[f"{v:.2f}" for v in ratings_r], textposition='auto'))
        fig4.add_hline(y=2.5, line_dash="dash", line_color="orange")
        fig4.update_layout(title="Rating Final por Líder (1=Excelente → 5=Insuficiente)",
            yaxis=dict(range=[0,5]), height=400)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("ℹ️ Sem dados de avaliação disponíveis para o round selecionado.")

with tab_c4:
    if '9Box Posição' in df.columns:
        df_9b = df[df['9Box Posição'] != '—'].copy()
        if not df_9b.empty:
            dist9 = df_9b['9Box Posição'].value_counts().sort_index()
            fig5 = go.Figure(go.Bar(
                x=[NINEBOX_LABELS.get(int(p),'—') for p in dist9.index],
                y=dist9.values,
                marker_color=[NINEBOX_CORES.get(int(p),'gray') for p in dist9.index],
                text=dist9.values, textposition='auto'))
            fig5.update_layout(title="Distribuição 9Box", height=400, xaxis_tickangle=-30)
            st.plotly_chart(fig5, use_container_width=True)
        else:
            st.info("ℹ️ Sem dados de 9Box para o round selecionado.")

st.markdown("---")
st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
