import streamlit as st
from supabase import create_client
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime

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
        employees = supabase.table('employees').select(
            'id,nome,email,emailLider,empresa,holding,company_name,department_name,cargo,nivel,genero,etnia'
        ).execute().data
        evaluations = supabase.table('evaluations').select(
            'employee_id,evaluation_year,final_rating,nine_box_position,performance_rating,potential_rating,dimension_averages,round_code'
        ).execute().data
        return arq, micro, employees, evaluations
    except Exception as e:
        st.error(f"Erro ao carregar dados: {e}")
        return [], [], [], []

def calcular_arquetipos_lider(consolidado_arq, matriz):
    """Calcula arquétipos dominante/suporte para cada líder"""
    arquetipos_lista = ['Imperativo', 'Resoluto', 'Cuidativo', 'Consultivo', 'Prescritivo', 'Formador']
    resultados = {}

    for item in consolidado_arq:
        if not isinstance(item, dict) or 'dados_json' not in item:
            continue
        dados = item['dados_json']
        email_lider = item.get('emaillider', '').lower()
        codrodada = item.get('codrodada', '')

        equipe = dados.get('avaliacoesEquipe', [])
        if not equipe:
            continue

        soma_por_arq = {a: 0 for a in arquetipos_lista}
        max_por_arq = {a: 0 for a in arquetipos_lista}

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
                        soma_por_arq[arq] += linha['PONTOS_OBTIDOS'].iloc[0]
                        max_por_arq[arq] += linha['PONTOS_MAXIMOS'].iloc[0]

        percentuais = {}
        for arq in arquetipos_lista:
            percentuais[arq] = round((soma_por_arq[arq] / max_por_arq[arq]) * 100, 1) if max_por_arq[arq] > 0 else 0

        dominantes = [a for a, p in percentuais.items() if p >= 60]
        suporte = [a for a, p in percentuais.items() if 50 <= p < 60]

        key = f"{email_lider}|{codrodada}"
        resultados[key] = {
            'emaillider': email_lider,
            'codrodada': codrodada,
            'percentuais': percentuais,
            'dominantes': dominantes,
            'suporte': suporte,
            'n_respondentes_arq': len(equipe)
        }

    return resultados

