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
NORMALIZAR_POR_SUBDIMENSAO = False  # deixa sempre False para mostrar valores brutos por questão


# ==================== FUNÇÕES SAÚDE EMOCIONAL ====================

# ==================== FUNÇÕES SAÚDE EMOCIONAL ====================

# ANALISAR AFIRMAÇÕES EXISTENTES PARA SAÚDE EMOCIONAL (COM FILTROS)
def analisar_afirmacoes_saude_emocional(matriz_arq, matriz_micro, df_arquetipos, df_microambiente, filtros):
    """
    Lê a TABELA_SAUDE_EMOCIONAL.csv e usa ESSA tabela como única
    fonte de verdade para:
      - quais afirmações entram em Saúde Emocional (97 no total)
      - a dimensão de saúde emocional de cada afirmação
    """
    import pandas as pd
    import os

    # 1. Carregar CSV NOVO
    arquivo_csv = 'TABELA_SAUDE_EMOCIONAL.csv'

    if not os.path.exists(arquivo_csv):
        st.error(f"❌ CSV não encontrado: {arquivo_csv}")
        return [], df_arquetipos, df_microambiente

    # Atenção: separador ';'
    df_csv = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig')

    # Normalizar colunas
    df_csv['TIPO'] = df_csv['TIPO'].astype(str).str.strip().str.upper()
    df_csv['COD_AFIRMACAO'] = df_csv['COD_AFIRMACAO'].astype(str).str.strip()
    df_csv['DIMENSAO_SAUDE_EMOCIONAL'] = (
        df_csv['DIMENSAO_SAUDE_EMOCIONAL']
        .astype(str)
        .str.strip()
        .replace({'Equilíbrio Vida- Trabalho': 'Equilíbrio Vida-Trabalho'})
    )

    # Debug opcional: ver total e distribuição (somar = 97)
    st.info(f"✅ CSV de Saúde Emocional carregado: {len(df_csv)} afirmações (esperado: 97)")
    contagem_dim = df_csv['DIMENSAO_SAUDE_EMOCIONAL'].value_counts().sort_index()
    st.write("📋 Distribuição por dimensão (TABELA_SAUDE_EMOCIONAL):")
    for dim, qtd in contagem_dim.items():
        st.write(f"- {dim}: {qtd} afirmações")

    # 2. Aplicar filtros aos dados de respostas (mantendo sua lógica atual)
    df_arq_filtrado = df_arquetipos.copy()
    df_micro_filtrado = df_microambiente.copy()




    
    if filtros['empresa'] != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['empresa'] == filtros['empresa']]
    if filtros['codrodada'] != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['codrodada'] == filtros['codrodada']]
    
    # ✅ FILTRO DE LÍDER (estava faltando)
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
            df_arq_filtrado = df_arq_filtrado[
                df_arq_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro
            ]

    # Mesmos filtros para microambiente
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
            df_micro_filtrado = df_micro_filtrado[
                df_micro_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro
            ]

    # 3. Criar dicionário TIPO + CÓDIGO -> dimensão de saúde emocional
    # Ex.: ARQUETIPOS + Q01 -> 'Prevenção de Estresse'
    csv_dict = {}
    for _, row in df_csv.iterrows():
        tipo = row['TIPO']           # ARQUETIPOS / MICROAMBIENTE
        codigo = row['COD_AFIRMACAO']
        dimensao_se = row['DIMENSAO_SAUDE_EMOCIONAL']

        tipo = str(tipo).upper().strip()
        codigo = str(codigo).strip()

        if tipo.startswith('ARQ'):          # ARQUETIPOS
            tipo_codigo = f"arq_{codigo}"
        elif tipo.startswith('MICRO'):      # MICROAMBIENTE
            tipo_codigo = f"micro_{codigo}"
        else:
            # se algum dia vier outro tipo, ignora
            continue

        csv_dict[tipo_codigo] = dimensao_se

    # 4. Montar lista de afirmações de saúde emocional (apenas o que estiver no CSV)
    afirmacoes_se = []
    codigos_processados = set()

    # Arquétipos
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

    # Microambiente
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
    
# MAPEAR COMPLIANCE COM NR-1
def mapear_compliance_nr1(afirmacoes_saude_emocional):
    """Mapeia as afirmações identificadas com os requisitos da NR-1 + adendo saúde mental"""
    
    # Requisitos da NR-1 + adendo saúde mental (baseado na legislação atual)
    requisitos_nr1 = {
        'Prevenção de Estresse': [],
        'Ambiente Psicológico Seguro': [],
        'Suporte Emocional': [],
        'Comunicação Positiva': [],
        'Equilíbrio Vida-Trabalho': []
    }
    
    # Mapear afirmações usando a dimensão de saúde emocional do CSV
    for afirmacao in afirmacoes_saude_emocional:
        dimensao_se = afirmacao.get('dimensao_saude_emocional', 'Suporte Emocional')
        
        # Adicionar à categoria correspondente
        if dimensao_se in requisitos_nr1:
            requisitos_nr1[dimensao_se].append(afirmacao)
        else:
            # Fallback para Suporte Emocional se não encontrar
            requisitos_nr1['Suporte Emocional'].append(afirmacao)
    
    return requisitos_nr1

# Limpar cache para forçar atualização
st.cache_data.clear()

# Configuração da página
st.set_page_config(
    page_title="🎯 LeaderTrack Dashboard",
    page_icon="",
    layout="wide"
)

# Configurações do Supabase
SUPABASE_URL = "https://xmsjjknpnowsswwrbvpc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtc2pqa25wbm93c3N3d3JidnBjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MDg0NDUsImV4cCI6MjA2ODA4NDQ0NX0.OexXJX7lK_DefGb72VDWGLDcUXamoQIgYOv5Zo_e9L4"

# Inicializar cliente Supabase
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ==================== CARREGAR CLASSIFICAÇÕES DE SAÚDE EMOCIONAL ====================
@st.cache_data(ttl=3600)
@st.cache_data(ttl=3600)
def carregar_classificacoes_saude_emocional():
    """
    Carrega as classificações das 97 afirmações de saúde emocional
    USANDO a TABELA_SAUDE_EMOCIONAL.csv como fonte única.
    Retorna um dicionário de chaves:
      - "arq_Q01", "micro_Q10" etc. -> dimensão
      - "Q01" (fallback simples)    -> dimensão
    """
    import os

    arquivo_csv = 'TABELA_SAUDE_EMOCIONAL.csv'
    caminho_completo = os.path.abspath(arquivo_csv)

    try:
        if not os.path.exists(arquivo_csv):
            st.error("❌ **ARQUIVO NÃO ENCONTRADO!**")
            st.error(f"📁 Procurando em: `{caminho_completo}`")
            st.error(f"💡 Certifique-se de que o arquivo `{arquivo_csv}` está no mesmo diretório que `app.py`")
            return {}

        df_classificacoes = pd.read_csv(arquivo_csv, sep=';', encoding='utf-8-sig')

        # Normalizar colunas
        df_classificacoes['TIPO'] = df_classificacoes['TIPO'].astype(str).str.strip().str.upper()
        df_classificacoes['COD_AFIRMACAO'] = df_classificacoes['COD_AFIRMACAO'].astype(str).str.strip()
        df_classificacoes['DIMENSAO_SAUDE_EMOCIONAL'] = (
            df_classificacoes['DIMENSAO_SAUDE_EMOCIONAL']
            .astype(str)
            .str.strip()
            .replace({'Equilíbrio Vida- Trabalho': 'Equilíbrio Vida-Trabalho'})
        )

        st.success("✅ **TABELA_SAUDE_EMOCIONAL.csv carregada com sucesso!**")
        st.info(f"📊 Total de linhas no CSV: {len(df_classificacoes)}")

        classificacoes = {}

        for _, row in df_classificacoes.iterrows():
            tipo = row['TIPO']
            codigo = row['COD_AFIRMACAO']
            dimensao = row['DIMENSAO_SAUDE_EMOCIONAL']

            tipo = str(tipo).upper().strip()
            codigo = str(codigo).strip()

            # chave composta
            if tipo.startswith('ARQ'):
                tipo_codigo = f"arq_{codigo}"
            elif tipo.startswith('MICRO'):
                tipo_codigo = f"micro_{codigo}"
            else:
                tipo_codigo = codigo  # se algum dia vier outro tipo

            classificacoes[tipo_codigo] = dimensao

            # chave simples como fallback (Q01, Q02, ...)
            if codigo not in classificacoes:
                classificacoes[codigo] = dimensao

        # Debug: distribuição por dimensão
        contagem_dim = df_classificacoes['DIMENSAO_SAUDE_EMOCIONAL'].value_counts().sort_index()
        st.info("📋 **Distribuição por dimensão (TABELA_SAUDE_EMOCIONAL):**")
        for dim, qtd in contagem_dim.items():
            st.write(f"  - {dim}: {qtd} afirmações")

        st.info(f"🔑 **Total de chaves no dicionário:** {len(classificacoes)}")

        return classificacoes

    except Exception as e:
        st.error(f"❌ **ERRO ao carregar classificações:** {str(e)}")
        st.error(f"📁 Tentando carregar de: `{caminho_completo}`")
        import traceback
        st.code(traceback.format_exc())
        return {}

# ==================== FUNÇÕES ARQUÉTIPOS ====================

# CARREGAR MATRIZ DE ARQUÉTIPOS
@st.cache_data(ttl=3600)
def carregar_matriz_arquetipos():
    """Carrega a matriz de arquétipos do Excel"""
    try:
        matriz = pd.read_excel('TABELA_GERAL_ARQUETIPOS_COM_CHAVE.xlsx')
        return matriz
    except Exception as e:
        st.error(f"❌ Erro ao carregar matriz de arquétipos: {str(e)}")
        return None

# CALCULAR ARQUÉTIPOS PARA UM RESPONDENTE
def calcular_arquetipos_respondente(respostas, matriz):
    """Calcula percentuais de arquétipos para um respondente individual"""
    
    arquétipos = ['Imperativo', 'Resoluto', 'Cuidativo', 'Consultivo', 'Prescritivo', 'Formador']
    pontos_por_arquétipo = {arq: 0 for arq in arquétipos}
    pontos_maximos_por_arquétipo = {arq: 0 for arq in arquétipos}
    
    # Para cada questão respondida
    for questao, estrelas in respostas.items():
        if questao.startswith('Q'):
            estrelas_int = int(estrelas)
            
            # Para cada arquétipo
            for arquétipo in arquétipos:
                # Gerar chave: ARQUETIPO + ESTRELAS + QUESTAO
                chave = f"{arquétipo}{estrelas_int}{questao}"
                
                # Buscar na matriz
                linha = matriz[matriz['CHAVE'] == chave]
                if not linha.empty:
                    pontos_obtidos = linha['PONTOS_OBTIDOS'].iloc[0]
                    pontos_maximos = linha['PONTOS_MAXIMOS'].iloc[0]
                    
                    pontos_por_arquétipo[arquétipo] += pontos_obtidos
                    pontos_maximos_por_arquétipo[arquétipo] += pontos_maximos
    
    # Calcular percentuais
    arquétipos_percentuais = {}
    for arquétipo in arquétipos:
        pontos_total = pontos_por_arquétipo[arquétipo]
        pontos_maximos = pontos_maximos_por_arquétipo[arquétipo]
        
        percentual = (pontos_total / pontos_maximos) * 100 if pontos_maximos > 0 else 0
        arquétipos_percentuais[arquétipo] = percentual
    
    return arquétipos_percentuais

# ==================== FUNÇÕES MICROAMBIENTE ====================

# CARREGAR MATRIZES DE MICROAMBIENTE
@st.cache_data(ttl=3600)
def carregar_matrizes_microambiente():
    """Carrega matrizes de microambiente do Excel"""
    try:
        matriz = pd.read_excel('TABELA_GERAL_MICROAMBIENTE_COM_CHAVE.xlsx')
        pontos_max_dimensao = pd.read_excel('pontos_maximos_dimensao_microambiente.xlsx')
        pontos_max_subdimensao = pd.read_excel('pontos_maximos_subdimensao_microambiente.xlsx')
        return matriz, pontos_max_dimensao, pontos_max_subdimensao
    except Exception as e:
        st.error(f"❌ Erro ao carregar matrizes de microambiente: {str(e)}")
        return None, None, None

# CALCULAR MICROAMBIENTE PARA UM RESPONDENTE (CORRIGIDA)
# CALCULAR MICROAMBIENTE PARA UM RESPONDENTE (CORRIGIDA COM ARREDONDAMENTO)
# CALCULAR MICROAMBIENTE PARA UM RESPONDENTE (CORRIGIDA COM ARREDONDAMENTO)
def calcular_microambiente_respondente(respostas, matriz, pontos_max_dimensao, pontos_max_subdimensao):
    """Calcula percentuais de microambiente para um respondente individual"""
    
    # MAPEAMENTO CORRETO DAS QUESTÕES (igual aos gráficos)
    MAPEAMENTO_QUESTOES = {
        'Q01': 'Q01',  # COD Q01 = Questão 1
        'Q02': 'Q12',  # COD Q02 = Questão 12  
        'Q03': 'Q23',  # COD Q03 = Questão 23
        'Q04': 'Q34',  # COD Q04 = Questão 34
        'Q05': 'Q44',  # COD Q05 = Questão 44
        'Q06': 'Q45',  # COD Q06 = Questão 45
        'Q07': 'Q46',  # COD Q07 = Questão 46
        'Q08': 'Q47',  # COD Q08 = Questão 47
        'Q09': 'Q48',  # COD Q09 = Questão 48
        'Q10': 'Q02',  # COD Q10 = Questão 2
        'Q11': 'Q03',  # COD Q11 = Questão 3
        'Q12': 'Q04',  # COD Q12 = Questão 4
        'Q13': 'Q05',  # COD Q13 = Questão 5
        'Q14': 'Q06',  # COD Q14 = Questão 6
        'Q15': 'Q07',  # COD Q15 = Questão 7
        'Q16': 'Q08',  # COD Q16 = Questão 8
        'Q17': 'Q09',  # COD Q17 = Questão 9
        'Q18': 'Q10',  # COD Q18 = Questão 10
        'Q19': 'Q11',  # COD Q19 = Questão 11
        'Q20': 'Q13',  # COD Q20 = Questão 13
        'Q21': 'Q14',  # COD Q21 = Questão 14
        'Q22': 'Q15',  # COD Q22 = Questão 15 (Performance) ✅
        'Q23': 'Q16',  # COD Q23 = Questão 16
        'Q24': 'Q17',  # COD Q24 = Questão 17
        'Q25': 'Q18',  # COD Q25 = Questão 18
        'Q26': 'Q19',  # COD Q26 = Questão 19
        'Q27': 'Q20',  # COD Q27 = Questão 20
        'Q28': 'Q21',  # COD Q28 = Questão 21
        'Q29': 'Q22',  # COD Q29 = Questão 22
        'Q30': 'Q24',  # COD Q30 = Questão 24
        'Q31': 'Q25',  # COD Q31 = Questão 25
        'Q32': 'Q26',  # COD Q32 = Questão 26
        'Q33': 'Q27',  # COD Q33 = Questão 27
        'Q34': 'Q28',  # COD Q34 = Questão 28
        'Q35': 'Q29',  # COD Q35 = Questão 29
        'Q36': 'Q30',  # COD Q36 = Questão 30
        'Q37': 'Q31',  # COD Q37 = Questão 31
        'Q38': 'Q32',  # COD Q38 = Questão 32
        'Q39': 'Q33',  # COD Q39 = Questão 33
        'Q40': 'Q35',  # COD Q40 = Questão 35
        'Q41': 'Q36',  # COD Q41 = Questão 36
        'Q42': 'Q37',  # COD Q42 = Questão 37
        'Q43': 'Q38',  # COD Q43 = Questão 38
        'Q44': 'Q39',  # COD Q44 = Questão 39
        'Q45': 'Q40',  # COD Q45 = Questão 40
        'Q46': 'Q41',  # COD Q46 = Questão 41
        'Q47': 'Q42',  # COD Q47 = Questão 42
        'Q48': 'Q43'   # COD Q48 = Questão 43
    }
    
    dimensoes = ['Adaptabilidade', 'Colaboração Mútua', 'Nitidez', 'Performance', 'Reconhecimento', 'Responsabilidade']
    subdimensoes = [
        'Criação', 'Simplificação de Processos', 'Credibilidade Recíproca', 'Dedicação', 'Parceria', 
        'Satisfação em Fazer Parte', 'Obrigações e Deveres', 'Propósito e Objetivo', 'Aprimoramento', 
        'Qualidade Superior', 'Celebração', 'Performance', 'Liberdade de Ação', 'Responsabilização'
    ]
    
    # Separar respostas Real (C) e Ideal (k)
    respostas_real = {}
    respostas_ideal = {}

    for questao, estrelas in respostas.items():
        if questao.startswith('Q'):
            if questao.endswith('C'):  # Como é (Real)
                questao_num = questao[:-1]  # Remove o 'C'
                respostas_real[questao_num] = int(estrelas)
            elif questao.endswith('k'):  # Como deveria ser (Ideal)
                questao_num = questao[:-1]  # Remove o 'k'
                respostas_ideal[questao_num] = int(estrelas)
    
    # Calcular pontos por dimensão (Real)
    pontos_por_dimensao_real = {dim: 0 for dim in dimensoes}
    pontos_por_subdimensao_real = {sub: 0 for sub in subdimensoes}
    
    # Calcular pontos por dimensão (Ideal)
    pontos_por_dimensao_ideal = {dim: 0 for dim in dimensoes}
    pontos_por_subdimensao_ideal = {sub: 0 for sub in subdimensoes}
    
    # Processar respostas com combinação Real + Ideal
    for questao in respostas_real:
        if questao in respostas_ideal:
            estrelas_real = respostas_real[questao]
            estrelas_ideal = respostas_ideal[questao]
            
            # Chave com combinação Real + Ideal (usando mapeamento)
            questao_mapeada = MAPEAMENTO_QUESTOES.get(questao, questao)
            chave_original = f"{questao}_I{estrelas_ideal}_R{estrelas_real}"
            chave_transformada = f"{questao_mapeada}_I{estrelas_ideal}_R{estrelas_real}"
            linha = matriz[matriz['CHAVE'] == chave_transformada]
            
            
            
            
            if not linha.empty:
                dimensao = linha['DIMENSAO'].iloc[0]
                subdimensao = linha['SUBDIMENSAO'].iloc[0]
                pontos_real = linha['PONTUACAO_REAL'].iloc[0]
                pontos_ideal = linha['PONTUACAO_IDEAL'].iloc[0]
                
                pontos_por_dimensao_real[dimensao] += pontos_real
                pontos_por_dimensao_ideal[dimensao] += pontos_ideal
                pontos_por_subdimensao_real[subdimensao] += pontos_real
                pontos_por_subdimensao_ideal[subdimensao] += pontos_ideal
    
    # Calcular percentuais por dimensão (Real)
    dimensoes_percentuais_real = {}
    for dimensao in dimensoes:
        pontos_total = pontos_por_dimensao_real[dimensao]
        pontos_maximos = pontos_max_dimensao[pontos_max_dimensao['DIMENSAO'] == dimensao]['PONTOS_MAXIMOS_DIMENSAO'].iloc[0]
        percentual = (pontos_total / pontos_maximos) * 100 if pontos_maximos > 0 else 0
        dimensoes_percentuais_real[dimensao] = percentual
    
    # Calcular percentuais por dimensão (Ideal)
    dimensoes_percentuais_ideal = {}
    for dimensao in dimensoes:
        pontos_total = pontos_por_dimensao_ideal[dimensao]
        pontos_maximos = pontos_max_dimensao[pontos_max_dimensao['DIMENSAO'] == dimensao]['PONTOS_MAXIMOS_DIMENSAO'].iloc[0]
        percentual = (pontos_total / pontos_maximos) * 100 if pontos_maximos > 0 else 0
        dimensoes_percentuais_ideal[dimensao] = percentual
    
    # Calcular percentuais por subdimensão (Real)
    subdimensoes_percentuais_real = {}
    for subdimensao in subdimensoes:
        pontos_total = pontos_por_subdimensao_real[subdimensao]
        pontos_maximos = pontos_max_subdimensao[pontos_max_subdimensao['SUBDIMENSAO'] == subdimensao]['PONTOS_MAXIMOS_SUBDIMENSAO'].iloc[0]
        percentual = (pontos_total / pontos_maximos) * 100 if pontos_maximos > 0 else 0
        subdimensoes_percentuais_real[subdimensao] = percentual
    
    # Calcular percentuais por subdimensão (Ideal)
    subdimensoes_percentuais_ideal = {}
    for subdimensao in subdimensoes:
        pontos_total = pontos_por_subdimensao_ideal[subdimensao]
        pontos_maximos = pontos_max_subdimensao[pontos_max_subdimensao['SUBDIMENSAO'] == subdimensao]['PONTOS_MAXIMOS_SUBDIMENSAO'].iloc[0]
        percentual = (pontos_total / pontos_maximos) * 100 if pontos_maximos > 0 else 0
        subdimensoes_percentuais_ideal[subdimensao] = percentual
    
    return (dimensoes_percentuais_real, dimensoes_percentuais_ideal, 
            subdimensoes_percentuais_real, subdimensoes_percentuais_ideal)
    

