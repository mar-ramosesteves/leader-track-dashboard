import streamlit as st
from supabase import create_client
import pandas as pd
import numpy as np

st.set_page_config(page_title="🔍 Diagnóstico SE", layout="wide")
st.title("🔍 Diagnóstico Saúde Emocional")

SUPABASE_URL = "https://xmsjjknpnowsswwrbvpc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtc2pqa25wbm93c3N3d3JidnBjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MDg0NDUsImV4cCI6MjA2ODA4NDQ0NX0.OexXJX7lK_DefGb72VDWGLDcUXamoQIgYOv5Zo_e9L4"

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

EMAIL = "marcelo.esteves@fastco.pro"
RODADA = "av1225"

st.subheader(f"Testando: {EMAIL} / {RODADA}")

# Carregar dados
micro_data = supabase.table('consolidado_microambiente').select('*').execute().data
matriz_micro = pd.read_excel('TABELA_GERAL_MICROAMBIENTE_COM_CHAVE.xlsx')

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

# Encontrar registro do Marcelo
encontrado = False
for item in micro_data:
    if not isinstance(item, dict) or 'dados_json' not in item:
        continue
    el = item.get('emaillider','').lower().strip()
    cr = item.get('codrodada','')
    if el == EMAIL and cr == RODADA:
        encontrado = True
        dados = item['dados_json']
        equipe = dados.get('avaliacoesEquipe', [])
        st.success(f"✅ Registro encontrado! Equipe: {len(equipe)} respondentes")

        # Testar Q48 canônico
        # Q48 canônico → form Q09
        q_can = 'Q48'
        q_form = REVERSO.get(q_can, q_can)
        st.write(f"**Q48 canônico → form: {q_form}**")
        st.write(f"Buscando: `{q_form}C` e `{q_form}k`")

        soma_real = soma_ideal = count = 0
        rows = []
        for av in equipe:
            qR, qI = f"{q_form}C", f"{q_form}k"
            nome = av.get('nome', '?')
            if qR in av and qI in av:
                r, i = int(av[qR]), int(av[qI])
                chave = f"{q_can}_I{i}_R{r}"
                linha = matriz_micro[matriz_micro['CHAVE'] == chave]
                if not linha.empty:
                    real = float(linha['PONTUACAO_REAL'].iloc[0])
                    ideal = float(linha['PONTUACAO_IDEAL'].iloc[0])
                    soma_real += real
                    soma_ideal += ideal
                    count += 1
                    rows.append({'Nome': nome, 'Real': r, 'Ideal': i, 'Chave': chave, 'Pont.Real': real, 'Pont.Ideal': ideal})
                else:
                    rows.append({'Nome': nome, 'Real': r, 'Ideal': i, 'Chave': chave, 'Pont.Real': 'NÃO ENCONTRADO', 'Pont.Ideal': ''})
            else:
                rows.append({'Nome': nome, 'Real': f'{q_form}C não encontrado', 'Ideal': '', 'Chave': '', 'Pont.Real': '', 'Pont.Ideal': ''})

        st.dataframe(pd.DataFrame(rows), use_container_width=True)

        if count > 0:
            real_pct = soma_real/count
            ideal_pct = soma_ideal/count
            gap = ideal_pct - real_pct
            score = max(0, 100-gap)
            st.metric("Real%", f"{real_pct:.1f}%")
            st.metric("Ideal%", f"{ideal_pct:.1f}%")
            st.metric("Gap", f"{gap:.1f}%")
            st.metric("Score", f"{score:.1f}%")
            st.info(f"Dashboard mostra: gap=3% → score=97%")
        break

if not encontrado:
    st.error(f"❌ Registro NÃO encontrado para {EMAIL} / {RODADA}")
    st.write("Registros disponíveis:")
    for item in micro_data:
        if isinstance(item, dict):
            el = item.get('emaillider','')
            cr = item.get('codrodada','')
            st.write(f"- `{el}` / `{cr}`")