def calcular_gaps_microambiente(consolidado_micro, matriz_micro):
    """Calcula gaps de microambiente para cada líder"""
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
        email_lider = item.get('emaillider', '').lower()
        codrodada = item.get('codrodada', '')

        equipe = dados.get('avaliacoesEquipe', [])
        if not equipe:
            continue

        gaps_por_questao = {}
        afirmacoes_gap_critico = []
        real_baixo = []

        questoes_canonicas = matriz_micro['COD'].unique()

        for q_can in questoes_canonicas:
            q_form = REVERSO.get(q_can, q_can)
            soma_real = 0
            soma_ideal = 0
            count = 0

            for av in equipe:
                respostas = av if isinstance(av, dict) else {}
                qR = f"{q_form}C"
                qI = f"{q_form}k"
                if qR in respostas and qI in respostas:
                    try:
                        r = int(respostas[qR])
                        i = int(respostas[qI])
                    except:
                        continue
                    chave = f"{q_can}_I{i}_R{r}"
                    linha = matriz_micro[matriz_micro['CHAVE'] == chave]
                    if not linha.empty:
                        soma_real += float(linha['PONTUACAO_REAL'].iloc[0])
                        soma_ideal += float(linha['PONTUACAO_IDEAL'].iloc[0])
                        count += 1

            if count > 0:
                real_pct = round(soma_real / count, 2)
                ideal_pct = round(soma_ideal / count, 2)
                gap = round(ideal_pct - real_pct, 2)
                linhas_q = matriz_micro[matriz_micro['COD'] == q_can]
                if not linhas_q.empty:
                    dim = linhas_q.iloc[0]['DIMENSAO']
                    subdim = linhas_q.iloc[0]['SUBDIMENSAO']
                    afirmacao = linhas_q.iloc[0]['AFIRMACAO']
                    gaps_por_questao[q_can] = {
                        'real': real_pct, 'ideal': ideal_pct, 'gap': gap,
                        'dimensao': dim, 'subdimensao': subdim, 'afirmacao': afirmacao
                    }
                    if abs(gap) > 20:
                        afirmacoes_gap_critico.append({
                            'questao': q_can, 'afirmacao': afirmacao,
                            'dimensao': dim, 'subdimensao': subdim,
                            'real': real_pct, 'ideal': ideal_pct, 'gap': gap
                        })
                    if ideal_pct < 80:
                        real_baixo.append({
                            'questao': q_can, 'afirmacao': afirmacao,
                            'dimensao': dim, 'subdimensao': subdim,
                            'real': real_pct, 'ideal': ideal_pct, 'gap': gap
                        })

        # Gaps por dimensão
        gaps_dim = {}
        gaps_subdim = {}
        for q, dados_q in gaps_por_questao.items():
            dim = dados_q['dimensao']
            subdim = dados_q['subdimensao']
            if dim not in gaps_dim:
                gaps_dim[dim] = []
            gaps_dim[dim].append(dados_q['gap'])
            if subdim not in gaps_subdim:
                gaps_subdim[subdim] = []
            gaps_subdim[subdim].append(dados_q['gap'])

        gap_medio_dim = {d: round(np.mean(v), 1) for d, v in gaps_dim.items()}
        gap_medio_subdim = {s: round(np.mean(v), 1) for s, v in gaps_subdim.items()}
        gap_geral = round(np.mean([d['gap'] for d in gaps_por_questao.values()]), 1) if gaps_por_questao else 0
        qtd_gaps_criticos = len(afirmacoes_gap_critico)

        key = f"{email_lider}|{codrodada}"
        resultados[key] = {
            'emaillider': email_lider,
            'codrodada': codrodada,
            'gap_geral': gap_geral,
            'qtd_gaps_criticos': qtd_gaps_criticos,
            'gap_por_dimensao': gap_medio_dim,
            'gap_por_subdimensao': gap_medio_subdim,
            'afirmacoes_gap_critico': afirmacoes_gap_critico,
            'afirmacoes_ideal_baixo': real_baixo,
            'n_respondentes_micro': len(equipe)
        }

    return resultados

def classificar_termometro(qtd_gaps):
    if qtd_gaps <= 3: return "ALTO ESTÍMULO", "🟢"
    elif qtd_gaps <= 6: return "ESTÍMULO", "🟩"
    elif qtd_gaps <= 9: return "NEUTRO", "🟡"
    elif qtd_gaps <= 12: return "BAIXO ESTÍMULO", "🟠"
    else: return "DESMOTIVAÇÃO", "🔴"

def rating_label(rating):
    labels = {1: "⭐ Excelente", 2: "✅ Bom", 3: "🟡 Regular", 4: "🟠 Abaixo", 5: "🔴 Insuficiente"}
    return labels.get(int(rating) if rating else 0, "—")

def nine_box_label(pos):
    labels = {
        1:"🌟 Alto Pot/Alto Des", 2:"⬆️ Alto Pot/Méd Des", 3:"💎 Alto Pot/Bx Des",
        4:"🚀 Méd Pot/Alto Des", 5:"✅ Méd Pot/Méd Des", 6:"⚠️ Méd Pot/Bx Des",
        7:"💪 Bx Pot/Alto Des",  8:"📈 Bx Pot/Méd Des",  9:"🔴 Bx Pot/Bx Des"
    }
    return labels.get(int(pos) if pos else 0, "—")

# ==================== INTERFACE ====================

st.title("📊 Visão Executiva Consolidada")
st.markdown("**Análise completa de todos os líderes em uma única página**")
st.markdown("---")

