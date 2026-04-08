import streamlit as st
from supabase import create_client, Client
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import openpyxl

# === Configuração global ===
NORMALIZAR_POR_SUBDIMENSAO = False

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


# Limpar cache
st.cache_data.clear()

st.set_page_config(page_title="🎯 LeaderTrack Dashboard", page_icon="", layout="wide")

SUPABASE_URL = "https://xmsjjknpnowsswwrbvpc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtc2pqa25wbm93c3N3d3JidnBjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MDg0NDUsImV4cCI6MjA2ODA4NDQ0NX0.OexXJX7lK_DefGb72VDWGLDcUXamoQIgYOv5Zo_e9L4"

@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

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
    for item in consolidado_arq:
        if isinstance(item, dict) and 'dados_json' in item:
            dados = item['dados_json']
            if 'autoavaliacao' in dados and 'respostas' in dados['autoavaliacao']:
                auto = dados['autoavaliacao']
                arquétipos_auto = calcular_arquetipos_respondente(auto['respostas'], matriz)
                respondentes_processados.append({
                    'empresa': auto.get('empresa', 'N/A'),
                    'codrodada': auto.get('codrodada', 'N/A'),
                    'emailLider': auto.get('emailLider', 'N/A'),
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
                    'respostas': auto['respostas']
                })
            if 'avaliacoesEquipe' in dados:
                for membro in dados['avaliacoesEquipe']:
                    if 'respostas' in membro:
                        arquétipos_equipe = calcular_arquetipos_respondente(membro['respostas'], matriz)
                        respondentes_processados.append({
                            'empresa': membro.get('empresa', 'N/A'),
                            'codrodada': membro.get('codrodada', 'N/A'),
                            'emailLider': membro.get('emailLider', 'N/A'),
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
                            'respostas': membro['respostas']
                        })
    return pd.DataFrame(respondentes_processados)


def processar_dados_microambiente(consolidado_micro, matriz, pontos_max_dimensao, pontos_max_subdimensao):
    respondentes_processados = []
    for item in consolidado_micro:
        if isinstance(item, dict) and 'dados_json' in item:
            dados = item['dados_json']
            if 'autoavaliacao' in dados:
                auto = dados['autoavaliacao']
                dimensoes_real, dimensoes_ideal, subdimensoes_real, subdimensoes_ideal = calcular_microambiente_respondente(auto, matriz, pontos_max_dimensao, pontos_max_subdimensao)
                respondentes_processados.append({
                    'empresa': auto.get('empresa', ''),
                    'codrodada': auto.get('codrodada', ''),
                    'emailLider': auto.get('emailLider', ''),
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
                    'respostas': auto
                })
            if 'avaliacoesEquipe' in dados:
                for membro in dados['avaliacoesEquipe']:
                    dimensoes_real, dimensoes_ideal, subdimensoes_real, subdimensoes_ideal = calcular_microambiente_respondente(membro, matriz, pontos_max_dimensao, pontos_max_subdimensao)
                    respondentes_processados.append({
                        'empresa': membro.get('empresa', ''),
                        'codrodada': membro.get('codrodada', ''),
                        'emailLider': membro.get('emailLider', ''),
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
                        'respostas': membro
                    })
    return pd.DataFrame(respondentes_processados)


# ==================== CALCULAR MÉDIAS COM FILTROS ====================

def calcular_medias_arquetipos(df_respondentes, filtros):
    df_filtrado = df_respondentes.copy()
    if filtros['empresa'] != "Todas":
        df_filtrado = df_filtrado[df_filtrado['empresa'] == filtros['empresa']]
    if filtros['codrodada'] != "Todas":
        df_filtrado = df_filtrado[df_filtrado['codrodada'] == filtros['codrodada']]
    if filtros['emaillider'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['emailLider'] == filtros['emaillider']]
    if filtros['estado'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['estado'] == filtros['estado']]
    if filtros['sexo'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['sexo'] == filtros['sexo']]
    if filtros['etnia'] != "Todas":
        df_filtrado = df_filtrado[df_filtrado['etnia'] == filtros['etnia']]
    if filtros['departamento'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['departamento'] == filtros['departamento']]
    if filtros['cargo'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['cargo'] == filtros['cargo']]
    if 'holding' in filtros and filtros['holding'] != "Todas":
        if 'holding' in df_filtrado.columns:
            holding_filtro = str(filtros['holding']).upper().strip()
            df_filtrado = df_filtrado[df_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro]
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
    if filtros['empresa'] != "Todas":
        df_filtrado = df_filtrado[df_filtrado['empresa'] == filtros['empresa']]
    if filtros['codrodada'] != "Todas":
        df_filtrado = df_filtrado[df_filtrado['codrodada'] == filtros['codrodada']]
    if filtros['emaillider'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['emailLider'] == filtros['emaillider']]
    if filtros['estado'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['estado'] == filtros['estado']]
    if filtros['sexo'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['sexo'] == filtros['sexo']]
    if filtros['etnia'] != "Todas":
        df_filtrado = df_filtrado[df_filtrado['etnia'] == filtros['etnia']]
    if filtros['departamento'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['departamento'] == filtros['departamento']]
    if filtros['cargo'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['cargo'] == filtros['cargo']]
    if 'holding' in filtros and filtros['holding'] != "Todas":
        if 'holding' in df_filtrado.columns:
            holding_filtro = str(filtros['holding']).upper().strip()
            df_filtrado = df_filtrado[df_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro]
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