# ==================== FUNÇÕES COMPARTILHADAS ====================

# ==== MAPAS GLOBAIS FORM <-> MATRIZ (usados em microambiente e saúde emocional) ====
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
    Calcula Real, Ideal e Gap (Ideal-Real) para UMA questão usando a MATRIZ:
    - média das PONTUAÇÕES (% 0–100) por respondente
    - codigo_matriz: ex. 'Q45' (código canônico da MATRIZ)
    Retorna (real_pct, ideal_pct, gap_pct) ou (None, None, None) se não houver dados.
    """
    # código usado no JSON (FORM)
    codigo_form = _MAP_MATRIZ_TO_FORM.get(codigo_matriz, codigo_matriz)

    estrelas_real, estrelas_ideal = [], []
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
            estrelas_real.append(r)
            estrelas_ideal.append(i)

    if not estrelas_real or not estrelas_ideal:
        return None, None, None

    media_real  = float(np.mean(estrelas_real))
    media_ideal = float(np.mean(estrelas_ideal))
    real_pct  = round((media_real  / 6) * 100, 2)
    ideal_pct = round((media_ideal / 6) * 100, 2)
    gap       = round(ideal_pct - real_pct, 2)
    return real_pct, ideal_pct, gap


# PROCESSAR DADOS INDIVIDUAIS (ARQUÉTIPOS) - CORRIGIDA COM NOMES CORRETOS
def processar_dados_arquetipos(consolidado_arq, matriz):
    """Processa todos os respondentes e calcula arquétipos"""
    
    respondentes_processados = []
    
    for item in consolidado_arq:
        if isinstance(item, dict) and 'dados_json' in item:
            dados = item['dados_json']
            
            # Processar autoavaliação
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
                    'tipo': 'Autoavaliação',  # Nome padronizado
                    'arquétipos': arquétipos_auto,
                    'respostas': auto['respostas']
                })
            
            # Processar avaliações da equipe
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
                            'tipo': 'Avaliação Equipe',  # Nome padronizado
                            'arquétipos': arquétipos_equipe,
                            'respostas': membro['respostas']
                        })
    
    return pd.DataFrame(respondentes_processados)

    # ==== HELPERS PARA REAL/IDEAL/GAP por questão (usando a MATRIZ, valor bruto 0–100) ====
    
    # Mapa do FORM -> MATRIZ e inverso (mesmo usado no microambiente)
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
        Calcula Real, Ideal e Gap (Ideal-Real) para UMA questão usando a MATRIZ:
        - média das PONTUAÇÕES (% 0–100) por respondente
        - codigo_matriz: ex. 'Q45' (código canônico da MATRIZ)
        Retorna (real_pct, ideal_pct, gap_pct) ou (None, None, None) se não houver dados.
        """
        # código usado no JSON (FORM)
        codigo_form = _MAP_MATRIZ_TO_FORM.get(codigo_matriz, codigo_matriz)
    
        estrelas_real, estrelas_ideal = [], []
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
            estrelas_real.append(r)
            estrelas_ideal.append(i)

    if not estrelas_real or not estrelas_ideal:
        return None, None, None

    media_real  = float(np.mean(estrelas_real))
    media_ideal = float(np.mean(estrelas_ideal))
    real_pct  = round((media_real  / 6) * 100, 2)
    ideal_pct = round((media_ideal / 6) * 100, 2)
    gap       = round(ideal_pct - real_pct, 2)
    return real_pct, ideal_pct, gap


# PROCESSAR DADOS APENAS DA EQUIPE (MICROAMBIENTE)
# PROCESSAR DADOS INDIVIDUAIS (MICROAMBIENTE) - CORRIGIDA COM NOMES CORRETOS
def processar_dados_microambiente(consolidado_micro, matriz, pontos_max_dimensao, pontos_max_subdimensao):
    """Processa todos os respondentes e calcula microambiente"""
    
    respondentes_processados = []
    
    for item in consolidado_micro:
        if isinstance(item, dict) and 'dados_json' in item:
            
            dados = item['dados_json']
            
            
            # Processar autoavaliação
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
            
            # Processar avaliações da equipe
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


# CALCULAR MÉDIAS COM FILTROS (ARQUÉTIPOS) - ATUALIZADA
def calcular_medias_arquetipos(df_respondentes, filtros):
    """Aplica filtros demográficos e calcula médias dos arquétipos"""
    
    df_filtrado = df_respondentes.copy()
    
    # Aplicar filtros
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
            # Normalizar para comparação (ambos em maiúsculas)
            holding_filtro = str(filtros['holding']).upper().strip()
            df_filtrado = df_filtrado[df_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro]
    
    # Separar autoavaliação e equipe
    df_auto = df_filtrado[df_filtrado['tipo'] == 'Autoavaliação']
    df_equipe = df_filtrado[df_filtrado['tipo'] == 'Avaliação Equipe']
    
    arquétipos = ['Imperativo', 'Resoluto', 'Cuidativo', 'Consultivo', 'Prescritivo', 'Formador']
    
    # Calcular médias de autoavaliação
    medias_auto = []
    for arq in arquétipos:
        valores = []
        for _, row in df_auto.iterrows():
            if 'arquétipos' in row and isinstance(row['arquétipos'], dict) and arq in row['arquétipos']:
                valores.append(row['arquétipos'][arq])
        media = np.mean(valores) if valores else 0
        medias_auto.append(media)
    
    # Calcular médias da equipe
    medias_equipe = []
    for arq in arquétipos:
        valores = []
        for _, row in df_equipe.iterrows():
            if 'arquétipos' in row and isinstance(row['arquétipos'], dict) and arq in row['arquétipos']:
                valores.append(row['arquétipos'][arq])
        media = np.mean(valores) if valores else 0
        medias_equipe.append(media)
    
    return arquétipos, medias_auto, medias_equipe, df_filtrado


# CALCULAR MÉDIAS COM FILTROS (MICROAMBIENTE) - CORRIGIDA
def calcular_medias_microambiente(df_respondentes, filtros):
    """Aplica filtros demográficos e calcula médias do microambiente"""
    
   
    
    df_filtrado = df_respondentes.copy()
    
    # Aplicar filtros
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
            # Normalizar para comparação (ambos em maiúsculas)
            holding_filtro = str(filtros['holding']).upper().strip()
            df_filtrado = df_filtrado[df_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro]
    
    # Separar autoavaliação e equipe
    df_auto = df_filtrado[df_filtrado['tipo'] == 'Autoavaliação']
    df_equipe = df_filtrado[df_filtrado['tipo'] == 'Avaliação Equipe']
    
    
    
    dimensoes = ['Adaptabilidade', 'Colaboração Mútua', 'Nitidez', 'Performance', 'Reconhecimento', 'Responsabilidade']
    subdimensoes = [
        'Criação', 'Simplificação de Processos', 'Credibilidade Recíproca', 'Dedicação', 'Parceria', 
        'Satisfação em Fazer Parte', 'Obrigações e Deveres', 'Propósito e Objetivo', 'Aprimoramento', 
        'Qualidade Superior', 'Celebração', 'Performance', 'Liberdade de Ação', 'Responsabilização'
    ]
    
    # Calcular médias de autoavaliação (Real)
    medias_real = []
    for dim in dimensoes:
        valores = []
        for _, row in df_auto.iterrows():
            if 'dimensoes_real' in row and isinstance(row['dimensoes_real'], dict) and dim in row['dimensoes_real']:
                valores.append(row['dimensoes_real'][dim])
        media = np.mean(valores) if valores else 0
        medias_real.append(media)
    
    # Calcular médias de autoavaliação (Ideal)
    medias_ideal = []
    for dim in dimensoes:
        valores = []
        for _, row in df_auto.iterrows():
            if 'dimensoes_ideal' in row and isinstance(row['dimensoes_ideal'], dict) and dim in row['dimensoes_ideal']:
                valores.append(row['dimensoes_ideal'][dim])
        media = np.mean(valores) if valores else 0
        medias_ideal.append(media)
    
    # Calcular médias da equipe (Real) - CORRIGIDO
    medias_equipe_real = []
    for dim in dimensoes:
        valores = []
        for _, row in df_equipe.iterrows():
            if 'dimensoes_real' in row and isinstance(row['dimensoes_real'], dict) and dim in row['dimensoes_real']:
                valores.append(row['dimensoes_real'][dim])
        media = np.mean(valores) if valores else 0
        medias_equipe_real.append(media)
        
        
    
    # Calcular médias da equipe (Ideal) - CORRIGIDO
    medias_equipe_ideal = []
    for dim in dimensoes:
        valores = []
        for _, row in df_equipe.iterrows():
            if 'dimensoes_ideal' in row and isinstance(row['dimensoes_ideal'], dict) and dim in row['dimensoes_ideal']:
                valores.append(row['dimensoes_ideal'][dim])
        media = np.mean(valores) if valores else 0
        medias_equipe_ideal.append(media)
    
    # Calcular médias de subdimensões da equipe (Real) - CORRIGIDO
    medias_subdimensoes_equipe_real = []
    for sub in subdimensoes:
        valores = []
        for _, row in df_equipe.iterrows():
            if 'subdimensoes_real' in row and isinstance(row['subdimensoes_real'], dict) and sub in row['subdimensoes_real']:
                valores.append(row['subdimensoes_real'][sub])
        media = np.mean(valores) if valores else 0
        medias_subdimensoes_equipe_real.append(media)
        
        
    
    # Calcular médias de subdimensões da equipe (Ideal) - CORRIGIDO
    medias_subdimensoes_equipe_ideal = []
    for sub in subdimensoes:
        valores = []
        for _, row in df_equipe.iterrows():
            if 'subdimensoes_ideal' in row and isinstance(row['subdimensoes_ideal'], dict) and sub in row['subdimensoes_ideal']:
                valores.append(row['subdimensoes_ideal'][sub])
        media = np.mean(valores) if valores else 0
        medias_subdimensoes_equipe_ideal.append(media)
    
    return dimensoes, medias_real, medias_ideal, medias_equipe_real, medias_equipe_ideal, medias_subdimensoes_equipe_real, medias_subdimensoes_equipe_ideal, df_filtrado
    

# ==================== FUNÇÕES DE GRÁFICOS ====================

# GERAR GRÁFICO ARQUÉTIPOS
def gerar_grafico_arquetipos(medias_auto, medias_equipe, arquétipos, titulo, tipo_visualizacao):
    """Gera gráfico comparativo de arquétipos"""
    
    if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique":
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Autoavaliação',
            x=arquétipos,
            y=medias_auto,
            marker_color='#1f77b4',
            text=[f"{v:.1f}%" for v in medias_auto],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Autoavaliação: %{y:.1f}%<br><extra>Clique para ver questões!</extra>',
            customdata=arquétipos
        ))
        
        fig.add_trace(go.Bar(
            name='Média da Equipe',
            x=arquétipos,
            y=medias_equipe,
            marker_color='#ff7f0e',
            text=[f"{v:.1f}%" for v in medias_equipe],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Média da Equipe: %{y:.1f}%<br><extra>Clique para ver questões!</extra>',
            customdata=arquétipos
        ))
        
        # Adicionar linhas horizontais fixas
        fig.add_hline(y=50, line_dash="dash", line_color="orange", 
                      annotation_text="Suporte (50%)", 
                      annotation_position="right",
                      line_width=2)
        
        fig.add_hline(y=60, line_dash="dash", line_color="red", 
                      annotation_text="Dominante (60%)", 
                      annotation_position="right",
                      line_width=2)
        
        fig.update_layout(
            title=f"📊 {titulo}",
            xaxis_title="Arquétipos",
            yaxis_title="Pontuação (%)",
            yaxis=dict(range=[0, 100]),
            barmode='group',
            height=600,
            hovermode='closest',
            showlegend=True,
            clickmode='event+select'
        )
    else:
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Autoavaliação',
            x=arquétipos,
            y=medias_auto,
            marker_color='#1f77b4',
            hovertemplate='<b>%{x}</b><br>Autoavaliação: %{y:.1f}%<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='Média da Equipe',
            x=arquétipos,
            y=medias_equipe,
            marker_color='#ff7f0e',
            hovertemplate='<b>%{x}</b><br>Média da Equipe: %{y:.1f}%<extra></extra>'
        ))
        
        # Adicionar linhas horizontais fixas
        fig.add_hline(y=50, line_dash="dash", line_color="orange", 
                      annotation_text="Suporte (50%)", 
                      annotation_position="right",
                      line_width=2)
        
        fig.add_hline(y=60, line_dash="dash", line_color="red", 
                      annotation_text="Dominante (60%)", 
                      annotation_position="right",
                      line_width=2)
        
        fig.update_layout(
            title=f"📈 {titulo}",
            xaxis_title="Arquétipos",
            yaxis_title="Pontuação (%)",
            yaxis=dict(range=[0, 100]),
            barmode='group',
            height=500,
            hovermode='closest',
            showlegend=True
        )
    
    return fig

# GERAR GRÁFICO MICROAMBIENTE
def gerar_grafico_microambiente_linha(medias_real, medias_ideal, dimensoes, titulo):
    """Gera gráfico de linha para microambiente"""
    
    
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dimensoes,
        y=medias_real,
        mode='lines+markers+text',
        name='Como é (Real)',
        line=dict(color='orange', width=3),
        marker=dict(size=8),
        text=[f"{v:.1f}%" for v in medias_real],
        textposition='top center'
    ))
    
    fig.add_trace(go.Scatter(
        x=dimensoes,
        y=medias_ideal,
        mode='lines+markers+text',
        name='Como deveria ser (Ideal)',
        line=dict(color='darkblue', width=3),
        marker=dict(size=8),
        text=[f"{v:.1f}%" for v in medias_ideal],
        textposition='bottom center'
    ))
    
    fig.update_layout(
        title=f"   {titulo}",
        xaxis_title="Dimensões",
        yaxis_title="Pontuação (%)",
        yaxis=dict(range=[0, 100]),
        height=500
    )
    
    return fig
# ==================== FUNÇÕES DE DRILL-DOWN ====================

# DRILL-DOWN ARQUÉTIPOS (CORRIGIDA)
def gerar_drill_down_arquetipos(arquétipo_clicado, df_respondentes_filtrado, matriz):
    """Gera detalhamento das questões de arquétipos"""
    
    # Identificar questões de impacto (onde PONTOS_MAXIMOS = 200)
    questoes_impacto = matriz[
        (matriz['ARQUETIPO'] == arquétipo_clicado) & 
        (matriz['PONTOS_MAXIMOS'] == 200)
    ]['COD_AFIRMACAO'].unique().tolist()
    
    if not questoes_impacto:
        return None
    
    questoes_detalhadas = []
    
    for questao in questoes_impacto:
        # Buscar afirmação na matriz
        linha_questao = matriz[matriz['COD_AFIRMACAO'] == questao].iloc[0]
        afirmacao = linha_questao['AFIRMACAO']
        
        # Calcular média de estrelas para esta questão
        estrelas_questao = []
        for _, respondente in df_respondentes_filtrado.iterrows():
            if 'respostas' in respondente and questao in respondente['respostas']:
                estrelas = int(respondente['respostas'][questao])
                estrelas_questao.append(estrelas)
        
        if estrelas_questao:
            # Calcular média e arredondar
            
            media_estrelas = np.mean(estrelas_questao)
            media_arredondada = round(media_estrelas)
            percentual_calculado = round((media_estrelas / 6) * 100, 2)
            
            # Buscar tendência baseado na média arredondada (apenas para o texto da tendência)
            chave = f"{arquétipo_clicado}{media_arredondada}{questao}"
            linha = matriz[matriz['CHAVE'] == chave]
            tendencia_percentual = percentual_calculado if not linha.empty else 0
            tendencia_info = linha['Tendência'].iloc[0] if not linha.empty else 'N/A'
            
            # CALCULAR VALOR PARA O GRÁFICO (negativo para desfavorável, positivo para favorável)
            if 'DESFAVORÁVEL' in tendencia_info:
                valor_grafico = -tendencia_percentual  # Negativo para desfavorável
            else:
                valor_grafico = tendencia_percentual   # Positivo para favorável
            
            questoes_detalhadas.append({
                'questao': questao,
                'afirmacao': afirmacao,
                'media_estrelas': media_estrelas,
                'media_arredondada': media_arredondada,
                'tendencia': tendencia_percentual,
                'tendencia_info': tendencia_info,
                'valor_grafico': valor_grafico,  # ADICIONAR ESTA LINHA
                'n_respostas': len(estrelas_questao)
            })
    
    # Ordenar por % tendência (maior para menor)
    questoes_detalhadas.sort(key=lambda x: x['tendencia'], reverse=True)
    
    return questoes_detalhadas