# Carregar dados
with st.spinner("Carregando dados..."):
    matriz_arq = carregar_matriz_arquetipos()
    matriz_micro = carregar_matriz_microambiente()
    consolidado_arq, consolidado_micro, employees, evaluations = carregar_dados()

if not consolidado_arq or not consolidado_micro:
    st.error("❌ Dados não encontrados.")
    st.stop()

# Processar dados
with st.spinner("Calculando indicadores..."):
    dados_arq = calcular_arquetipos_lider(consolidado_arq, matriz_arq)
    dados_micro = calcular_gaps_microambiente(consolidado_micro, matriz_micro)

# Montar DataFrame de employees
df_emp = pd.DataFrame(employees) if employees else pd.DataFrame()
df_eval = pd.DataFrame(evaluations) if evaluations else pd.DataFrame()

# ==================== FILTROS ====================
st.sidebar.header("🎛️ Filtros")

# Coletar líderes únicos
lideres_arq = set(v['emaillider'] for v in dados_arq.values())
lideres_micro = set(v['emaillider'] for v in dados_micro.values())
todos_lideres = sorted(lideres_arq.union(lideres_micro))

rodadas_arq = set(v['codrodada'] for v in dados_arq.values())
rodadas_micro = set(v['codrodada'] for v in dados_micro.values())
todas_rodadas = sorted(rodadas_arq.union(rodadas_micro))

# Filtros de holding e empresa do employees
holdings = ["Todas"]
empresas = ["Todas"]
if not df_emp.empty:
    if 'holding' in df_emp.columns:
        holdings += sorted([str(h).upper() for h in df_emp['holding'].dropna().unique() if h])
    if 'empresa' in df_emp.columns:
        empresas += sorted([str(e) for e in df_emp['empresa'].dropna().unique() if e])

holding_sel = st.sidebar.selectbox("🏢 Holding", holdings)
empresa_sel = st.sidebar.selectbox("🏭 Empresa", empresas)
rodada_sel = st.sidebar.selectbox("📅 Rodada", ["Todas"] + list(todas_rodadas))
lider_sel = st.sidebar.multiselect("👤 Líder(es)", todos_lideres)

# Ano de avaliação
anos_disp = ["Todos"]
if not df_eval.empty and 'evaluation_year' in df_eval.columns:
    anos_disp += sorted([str(a) for a in df_eval['evaluation_year'].dropna().unique()], reverse=True)
ano_sel = st.sidebar.selectbox("📆 Ano Avaliação", anos_disp)

# ==================== MONTAR TABELA CONSOLIDADA ====================
linhas = []