def adicionar_holding_ao_dataframe(df, email_to_holding):
    holdings = []
    for _, row in df.iterrows():
        email = str(row.get('email', '')).lower()
        empresa = str(row.get('empresa', '')).lower()
        holding = email_to_holding.get(email, None)
        if holding:
            holding = str(holding).upper().strip()
        if not holding:
            holding = email_to_holding.get(empresa, None)
            if holding:
                holding = str(holding).upper().strip()
        if not holding:
            if empresa in ['astro34', 'spectral_v', 'spectral_a', 'spectral_sales', 'fastco', 'futurex'] or \
               any(x in empresa for x in ['astro34', 'spectral', 'fastco', 'futurex']):
                holding = 'PROSPERA'
            else:
                holding = empresa.upper() if empresa else 'N/A'
        holdings.append(str(holding).upper().strip() if holding else 'N/A')
    df['holding'] = holdings
    return df


@st.cache_data(ttl=300)
def fetch_data():
    try:
        supabase = init_supabase()
        consolidado_arq = supabase.table('consolidado_arquetipos').select('*').execute()
        consolidado_micro = supabase.table('consolidado_microambiente').select('*').execute()
        return consolidado_arq.data, consolidado_micro.data
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {str(e)}")
        return [], []


# ==================== INTERFACE PRINCIPAL ====================

st.title("🎯 LeaderTrack Dashboard")
st.markdown("---")

with st.spinner("Carregando matrizes..."):
    matriz_arq = carregar_matriz_arquetipos()
    matriz_micro, pontos_max_dimensao, pontos_max_subdimensao = carregar_matrizes_microambiente()