# DRILL-DOWN MICROAMBIENTE (CORRIGIDA)
# DRILL-DOWN MICROAMBIENTE (CORRIGIDA E ALINHADA AO GRÁFICO PRINCIPAL, SEM MUDAR AS CHAMADAS)
def gerar_drill_down_microambiente(dimensao_clicada, df_respondentes_filtrado, matriz, tipo_analise):
    """Drill de Microambiente com valor BRUTO por questão (0–100) e Gap = Ideal-Real."""

    # 1) Fonte: equipe, auto ou ambos
    if tipo_analise == "Média da Equipe":
        df_dados = df_respondentes_filtrado[df_respondentes_filtrado['tipo'] == 'Avaliação Equipe']
    elif tipo_analise == "Autoavaliação":
        df_dados = df_respondentes_filtrado[df_respondentes_filtrado['tipo'] == 'Autoavaliação']
    else:
        df_dados = df_respondentes_filtrado

    questoes_detalhadas = []

    # 2) Questões da DIMENSÃO clicada (usando códigos CANÔNICOS da MATRIZ)
    linhas_dim = matriz[matriz['DIMENSAO'] == dimensao_clicada][['COD','AFIRMACAO','SUBDIMENSAO']].drop_duplicates()

    for _, row in linhas_dim.iterrows():
        codigo_matriz = row['COD']               # ex.: Q45 (código da MATRIZ)
        afirmacao     = row['AFIRMACAO']
        subdim        = row['SUBDIMENSAO']
        # rótulo no FORM (Q06 etc.)
        codigo_form   = _MAP_MATRIZ_TO_FORM.get(codigo_matriz, codigo_matriz)

        # calcula Real/Ideal/Gap usando a MATRIZ por respondente
        real_pct, ideal_pct, gap = calcular_real_ideal_gap_por_questao(df_dados, matriz, codigo_matriz)
        if real_pct is None:
            continue

        questoes_detalhadas.append({
            'questao': codigo_form,              # rótulo do FORM
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

    # 3) Ordena por gap (maior para menor)
    questoes_detalhadas.sort(key=lambda x: x['gap'], reverse=True)
    return questoes_detalhadas

    
# ==================== BUSCAR DADOS ====================

# Função auxiliar para adicionar holding aos DataFrames
def adicionar_holding_ao_dataframe(df, email_to_holding):
    """Adiciona a coluna 'holding' ao DataFrame baseado no email ou empresa"""
    holdings = []
    for _, row in df.iterrows():
        email = str(row.get('email', '')).lower()
        empresa = str(row.get('empresa', '')).lower()
        
        # Tenta buscar por email primeiro
        holding = email_to_holding.get(email, None)
        if holding:
            holding = str(holding).upper().strip()
        
        # Se não encontrou por email, tenta por empresa
        if not holding:
            holding = email_to_holding.get(empresa, None)
            if holding:
                holding = str(holding).upper().strip()
        
        # Se ainda não encontrou, calcula baseado na empresa
        if not holding:
            if empresa in ['astro34', 'spectral_v', 'spectral_a', 'spectral_sales', 'fastco', 'futurex'] or \
               'astro34' in empresa or 'spectral' in empresa or 'fastco' in empresa or 'futurex' in empresa:
                holding = 'PROSPERA'
            else:
                holding = empresa.upper() if empresa else 'N/A'
        
        # Garantir que holding está em maiúsculas
        holding = str(holding).upper().strip() if holding else 'N/A'
        holdings.append(holding)
    
    df['holding'] = holdings
    return df

# Buscar dados
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

# INTERFACE PRINCIPAL
st.title("🎯 LeaderTrack Dashboard")
st.markdown("---")

# Carregar matrizes
with st.spinner("Carregando matrizes..."):
    matriz_arq = carregar_matriz_arquetipos()
    matriz_micro, pontos_max_dimensao, pontos_max_subdimensao = carregar_matrizes_microambiente()

if matriz_arq is not None and matriz_micro is not None:
    # Buscar dados
    with st.spinner("Carregando dados dos respondentes..."):
        consolidado_arq, consolidado_micro = fetch_data()
        
    
    if consolidado_arq and consolidado_micro:
        st.success("✅ Conectado ao Supabase!")
                
        # Buscar dados de holding da tabela employees
        with st.spinner("Carregando dados de holding..."):
            try:
                supabase = init_supabase()
                # Tentar diferentes combinações de colunas
                employees_data = None
                try:
                    # Tentativa 1: com email
                    employees_data = supabase.table('employees').select('email, holding, empresa').execute()
                except:
                    try:
                        # Tentativa 2: sem email, apenas holding e empresa
                        employees_data = supabase.table('employees').select('holding, empresa').execute()
                    except:
                        try:
                            # Tentativa 3: apenas holding
                            employees_data = supabase.table('employees').select('holding').execute()
                        except:
                            # Tentativa 4: buscar todas as colunas e ver o que tem
                            employees_data = supabase.table('employees').select('*').execute()
                
                # Criar um dicionário para mapear email/empresa -> holding
                email_to_holding = {}
                if employees_data and employees_data.data:
                    for emp in employees_data.data:
                        # Tentar obter email (pode não existir)
                        email = emp.get('email', '').lower() if emp.get('email') else ''
                        holding = str(emp.get('holding', 'N/A')).upper().strip()
                        empresa = emp.get('empresa', '')
                        
                        # Mapear por email se existir
                        if email:
                            email_to_holding[email] = holding
                        
                        # Mapear por empresa (sempre que existir)
                        if empresa:
                            empresa_lower = empresa.lower()
                            if empresa_lower not in email_to_holding:
                                email_to_holding[empresa_lower] = holding
            except Exception as e:
                st.warning(f"⚠️ Aviso: Não foi possível carregar dados de holding: {str(e)}")
                email_to_holding = {}
        
        # Processar dados individuais
        with st.spinner("Calculando arquétipos individuais..."):
            df_arquetipos = processar_dados_arquetipos(consolidado_arq, matriz_arq)
            # Adicionar holding aos dados de arquétipos
            df_arquetipos = adicionar_holding_ao_dataframe(df_arquetipos, email_to_holding)
        
        with st.spinner("Calculando microambiente individual..."):
            df_microambiente = processar_dados_microambiente(consolidado_micro, matriz_micro, pontos_max_dimensao, pontos_max_subdimensao)
            # Adicionar holding aos dados de microambiente
            df_microambiente = adicionar_holding_ao_dataframe(df_microambiente, email_to_holding)
        
        # Normalizar dados para minúsculas (convertendo para string primeiro)
        df_arquetipos['empresa'] = df_arquetipos['empresa'].astype(str).str.lower()
        df_microambiente['empresa'] = df_microambiente['empresa'].astype(str).str.lower()
        
        # Normalizar TODOS os campos para minúsculas
        df_arquetipos['empresa'] = df_arquetipos['empresa'].astype(str).str.lower()
        df_arquetipos['codrodada'] = df_arquetipos['codrodada'].astype(str).str.lower()
        df_arquetipos['emailLider'] = df_arquetipos['emailLider'].astype(str).str.lower()
        df_arquetipos['estado'] = df_arquetipos['estado'].astype(str).str.lower()
        df_arquetipos['sexo'] = df_arquetipos['sexo'].astype(str).str.lower()
        df_arquetipos['etnia'] = df_arquetipos['etnia'].astype(str).str.lower()
        df_arquetipos['departamento'] = df_arquetipos['departamento'].astype(str).str.lower()
        df_arquetipos['cargo'] = df_arquetipos['cargo'].astype(str).str.lower()
        
        df_microambiente['empresa'] = df_microambiente['empresa'].astype(str).str.lower()
        df_microambiente['codrodada'] = df_microambiente['codrodada'].astype(str).str.lower()
        df_microambiente['emailLider'] = df_microambiente['emailLider'].astype(str).str.lower()
        df_microambiente['estado'] = df_microambiente['estado'].astype(str).str.lower()
        df_microambiente['sexo'] = df_microambiente['sexo'].astype(str).str.lower()
        df_microambiente['etnia'] = df_microambiente['etnia'].astype(str).str.lower()
        df_microambiente['departamento'] = df_microambiente['departamento'].astype(str).str.lower()
        df_microambiente['cargo'] = df_microambiente['cargo'].astype(str).str.lower()
        
        # Normalizar holding para maiúsculas (se existir)
        if 'holding' in df_arquetipos.columns:
            df_arquetipos['holding'] = df_arquetipos['holding'].astype(str).str.upper()
        if 'holding' in df_microambiente.columns:
            df_microambiente['holding'] = df_microambiente['holding'].astype(str).str.upper()
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("   Total Arquétipos", len(df_arquetipos))
        with col2:
            st.metric("🏢 Total Microambiente", len(df_microambiente))
        with col3:
            auto_count = len(df_arquetipos[df_arquetipos['tipo'] == 'Autoavaliação'])
            st.metric("👤 Autoavaliações", auto_count)
        with col4:
            st.metric("   Última Atualização", datetime.now().strftime("%H:%M"))
        
                # FILTROS
        st.sidebar.header("🎛️ Filtros Globais")
        
        # Filtros principais
        st.sidebar.subheader(" Filtros Principais")
        
        # Combinar holdings de ambos os datasets
        holdings_arq = set()
        holdings_micro = set()
        
        if 'holding' in df_arquetipos.columns:
            holdings_arq = set(df_arquetipos['holding'].dropna().unique())
        
        if 'holding' in df_microambiente.columns:
            holdings_micro = set(df_microambiente['holding'].dropna().unique())
        
        todas_holdings = sorted([str(h) for h in list(holdings_arq.union(holdings_micro))])
        
        # Remover valores vazios ou 'N/A' se não quiser mostrá-los
        todas_holdings = [h for h in todas_holdings if h and str(h).strip() and str(h).upper() != 'N/A']
        
        holdings = ["Todas"] + todas_holdings
        
        # Criar o filtro de holding
        if len(holdings) > 1:  # Se houver mais de "Todas"
            holding_selecionada = st.sidebar.selectbox("🏢 Holding", holdings)
        else:
            holding_selecionada = "Todas"
            st.sidebar.info("ℹ️ Nenhuma holding encontrada nos dados")
        
        # Combinar empresas de ambos os datasets (tudo minúsculas)
        empresas_arq = set(df_arquetipos['empresa'].unique())
        empresas_micro = set(df_microambiente['empresa'].unique())
        todas_empresas = sorted([str(e) for e in list(empresas_arq.union(empresas_micro))])
        empresas = ["Todas"] + todas_empresas
        empresa_selecionada = st.sidebar.selectbox("   Empresa", empresas)
        
        # Combinar codrodadas de ambos os datasets
        codrodadas_arq = set(df_arquetipos['codrodada'].unique())
        codrodadas_micro = set(df_microambiente['codrodada'].unique())
        todas_codrodadas = sorted([str(c) for c in list(codrodadas_arq.union(codrodadas_micro))])
        codrodadas = ["Todas"] + todas_codrodadas
        codrodada_selecionada = st.sidebar.selectbox("   Código da Rodada", codrodadas)
        
        # Combinar emails de líderes de ambos os datasets
        emailliders_arq = set(df_arquetipos['emailLider'].unique())
        emailliders_micro = set(df_microambiente['emailLider'].unique())
        todos_emailliders = sorted([str(e) for e in list(emailliders_arq.union(emailliders_micro))])
        emailliders = ["Todos"] + todos_emailliders
        emaillider_selecionado = st.sidebar.selectbox("👤 Email do Líder", emailliders)
        
        # Combinar estados de ambos os datasets
        estados_arq = set(df_arquetipos['estado'].unique())
        estados_micro = set(df_microambiente['estado'].unique())
        todos_estados = sorted([str(e) for e in list(estados_arq.union(estados_micro))])
        estados = ["Todos"] + todos_estados
        estado_selecionado = st.sidebar.selectbox("🗺️ Estado", estados)
        
        # Combinar gêneros de ambos os datasets
        generos_arq = set(df_arquetipos['sexo'].unique())
        generos_micro = set(df_microambiente['sexo'].unique())
        todos_generos = sorted([str(g) for g in list(generos_arq.union(generos_micro))])
        generos = ["Todos"] + todos_generos
        genero_selecionado = st.sidebar.selectbox("⚧ Gênero", generos)
        
        # Combinar etnias de ambos os datasets
        etnias_arq = set(df_arquetipos['etnia'].unique())
        etnias_micro = set(df_microambiente['etnia'].unique())
        todas_etnias = sorted([str(e) for e in list(etnias_arq.union(etnias_micro))])
        etnias = ["Todas"] + todas_etnias
        etnia_selecionada = st.sidebar.selectbox("   Etnia", etnias)
        
        # Combinar departamentos de ambos os datasets
        departamentos_arq = set(df_arquetipos['departamento'].unique())
        departamentos_micro = set(df_microambiente['departamento'].unique())
        todos_departamentos = sorted([str(d) for d in list(departamentos_arq.union(departamentos_micro))])
        departamentos = ["Todos"] + todos_departamentos
        departamento_selecionado = st.sidebar.selectbox("🏢 Departamento", departamentos)

        
        # Combinar cargos de ambos os datasets
        cargos_arq = set(df_arquetipos['cargo'].unique())
        cargos_micro = set(df_microambiente['cargo'].unique())
        todos_cargos = sorted([str(c) for c in list(cargos_arq.union(cargos_micro))])
        cargos = ["Todos"] + todos_cargos
        cargo_selecionado = st.sidebar.selectbox("💼 Cargo", cargos)
        
        # Dicionário de filtros (normalizar para minúsculas)
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
        
        # TABS PRINCIPAIS
        tab1, tab2, tab3 = st.tabs(["📊 Arquétipos", "🏢 Microambiente", "💚 Saúde Emocional"])
        
        # ==================== TAB ARQUÉTIPOS ====================
        with tab1:
            st.header("📊 Análise de Arquétipos de Liderança")
            
            # Calcular médias com filtros
            arquétipos, medias_auto, medias_equipe, df_filtrado_arq = calcular_medias_arquetipos(df_arquetipos, filtros)
            
            if arquétipos:
                # Criar título dinâmico
                titulo_parts = []
                for key, value in filtros.items():
                    if value not in ["Todas", "Todos"]:
                        titulo_parts.append(f"{key}: {value}")
                
                titulo = " | ".join(titulo_parts) if titulo_parts else "Média Geral de Todos os Respondentes"
                
                # Opções de visualização
                st.markdown("**🎨 Escolha o tipo de visualização:**")
                tipo_visualizacao = st.radio(
                    "Tipo de Gráfico:",
                    ["📊 Gráfico com Rótulos e Clique", "📈 Gráfico Simples"],
                    horizontal=True,
                    key="arquetipos"
                )
                
                # Gerar e exibir gráfico
                fig = gerar_grafico_arquetipos(medias_auto, medias_equipe, arquétipos, titulo, tipo_visualizacao)
                st.plotly_chart(fig, use_container_width=True)
                
                if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique":
                    st.info("💡 **Dica:** Clique nas barras para ver as questões detalhadas!")
                    
                    # DRILL-DOWN INTERATIVO
                    st.subheader("🔍 Drill-Down por Arquétipo")
                    
                    # Seleção manual do arquétipo para drill-down
                    arquétipo_selecionado = st.selectbox(
                        "Selecione um arquétipo para ver as questões detalhadas:",
                        arquétipos,
                        index=None,
                        placeholder="Escolha um arquétipo...",
                        key="arquetipo_select"
                    )
                    
                    if arquétipo_selecionado:
                        st.markdown(f"### 📋 Questões que Impactam: **{arquétipo_selecionado}**")
                        
                        # Gerar drill-down
                        questoes_detalhadas = gerar_drill_down_arquetipos(arquétipo_selecionado, df_filtrado_arq, matriz_arq)
                        
                        if questoes_detalhadas:
                            # Criar gráfico das questões
                            questoes = [q['questao'] for q in questoes_detalhadas]
                            valores_grafico = [q['valor_grafico'] for q in questoes_detalhadas]
                            
                            fig_questoes = go.Figure()
                            # Criar cores baseadas na tendência
                            # Criar cores baseadas na tendência
                            cores_barras = []
                            for q in questoes_detalhadas:
                                tendencia_info = q['tendencia_info']
                                if tendencia_info == 'MUITO DESFAVORÁVEL':  # MAIS ESPECÍFICA PRIMEIRO
                                    cores_barras.append('rgba(255, 0, 0, 0.8)')    # Vermelho
                                elif tendencia_info == 'POUCO DESFAVORÁVEL':
                                    cores_barras.append('rgba(255, 255, 0, 0.7)')  # Amarelo
                                elif tendencia_info == 'DESFAVORÁVEL':  # MAIS GENÉRICA DEPOIS
                                    cores_barras.append('rgba(255, 165, 0, 0.7)')  # Laranja
                                elif tendencia_info == 'FAVORÁVEL':
                                    cores_barras.append('rgba(0, 255, 0, 0.3)')    # Verde claro
                                elif tendencia_info == 'MUITO FAVORÁVEL':
                                    cores_barras.append('rgba(0, 128, 0, 0.5)')    # Verde escuro
                                elif tendencia_info == 'POUCO FAVORÁVEL':
                                    cores_barras.append('rgba(0, 128, 0, 0.4)')    # Verde escuro
                                
                                else:
                                    cores_barras.append('rgba(128, 128, 128, 0.5)') # Cinza
                            
                            fig_questoes.add_trace(go.Bar(
                                x=questoes,
                                y=valores_grafico,
                                marker_color=cores_barras,  # USAR AS CORES PERSONALIZADAS
                                text=[f"{v:.1f}%" for v in valores_grafico],
                                textposition='auto',
                                hovertemplate='<b>%{x}</b><br>% Tendência: %{y:.1f}%<br>Média: %{customdata:.1f} estrelas<extra></extra>',
                                customdata=[q['media_estrelas'] for q in questoes_detalhadas]
                            ))
                            
                            fig_questoes.update_layout(
                                title=f"📊 % Tendência das Questões - {arquétipo_selecionado}",
                                xaxis_title="Questões",
                                yaxis_title="% Tendência",
                                yaxis=dict(range=[-100, 100]),  # Permitir valores negativos e positivos
                                height=400
                            )
                            
                            st.plotly_chart(fig_questoes, use_container_width=True)
                            
                            # Tabela detalhada
                            st.subheader("📋 Detalhamento das Questões")
                            
                            df_questoes = pd.DataFrame(questoes_detalhadas)
                            df_questoes['Tendência'] = df_questoes['tendencia_info']
                            df_questoes['% Tendência'] = df_questoes['tendencia'].apply(lambda x: f"{x:.1f}%")
                            df_questoes['Questão'] = df_questoes['questao']
                            df_questoes['Afirmação'] = df_questoes['afirmacao']
                            df_questoes['Média Estrelas'] = df_questoes['media_estrelas'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Média Arredondada'] = df_questoes['media_arredondada']
                            df_questoes['Nº Respostas'] = df_questoes['n_respostas']

                            
                            
                            
                            # Função para aplicar cores baseadas na tendência
                            def color_tendencia(val):
                                val_str = str(val).strip()  # Remove espaços extras
                                
                                if val_str == 'POUCO DESFAVORÁVEL':
                                    return 'background-color: rgba(255, 255, 0, 0.4)'  # Amarelo
                                elif val_str == 'DESFAVORÁVEL':
                                    return 'background-color: rgba(255, 165, 0, 0.5)'  # Laranja
                                elif val_str == 'MUITO DESFAVORÁVEL':
                                    return 'background-color: rgba(255, 0, 0, 0.8)'    # Vermelho bem intenso!
                                elif val_str == 'MUITO FAVORÁVEL':
                                    return 'background-color: rgba(0, 255, 0, 0.1)'    # Verde claro
                                elif val_str == 'FAVORÁVEL':
                                    return 'background-color: rgba(0, 255, 0, 0.2)'    # Verde claro
                                elif val_str == 'POUCO FAVORÁVEL':
                                    return 'background-color: rgba(0, 128, 0, 0.3)'    # Verde mais escuro
                                else:
                                    return 'background-color: rgba(200, 200, 200, 0.1)' # Cinza para outros casos
                            
                            # Aplicar cores
                            df_questoes_styled = df_questoes[['Questão', 'Afirmação', '% Tendência', 'Tendência', 'Média Estrelas', 'Média Arredondada', 'Nº Respostas']].style.map(color_tendencia, subset=['Tendência'])
                            
                            # Exibir tabela colorida
                            st.dataframe(
                                df_questoes_styled,
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Informações adicionais
                            st.info(f"**📊 Informações:** Média calculada com {len(df_filtrado_arq)} respondentes filtrados. % Tendência baseado na média arredondada de estrelas.")
                            
                        else:
                            st.warning(f"⚠️ Nenhuma questão de impacto encontrada para {arquétipo_selecionado}")
                
                # Informações do relatório
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**📊 Respondentes Analisados:** {len(df_filtrado_arq)}")
                with col2:
                    st.info(f"**👥 Total de Avaliações:** {len(df_filtrado_arq)}")
                with col3:
                    st.info(f"**📈 Arquétipos Analisados:** {len(arquétipos)}")
                
                # Tabela com as médias
                st.subheader("📋 Tabela de Médias")
                df_medias = pd.DataFrame({
                    'Arquétipo': arquétipos,
                    'Autoavaliação (%)': [f"{v:.1f}%" for v in medias_auto],
                    'Média Equipe (%)': [f"{v:.1f}%" for v in medias_equipe]
                })
                st.dataframe(df_medias, use_container_width=True)
                
            else:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
        
        # ==================== TAB MICROAMBIENTE ====================
        with tab2:
            st.header("🏢 Análise de Microambiente de Equipes")
            
            # Calcular médias com filtros
            dimensoes, medias_real, medias_ideal, medias_equipe_real, medias_equipe_ideal, medias_subdimensoes_equipe_real, medias_subdimensoes_equipe_ideal, df_filtrado_micro = calcular_medias_microambiente(df_microambiente, filtros)
            
            if dimensoes:
                # Criar título dinâmico
                titulo_parts = []
                for key, value in filtros.items():
                    if value not in ["Todas", "Todos"]:
                        titulo_parts.append(f"{key}: {value}")
                
                titulo = " | ".join(titulo_parts) if titulo_parts else "Média Geral de Todos os Respondentes"
                
                                                # ==================== FILTRO DE TIPO DE ANÁLISE ====================
                st.markdown("**🎯 Escolha o tipo de análise:**")
                tipo_analise = st.radio(
                    "Tipo de Análise:",
                    ["Autoavaliação", "Média da Equipe", "Comparativo (Auto vs Equipe)"],
                    horizontal=True,
                    key="tipo_analise_micro"
                )
                
                # Calcular médias baseado no tipo selecionado
                if tipo_analise == "Autoavaliação":
                    medias_real_final = medias_real
                    medias_ideal_final = medias_ideal
                    titulo_analise = "Autoavaliação"
                elif tipo_analise == "Média da Equipe":
                    medias_real_final = medias_equipe_real
                    medias_ideal_final = medias_equipe_ideal
                    titulo_analise = "Média da Equipe"
                else:  # Comparativo
                    medias_real_final = medias_real
                    medias_ideal_final = medias_ideal
                    titulo_analise = "Comparativo"
                
                # Opções de visualização
                st.markdown("**🎨 Escolha o tipo de visualização:**")
                tipo_visualizacao = st.radio(
                    "Tipo de Gráfico:",
                    ["📊 Gráfico com Rótulos e Clique", "📈 Gráfico Simples"],
                    horizontal=True,
                    key="microambiente"
                )
                
               
                # Gerar e exibir gráfico
                fig = gerar_grafico_microambiente_linha(medias_real_final, medias_ideal_final, dimensoes, f"{titulo} - {titulo_analise}")
                st.plotly_chart(fig, use_container_width=True, key=f"grafico_dimensoes_{tipo_analise}")

                

                
                
                                # ==================== GRÁFICO DE SUBDIMENSÕES ====================
                st.subheader("📊 Análise por Subdimensões")
                
                # Separar dados por tipo
                df_auto = df_filtrado_micro[df_filtrado_micro['tipo'] == 'Autoavaliação']
                df_equipe = df_filtrado_micro[df_filtrado_micro['tipo'] == 'Avaliação Equipe']
                
                # Calcular médias por subdimensão baseado no tipo selecionado
                subdimensoes = [
                    'Criação', 'Simplificação de Processos', 'Credibilidade Recíproca', 'Dedicação', 'Parceria', 
                    'Satisfação em Fazer Parte', 'Obrigações e Deveres', 'Propósito e Objetivo', 'Aprimoramento', 
                    'Qualidade Superior', 'Celebração', 'Performance', 'Liberdade de Ação', 'Responsabilização'
                ]
                
                if tipo_analise == "Autoavaliação":
                    # Calcular médias de autoavaliação por subdimensão
                    medias_sub_real = []
                    medias_sub_ideal = []
                    for sub in subdimensoes:
                        valores_real = []
                        valores_ideal = []
                        for _, row in df_auto.iterrows():
                            if 'subdimensoes_real' in row and isinstance(row['subdimensoes_real'], dict) and sub in row['subdimensoes_real']:
                                valores_real.append(row['subdimensoes_real'][sub])
                            if 'subdimensoes_ideal' in row and isinstance(row['subdimensoes_ideal'], dict) and sub in row['subdimensoes_ideal']:
                                valores_ideal.append(row['subdimensoes_ideal'][sub])
                        medias_sub_real.append(np.mean(valores_real) if valores_real else 0)
                        medias_sub_ideal.append(np.mean(valores_ideal) if valores_ideal else 0)
                else:
                    # Calcular médias da equipe por subdimensão
                    medias_sub_real = []
                    medias_sub_ideal = []
                    for sub in subdimensoes:
                        valores_real = []
                        valores_ideal = []
                        for _, row in df_equipe.iterrows():
                            if 'subdimensoes_real' in row and isinstance(row['subdimensoes_real'], dict) and sub in row['subdimensoes_real']:
                                valores_real.append(row['subdimensoes_real'][sub])
                            if 'subdimensoes_ideal' in row and isinstance(row['subdimensoes_ideal'], dict) and sub in row['subdimensoes_ideal']:
                                valores_ideal.append(row['subdimensoes_ideal'][sub])
                        medias_sub_real.append(np.mean(valores_real) if valores_real else 0)
                        medias_sub_ideal.append(np.mean(valores_ideal) if valores_ideal else 0)
                
                # Gerar gráfico de subdimensões
                # Criar cores baseadas nos valores %
                cores_real = []
                cores_ideal = []
                
                for real, ideal in zip(medias_sub_real, medias_sub_ideal):
                    # Cor para Real
                    if real < 30:
                        cores_real.append('rgba(255, 0, 0, 0.8)')  # Vermelho
                    elif real < 50:
                        cores_real.append('rgba(255, 165, 0, 0.7)')  # Laranja
                    elif real < 70:
                        cores_real.append('rgba(255, 255, 0, 0.6)')  # Amarelo
                    else:
                        cores_real.append('rgba(0, 255, 0, 0.5)')  # Verde
                    
                    # Cor para Ideal
                    if ideal < 30:
                        cores_ideal.append('rgba(255, 0, 0, 0.8)')  # Vermelho
                    elif ideal < 50:
                        cores_ideal.append('rgba(255, 165, 0, 0.7)')  # Laranja
                    elif ideal < 70:
                        cores_ideal.append('rgba(255, 255, 0, 0.6)')  # Amarelo
                    else:
                        cores_ideal.append('rgba(0, 255, 0, 0.5)')  # Verde
                
                # Criar gráfico com cores personalizadas
                fig_sub = go.Figure()
                
                fig_sub.add_trace(go.Scatter(
                    x=subdimensoes,
                    y=medias_sub_real,
                    mode='lines+markers+text',
                    name='Como é (Real)',
                    line=dict(color='orange', width=3),
                    marker=dict(size=8, color=cores_real),
                    text=[f"{v:.1f}%" for v in medias_sub_real],
                    textposition='top center'
                ))
                
                fig_sub.add_trace(go.Scatter(
                    x=subdimensoes,
                    y=medias_sub_ideal,
                    mode='lines+markers+text',
                    name='Como deveria ser (Ideal)',
                    line=dict(color='darkblue', width=3),
                    marker=dict(size=8, color=cores_ideal),
                    text=[f"{v:.1f}%" for v in medias_sub_ideal],
                    textposition='bottom center'
                ))
                
                fig_sub.update_layout(
                    title=f"📊 Microambiente por Subdimensões - {titulo_analise}",
                    xaxis_title="Subdimensões",
                    yaxis_title="Pontuação (%)",
                    yaxis=dict(range=[0, 100]),
                    height=500
                )

                
                st.plotly_chart(fig_sub, use_container_width=True)
                
                if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique":
                    st.info("💡 **Dica:** Clique nas barras para ver as questões detalhadas!")
                    
                    # DRILL-DOWN INTERATIVO
                    st.subheader("🔍 Drill-Down por Dimensão")
                    
                    # Seleção manual da dimensão para drill-down
                    dimensao_selecionada = st.selectbox(
                        "Selecione uma dimensão para ver as questões detalhadas:",
                        dimensoes,
                        index=None,
                        placeholder="Escolha uma dimensão...",
                        key="dimensao_select_micro"
                    )
                    
                    if dimensao_selecionada:
                        st.markdown(f"### 📋 Questões que Impactam: **{dimensao_selecionada}**")
                        
                        # Gerar drill-down
                        # Gerar drill-down
                        questoes_detalhadas = gerar_drill_down_microambiente(dimensao_selecionada, df_filtrado_micro, matriz_micro, tipo_analise)
                        
                        if questoes_detalhadas:
                            # Criar gráfico das questões
                            questoes = [q['questao'] for q in questoes_detalhadas]
                            gaps = [q['gap'] for q in questoes_detalhadas]


                            
                            # Criar cores baseadas no gap (escala 0-100)
                            cores_gaps = []
                            for gap in gaps:
                                if gap > 80:
                                    cores_gaps.append('rgba(255, 0, 0, 0.8)')  # Vermelho (80-100)
                                elif gap > 60:
                                    cores_gaps.append('rgba(255, 100, 0, 0.8)')  # Vermelho-laranja (60-80)
                                elif gap > 40:
                                    cores_gaps.append('rgba(255, 165, 0, 0.7)')  # Laranja (40-60)
                                elif gap > 20:
                                    cores_gaps.append('rgba(255, 255, 0, 0.6)')  # Amarelo (20-40)
                                elif gap > 0:
                                    cores_gaps.append('rgba(144, 238, 144, 0.6)')  # Verde claro (0-20)
                                else:
                                    cores_gaps.append('rgba(0, 255, 0, 0.5)')  # Verde (0 ou negativo)
                            fig_questoes = go.Figure()
                            
                            fig_questoes.add_trace(go.Bar(
                                x=questoes,
                                y=gaps,
                                marker_color=cores_gaps,
                                text=[f"{v:.1f}" for v in gaps],
                                textposition='auto',
                                hovertemplate='<b>%{x}</b><br>Gap: %{y:.1f}<br>Real: %{customdata[0]:.1f} | Ideal: %{customdata[1]:.1f}<extra></extra>',
                                customdata=[[q['pontuacao_real'], q['pontuacao_ideal']] for q in questoes_detalhadas]
                            ))
                            
                            fig_questoes.update_layout(
                                title=f"   Gap das Questões - {dimensao_selecionada}",
                                xaxis_title="Questões",
                                yaxis_title="Gap (Ideal - Real)",
                                height=400
                            )
                            
                            st.plotly_chart(fig_questoes, use_container_width=True)
                            
                            # Tabela detalhada
                            st.subheader("📋 Detalhamento das Questões")

                            df_questoes = pd.DataFrame(questoes_detalhadas)
                            df_questoes['Questão'] = df_questoes['questao']
                            
                            df_questoes['Afirmação'] = df_questoes['afirmacao']
                            df_questoes['Dimensão'] = df_questoes['dimensao']
                            df_questoes['Subdimensão'] = df_questoes['subdimensao']
                            df_questoes['Média Real'] = df_questoes['media_real'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Média Ideal'] = df_questoes['media_ideal'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Pontuação Real'] = df_questoes['pontuacao_real'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Pontuação Ideal'] = df_questoes['pontuacao_ideal'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Gap'] = df_questoes['gap'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Nº Respostas'] = df_questoes['n_respostas']
                            
                            # Ordenar por dimensão e depois por subdimensão
                            df_questoes = df_questoes.sort_values(['Dimensão', 'Subdimensão'])
                            
                            # Função para aplicar cores baseadas no gap
                            def color_gap(val):
                                try:
                                    gap_val = float(val)
                                    if gap_val > 80:
                                        return 'background-color: rgba(255, 0, 0, 0.8)'  # Vermelho
                                    elif gap_val > 60:
                                        return 'background-color: rgba(255, 100, 0, 0.8)'  # Vermelho-laranja
                                    elif gap_val > 40:
                                        return 'background-color: rgba(255, 165, 0, 0.7)'  # Laranja
                                    elif gap_val > 20:
                                        return 'background-color: rgba(255, 255, 0, 0.6)'  # Amarelo
                                    elif gap_val > 0:
                                        return 'background-color: rgba(144, 238, 144, 0.6)'  # Verde claro
                                    else:
                                        return 'background-color: rgba(0, 255, 0, 0.5)'  # Verde
                                except:
                                    return 'background-color: transparent'
                            
                            # Aplicar cores
                            df_questoes_styled = df_questoes[['Questão', 'Afirmação', 'Dimensão', 'Subdimensão', 'Média Real', 'Média Ideal', 'Pontuação Real', 'Pontuação Ideal', 'Gap', 'Nº Respostas']].style.map(color_gap, subset=['Gap'])
                            
                            st.dataframe(
                                df_questoes_styled,
                                use_container_width=True,
                                hide_index=True
                            )
                            
                            # Informações adicionais
                            st.info(f"**📊 Informações:** Média calculada com {len(df_filtrado_micro)} respondentes filtrados. Gap = Ideal - Real.")
                            
                        else:
                            st.warning(f"⚠️ Nenhuma questão de impacto encontrada para {dimensao_selecionada}")
                
                # Informações do relatório
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.info(f"**📊 Respondentes Analisados:** {len(df_filtrado_micro)}")
                with col2:
                    st.info(f"**👥 Total de Avaliações:** {len(df_filtrado_micro)}")
                with col3:
                    st.info(f"**📈 Dimensões Analisadas:** {len(dimensoes)}")
                
                # Tabela com as médias
                st.subheader("📋 Tabela de Médias")
                df_medias = pd.DataFrame({
                    'Dimensão': dimensoes,
                    f'{titulo_analise} (Real) (%)': [f"{v:.1f}%" for v in medias_real_final],
                    f'{titulo_analise} (Ideal) (%)': [f"{v:.1f}%" for v in medias_ideal_final]
                })
                st.dataframe(df_medias, use_container_width=True)
                
            else:
                st.warning("⚠️ Nenhum dado encontrado com os filtros aplicados.")
                
    
        # ==================== TAB SAÚDE EMOCIONAL ====================

# ==================== TAB SAÚDE EMOCIONAL ====================
# ==== HELPERS PARA REAL/IDEAL/GAP por questão (usando a MATRIZ, valor bruto 0–100) ====

# Mapa do FORM -> MATRIZ e inverso (mesmo usado no microambiente)
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
    Calcula Real, Ideal e Gap (Ideal-Real) para UMA questão usando a MATRIZ:
    - média das PONTUAÇÕES (% 0–100) por respondente
    - codigo_matriz: ex. 'Q45' (código canônico da MATRIZ)
    Retorna (real_pct, ideal_pct, gap_pct) ou (None, None, None) se não houver dados.
    """
    # código usado no JSON (FORM)
    codigo_form = _MAP_MATRIZ_TO_FORM.get(codigo_matriz, codigo_matriz)

    estrelas_real, estrelas_ideal = [], []
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
            estrelas_real.append(r)
            estrelas_ideal.append(i)

    if not estrelas_real or not estrelas_ideal:
        return None, None, None

    media_real  = float(np.mean(estrelas_real))
    media_ideal = float(np.mean(estrelas_ideal))
    real_pct  = round((media_real  / 6) * 100, 2)
    ideal_pct = round((media_ideal / 6) * 100, 2)
    gap       = round(ideal_pct - real_pct, 2)
    return real_pct, ideal_pct, gap
    
with tab3:
    st.header("💚 Análise de Saúde Emocional + Compliance NR-1")
    st.markdown("**🔍 Analisando afirmações existentes relacionadas à saúde emocional...**")
    
    # ==================== RECLASSIFICAÇÕES DEFINITIVAS DE SAÚDE EMOCIONAL ====================
    # Dicionário fixo com todas as reclassificações (código -> dimensão)
    # Este dicionário é definitivo e será usado sempre, garantindo que 100% das afirmações sejam classificadas
    RECLASSIFICACOES_DEFINITIVAS = {
        # Reclassificações definitivas baseadas na imagem fornecida - TODAS as 97 afirmações
        # Total: 97 afirmações (49 arquétipos Q01-Q49 + 48 microambiente Q01-Q48)
        # Baseado no arquivo: reclassificacoes_completas_97_afirmacoes.csv
        # Chaves compostas: "arq_Q01" para arquétipos, "micro_Q01" para microambiente
        # Chaves simples: "Q01" como fallback (usa última ocorrência do CSV)
        
        # ========== ARQUÉTIPOS (49 afirmações) ==========
        # Prevenção de Estresse (4 arquétipos)
        'arq_Q10': 'Prevenção de Estresse', 'arq_Q14': 'Prevenção de Estresse', 'arq_Q17': 'Prevenção de Estresse',
        'arq_Q24': 'Prevenção de Estresse',
        
        # Ambiente Psicológico Seguro (2 arquétipos)
        'arq_Q32': 'Ambiente Psicológico Seguro', 'arq_Q44': 'Ambiente Psicológico Seguro',
        
        # Suporte Emocional (15 arquétipos)
        'arq_Q01': 'Suporte Emocional', 'arq_Q03': 'Suporte Emocional', 'arq_Q04': 'Suporte Emocional',
        'arq_Q09': 'Suporte Emocional', 'arq_Q13': 'Suporte Emocional', 'arq_Q15': 'Suporte Emocional',
        'arq_Q16': 'Suporte Emocional', 'arq_Q18': 'Suporte Emocional', 'arq_Q19': 'Suporte Emocional',
        'arq_Q25': 'Suporte Emocional', 'arq_Q31': 'Suporte Emocional', 'arq_Q36': 'Suporte Emocional',
        'arq_Q40': 'Suporte Emocional', 'arq_Q41': 'Suporte Emocional', 'arq_Q43': 'Suporte Emocional',
        'arq_Q49': 'Suporte Emocional',
        
        # Comunicação Positiva (28 arquétipos)
        'arq_Q02': 'Comunicação Positiva', 'arq_Q05': 'Comunicação Positiva', 'arq_Q07': 'Comunicação Positiva',
        'arq_Q08': 'Comunicação Positiva', 'arq_Q11': 'Comunicação Positiva', 'arq_Q12': 'Comunicação Positiva',
        'arq_Q20': 'Comunicação Positiva', 'arq_Q21': 'Comunicação Positiva', 'arq_Q22': 'Comunicação Positiva',
        'arq_Q23': 'Comunicação Positiva', 'arq_Q27': 'Comunicação Positiva', 'arq_Q28': 'Comunicação Positiva',
        'arq_Q29': 'Comunicação Positiva', 'arq_Q30': 'Comunicação Positiva', 'arq_Q33': 'Comunicação Positiva',
        'arq_Q34': 'Comunicação Positiva', 'arq_Q35': 'Comunicação Positiva', 'arq_Q37': 'Comunicação Positiva',
        'arq_Q38': 'Comunicação Positiva', 'arq_Q39': 'Comunicação Positiva', 'arq_Q42': 'Comunicação Positiva',
        'arq_Q45': 'Comunicação Positiva', 'arq_Q46': 'Comunicação Positiva', 'arq_Q47': 'Comunicação Positiva',
        'arq_Q48': 'Comunicação Positiva',
        
        # ========== MICROAMBIENTE (48 afirmações) ==========
        # Ambiente Psicológico Seguro (11 microambiente)
        'micro_Q06': 'Ambiente Psicológico Seguro', 'micro_Q07': 'Ambiente Psicológico Seguro',
        'micro_Q08': 'Ambiente Psicológico Seguro', 'micro_Q23': 'Ambiente Psicológico Seguro',
        'micro_Q26': 'Ambiente Psicológico Seguro', 'micro_Q39': 'Ambiente Psicológico Seguro',
        'micro_Q40': 'Ambiente Psicológico Seguro', 'micro_Q41': 'Ambiente Psicológico Seguro',
        'micro_Q44': 'Ambiente Psicológico Seguro', 'micro_Q47': 'Ambiente Psicológico Seguro',
        'micro_Q48': 'Ambiente Psicológico Seguro',
        
        # Comunicação Positiva (37 microambiente)
        'micro_Q01': 'Comunicação Positiva', 'micro_Q04': 'Comunicação Positiva', 'micro_Q05': 'Comunicação Positiva',
        'micro_Q09': 'Comunicação Positiva', 'micro_Q10': 'Comunicação Positiva', 'micro_Q11': 'Comunicação Positiva',
        'micro_Q12': 'Comunicação Positiva', 'micro_Q13': 'Comunicação Positiva', 'micro_Q14': 'Comunicação Positiva',
        'micro_Q15': 'Comunicação Positiva', 'micro_Q16': 'Comunicação Positiva', 'micro_Q17': 'Comunicação Positiva',
        'micro_Q22': 'Comunicação Positiva', 'micro_Q24': 'Comunicação Positiva', 'micro_Q34': 'Comunicação Positiva',
        'micro_Q35': 'Comunicação Positiva', 'micro_Q37': 'Comunicação Positiva', 'micro_Q38': 'Comunicação Positiva',
        'micro_Q42': 'Comunicação Positiva', 'micro_Q43': 'Comunicação Positiva', 'micro_Q45': 'Comunicação Positiva',
        'micro_Q46': 'Comunicação Positiva',
        
        # ========== FALLBACK (chaves simples - última ocorrência do CSV) ==========
        # Usado quando não encontrar chave composta
        'Q01': 'Comunicação Positiva', 'Q02': 'Comunicação Positiva', 'Q03': 'Comunicação Positiva',
        'Q04': 'Comunicação Positiva', 'Q05': 'Comunicação Positiva', 'Q06': 'Ambiente Psicológico Seguro',
        'Q07': 'Ambiente Psicológico Seguro', 'Q08': 'Ambiente Psicológico Seguro', 'Q09': 'Comunicação Positiva',
        'Q10': 'Comunicação Positiva', 'Q11': 'Comunicação Positiva', 'Q12': 'Comunicação Positiva',
        'Q13': 'Comunicação Positiva', 'Q14': 'Comunicação Positiva', 'Q15': 'Comunicação Positiva',
        'Q16': 'Comunicação Positiva', 'Q17': 'Comunicação Positiva', 'Q18': 'Suporte Emocional',
        'Q19': 'Suporte Emocional', 'Q20': 'Comunicação Positiva', 'Q21': 'Comunicação Positiva',
        'Q22': 'Comunicação Positiva', 'Q23': 'Ambiente Psicológico Seguro', 'Q24': 'Comunicação Positiva',
        'Q25': 'Suporte Emocional', 'Q26': 'Ambiente Psicológico Seguro', 'Q27': 'Comunicação Positiva',
        'Q28': 'Comunicação Positiva', 'Q29': 'Comunicação Positiva', 'Q30': 'Comunicação Positiva',
        'Q31': 'Suporte Emocional', 'Q32': 'Ambiente Psicológico Seguro', 'Q33': 'Comunicação Positiva',
        'Q34': 'Comunicação Positiva', 'Q35': 'Comunicação Positiva', 'Q36': 'Suporte Emocional',
        'Q37': 'Comunicação Positiva', 'Q38': 'Comunicação Positiva', 'Q39': 'Ambiente Psicológico Seguro',
        'Q40': 'Ambiente Psicológico Seguro', 'Q41': 'Ambiente Psicológico Seguro', 'Q42': 'Comunicação Positiva',
        'Q43': 'Comunicação Positiva', 'Q44': 'Ambiente Psicológico Seguro', 'Q45': 'Comunicação Positiva',
        'Q46': 'Comunicação Positiva', 'Q47': 'Ambiente Psicológico Seguro', 'Q48': 'Ambiente Psicológico Seguro',
        'Q49': 'Suporte Emocional',
    }
    
    # Analisar afirmações de saúde emocional
    with st.spinner("Identificando afirmações de saúde emocional..."):
        afirmacoes_saude_emocional, df_arq_filtrado, df_micro_filtrado = analisar_afirmacoes_saude_emocional(matriz_arq, matriz_micro, df_arquetipos, df_microambiente, filtros)
        
        # Se houver reclassificações importadas, incluir TODAS as afirmações (não apenas as com palavras-chave)
        # Isso será feito depois do upload do CSV, mas precisamos preparar a estrutura
        
        
        
        # ✅ CALCULAR COMPLIANCE AQUI (DEPOIS DOS FILTROS!)
       
        compliance_nr1 = mapear_compliance_nr1(afirmacoes_saude_emocional)
    
        if afirmacoes_saude_emocional:
            # Métricas principais
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("🧠 Arquétipos SE", len([
                    a for a in afirmacoes_saude_emocional 
                    if a['tipo'] == 'Arquétipo'
                ]))
            
            with col2:
                st.metric(" Microambiente SE", len([
                    a for a in afirmacoes_saude_emocional 
                    if a['tipo'] == 'Microambiente'
                ]))
            
            with col3:
                st.metric("💚 Total SE", len(afirmacoes_saude_emocional))
            
            with col4:
                # Métrica de percentual baseado no total do CSV oficial de Saúde Emocional
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

        
        # ==================== GRÁFICO 1: COMPLIANCE NR-1 COM VALORES ====================
        st.subheader("📊 Compliance NR-1 + Adendo Saúde Mental - Valores das Questões")

        # Calcular VALORES das questões por categoria (não contagem)
        categoria_valores = {
            'Prevenção de Estresse': [],
            'Ambiente Psicológico Seguro': [],
            'Suporte Emocional': [],
            'Comunicação Positiva': [],
            'Equilíbrio Vida-Trabalho': []
        }
        
        # Para cada afirmação, calcular seu valor baseado nos dados filtrados
        for af in afirmacoes_saude_emocional:
            codigo = af['chave']
            
            # USAR APENAS a dimensão que já vem do CSV (dimensao_saude_emocional)
            categoria = af.get('dimensao_saude_emocional', 'Suporte Emocional')
            
            # Normalizar nome da dimensão
            if categoria not in categoria_valores:
                # Se não estiver nas categorias esperadas, usar Suporte Emocional como padrão
                categoria = 'Suporte Emocional'
            
            # Calcular valor da questão
            # Calcular valor da questão
            if af['tipo'] == 'Arquétipo':
                # Para arquétipos, usar % tendência
                arquétipo = af['dimensao']
                estrelas_questao = []
                
                for _, respondente in df_arq_filtrado.iterrows():
                    if 'respostas' in respondente and codigo in respondente['respostas']:
                        estrelas = int(respondente['respostas'][codigo])
                        estrelas_questao.append(estrelas)
                
                if estrelas_questao:
                    media_estrelas = np.mean(estrelas_questao)
                    media_arredondada = round(media_estrelas)
                    percentual_corrigido = round((media_estrelas / 6) * 100, 2)
                    
                    # Buscar apenas o TEXTO da tendência na tabela
                    chave = f"{arquétipo}{media_arredondada}{codigo}"
                    linha_tendencia = matriz_arq[matriz_arq['CHAVE'] == chave]
                    
                    if not linha_tendencia.empty:
                        tendencia_info = linha_tendencia['Tendência'].iloc[0]
                        
                        # Converter para score usando percentual corrigido
                        if 'DESFAVORÁVEL' in tendencia_info:
                            valor = max(0, 100 - percentual_corrigido)
                        else:
                            valor = percentual_corrigido
                        
                        categoria_valores[categoria].append(valor)


            
            else:  # Microambiente
                # Para microambiente, usar a mesma lógica do drill: CANÔNICO (matriz) → FORM (JSON)
                codigo_canonico = af['chave']  # ex.: Q45 (matriz)
            
                # Mapeamento formulário -> canônico
                MAPEAMENTO_QUESTOES = {
                    'Q01': 'Q01','Q02': 'Q12','Q03': 'Q23','Q04': 'Q34','Q05': 'Q44','Q06': 'Q45',
                    'Q07': 'Q46','Q08': 'Q47','Q09': 'Q48','Q10': 'Q02','Q11': 'Q03','Q12': 'Q04',
                    'Q13': 'Q05','Q14': 'Q06','Q15': 'Q07','Q16': 'Q08','Q17': 'Q09','Q18': 'Q10',
                    'Q19': 'Q11','Q20': 'Q13','Q21': 'Q14','Q22': 'Q15','Q23': 'Q16','Q24': 'Q17',
                    'Q25': 'Q18','Q26': 'Q19','Q27': 'Q20','Q28': 'Q21','Q29': 'Q22','Q30': 'Q24',
                    'Q31': 'Q25','Q32': 'Q26','Q33': 'Q27','Q34': 'Q28','Q35': 'Q29','Q36': 'Q30',
                    'Q37': 'Q31','Q38': 'Q32','Q39': 'Q33','Q40': 'Q35','Q41': 'Q36','Q42': 'Q37',
                    'Q43': 'Q38','Q44': 'Q39','Q45': 'Q40','Q46': 'Q41','Q47': 'Q42','Q48': 'Q43'
                }
                # Reverso: CANÔNICO -> FORM
                REVERSO_FORM = {can: form for form, can in MAPEAMENTO_QUESTOES.items()}
                codigo_form_json = REVERSO_FORM.get(codigo_canonico, codigo_canonico)  # ex.: Q45 -> Q06
            
                estrelas_real = []
                estrelas_ideal = []
            
                for _, respondente in df_micro_filtrado.iterrows():
                    respostas = respondente.get('respostas', {})
                    if not isinstance(respostas, dict):
                        continue
            
                    questao_real = f"{codigo_form_json}C"   # usar FORM do JSON
                    questao_ideal = f"{codigo_form_json}k"
            
                    if questao_real in respostas:
                        estrelas_real.append(int(respostas[questao_real]))
                    if questao_ideal in respostas:
                        estrelas_ideal.append(int(respostas[questao_ideal]))
            
                if estrelas_real and estrelas_ideal:
                    media_real = np.mean(estrelas_real)
                    media_ideal = np.mean(estrelas_ideal)
                    
                    # Calcular percentuais diretamente da média sem arredondar
                    pontuacao_real = round((media_real / 6) * 100, 2)
                    pontuacao_ideal = round((media_ideal / 6) * 100, 2)
                    gap = round(pontuacao_ideal - pontuacao_real, 2)
            
                    # Score para a categoria (quanto menor o gap, maior o score)
                    valor = max(0.0, 100.0 - gap)
                    categoria_valores[categoria].append(valor)






        # Calcular médias por categoria
        categoria_medias = {}
        for categoria, valores in categoria_valores.items():
            if valores:
                categoria_medias[categoria] = np.mean(valores)
            else:
                categoria_medias[categoria] = 0
        
        # Gráfico de barras horizontais com VALORES
        fig_compliance = go.Figure()

        # Cores baseadas no valor (alinhadas com o Score Final)
        # Excelente:  >= 80
        # Ótimo:      75 a 79,99
        # Bom:        70 a 74,99
        # Regular:    60 a 69,99
        # Não adequado: abaixo de 60
        cores_compliance = []
        for valor in categoria_medias.values():
            if valor >= 80:
                # Excelente - verde bem forte
                cores_compliance.append('rgba(0, 128, 0, 0.9)')
            elif valor >= 75:
                # Ótimo - verde
                cores_compliance.append('rgba(46, 204, 113, 0.9)')
            elif valor >= 70:
                # Bom - verde claro
                cores_compliance.append('rgba(144, 238, 144, 0.9)')
            elif valor >= 60:
                # Regular - amarelo
                cores_compliance.append('rgba(255, 215, 0, 0.9)')
            else:
                # Não adequado - laranja/vermelho
                cores_compliance.append('rgba(255, 99, 71, 0.9)')
        
        fig_compliance.add_trace(go.Bar(
            y=list(categoria_medias.keys()),
            x=list(categoria_medias.values()),
            orientation='h',
            marker_color=cores_compliance,
            text=[f"{v:.1f}%" for v in categoria_medias.values()],
            textposition='auto',
            hovertemplate='<b>%{y}</b><br>Score Médio: %{x:.1f}%<br>Questões: %{customdata}<br><extra>Clique para ver detalhes!</extra>',
            customdata=[len(categoria_valores[k]) for k in categoria_medias.keys()]
        ))
        
        fig_compliance.update_layout(
            title="📊 Score Médio por Categoria NR-1",
            xaxis_title="Score Médio (%)",
            yaxis_title="Categorias de Compliance",
            xaxis=dict(range=[0, 100]),
            height=400,
            showlegend=False,
            clickmode='event+select',
            hovermode='closest'
        )
        
        st.plotly_chart(fig_compliance, use_container_width=True)
        st.divider()
        
        # ==================== IMPORTAR E APLICAR RECLASSIFICAÇÕES ====================
        st.subheader("📤 Importar Reclassificações de Afirmações")
        st.markdown("**📋 Faça upload do CSV com as reclassificações (colunas: COD, STATUS, DE, PARA, Tipo, Código, Afirmação)**")
        
        uploaded_file = st.file_uploader(
            "Escolha o arquivo CSV com as reclassificações",
            type=['csv'],
            key="upload_reclassificacoes"
        )
        
        # Dicionário para armazenar reclassificações (será usado na classificação)
        reclassificacoes = {}
        novas_afirmacoes = []
        
        if uploaded_file is not None:
            try:
                df_reclass = pd.read_csv(uploaded_file, encoding='utf-8-sig')
                
                # Normalizar nomes das colunas (remover acentos, espaços, etc.)
                df_reclass.columns = df_reclass.columns.str.strip()
                
                # Verificar colunas necessárias
                colunas_necessarias = ['COD', 'STATUS', 'DE', 'PARA', 'Tipo', 'Código']
                colunas_encontradas = [col for col in colunas_necessarias if col in df_reclass.columns]
                
                if len(colunas_encontradas) >= 4:  # Pelo menos COD, STATUS, PARA, Tipo
                    st.success(f"✅ Arquivo carregado com sucesso! {len(df_reclass)} linhas processadas.")
                    
                    # Processar reclassificações
                    for _, row in df_reclass.iterrows():
                        cod = str(row.get('COD', '')).strip()
                        status = str(row.get('STATUS', '')).strip()
                        de = str(row.get('DE', '')).strip() if pd.notna(row.get('DE')) else ''
                        para = str(row.get('PARA', '')).strip() if pd.notna(row.get('PARA')) else ''
                        tipo = str(row.get('Tipo', '')).strip()
                        codigo_original = str(row.get('Código', '')).strip()
                        
                        # Obter texto da afirmação (pode estar em qualquer coluna que não seja as já processadas)
                        coluna_afirmacao = None
                        for col in df_reclass.columns:
                            if col not in ['COD', 'STATUS', 'DE', 'PARA', 'Tipo', 'Código'] and pd.notna(row.get(col)):
                                coluna_afirmacao = col
                                break
                        
                        afirmacao_texto = ''
                        if coluna_afirmacao:
                            afirmacao_texto = str(row.get(coluna_afirmacao, '')).strip()
                        
                        if para and para.upper() != 'NAN' and para != '':
                            # Identificar se é código novo (aXX ou mXX) ou existente (QXX)
                            if cod.startswith('a') or cod.startswith('m'):
                                # Nova afirmação
                                novas_afirmacoes.append({
                                    'cod': cod,
                                    'codigo_original': codigo_original if codigo_original and codigo_original != '' else cod,
                                    'tipo': tipo,
                                    'afirmacao': afirmacao_texto,
                                    'dimensao': para,
                                    'status': status
                                })
                            else:
                                # Reclassificação de afirmação existente
                                # Usar código original se disponível, senão usar COD
                                # Normalizar código (remover espaços, converter para string)
                                codigo_chave = str(codigo_original).strip() if codigo_original and str(codigo_original).strip() != '' else str(cod).strip()
                                # Também armazenar por COD para garantir que encontre
                                reclassificacoes[codigo_chave] = {
                                    'de': de,
                                    'para': para,
                                    'tipo': tipo,
                                    'cod': cod
                                }
                                # Se COD e código_original forem diferentes, armazenar ambos
                                if cod != codigo_chave and codigo_original:
                                    reclassificacoes[str(cod).strip()] = {
                                        'de': de,
                                        'para': para,
                                        'tipo': tipo,
                                        'cod': cod
                                    }
                    
                    st.info(f"📊 Processadas: {len(reclassificacoes)} reclassificações e {len(novas_afirmacoes)} novas afirmações")
                    
                    # Mostrar preview
                    with st.expander("👁️ Visualizar Reclassificações Processadas"):
                        if reclassificacoes:
                            st.markdown("**🔄 Reclassificações:**")
                            df_reclass_preview = pd.DataFrame([
                                {
                                    'Código': k,
                                    'DE': v['de'] if v['de'] else '(sem origem)',
                                    'PARA': v['para'],
                                    'Tipo': v['tipo']
                                }
                                for k, v in reclassificacoes.items()
                            ])
                            st.dataframe(df_reclass_preview, use_container_width=True, hide_index=True)
                        
                        if novas_afirmacoes:
                            st.markdown("**➕ Novas Afirmações:**")
                            df_novas_preview = pd.DataFrame(novas_afirmacoes)
                            st.dataframe(df_novas_preview, use_container_width=True, hide_index=True)
                else:
                    st.error(f"❌ Colunas necessárias não encontradas. Encontradas: {', '.join(df_reclass.columns.tolist())}")
                    st.info("💡 Colunas esperadas: COD, STATUS, DE, PARA, Tipo, Código, e uma coluna com o texto da afirmação")
            except Exception as e:
                st.error(f"❌ Erro ao processar arquivo: {str(e)}")
                st.info("💡 Verifique se o arquivo está no formato CSV correto e com encoding UTF-8")
        
        # NÃO expandir mais - usar APENAS as afirmações que estão no CSV
        # O CSV já contém todas as afirmações que devem ser consideradas
        st.info(f"✅ **Afirmações do CSV incluídas!** Total: {len(afirmacoes_saude_emocional)} afirmações (apenas as que estão no CSV)")
        
        st.divider()
        
        # ==================== MAPEAMENTO COMPLETO: AFIRMAÇÕES POR DIMENSÃO ====================
        st.subheader("📋 Mapeamento Completo: Afirmações por Dimensão de Saúde Emocional")
        st.markdown("**🔍 Use esta seção para revisar e ajustar a classificação das afirmações nas dimensões.**")
        
        # Criar dicionário organizado por dimensão
        mapeamento_por_dimensao = {
            'Prevenção de Estresse': {'arquetipos': [], 'microambiente': []},
            'Ambiente Psicológico Seguro': {'arquetipos': [], 'microambiente': []},
            'Suporte Emocional': {'arquetipos': [], 'microambiente': []},
            'Comunicação Positiva': {'arquetipos': [], 'microambiente': []},
            'Equilíbrio Vida-Trabalho': {'arquetipos': [], 'microambiente': []}
        }
        
        # Palavras-chave para cada dimensão (mesma lógica usada no código)
        palavras_chave_dimensoes = {
            'Prevenção de Estresse': ['estresse', 'ansiedade', 'pressão', 'pressao', 'cobrança', 'cobranca', 'deadline', 'prazos', 'tensão', 'tensao', 'sobrecarga', 'preocupa com o tempo', 'preocupa com detalhes', 'preocupa se', 'preocupa com', 'necessidade de se aprofundar', 'aprofundar nos detalhes', 'detalhes na execução', 'detalhes de realização', 'detalhes do trabalho', 'sem necessidade de ficar de olho', 'fazer todo o possivel', 'resolver problemas particulares', 'problemas particulares urgentes', 'atuar na solução de conflitos', 'solução de conflitos em sua equipe', 'risco calculado', 'resultasse em algo negativo', 'seriam apoiados', 'leais uns com os outros', 'mais elogiados e incentivados', 'do que criticados'],
            'Ambiente Psicológico Seguro': ['ambiente', 'seguro', 'proteção', 'protecao', 'respeito', 'cuidadoso', 'palavras'],
            'Suporte Emocional': ['suporte', 'apoio', 'ajuda', 'assistência', 'assistencia', 'ajudar', 'resolver', 'percebe', 'oferece'],
            'Comunicação Positiva': ['feedback', 'positivo', 'construtivo', 'encorajamento', 'comentários', 'comentarios', 'positivos', 'desenvolvimento', 'futuro'],
            'Equilíbrio Vida-Trabalho': ['equilíbrio', 'equilibrio', 'flexibilidade', 'horários', 'horarios', 'tempo', 'família', 'familia', 'pessoal', 'relação', 'relacao', 'vida pessoal']
        }
        
        # Normalizar nome da dimensão (remover acentos e normalizar)
        dimensoes_normalizadas = {
            'Prevenção de Estresse': 'Prevenção de Estresse',
            'Prevencao de Estresse': 'Prevenção de Estresse',
            'Ambiente Psicológico Seguro': 'Ambiente Psicológico Seguro',
            'Ambiente Psicologico Seguro': 'Ambiente Psicológico Seguro',
            'Suporte Emocional': 'Suporte Emocional',
            'Comunicação Positiva': 'Comunicação Positiva',
            'Comunicacao Positiva': 'Comunicação Positiva',
            'Equilíbrio Vida-Trabalho': 'Equilíbrio Vida-Trabalho',
            'Equilibrio Vida-Trabalho': 'Equilíbrio Vida-Trabalho',
            'Equilíbrio Vida- Trabalho': 'Equilíbrio Vida-Trabalho',
            'Equilibrio Vida- Trabalho': 'Equilíbrio Vida-Trabalho'
        }

        
        # Carregar classificações do CSV
        classificacoes = carregar_classificacoes_saude_emocional()
        
        # Set para rastrear códigos já processados (evitar duplicatas)
        codigos_processados = set()
        
        # Classificar todas as afirmações de saúde emocional
        for af in afirmacoes_saude_emocional:
            codigo_af = str(af['chave']).strip()
            tipo_af = af.get('tipo', '').strip()
            
            # Criar chave composta para evitar duplicatas
            if 'Arquétipo' in tipo_af or 'Arquetipo' in tipo_af:
                codigo_key = f"arq_{codigo_af}"
            elif 'Microambiente' in tipo_af or 'Micro' in tipo_af:
                codigo_key = f"micro_{codigo_af}"
            else:
                codigo_key = codigo_af
            
            # Verificar se já foi processado (evitar duplicatas)
            if codigo_key in codigos_processados:
                continue
            codigos_processados.add(codigo_key)
            
            # PRIMEIRO: Usar dimensao_saude_emocional que já vem da função analisar_afirmacoes_saude_emocional
            categoria_atribuida = af.get('dimensao_saude_emocional', None)
            
            # Se não tiver, buscar no CSV usando chave composta
            if not categoria_atribuida:
                if codigo_key in classificacoes:
                    categoria_atribuida = classificacoes[codigo_key]
                elif codigo_af in classificacoes:
                    categoria_atribuida = classificacoes[codigo_af]
            
            # Se ainda não encontrou, verificar CSV importado (se houver)
            if not categoria_atribuida and reclassificacoes:
                if codigo_key in reclassificacoes:
                    categoria_atribuida = reclassificacoes[codigo_key].get('para', None)
                elif codigo_af in reclassificacoes:
                    categoria_atribuida = reclassificacoes[codigo_af].get('para', None)
            
            # Se ainda não encontrou, usar dimensao_saude_emocional que já vem da função
            if not categoria_atribuida:
                categoria_atribuida = af.get('dimensao_saude_emocional', None)
            
            # Se ainda não encontrou, usar Suporte Emocional como padrão
            if not categoria_atribuida:
                categoria_atribuida = 'Suporte Emocional'
            
            # Normalizar nome da dimensão
            categoria_atribuida = dimensoes_normalizadas.get(categoria_atribuida, categoria_atribuida)
            
            # Garantir que a dimensão existe no mapeamento
            if categoria_atribuida not in mapeamento_por_dimensao:
                categoria_atribuida = 'Suporte Emocional'  # Fallback
            
            # Adicionar à dimensão correspondente
            if af['tipo'] == 'Arquétipo':
                mapeamento_por_dimensao[categoria_atribuida]['arquetipos'].append({
                    'codigo': af['chave'],
                    'afirmacao': af['afirmacao'],
                    'dimensao': af['dimensao']
                })
            else:  # Microambiente
                mapeamento_por_dimensao[categoria_atribuida]['microambiente'].append({
                    'codigo': af['chave'],
                    'afirmacao': af['afirmacao'],
                    'dimensao': af['dimensao'],
                    'subdimensao': af['subdimensao']
                })
        
        # Adicionar novas afirmações do CSV (apenas se não estiverem já na lista)
        for nova_af in novas_afirmacoes:
            codigo_nova = str(nova_af.get('codigo_original', nova_af['cod'])).strip()
            
            # Verificar se já foi processado (evitar duplicatas)
            if codigo_nova in codigos_processados:
                continue
            codigos_processados.add(codigo_nova)
            
            dimensao = nova_af['dimensao']
            # Normalizar dimensão
            dimensao = dimensoes_normalizadas.get(dimensao, dimensao)
            if dimensao not in mapeamento_por_dimensao:
                dimensao = 'Suporte Emocional'  # Fallback
            
            if nova_af['tipo'] == 'Arquétipo' or 'Arquétipo' in nova_af['tipo']:
                mapeamento_por_dimensao[dimensao]['arquetipos'].append({
                    'codigo': codigo_nova,
                    'afirmacao': nova_af['afirmacao'],
                    'dimensao': 'N/A'
                })
            else:  # Microambiente
                mapeamento_por_dimensao[dimensao]['microambiente'].append({
                    'codigo': codigo_nova,
                    'afirmacao': nova_af['afirmacao'],
                    'dimensao': 'N/A',
                    'subdimensao': 'N/A'
                })
        
        # Criar DataFrame completo para exportação
        dados_exportacao = []
        
        # Calcular total geral para verificação
        total_mapeamento = sum(len(dados['arquetipos']) + len(dados['microambiente']) for dados in mapeamento_por_dimensao.values())
        
        # Exibir mapeamento organizado (sempre mostrar todas as dimensões, mesmo vazias)
        for dimensao, dados in mapeamento_por_dimensao.items():
            total_arq = len(dados['arquetipos'])
            total_micro = len(dados['microambiente'])
            total_geral = total_arq + total_micro
            
            # Sempre mostrar a dimensão, mesmo se estiver vazia
            if total_geral > 0:
                with st.expander(f"📁 **{dimensao}** ({total_geral} afirmações: {total_arq} arquétipos + {total_micro} microambiente)", expanded=False):
                    # Mostrar palavras-chave que identificam esta dimensão
                    palavras_dimensao = palavras_chave_dimensoes.get(dimensao, [])
                    st.markdown(f"**🔑 Palavras-chave:** {', '.join(palavras_dimensao[:10])}{'...' if len(palavras_dimensao) > 10 else ''}")
                    st.markdown("---")
                    
                    # Mostrar afirmações de arquétipos
                    if dados['arquetipos']:
                        st.markdown(f"### 🧠 Arquétipos ({total_arq} afirmações)")
                        df_arq = pd.DataFrame(dados['arquetipos'])
                        df_arq.columns = ['Código', 'Afirmação', 'Arquétipo']
                        st.dataframe(df_arq, use_container_width=True, hide_index=True)
                        
                        # Adicionar para exportação
                        for _, row in df_arq.iterrows():
                            dados_exportacao.append({
                                'Dimensão Saúde Emocional': dimensao,
                                'Tipo': 'Arquétipo',
                                'Código': row['Código'],
                                'Afirmação': row['Afirmação'],
                                'Arquétipo/Dimensão': row['Arquétipo'],
                                'Subdimensão': 'N/A'
                            })
                    
                    # Mostrar afirmações de microambiente
                    if dados['microambiente']:
                        st.markdown(f"### 🏢 Microambiente ({total_micro} afirmações)")
                        df_micro = pd.DataFrame(dados['microambiente'])
                        df_micro.columns = ['Código', 'Afirmação', 'Dimensão', 'Subdimensão']
                        st.dataframe(df_micro, use_container_width=True, hide_index=True)
                        
                        # Adicionar para exportação
                        for _, row in df_micro.iterrows():
                            dados_exportacao.append({
                                'Dimensão Saúde Emocional': dimensao,
                                'Tipo': 'Microambiente',
                                'Código': row['Código'],
                                'Afirmação': row['Afirmação'],
                                'Arquétipo/Dimensão': row['Dimensão'],
                                'Subdimensão': row['Subdimensão']
                            })
            else:
                # Mostrar dimensão vazia com mensagem
                with st.expander(f"📁 **{dimensao}** (0 afirmações)", expanded=False):
                    st.info(f"ℹ️ Nenhuma afirmação classificada nesta dimensão ainda.")
        
        # Botão de download do mapeamento completo
        if dados_exportacao:
            df_export = pd.DataFrame(dados_exportacao)
            csv_mapeamento = df_export.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Download CSV - Mapeamento Completo por Dimensão",
                data=csv_mapeamento,
                file_name="mapeamento_saude_emocional_por_dimensao.csv",
                mime="text/csv",
                key="download_mapeamento"
            )
        
        # Mostrar total do mapeamento
        st.markdown(f"**📊 Total de afirmações no mapeamento: {total_mapeamento}**")
        if reclassificacoes or novas_afirmacoes:
            total_esperado = len(afirmacoes_saude_emocional)
            if total_mapeamento != total_esperado:
                st.warning(f"⚠️ **Atenção:** O mapeamento tem {total_mapeamento} afirmações, mas deveria ter {total_esperado}. Verifique se todas as afirmações foram classificadas.")
            else:
                st.success(f"✅ **Perfeito!** Todas as {total_esperado} afirmações estão classificadas nas dimensões.")
        
        st.info("💡 **Dica:** Use esta tabela para revisar se as afirmações estão classificadas corretamente. Se precisar ajustar, você pode modificar as palavras-chave no código (variável `palavras_chave_dimensoes`).")
        st.divider()
        
        # ==================== AFIRMAÇÕES QUE NÃO ESTÃO EM SAÚDE EMOCIONAL ====================
        st.subheader("📝 Afirmações que NÃO estão em Saúde Emocional")
        st.markdown("**🔍 Lista completa de afirmações que não foram classificadas como saúde emocional, com códigos únicos para movimentação.**")
        
        # Obter códigos das afirmações de saúde emocional (com tipo para evitar conflitos)
        codigos_se_arq = set()
        codigos_se_micro = set()
        for af in afirmacoes_saude_emocional:
            if af['tipo'] == 'Arquétipo':
                codigos_se_arq.add(str(af['chave']).strip())
            else:
                codigos_se_micro.add(str(af['chave']).strip())
        
        # Obter TODAS as afirmações únicas de arquétipos (usando drop_duplicates)
        todas_afirmacoes_arq = matriz_arq[['COD_AFIRMACAO', 'AFIRMACAO', 'ARQUETIPO']].drop_duplicates(subset=['COD_AFIRMACAO'])
        
        # Listar todas as afirmações de arquétipos que NÃO estão em SE
        afirmacoes_nao_se_arq = []
        codigos_arq_unicos = set()
        
        for _, row in todas_afirmacoes_arq.iterrows():
            codigo = str(row['COD_AFIRMACAO']).strip()
            if codigo not in codigos_se_arq and codigo not in codigos_arq_unicos:
                codigos_arq_unicos.add(codigo)
                afirmacoes_nao_se_arq.append({
                    'codigo_original': codigo,
                    'afirmacao': row['AFIRMACAO'],
                    'arquetipo': row['ARQUETIPO']
                })
        
        # Obter TODAS as afirmações únicas de microambiente (usando drop_duplicates)
        todas_afirmacoes_micro = matriz_micro[['COD', 'AFIRMACAO', 'DIMENSAO', 'SUBDIMENSAO']].drop_duplicates(subset=['COD'])
        
        # Listar todas as afirmações de microambiente que NÃO estão em SE
        afirmacoes_nao_se_micro = []
        codigos_micro_unicos = set()
        
        for _, row in todas_afirmacoes_micro.iterrows():
            codigo = str(row['COD']).strip()
            if codigo not in codigos_se_micro and codigo not in codigos_micro_unicos:
                codigos_micro_unicos.add(codigo)
                afirmacoes_nao_se_micro.append({
                    'codigo_original': codigo,
                    'afirmacao': row['AFIRMACAO'],
                    'dimensao': row['DIMENSAO'],
                    'subdimensao': row['SUBDIMENSAO']
                })
        
        # DEBUG: Mostrar totais para verificação
        total_arq_unicos = len(todas_afirmacoes_arq)
        total_micro_unicos = len(todas_afirmacoes_micro)
        total_geral_esperado = total_arq_unicos + total_micro_unicos
        total_se = len(codigos_se_arq) + len(codigos_se_micro)
        total_nao_se = len(afirmacoes_nao_se_arq) + len(afirmacoes_nao_se_micro)
        
        # Verificar códigos que estão faltando
        todos_codigos_arq_esperados = set(str(cod).strip() for cod in todas_afirmacoes_arq['COD_AFIRMACAO'].unique())
        todos_codigos_micro_esperados = set(str(cod).strip() for cod in todas_afirmacoes_micro['COD'].unique())
        
        # Códigos encontrados (SE + Não-SE)
        codigos_encontrados_arq = codigos_se_arq.union(set(af['codigo_original'] for af in afirmacoes_nao_se_arq))
        codigos_encontrados_micro = codigos_se_micro.union(set(af['codigo_original'] for af in afirmacoes_nao_se_micro))
        
        # Códigos faltantes
        codigos_faltantes_arq = todos_codigos_arq_esperados - codigos_encontrados_arq
        codigos_faltantes_micro = todos_codigos_micro_esperados - codigos_encontrados_micro
        
        st.markdown(f"**📊 Verificação de Contagem Detalhada:**")
        st.markdown(f"- Total de afirmações únicas (Arquétipos): {total_arq_unicos}")
        st.markdown(f"- Total de afirmações únicas (Microambiente): {total_micro_unicos}")
        st.markdown(f"- **Total esperado: {total_geral_esperado} afirmações**")
        st.markdown(f"- Total em Saúde Emocional: {total_se}")
        st.markdown(f"- Total NÃO em Saúde Emocional: {total_nao_se}")
        st.markdown(f"- **Soma (SE + Não-SE): {total_se + total_nao_se}**")
        st.markdown(f"- **Diferença: {total_geral_esperado - (total_se + total_nao_se)} afirmações faltando**")
        
        total_codigos_faltantes = len(codigos_faltantes_arq) + len(codigos_faltantes_micro)
        if total_codigos_faltantes > 0:
            st.error(f"❌ **Erro:** {total_codigos_faltantes} códigos não foram encontrados!")
            if codigos_faltantes_arq:
                st.error(f"   - Arquétipos faltantes ({len(codigos_faltantes_arq)}): {sorted(codigos_faltantes_arq)[:20]}{'...' if len(codigos_faltantes_arq) > 20 else ''}")
            if codigos_faltantes_micro:
                st.error(f"   - Microambiente faltantes ({len(codigos_faltantes_micro)}): {sorted(codigos_faltantes_micro)[:20]}{'...' if len(codigos_faltantes_micro) > 20 else ''}")
            
            # Mostrar detalhes das afirmações faltantes
            with st.expander("🔍 Ver afirmações faltantes em detalhes"):
                if codigos_faltantes_arq:
                    st.markdown("**Arquétipos faltantes:**")
                    # Converter códigos para o mesmo tipo que está no DataFrame
                    codigos_faltantes_arq_conv = [str(c).strip() for c in codigos_faltantes_arq]
                    df_faltantes_arq = todas_afirmacoes_arq[todas_afirmacoes_arq['COD_AFIRMACAO'].astype(str).str.strip().isin(codigos_faltantes_arq_conv)]
                    if not df_faltantes_arq.empty:
                        st.dataframe(df_faltantes_arq[['COD_AFIRMACAO', 'AFIRMACAO', 'ARQUETIPO']], use_container_width=True, hide_index=True)
                
                if codigos_faltantes_micro:
                    st.markdown("**Microambiente faltantes:**")
                    # Converter códigos para o mesmo tipo que está no DataFrame
                    codigos_faltantes_micro_conv = [str(c).strip() for c in codigos_faltantes_micro]
                    df_faltantes_micro = todas_afirmacoes_micro[todas_afirmacoes_micro['COD'].astype(str).str.strip().isin(codigos_faltantes_micro_conv)]
                    if not df_faltantes_micro.empty:
                        st.dataframe(df_faltantes_micro[['COD', 'AFIRMACAO', 'DIMENSAO', 'SUBDIMENSAO']], use_container_width=True, hide_index=True)
        
        if total_se + total_nao_se != total_geral_esperado:
            st.warning(f"⚠️ **Atenção:** Há uma diferença de {total_geral_esperado - (total_se + total_nao_se)} afirmações. Verificando...")
            st.info(f"💡 Arquétipos: esperados {len(todos_codigos_arq_esperados)}, encontrados {len(codigos_encontrados_arq)}")
            st.info(f"💡 Microambiente: esperados {len(todos_codigos_micro_esperados)}, encontrados {len(codigos_encontrados_micro)}")
            
            # Mostrar distribuição
            st.markdown("**📈 Distribuição Detalhada:**")
            st.markdown(f"- Arquétipos em SE: {len(codigos_se_arq)}")
            st.markdown(f"- Arquétipos NÃO em SE: {len(afirmacoes_nao_se_arq)}")
            st.markdown(f"- **Total Arquétipos: {len(codigos_se_arq) + len(afirmacoes_nao_se_arq)} / {total_arq_unicos}**")
            st.markdown(f"- Microambiente em SE: {len(codigos_se_micro)}")
            st.markdown(f"- Microambiente NÃO em SE: {len(afirmacoes_nao_se_micro)}")
            st.markdown(f"- **Total Microambiente: {len(codigos_se_micro) + len(afirmacoes_nao_se_micro)} / {total_micro_unicos}**")
        
        # Criar códigos únicos (a01, a02, ... para arquétipos, m01, m02, ... para microambiente)
        afirmacoes_com_codigo = []
        
        # Arquétipos
        for idx, af in enumerate(afirmacoes_nao_se_arq, 1):
            codigo_unico = f"a{idx:02d}"  # a01, a02, a03, ...
            afirmacoes_com_codigo.append({
                'codigo': codigo_unico,
                'codigo_original': af['codigo_original'],
                'tipo': 'Arquétipo',
                'afirmacao': af['afirmacao'],
                'dimensao': af['arquetipo'],
                'subdimensao': 'N/A'
            })
        
        # Microambiente
        for idx, af in enumerate(afirmacoes_nao_se_micro, 1):
            codigo_unico = f"m{idx:02d}"  # m01, m02, m03, ...
            afirmacoes_com_codigo.append({
                'codigo': codigo_unico,
                'codigo_original': af['codigo_original'],
                'tipo': 'Microambiente',
                'afirmacao': af['afirmacao'],
                'dimensao': af['dimensao'],
                'subdimensao': af['subdimensao']
            })
        
        # Exibir no dashboard
        col1, col2 = st.columns(2)
        with col1:
            st.metric("🧠 Arquétipos não-SE", len(afirmacoes_nao_se_arq))
        with col2:
            st.metric("🏢 Microambiente não-SE", len(afirmacoes_nao_se_micro))
        
        # Tabela completa
        if afirmacoes_com_codigo:
            df_nao_se = pd.DataFrame(afirmacoes_com_codigo)
            df_nao_se.columns = ['Código', 'Código Original', 'Tipo', 'Afirmação', 'Dimensão/Arquétipo', 'Subdimensão']
            st.dataframe(df_nao_se, use_container_width=True, hide_index=True)
            
            # Botão de download
            csv_nao_se = df_nao_se.to_csv(index=False, encoding='utf-8-sig')
            st.download_button(
                label="📥 Download CSV - Afirmações NÃO em Saúde Emocional",
                data=csv_nao_se,
                file_name="afirmacoes_nao_saude_emocional.csv",
                mime="text/csv",
                key="download_nao_se"
            )
            
            # Salvar também em arquivo TXT simples
            try:
                with open('AFIRMACOES_NAO_SAUDE_EMOCIONAL.txt', 'w', encoding='utf-8') as f:
                    f.write("=" * 80 + "\n")
                    f.write("AFIRMAÇÕES QUE NÃO ESTÃO EM SAÚDE EMOCIONAL\n")
                    f.write("=" * 80 + "\n\n")
                    f.write(f"Total: {len(afirmacoes_com_codigo)} afirmações\n")
                    f.write(f"  - Arquétipos: {len(afirmacoes_nao_se_arq)}\n")
                    f.write(f"  - Microambiente: {len(afirmacoes_nao_se_micro)}\n\n")
                    f.write("=" * 80 + "\n\n")
                    
                    # Arquétipos
                    f.write("ARQUÉTIPOS\n")
                    f.write("-" * 80 + "\n")
                    for af in afirmacoes_nao_se_arq:
                        idx = afirmacoes_nao_se_arq.index(af) + 1
                        codigo_unico = f"a{idx:02d}"
                        f.write(f"\n[{codigo_unico}] {af['codigo_original']}\n")
                        f.write(f"Arquétipo: {af['arquetipo']}\n")
                        f.write(f"Afirmação: {af['afirmacao']}\n")
                        f.write("-" * 80 + "\n")
                    
                    f.write("\n\n")
                    
                    # Microambiente
                    f.write("MICROAMBIENTE\n")
                    f.write("-" * 80 + "\n")
                    for af in afirmacoes_nao_se_micro:
                        idx = afirmacoes_nao_se_micro.index(af) + 1
                        codigo_unico = f"m{idx:02d}"
                        f.write(f"\n[{codigo_unico}] {af['codigo_original']}\n")
                        f.write(f"Dimensão: {af['dimensao']}\n")
                        f.write(f"Subdimensão: {af['subdimensao']}\n")
                        f.write(f"Afirmação: {af['afirmacao']}\n")
                        f.write("-" * 80 + "\n")
                    
                    f.write("\n\n")
                    f.write("=" * 80 + "\n")
                    f.write("INSTRUÇÕES PARA MOVIMENTAÇÃO:\n")
                    f.write("=" * 80 + "\n")
                    f.write("Para adicionar uma afirmação à Saúde Emocional, forneça o código.\n")
                    f.write("Exemplo: 'Adicionar a05 à Prevenção de Estresse'\n")
                    f.write("Exemplo: 'Mover m12 de Suporte Emocional para Comunicação Positiva'\n")
                    f.write("=" * 80 + "\n")
                
                st.success(f"✅ Arquivo salvo: `AFIRMACOES_NAO_SAUDE_EMOCIONAL.txt` ({len(afirmacoes_com_codigo)} afirmações)")
            except Exception as e:
                st.warning(f"⚠️ Não foi possível salvar arquivo TXT: {str(e)}")
            
            st.info("💡 **Como usar os códigos:** Use os códigos (ex: `a05`, `m12`) para me pedir movimentações. Exemplo: 'Adicionar a05 à Prevenção de Estresse' ou 'Mover m12 para Comunicação Positiva'")
        else:
            st.success("✅ Todas as afirmações já estão classificadas em Saúde Emocional!")
        
        st.divider()
        
        # ==================== DRILL-DOWN POR CATEGORIA ====================
        st.subheader("🔍 Drill-Down por Categoria de Compliance")
        
        # Seleção da categoria para drill-down
        col1, col2 = st.columns([2, 1])
        
        with col1:
            categoria_selecionada = st.selectbox(
                "Selecione uma categoria para ver as questões detalhadas:",
                ["Todas", "Prevenção de Estresse", "Ambiente Psicológico Seguro", "Suporte Emocional", "Comunicação Positiva", "Equilíbrio Vida-Trabalho"],
                index=None,
                placeholder="Escolha uma categoria...",
                key="categoria_compliance_select"
            )
        
        with col2:
            st.markdown("**💡 Dica:** Você também pode clicar diretamente nas barras do gráfico acima!")
        
        # Adicionar seleção automática via gráfico
        if st.session_state.get('categoria_clicada'):
            categoria_selecionada = st.session_state.categoria_clicada
            st.success(f" Categoria selecionada via gráfico: **{categoria_selecionada}**")
        
        # ==================== APLICAR FILTRO NOS DADOS DOS GRÁFICOS ====================
        # Usar dados filtrados se uma categoria específica foi selecionada
        if categoria_selecionada and categoria_selecionada != "Todas":
            # Filtrar usando diretamente a dimensão de saúde emocional da TABELA_SAUDE_EMOCIONAL.csv
            afirmacoes_saude_emocional_filtradas = [
                af for af in afirmacoes_saude_emocional
                if af.get('dimensao_saude_emocional') == categoria_selecionada
            ]

            if afirmacoes_saude_emocional_filtradas:
                st.success(
                    f"✅ **Filtro aplicado:** {len(afirmacoes_saude_emocional_filtradas)} questões "
                    f"da categoria '{categoria_selecionada}'"
                )
            else:
                afirmacoes_saude_emocional_filtradas = afirmacoes_saude_emocional
                st.warning(
                    f"⚠️ **Nenhuma questão encontrada** para a categoria "
                    f"'{categoria_selecionada}'. Mostrando todas as questões."
                )
        else:
            # Sem filtro ou "Todas" selecionada
            afirmacoes_saude_emocional_filtradas = afirmacoes_saude_emocional
        
        # Separar afirmações por tipo (DEPOIS do filtro)
        afirmacoes_arq = [
            a for a in afirmacoes_saude_emocional_filtradas
            if a['tipo'] == 'Arquétipo'
        ]
        afirmacoes_micro = [
            a for a in afirmacoes_saude_emocional_filtradas
            if a['tipo'] == 'Microambiente'
        ]
        
        # ============================================================
        # 📋 Questões da Categoria (filtrando pela dimensão do CSV)
        # ============================================================
        if categoria_selecionada and categoria_selecionada != "Todas":
            st.markdown(f"### 📋 Questões da Categoria: **{categoria_selecionada}**")
        
            # ✅ FILTRO ÚNICO E CORRETO: pela dimensão definida na TABELA_SAUDE_EMOCIONAL.csv
            afirmacoes_categoria = [
                af for af in afirmacoes_saude_emocional_filtradas
                if af.get('dimensao_saude_emocional') == categoria_selecionada
            ]
        
            if afirmacoes_categoria:
                st.success(f"✅ Encontradas {len(afirmacoes_categoria)} questões na categoria {categoria_selecionada}")
        
                # Mostrar questões encontradas com dados enriquecidos
                for i, af in enumerate(afirmacoes_categoria, 1):
                    with st.expander(f" Questão {i}: {af['afirmacao'][:100]}..."):
                        st.markdown(f"**Tipo:** {af['tipo']}")
                        st.markdown(f"**Dimensão:** {af['dimensao']}")
                        if af['subdimensao'] != 'N/A':
                            st.markdown(f"**Subdimensão:** {af['subdimensao']}")
                        st.markdown(f"**Afirmação completa:** {af['afirmacao']}")
        
                        # Adicionar dados da questão
                        st.divider()
                        st.markdown("**📊 Dados da Questão:**")
        
                        if af['tipo'] == 'Arquétipo':
                            # Para arquétipos, calcular % tendência
                            codigo = af['chave']
                            arquétipo = af['dimensao']
                            estrelas_questao = []
        
                            for _, respondente in df_arq_filtrado.iterrows():
                                if 'respostas' in respondente and codigo in respondente['respostas']:
                                    estrelas = int(respondente['respostas'][codigo])
                                    estrelas_questao.append(estrelas)
        
                            if estrelas_questao:
                                media_estrelas = np.mean(estrelas_questao)
                                media_arredondada = round(media_estrelas)
        
                                # Buscar % tendência
                                chave = f"{arquétipo}{media_arredondada}{codigo}"
                                linha_tendencia = matriz_arq[matriz_arq['CHAVE'] == chave]
        
                                if not linha_tendencia.empty:
                                    tendencia_percentual = linha_tendencia['% Tendência'].iloc[0] * 100
                                    tendencia_info = linha_tendencia['Tendência'].iloc[0]
        
                                    col1, col2, col3 = st.columns(3)
                                    with col1:
                                        st.metric("⭐ Média Estrelas", f"{media_estrelas:.1f}")
                                    with col2:
                                        st.metric("% Tendência", f"{tendencia_percentual:.1f}%")
                                    with col3:
                                        st.metric("Nº Respostas", len(estrelas_questao))
        
                                    st.info(f"**Tendência:** {tendencia_info}")
                                else:
                                    st.warning("⚠️ Dados de tendência não encontrados")
                            else:
                                st.warning("⚠️ Nenhuma resposta encontrada para esta questão")
        
                        else:  # Microambiente
                            codigo_canonico = af['chave']  # ex.: Q45 (matriz)
        
                            # Mapeamento form->canônico e reverso canônico->form
                            MAPEAMENTO_QUESTOES = {
                                'Q01': 'Q01','Q02': 'Q12','Q03': 'Q23','Q04': 'Q34','Q05': 'Q44','Q06': 'Q45',
                                'Q07': 'Q46','Q08': 'Q47','Q09': 'Q48','Q10': 'Q02','Q11': 'Q03','Q12': 'Q04',
                                'Q13': 'Q05','Q14': 'Q06','Q15': 'Q07','Q16': 'Q08','Q17': 'Q09','Q18': 'Q10',
                                'Q19': 'Q11','Q20': 'Q13','Q21': 'Q14','Q22': 'Q15','Q23': 'Q16','Q24': 'Q17',
                                'Q25': 'Q18','Q26': 'Q19','Q27': 'Q20','Q28': 'Q21','Q29': 'Q22','Q30': 'Q24',
                                'Q31': 'Q25','Q32': 'Q26','Q33': 'Q27','Q34': 'Q28','Q35': 'Q29','Q36': 'Q30',
                                'Q37': 'Q31','Q38': 'Q32','Q39': 'Q33','Q40': 'Q35','Q41': 'Q36','Q42': 'Q37',
                                'Q43': 'Q38','Q44': 'Q39','Q45': 'Q40','Q46': 'Q41','Q47': 'Q42','Q48': 'Q43'
                            }
                            REVERSO_FORM = {can: form for form, can in MAPEAMENTO_QUESTOES.items()}
                            codigo_form_json = REVERSO_FORM.get(codigo_canonico, codigo_canonico)  # ex.: Q45 -> Q06
        
                            estrelas_real = []
                            estrelas_ideal = []
        
                            for _, respondente in df_micro_filtrado.iterrows():
                                respostas = respondente.get('respostas', {})
                                if not isinstance(respostas, dict):
                                    continue
        
                                questao_real = f"{codigo_form_json}C"
                                questao_ideal = f"{codigo_form_json}k"
        
                                if questao_real in respostas:
                                    estrelas_real.append(int(respostas[questao_real]))
                                if questao_ideal in respostas:
                                    estrelas_ideal.append(int(respostas[questao_ideal]))
        
                            if estrelas_real and estrelas_ideal:
                                media_real = np.mean(estrelas_real)
                                media_ideal = np.mean(estrelas_ideal)
                                media_real_arredondada = round(media_real)
                                media_ideal_arredondada = round(media_ideal)
        
                                chave = f"{codigo_canonico}_I{media_ideal_arredondada}_R{media_real_arredondada}"
                                linha = matriz_micro[matriz_micro['CHAVE'] == chave]
        
                                if not linha.empty:
                                    pontuacao_real = float(linha['PONTUACAO_REAL'].iloc[0])
                                    pontuacao_ideal = float(linha['PONTUACAO_IDEAL'].iloc[0])
                                    gap = pontuacao_ideal - pontuacao_real
                                else:
                                    pontuacao_real = pontuacao_ideal = gap = 0.0
        
                                col1, col2, col3, col4 = st.columns(4)
                                with col1:
                                    st.metric("⭐ Real", f"{media_real:.1f} ({pontuacao_real:.1f}%)")
                                with col2:
                                    st.metric("⭐ Ideal", f"{media_ideal:.1f} ({pontuacao_ideal:.1f}%)")
                                with col3:
                                    st.metric(" Gap", f"{gap:.1f}%")
                                with col4:
                                    st.metric("Nº Respostas", len(estrelas_real))
        
                                if gap > 80:
                                    st.error(f" **Gap Alto:** {gap:.1f}%")
                                elif gap > 60:
                                    st.error(f" **Gap Alto:** {gap:.1f}%")
                                elif gap > 40:
                                    st.warning(f"🟠 **Gap Moderado:** {gap:.1f}%")
                                elif gap > 20:
                                    st.warning(f"🟡 **Gap Baixo:** {gap:.1f}%")
                                else:
                                    st.success(f"✅ **Gap Mínimo:** {gap:.1f}%")
                            else:
                                st.warning("⚠️ Dados insuficientes para calcular gap")
            else:
                st.warning(f"⚠️ Nenhuma questão encontrada na categoria {categoria_selecionada}.")










    
        # ==================== GRÁFICO 2: MICROAMBIENTE REAL VS IDEAL + GAP ====================
        st.subheader("🏢 Microambiente: Como é vs Como deveria ser vs Gap")
        
        # Filtrar apenas questões de microambiente
        afirmacoes_micro = [a for a in afirmacoes_saude_emocional_filtradas if a['tipo'] == 'Microambiente']
        
        if afirmacoes_micro:
            
            
            
            
            # >>> NOVO (com quebra de linha nas afirmações)
            questoes_micro = []
            medias_real = []
            medias_ideal = []
            gaps = []
            
            def _wrap_affirmacao(txt, max_chars=58, max_lines=3):
                palavras = str(txt).split()
                linhas, atual = [], ""
                for p in palavras:
                    if len(atual) + len(p) + 1 <= max_chars:
                        atual = (atual + " " + p).strip()
                    else:
                        linhas.append(atual)
                        atual = p
                        if len(linhas) == max_lines - 1:  # última linha; corta aqui
                            break
                if atual:
                    linhas.append(atual)
                return "<br>".join(linhas)
            
            for af in afirmacoes_micro:
                codigo_matriz = af['chave']  # ex.: 'Q45'
                real_pct, ideal_pct, gap = calcular_real_ideal_gap_por_questao(
                    df_micro_filtrado, matriz_micro, codigo_matriz
                )
                if real_pct is None:
                    continue
            
                label_quebrado = _wrap_affirmacao(af['afirmacao'], max_chars=58, max_lines=3)
                questoes_micro.append(label_quebrado)
                medias_real.append(real_pct)
                medias_ideal.append(ideal_pct)
                gaps.append(gap)


            
            if questoes_micro:
                # Gráfico de barras agrupadas com 3 barras
                fig_micro = go.Figure()
                
                # Cores baseadas no gap
                cores_gap = []
                for gap in gaps:
                    if gap > 40:
                        cores_gap.append('rgba(255, 0, 0, 0.8)')      # Vermelho (gap alto)
                    elif gap > 20:
                        cores_gap.append('rgba(255, 165, 0, 0.7)')    # Laranja
                    elif gap > 10:
                        cores_gap.append('rgba(255, 255, 0, 0.7)')    # Amarelo
                    else:
                        cores_gap.append('rgba(0, 128, 0, 0.7)')      # Verde (gap baixo)
                
                # Barras para Real
                fig_micro.add_trace(go.Bar(
                    name='Como é (Real)',
                    x=questoes_micro,
                    y=medias_real,
                    marker_color='rgba(255, 165, 0, 0.7)',
                    text=[f"{v:.1f}%" for v in medias_real],
                    textposition='auto'
                ))
                
                # Barras para Ideal
                fig_micro.add_trace(go.Bar(
                    name='Como deveria ser (Ideal)',
                    x=questoes_micro,
                    y=medias_ideal,
                    marker_color='rgba(0, 128, 0, 0.7)',
                    text=[f"{v:.1f}%" for v in medias_ideal],
                    textposition='auto'
                ))
                
                # Barras para Gap (3ª barra) - COR DIFERENTE
                fig_micro.add_trace(go.Bar(
                    name='Gap (Ideal - Real)',
                    x=questoes_micro,
                    y=gaps,
                    marker_color='rgba(138, 43, 226, 0.7)',  # AZUL ROXO para diferenciar
                    text=[f"{v:.1f}" for v in gaps],
                    textposition='auto'
                ))
                
                fig_micro.update_layout(
                    title="🏢 Questões de Microambiente - Real vs Ideal vs Gap",
                    xaxis_title="Questões",
                    yaxis_title="Percentual (%) / Gap",
                    barmode='group',
                    height=600,
                    xaxis_tickangle=-45
                )
                
                st.plotly_chart(fig_micro, use_container_width=True)
                
                # Legenda das cores do gap
                st.markdown("**🎨 Legenda das Cores do Gap:**")
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.markdown("🟢 **Verde:** Gap ≤ 10% (Bom)")
                with col2:
                    st.markdown("🟡 **Amarelo:** Gap 10-20% (Regular)")
                with col3:
                    st.markdown("🟠 **Laranja:** Gap 20-40% (Ruim)")
                with col4:
                    st.markdown("🔴 **Vermelho:** Gap > 40% (Muito Ruim)")
        
        st.divider()
        
        # ==================== SCORE FINAL + TERMÔMETRO ====================
        st.subheader("🌡️ Score Final de Saúde Emocional")
        
        # Calcular score final de forma consistente com o gráfico de Compliance
        # Se uma categoria específica foi filtrada, usar o valor daquela categoria
        # Caso contrário, usar a média das 5 categorias
        if categoria_selecionada and categoria_selecionada != "Todas" and categoria_selecionada in categoria_medias:
            # Quando filtra uma categoria, mostrar o score daquela categoria específica
            score_final = categoria_medias[categoria_selecionada]
        elif categoria_medias and len(categoria_medias) > 0:
            # Sem filtro: calcular média das 5 categorias (mesmas do gráfico de Compliance)
            valores_categorias = [v for v in categoria_medias.values() if v > 0]
            if valores_categorias:
                score_final = np.mean(valores_categorias)
            else:
                score_final = 0
        else:
            score_final = 0
        
        # Calcular scores individuais para exibição (opcional, para referência)
        score_arquetipos = 0
        score_microambiente = 0
        
        # Score Arquétipos (baseado na distribuição das categorias)
        if afirmacoes_arq:
            # Calcular tendência geral dos arquétipos
            tendencias_gerais = []
            for af in afirmacoes_arq:
                codigo = af['chave']
                arquétipo = af['dimensao']
                
                # Buscar na matriz
                linha = matriz_arq[matriz_arq['COD_AFIRMACAO'] == codigo]
                if not linha.empty:
                    # Calcular média de estrelas
                    estrelas_questao = []
                    for _, respondente in df_arq_filtrado.iterrows():
                        if 'respostas' in respondente and codigo in respondente['respostas']:
                            estrelas = int(respondente['respostas'][codigo])
                            estrelas_questao.append(estrelas)
                    
                    if estrelas_questao:
                        media_estrelas = np.mean(estrelas_questao)
                        media_arredondada = round(media_estrelas)
                        percentual_corrigido = round((media_estrelas / 6) * 100, 2)
                        
                        # Buscar apenas o TEXTO da tendência na tabela
                        chave = f"{arquétipo}{media_arredondada}{codigo}"
                        linha_tendencia = matriz_arq[matriz_arq['CHAVE'] == chave]
                        
                        if not linha_tendencia.empty:
                            tendencia_info = linha_tendencia['Tendência'].iloc[0]
                            
                            # Converter para score usando percentual corrigido
                            if 'DESFAVORÁVEL' in tendencia_info:
                                score = max(0, 100 - percentual_corrigido)
                            else:
                                score = percentual_corrigido
                            
                            tendencias_gerais.append(score)
            
            if tendencias_gerais:
                score_arquetipos = np.mean(tendencias_gerais)

        
        # Score Microambiente (baseado no gap médio)
        if afirmacoes_micro and 'gaps' in locals() and gaps:
            gap_medio = np.mean(gaps)
            # Converter gap para score (gap baixo = score alto)
            score_microambiente = max(0, 100 - gap_medio)
        
        # Interpretação do score (faixas mais severas)
        if score_final >= 80:
            interpretacao = "🟢 EXCELENTE - acima de 80%"
            cor_score = "green"
        elif score_final >= 75:
            interpretacao = "🟢 ÓTIMO - entre 75% e 79,99%"
            cor_score = "darkgreen"
        elif score_final >= 70:
            interpretacao = "🟡 BOM - entre 70% e 74,99%"
            cor_score = "orange"
        elif score_final >= 60:
            interpretacao = "🟠 REGULAR - entre 60% e 69,99%"
            cor_score = "darkorange"
        else:
            interpretacao = "🔴 NÃO ADEQUADO - abaixo de 60%"
            cor_score = "red"

        
        # Exibir score final
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown(f"""
            <div style="text-align: center; padding: 20px; border: 3px solid {cor_score}; border-radius: 10px;">
                <h2 style="color: {cor_score}; margin: 0;">{score_final:.1f}%</h2>
                <p style="margin: 5px 0; font-size: 18px;">Score Final</p>
                <p style="margin: 5px 0; font-size: 14px;">Saúde Emocional</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div style="padding: 20px; background-color: rgba(0,0,0,0.05); border-radius: 10px;">
                <h3>📊 Como o Score é Calculado</h3>
                <p><strong>{interpretacao}</strong></p>
                <p><strong>🧠 Score Arquétipos:</strong> {score_arquetipos:.1f}% (referência)</p>
                <p><strong>🏢 Score Microambiente:</strong> {score_microambiente:.1f}% (referência)</p>
                <p><strong>💚 Score Final:</strong> {'Score da categoria filtrada' if categoria_selecionada and categoria_selecionada != 'Todas' else 'Média das 5 categorias do gráfico de Compliance'} (consistente com o gráfico acima)</p>
                <p><strong>🎯 Interpretação:</strong> Quanto maior o score, melhor a saúde emocional proporcionada pelo líder</p>
                <hr>
                <h4>Legenda dos Níveis</h4>
                <table style="width:100%; font-size: 13px; border-collapse: collapse;">
                    <tr>
                        <th style="text-align:left; padding: 4px; border-bottom: 1px solid #ccc;">Faixa</th>
                        <th style="text-align:left; padding: 4px; border-bottom: 1px solid #ccc;">Nível</th>
                        <th style="text-align:left; padding: 4px; border-bottom: 1px solid #ccc;">Descrição</th>
                    </tr>
                    <tr>
                        <td style="padding: 4px;">≥ 80%</td>
                        <td style="padding: 4px;">Excelente</td>
                        <td style="padding: 4px;">Ambiente saudável de excelência</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;">75% a 79,99%</td>
                        <td style="padding: 4px;">Ótimo</td>
                        <td style="padding: 4px;">Ambiente saudável</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;">70% a 74,99%</td>
                        <td style="padding: 4px;">Bom</td>
                        <td style="padding: 4px;">Ambiente saudável com pontos a melhorar</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;">60% a 69,99%</td>
                        <td style="padding: 4px;">Regular</td>
                        <td style="padding: 4px;">Ambiente necessita melhorias</td>
                    </tr>
                    <tr>
                        <td style="padding: 4px;">&lt; 60%</td>
                        <td style="padding: 4px;">Não Adequado</td>
                        <td style="padding: 4px;">Ambiente necessita apoio em plano de ação (PDI)</td>
                    </tr>
                </table>
            </div>
            """, unsafe_allow_html=True)

        
        st.divider()
        
        # ==================== TABELAS SEPARADAS ====================
        st.subheader("📋 Análise Detalhada por Tipo")
        
        # ==================== TABELA 1: ARQUÉTIPOS ====================
        if afirmacoes_arq:
            st.markdown("** Questões de Arquétipos - Saúde Emocional**")
            
            # Criar DataFrame para arquétipos
            df_arq_detalhado = pd.DataFrame(afirmacoes_arq)
            
            # Adicionar colunas de análise
            tendencias_arq = []
            percentuais_arq = []
            
            for _, row in df_arq_detalhado.iterrows():
                codigo = row['chave']
                arquétipo = row['dimensao']
                
                # Buscar na matriz
                linha = matriz_arq[matriz_arq['COD_AFIRMACAO'] == codigo]
                if not linha.empty:
                    # Calcular média de estrelas
                    estrelas_questao = []
                    for _, respondente in df_arq_filtrado.iterrows():
                        if 'respostas' in respondente and codigo in respondente['respostas']:
                            estrelas = int(respondente['respostas'][codigo])
                            estrelas_questao.append(estrelas)
                    
                    if estrelas_questao:
                        media_estrelas = np.mean(estrelas_questao)
                        media_arredondada = round(media_estrelas)
                        percentual_calculado = round((media_estrelas / 6) * 100, 2)
                        
                        # Buscar tendência baseado na média arredondada (apenas para o texto)
                        chave = f"{arquétipo}{media_arredondada}{codigo}"
                        linha_tendencia = matriz_arq[matriz_arq['CHAVE'] == chave]
                        
                        if not linha_tendencia.empty:
                            tendencia_info = linha_tendencia['Tendência'].iloc[0]
                            tendencias_arq.append(tendencia_info)
                            percentuais_arq.append(f"{percentual_calculado:.1f}%")
                        else:
                            tendencias_arq.append("N/A")
                            percentuais_arq.append("N/A")
                    else:
                        tendencias_arq.append("N/A")
                        percentuais_arq.append("N/A")
                else:
                    tendencias_arq.append("N/A")
                    percentuais_arq.append("N/A")
            
            df_arq_detalhado['% Tendência'] = percentuais_arq
            df_arq_detalhado['Tendência'] = tendencias_arq
            
                        
            # Função para aplicar cores baseadas na tendência
            def color_tendencia_arq(val):
                val_str = str(val).strip()
                
                if val_str == 'MUITO FAVORÁVEL':
                    return 'background-color: rgba(173, 216, 230, 0.8)'  # Azul claro
                elif val_str == 'FAVORÁVEL':
                    return 'background-color: rgba(0, 128, 0, 0.8)'      # Verde escuro
                elif val_str == 'POUCO FAVORÁVEL':
                    return 'background-color: rgba(144, 238, 144, 0.8)'  # Verde claro
                elif val_str == 'POUCO DESFAVORÁVEL':
                    return 'background-color: rgba(255, 255, 0, 0.7)'    # Amarelo
                elif val_str == 'DESFAVORÁVEL':
                    return 'background-color: rgba(255, 165, 0, 0.7)'    # Laranja
                elif val_str == 'MUITO DESFAVORÁVEL':
                    return 'background-color: rgba(255, 0, 0, 0.8)'      # Vermelho
                else:
                    return 'background-color: rgba(200, 200, 200, 0.3)'   # Cinza
            
            # Preparar colunas para exibição
            df_arq_exibir = df_arq_detalhado[['chave', 'afirmacao', 'dimensao', '% Tendência', 'Tendência']].copy()
            df_arq_exibir.columns = ['Questão', 'Afirmação', 'Arquétipo', '% Tendência', 'Tendência']
            
            # Aplicar cores
            df_arq_styled = df_arq_exibir.style.map(color_tendencia_arq, subset=['Tendência'])
            
            st.dataframe(df_arq_styled, use_container_width=True)
            
            # Download arquétipos
            csv_arq = df_arq_exibir.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV - Arquétipos SE",
                data=csv_arq,
                file_name="saude_emocional_arquetipos.csv",
                mime="text/csv"
            )
        
        st.divider()
        
        # ==================== TABELA 2: MICROAMBIENTE ====================
        if afirmacoes_micro:
            st.markdown("**🏢 Questões de Microambiente - Saúde Emocional**")
            
            # Criar DataFrame para microambiente
            df_micro_detalhado = pd.DataFrame(afirmacoes_micro)
            
            # Adicionar colunas de análise
            reais_micro = []
            ideais_micro = []
            gaps_micro = []


            # carrega pontos máximos da subdimensão (para converter em % como no microambiente)
            _, _, pontos_max_subdimensao = carregar_matrizes_microambiente()
            
            # mapeamento formulário->canônico e reverso canônico->form (para ler JSON corretamente)
            MAPEAMENTO_QUESTOES = {
                'Q01': 'Q01','Q02': 'Q12','Q03': 'Q23','Q04': 'Q34','Q05': 'Q44','Q06': 'Q45',
                'Q07': 'Q46','Q08': 'Q47','Q09': 'Q48','Q10': 'Q02','Q11': 'Q03','Q12': 'Q04',
                'Q13': 'Q05','Q14': 'Q06','Q15': 'Q07','Q16': 'Q08','Q17': 'Q09','Q18': 'Q10',
                'Q19': 'Q11','Q20': 'Q13','Q21': 'Q14','Q22': 'Q15','Q23': 'Q16','Q24': 'Q17',
                'Q25': 'Q18','Q26': 'Q19','Q27': 'Q20','Q28': 'Q21','Q29': 'Q22','Q30': 'Q24',
                'Q31': 'Q25','Q32': 'Q26','Q33': 'Q27','Q34': 'Q28','Q35': 'Q29','Q36': 'Q30',
                'Q37': 'Q31','Q38': 'Q32','Q39': 'Q33','Q40': 'Q35','Q41': 'Q36','Q42': 'Q37',
                'Q43': 'Q38','Q44': 'Q39','Q45': 'Q40','Q46': 'Q41','Q47': 'Q42','Q48': 'Q43'
            }
            REVERSO_FORM = {can: form for form, can in MAPEAMENTO_QUESTOES.items()}

            
            for _, row in df_micro_detalhado.iterrows():
                # usa a MATRIZ para obter Real/Ideal/GAP por questão (0–100)
                real_pct, ideal_pct, gap = calcular_real_ideal_gap_por_questao(
                    df_micro_filtrado, matriz_micro, row['chave']  # row['chave'] já é o canônico (ex.: Q45)
                )
                
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
            
            # Função para aplicar cores baseadas no gap
            def color_gap_micro(val):
                try:
                    gap_val = float(val)
                    if gap_val > 80:
                        return 'background-color: rgba(255, 0, 0, 0.8)'  # Vermelho
                    elif gap_val > 60:
                        return 'background-color: rgba(255, 100, 0, 0.8)'  # Vermelho-laranja
                    elif gap_val > 40:
                        return 'background-color: rgba(255, 165, 0, 0.7)'  # Laranja
                    elif gap_val > 20:
                        return 'background-color: rgba(255, 255, 0, 0.6)'  # Amarelo
                    elif gap_val > 0:
                        return 'background-color: rgba(144, 238, 144, 0.6)'  # Verde claro
                    else:
                        return 'background-color: rgba(0, 255, 0, 0.5)'  # Verde
                except:
                    return 'background-color: transparent'
            
            # Preparar colunas para exibição
            df_micro_exibir = df_micro_detalhado[['chave', 'afirmacao', 'dimensao', 'subdimensao', 'Real', 'Ideal', 'Gap']].copy()
            df_micro_exibir.columns = ['Questão', 'Afirmação', 'Dimensão', 'Subdimensão', 'Real (%)', 'Ideal (%)', 'Gap']
            
            # Aplicar cores
            df_micro_styled = df_micro_exibir.style.map(color_gap_micro, subset=['Gap'])
            
            st.dataframe(df_micro_styled, use_container_width=True)
            
            # Download microambiente
            csv_micro = df_micro_exibir.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV - Microambiente SE",
                data=csv_micro,
                file_name="saude_emocional_microambiente.csv",
                mime="text/csv"
            )
    
    if not afirmacoes_saude_emocional:
        st.warning("⚠️ Nenhuma afirmação relacionada à saúde emocional foi identificada.")
        st.info(" Dica: Verifique se as palavras-chave estão presentes nas afirmações existentes.")