for key, arq in dados_arq.items():
    email = arq['emaillider']
    rodada = arq['codrodada']

    # Filtro de rodada
    if rodada_sel != "Todas" and rodada != rodada_sel:
        continue
    # Filtro de líder
    if lider_sel and email not in lider_sel:
        continue

    # Dados de microambiente
    micro_key = f"{email}|{rodada}"
    micro = dados_micro.get(micro_key, {})

    # Dados do employee
    emp = {}
    if not df_emp.empty and 'emailLider' in df_emp.columns:
        emp_rows = df_emp[df_emp['emailLider'].str.lower() == email]
        if emp_rows.empty and 'email' in df_emp.columns:
            emp_rows = df_emp[df_emp['email'].str.lower() == email]
        if not emp_rows.empty:
            emp = emp_rows.iloc[0].to_dict()

    # Filtros de holding e empresa
    emp_holding = str(emp.get('holding', '')).upper() if emp else ''
    emp_empresa = str(emp.get('empresa', '')).lower() if emp else ''
    if holding_sel != "Todas" and emp_holding != holding_sel.upper():
        continue
    if empresa_sel != "Todas" and emp_empresa != empresa_sel.lower():
        continue

    # Dados de avaliação - buscar pelo email do líder na tabela employees
    eval_data = {}
    if not df_eval.empty and not df_emp.empty:
        # Encontrar employee_id do líder
        lider_emp = df_emp[df_emp['email'].str.lower() == email] if 'email' in df_emp.columns else pd.DataFrame()
        if not lider_emp.empty:
            emp_id = lider_emp.iloc[0]['id']
            evals = df_eval[df_eval['employee_id'] == emp_id]
            if ano_sel != "Todos":
                evals = evals[evals['evaluation_year'].astype(str) == ano_sel]
            if not evals.empty:
                eval_data = evals.iloc[-1].to_dict()

    # Arquétipos
    pcts = arq.get('percentuais', {})
    dominantes = arq.get('dominantes', [])
    suporte = arq.get('suporte', [])

    # Microambiente
    gap_geral = micro.get('gap_geral', None)
    qtd_gaps = micro.get('qtd_gaps_criticos', None)
    gap_dim = micro.get('gap_por_dimensao', {})
    termo_label, termo_emoji = classificar_termometro(qtd_gaps) if qtd_gaps is not None else ("—", "")

    # Rating
    final_rating = eval_data.get('final_rating', None)
    performance_rating = eval_data.get('performance_rating', None)
    nine_box = eval_data.get('nine_box_position', None)
    dim_avgs = eval_data.get('dimension_averages', {})
    if isinstance(dim_avgs, str):
        try:
            import json
            dim_avgs = json.loads(dim_avgs)
        except:
            dim_avgs = {}

    linhas.append({
        'Líder': email,
        'Rodada': rodada,
        'Empresa': emp.get('empresa', '—'),
        'Holding': emp.get('holding', '—'),
        'Nome': emp.get('nome', '—'),
        'Cargo': emp.get('cargo', '—'),
        # Arquétipos
        'Dominantes': ', '.join(dominantes) if dominantes else '—',
        'Suporte': ', '.join(suporte) if suporte else '—',
        'N Resp (Arq)': arq.get('n_respondentes_arq', 0),
        # Top 3 arquétipos
        'Top Arquétipo 1': sorted(pcts.items(), key=lambda x: -x[1])[0][0] + f" ({sorted(pcts.items(), key=lambda x: -x[1])[0][1]:.0f}%)" if pcts else '—',
        'Top Arquétipo 2': sorted(pcts.items(), key=lambda x: -x[1])[1][0] + f" ({sorted(pcts.items(), key=lambda x: -x[1])[1][1]:.0f}%)" if len(pcts) > 1 else '—',
        'Top Arquétipo 3': sorted(pcts.items(), key=lambda x: -x[1])[2][0] + f" ({sorted(pcts.items(), key=lambda x: -x[1])[2][1]:.0f}%)" if len(pcts) > 2 else '—',
        # Microambiente
        'Gap Geral (%)': gap_geral if gap_geral is not None else '—',
        'Qtd Gaps > 20%': qtd_gaps if qtd_gaps is not None else '—',
        'Termômetro': f"{termo_emoji} {termo_label}" if micro else '—',
        'N Resp (Micro)': micro.get('n_respondentes_micro', 0),
        # Gaps por dimensão
        'Gap Adaptabilidade': gap_dim.get('Adaptabilidade', '—'),
        'Gap Colaboração Mútua': gap_dim.get('Colaboração Mútua', '—'),
        'Gap Nitidez': gap_dim.get('Nitidez', '—'),
        'Gap Performance': gap_dim.get('Performance', '—'),
        'Gap Reconhecimento': gap_dim.get('Reconhecimento', '—'),
        'Gap Responsabilidade': gap_dim.get('Responsabilidade', '—'),
        # Avaliação
        'Rating Final': f"{final_rating:.2f}" if final_rating else '—',
        'Rating Label': rating_label(final_rating) if final_rating else '—',
        'Performance Rating': f"{performance_rating:.1f}" if performance_rating else '—',
        '9Box': nine_box_label(nine_box) if nine_box else '—',
        'Avg Institucional': f"{dim_avgs.get('INSTITUCIONAL', '—'):.2f}" if dim_avgs.get('INSTITUCIONAL') else '—',
        'Avg Funcional': f"{dim_avgs.get('FUNCIONAL', '—'):.2f}" if dim_avgs.get('FUNCIONAL') else '—',
        'Avg Individual': f"{dim_avgs.get('INDIVIDUAL', '—'):.2f}" if dim_avgs.get('INDIVIDUAL') else '—',
        'Avg Metas': f"{dim_avgs.get('METAS', '—'):.2f}" if dim_avgs.get('METAS') else '—',
        # Ref
        '_micro_data': micro,
        '_arq_data': arq,
    })