if matriz_arq is not None and matriz_micro is not None:
    with st.spinner("Carregando dados dos respondentes..."):
        consolidado_arq, consolidado_micro = fetch_data()

    if consolidado_arq and consolidado_micro:
        st.success("✅ Conectado ao Supabase!")

        with st.spinner("Carregando dados de holding..."):
            try:
                supabase = init_supabase()
                employees_data = None
                try:
                    employees_data = supabase.table('employees').select('email, holding, empresa').execute()
                except:
                    try:
                        employees_data = supabase.table('employees').select('holding, empresa').execute()
                    except:
                        try:
                            employees_data = supabase.table('employees').select('holding').execute()
                        except:
                            employees_data = supabase.table('employees').select('*').execute()
                email_to_holding = {}
                if employees_data and employees_data.data:
                    for emp in employees_data.data:
                        email = emp.get('email', '').lower() if emp.get('email') else ''
                        holding = str(emp.get('holding', 'N/A')).upper().strip()
                        empresa = emp.get('empresa', '')
                        if email:
                            email_to_holding[email] = holding
                        if empresa:
                            empresa_lower = empresa.lower()
                            if empresa_lower not in email_to_holding:
                                email_to_holding[empresa_lower] = holding
            except Exception as e:
                st.warning(f"⚠️ Aviso: Não foi possível carregar dados de holding: {str(e)}")
                email_to_holding = {}

        with st.spinner("Calculando arquétipos individuais..."):
            df_arquetipos = processar_dados_arquetipos(consolidado_arq, matriz_arq)
            df_arquetipos = adicionar_holding_ao_dataframe(df_arquetipos, email_to_holding)

        with st.spinner("Calculando microambiente individual..."):
            df_microambiente = processar_dados_microambiente(consolidado_micro, matriz_micro, pontos_max_dimensao, pontos_max_subdimensao)
            df_microambiente = adicionar_holding_ao_dataframe(df_microambiente, email_to_holding)

        # Normalizar campos
        for col in ['empresa', 'codrodada', 'emailLider', 'estado', 'sexo', 'etnia', 'departamento', 'cargo']:
            df_arquetipos[col] = df_arquetipos[col].astype(str).str.lower()
            df_microambiente[col] = df_microambiente[col].astype(str).str.lower()
        if 'holding' in df_arquetipos.columns:
            df_arquetipos['holding'] = df_arquetipos['holding'].astype(str).str.upper()
        if 'holding' in df_microambiente.columns:
            df_microambiente['holding'] = df_microambiente['holding'].astype(str).str.upper()

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

        holdings_arq = set(df_arquetipos['holding'].dropna().unique()) if 'holding' in df_arquetipos.columns else set()
        holdings_micro = set(df_microambiente['holding'].dropna().unique()) if 'holding' in df_microambiente.columns else set()
        todas_holdings = [h for h in sorted([str(h) for h in holdings_arq.union(holdings_micro)]) if h and str(h).strip() and str(h).upper() != 'N/A']
        holdings = ["Todas"] + todas_holdings
        holding_selecionada = st.sidebar.selectbox("🏢 Holding", holdings) if len(holdings) > 1 else "Todas"

        todas_empresas = sorted([str(e) for e in set(df_arquetipos['empresa'].unique()).union(set(df_microambiente['empresa'].unique()))])
        empresa_selecionada = st.sidebar.selectbox("Empresa", ["Todas"] + todas_empresas)

        todas_codrodadas = sorted([str(c) for c in set(df_arquetipos['codrodada'].unique()).union(set(df_microambiente['codrodada'].unique()))])
        codrodada_selecionada = st.sidebar.selectbox("Código da Rodada", ["Todas"] + todas_codrodadas)

        todos_emailliders = sorted([str(e) for e in set(df_arquetipos['emailLider'].unique()).union(set(df_microambiente['emailLider'].unique()))])
        emaillider_selecionado = st.sidebar.selectbox("👤 Email do Líder", ["Todos"] + todos_emailliders)

        todos_estados = sorted([str(e) for e in set(df_arquetipos['estado'].unique()).union(set(df_microambiente['estado'].unique()))])
        estado_selecionado = st.sidebar.selectbox("🗺️ Estado", ["Todos"] + todos_estados)

        todos_generos = sorted([str(g) for g in set(df_arquetipos['sexo'].unique()).union(set(df_microambiente['sexo'].unique()))])
        genero_selecionado = st.sidebar.selectbox("⚧ Gênero", ["Todos"] + todos_generos)

        todas_etnias = sorted([str(e) for e in set(df_arquetipos['etnia'].unique()).union(set(df_microambiente['etnia'].unique()))])
        etnia_selecionada = st.sidebar.selectbox("Etnia", ["Todas"] + todas_etnias)

        todos_departamentos = sorted([str(d) for d in set(df_arquetipos['departamento'].unique()).union(set(df_microambiente['departamento'].unique()))])
        departamento_selecionado = st.sidebar.selectbox("🏢 Departamento", ["Todos"] + todos_departamentos)

        todos_cargos = sorted([str(c) for c in set(df_arquetipos['cargo'].unique()).union(set(df_microambiente['cargo'].unique()))])
        cargo_selecionado = st.sidebar.selectbox("💼 Cargo", ["Todos"] + todos_cargos)

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

        tab1, tab2, tab3 = st.tabs(["📊 Arquétipos", "🏢 Microambiente", "💚 Saúde Emocional"])

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
                        df_arq_filtrado, matriz_arq, codigo, arquétipo
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
                                    df_arq_filtrado, matriz_arq, codigo, arquétipo)
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
                        df_arq_filtrado, matriz_arq, codigo, arquétipo)
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

            if score_final >= 80: interpretacao, cor_score = "🟢 EXCELENTE - acima de 80%", "green"
            elif score_final >= 75: interpretacao, cor_score = "🟢 ÓTIMO - entre 75% e 79,99%", "darkgreen"
            elif score_final >= 70: interpretacao, cor_score = "🟡 BOM - entre 70% e 74,99%", "orange"
            elif score_final >= 60: interpretacao, cor_score = "🟠 REGULAR - entre 60% e 69,99%", "darkorange"
            else: interpretacao, cor_score = "🔴 NÃO ADEQUADO - abaixo de 60%", "red"

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
                    <tr><td style="padding: 4px;">≥ 80%</td><td style="padding: 4px;">Excelente</td><td style="padding: 4px;">Ambiente saudável de excelência</td></tr>
                    <tr><td style="padding: 4px;">75% a 79,99%</td><td style="padding: 4px;">Ótimo</td><td style="padding: 4px;">Ambiente saudável</td></tr>
                    <tr><td style="padding: 4px;">70% a 74,99%</td><td style="padding: 4px;">Bom</td><td style="padding: 4px;">Ambiente saudável com pontos a melhorar</td></tr>
                    <tr><td style="padding: 4px;">60% a 69,99%</td><td style="padding: 4px;">Regular</td><td style="padding: 4px;">Ambiente necessita melhorias</td></tr>
                    <tr><td style="padding: 4px;">&lt; 60%</td><td style="padding: 4px;">Não Adequado</td><td style="padding: 4px;">Ambiente necessita apoio em plano de ação (PDI)</td></tr>
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
                        df_arq_filtrado, matriz_arq, codigo, arquétipo)
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

        if not afirmacoes_saude_emocional:
            st.warning("⚠️ Nenhuma afirmação relacionada à saúde emocional foi identificada.")