df = pd.DataFrame(linhas)

if df.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
    st.stop()

# ==================== MÉTRICAS GERAIS ====================
st.subheader(f"📈 Visão Geral — {len(df)} líder(es)")
c1, c2, c3, c4, c5 = st.columns(5)
with c1:
    gap_medio = df[df['Gap Geral (%)'] != '—']['Gap Geral (%)'].mean() if not df[df['Gap Geral (%)'] != '—'].empty else 0
    st.metric("Gap Médio Geral", f"{gap_medio:.1f}%")
with c2:
    qtd_media = pd.to_numeric(df['Qtd Gaps > 20%'].replace('—', np.nan), errors='coerce').mean()
    st.metric("Média Gaps Críticos", f"{qtd_media:.1f}" if not np.isnan(qtd_media) else "—")
with c3:
    ratings = pd.to_numeric(df['Rating Final'].replace('—', np.nan), errors='coerce')
    st.metric("Rating Médio", f"{ratings.mean():.2f}" if not ratings.isna().all() else "—")
with c4:
    lideres_desmot = df[df['Termômetro'].str.contains('DESMOTIV', na=False)]
    st.metric("🔴 Desmotivação", len(lideres_desmot))
with c5:
    lideres_excelente = df[df['Termômetro'].str.contains('ALTO ESTÍM', na=False)]
    st.metric("🟢 Alto Estímulo", len(lideres_excelente))

st.markdown("---")

# ==================== TABELA PRINCIPAL ====================
st.subheader("📋 Tabela Consolidada por Líder")

# Colunas para exibir
colunas_exibir = [
    'Nome', 'Empresa', 'Holding', 'Rodada',
    'Dominantes', 'Suporte', 'Top Arquétipo 1', 'Top Arquétipo 2',
    'Gap Geral (%)', 'Qtd Gaps > 20%', 'Termômetro',
    'Gap Adaptabilidade', 'Gap Colaboração Mútua', 'Gap Nitidez',
    'Gap Performance', 'Gap Reconhecimento', 'Gap Responsabilidade',
    'Rating Final', 'Rating Label', '9Box',
    'Avg Institucional', 'Avg Funcional', 'Avg Individual', 'Avg Metas',
    'N Resp (Arq)', 'N Resp (Micro)'
]

df_exibir = df[[c for c in colunas_exibir if c in df.columns]].copy()

# Colorir coluna Termômetro
def color_termometro(val):
    if 'ALTO ESTÍM' in str(val): return 'background-color: rgba(0,128,0,0.3)'
    elif 'ESTÍMULO' in str(val): return 'background-color: rgba(144,238,144,0.3)'
    elif 'NEUTRO' in str(val): return 'background-color: rgba(255,255,0,0.3)'
    elif 'BAIXO' in str(val): return 'background-color: rgba(255,165,0,0.3)'
    elif 'DESMOTIV' in str(val): return 'background-color: rgba(255,0,0,0.3)'
    return ''

def color_gap(val):
    try:
        v = float(val)
        if v > 30: return 'background-color: rgba(255,0,0,0.3)'
        elif v > 20: return 'background-color: rgba(255,165,0,0.3)'
        elif v > 10: return 'background-color: rgba(255,255,0,0.3)'
        else: return 'background-color: rgba(0,255,0,0.2)'
    except: return ''

def color_rating(val):
    try:
        v = float(val)
        if v <= 1.5: return 'background-color: rgba(0,128,0,0.4)'
        elif v <= 2.5: return 'background-color: rgba(144,238,144,0.4)'
        elif v <= 3.5: return 'background-color: rgba(255,255,0,0.4)'
        elif v <= 4.5: return 'background-color: rgba(255,165,0,0.4)'
        else: return 'background-color: rgba(255,0,0,0.4)'
    except: return ''

styled = df_exibir.style\
    .map(color_termometro, subset=['Termômetro'] if 'Termômetro' in df_exibir.columns else [])\
    .map(color_gap, subset=[c for c in ['Gap Geral (%)', 'Gap Adaptabilidade', 'Gap Colaboração Mútua', 'Gap Nitidez', 'Gap Performance', 'Gap Reconhecimento', 'Gap Responsabilidade'] if c in df_exibir.columns])\
    .map(color_rating, subset=['Rating Final'] if 'Rating Final' in df_exibir.columns else [])

st.dataframe(styled, use_container_width=True, hide_index=True, height=400)

# Download
csv = df_exibir.to_csv(index=False, encoding='utf-8-sig')
st.download_button("📥 Download CSV - Visão Executiva", data=csv, file_name="visao_executiva.csv", mime="text/csv")

st.markdown("---")

# ==================== DRILL-DOWN POR LÍDER ====================
st.subheader("🔍 Detalhamento por Líder")

lider_detail = st.selectbox("Selecione um líder para ver detalhes:", 
    ["—"] + list(df['Líder'].unique()))

if lider_detail != "—":
    row = df[df['Líder'] == lider_detail].iloc[0]
    micro_data = row.get('_micro_data', {})
    arq_data = row.get('_arq_data', {})

    st.markdown(f"### 👤 {row['Nome']} — {row['Empresa']} / {row['Holding']}")
    
    tab_arq, tab_micro, tab_gaps, tab_eval = st.tabs([
        "📊 Arquétipos", "🏢 Microambiente", "⚠️ Gaps Críticos", "⭐ Avaliação"
    ])

    with tab_arq:
        pcts = arq_data.get('percentuais', {})
        if pcts:
            fig = go.Figure()
            arquetipos_ord = sorted(pcts.items(), key=lambda x: -x[1])
            cores = ['rgba(0,128,0,0.8)' if v >= 60 else 'rgba(255,165,0,0.8)' if v >= 50 else 'rgba(200,200,200,0.6)' for _, v in arquetipos_ord]
            fig.add_trace(go.Bar(
                x=[a for a, v in arquetipos_ord],
                y=[v for a, v in arquetipos_ord],
                marker_color=cores,
                text=[f"{v:.1f}%" for a, v in arquetipos_ord],
                textposition='auto'
            ))
            fig.add_hline(y=60, line_dash="dash", line_color="green", annotation_text="Dominante (60%)")
            fig.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Suporte (50%)")
            fig.update_layout(title="Arquétipos - Média da Equipe", yaxis=dict(range=[0,100]), height=400)
            st.plotly_chart(fig, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.success(f"**Dominantes (≥60%):** {', '.join(arq_data.get('dominantes', [])) or 'Nenhum'}")
            with col2:
                st.warning(f"**Suporte (50-59%):** {', '.join(arq_data.get('suporte', [])) or 'Nenhum'}")

    with tab_micro:
        gap_dim = micro_data.get('gap_por_dimensao', {})
        gap_subdim = micro_data.get('gap_por_subdimensao', {})
        if gap_dim:
            col1, col2 = st.columns(2)
            with col1:
                fig_dim = go.Figure(go.Bar(
                    x=list(gap_dim.values()),
                    y=list(gap_dim.keys()),
                    orientation='h',
                    marker_color=['rgba(255,0,0,0.7)' if v > 20 else 'rgba(255,165,0,0.7)' if v > 10 else 'rgba(0,128,0,0.7)' for v in gap_dim.values()],
                    text=[f"{v:.1f}%" for v in gap_dim.values()],
                    textposition='auto'
                ))
                fig_dim.update_layout(title="Gap por Dimensão", height=350)
                st.plotly_chart(fig_dim, use_container_width=True)
            with col2:
                fig_sub = go.Figure(go.Bar(
                    x=list(gap_subdim.values()),
                    y=list(gap_subdim.keys()),
                    orientation='h',
                    marker_color=['rgba(255,0,0,0.7)' if v > 20 else 'rgba(255,165,0,0.7)' if v > 10 else 'rgba(0,128,0,0.7)' for v in gap_subdim.values()],
                    text=[f"{v:.1f}%" for v in gap_subdim.values()],
                    textposition='auto'
                ))
                fig_sub.update_layout(title="Gap por Subdimensão", height=350)
                st.plotly_chart(fig_sub, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            with col1: st.metric("Gap Geral", f"{micro_data.get('gap_geral', 0):.1f}%")
            with col2: st.metric("Gaps Críticos (>20%)", micro_data.get('qtd_gaps_criticos', 0))
            with col3: st.metric("Termômetro", row['Termômetro'])

    with tab_gaps:
        gaps_criticos = micro_data.get('afirmacoes_gap_critico', [])
        ideal_baixo = micro_data.get('afirmacoes_ideal_baixo', [])
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"### ⚠️ Afirmações com Gap > 20% ({len(gaps_criticos)})")
            if gaps_criticos:
                df_gc = pd.DataFrame(gaps_criticos)[['questao', 'afirmacao', 'dimensao', 'subdimensao', 'real', 'ideal', 'gap']]
                df_gc.columns = ['Questão', 'Afirmação', 'Dimensão', 'Subdimensão', 'Real (%)', 'Ideal (%)', 'Gap']
                df_gc = df_gc.sort_values('Gap', ascending=False)
                st.dataframe(df_gc, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Nenhum gap crítico!")
        
        with col2:
            st.markdown(f"### 📉 Afirmações com Ideal < 80% ({len(ideal_baixo)})")
            if ideal_baixo:
                df_ib = pd.DataFrame(ideal_baixo)[['questao', 'afirmacao', 'dimensao', 'real', 'ideal', 'gap']]
                df_ib.columns = ['Questão', 'Afirmação', 'Dimensão', 'Real (%)', 'Ideal (%)', 'Gap']
                df_ib = df_ib.sort_values('Ideal (%)')
                st.dataframe(df_ib, use_container_width=True, hide_index=True)
            else:
                st.success("✅ Todos os ideais acima de 80%!")

    with tab_eval:
        if row['Rating Final'] != '—':
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Rating Final", row['Rating Final'])
            with col2: st.metric("Classificação", row['Rating Label'])
            with col3: st.metric("9Box", row['9Box'])
            with col4: st.metric("Performance", row['Performance Rating'])
            
            st.markdown("**📊 Médias por Dimensão:**")
            col1, col2, col3, col4 = st.columns(4)
            with col1: st.metric("Institucional", row['Avg Institucional'])
            with col2: st.metric("Funcional", row['Avg Funcional'])
            with col3: st.metric("Individual", row['Avg Individual'])
            with col4: st.metric("Metas", row['Avg Metas'])
        else:
            st.info("ℹ️ Sem dados de avaliação para este líder.")

st.markdown("---")

# ==================== GRÁFICOS COMPARATIVOS ====================
st.subheader("📊 Comparativos entre Líderes")

tab_comp1, tab_comp2, tab_comp3 = st.tabs(["🏆 Arquétipos", "⚡ Gaps Microambiente", "⭐ Ratings"])

with tab_comp1:
    arquetipos_lista = ['Imperativo', 'Resoluto', 'Cuidativo', 'Consultivo', 'Prescritivo', 'Formador']
    nomes = []
    valores_por_arq = {a: [] for a in arquetipos_lista}
    for _, row in df.iterrows():
        pcts = row['_arq_data'].get('percentuais', {})
        if pcts:
            nomes.append(row['Nome'][:20] if row['Nome'] != '—' else row['Líder'][:20])
            for arq in arquetipos_lista:
                valores_por_arq[arq].append(pcts.get(arq, 0))
    if nomes:
        fig = go.Figure()
        cores_arq = ['#1f77b4','#ff7f0e','#2ca02c','#d62728','#9467bd','#8c564b']
        for i, arq in enumerate(arquetipos_lista):
            fig.add_trace(go.Bar(name=arq, x=nomes, y=valores_por_arq[arq], marker_color=cores_arq[i]))
        fig.add_hline(y=60, line_dash="dash", line_color="red", annotation_text="Dominante")
        fig.add_hline(y=50, line_dash="dash", line_color="orange", annotation_text="Suporte")
        fig.update_layout(barmode='group', title="Arquétipos por Líder", yaxis=dict(range=[0,100]), height=500)
        st.plotly_chart(fig, use_container_width=True)

with tab_comp2:
    nomes2 = []
    gaps_gerais = []
    qtds_criticos = []
    for _, row in df.iterrows():
        if row['Gap Geral (%)'] != '—':
            nomes2.append(row['Nome'][:20] if row['Nome'] != '—' else row['Líder'][:20])
            gaps_gerais.append(float(row['Gap Geral (%)']))
            qtds_criticos.append(int(row['Qtd Gaps > 20%']) if row['Qtd Gaps > 20%'] != '—' else 0)
    if nomes2:
        col1, col2 = st.columns(2)
        with col1:
            fig2 = go.Figure(go.Bar(x=nomes2, y=gaps_gerais,
                marker_color=['rgba(255,0,0,0.7)' if v > 20 else 'rgba(255,165,0,0.7)' if v > 10 else 'rgba(0,128,0,0.7)' for v in gaps_gerais],
                text=[f"{v:.1f}%" for v in gaps_gerais], textposition='auto'))
            fig2.update_layout(title="Gap Médio Geral por Líder", height=400)
            st.plotly_chart(fig2, use_container_width=True)
        with col2:
            fig3 = go.Figure(go.Bar(x=nomes2, y=qtds_criticos,
                marker_color=['rgba(255,0,0,0.7)' if v > 12 else 'rgba(255,165,0,0.7)' if v > 6 else 'rgba(0,128,0,0.7)' for v in qtds_criticos],
                text=[str(v) for v in qtds_criticos], textposition='auto'))
            fig3.update_layout(title="Quantidade de Gaps Críticos por Líder", height=400)
            st.plotly_chart(fig3, use_container_width=True)

with tab_comp3:
    nomes3 = []
    ratings3 = []
    for _, row in df.iterrows():
        if row['Rating Final'] != '—':
            nomes3.append(row['Nome'][:20] if row['Nome'] != '—' else row['Líder'][:20])
            ratings3.append(float(row['Rating Final']))
    if nomes3:
        fig4 = go.Figure(go.Bar(x=nomes3, y=ratings3,
            marker_color=['rgba(0,128,0,0.7)' if v <= 1.5 else 'rgba(144,238,144,0.7)' if v <= 2.5 else 'rgba(255,255,0,0.7)' if v <= 3.5 else 'rgba(255,165,0,0.7)' if v <= 4.5 else 'rgba(255,0,0,0.7)' for v in ratings3],
            text=[f"{v:.2f}" for v in ratings3], textposition='auto'))
        fig4.add_hline(y=2.5, line_dash="dash", line_color="orange", annotation_text="Bom/Regular")
        fig4.update_layout(title="Rating Final por Líder (1=Excelente, 5=Insuficiente)", 
            yaxis=dict(range=[0,5], autorange='reversed'), height=400)
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.info("ℹ️ Sem dados de avaliação disponíveis.")

st.markdown("---")
st.caption(f"Atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
