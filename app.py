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
    """Analisa afirmações existentes e identifica as relacionadas à saúde emocional com filtros aplicados"""
    
    
    
    # Palavras-chave relacionadas à saúde emocional (EXPANDIDAS para capturar mais questões)
    palavras_chave_saude_emocional = [
        # Empatia e Compreensão
        'empatia', 'compreensão', 'compreensao', 'entendimento', 'percebe', 'oferece',
        'compreensivo', 'atento', 'sensível', 'sensivel', 'cuidadoso',
            
        # Suporte e Apoio
        'suporte', 'apoio', 'ajuda', 'assistência', 'assistencia', 'ajudar', 'resolver',
        'orientar', 'guiar', 'acompanhar', 'estar presente', 'disponível', 'disponivel',
            
        # Estresse e Pressão (EXPANDIDO)
        'estresse', 'ansiedade', 'pressão', 'pressao', 'cobrança', 'cobranca', 'deadline', 
        'prazos', 'tensão', 'tensao', 'sobrecarga', 'excesso', 'cansaço', 'cansaco', 'fadiga', 
        'desgaste', 'preocupação', 'preocupacao', 'nervoso', 'irritado', 'frustrado', 'angustiado', 
        'estressado', 'sobrecarregado',
            
        # Bem-estar e Saúde
        'bem-estar', 'bem estar', 'saúde', 'saude', 'mental', 'felicidade', 'satisfação', 'satisfacao',
        'alegria', 'motivação', 'motivacao', 'energia', 'vitalidade', 'disposição', 'disposicao',
            
        # Reconhecimento e Valorização
        'reconhecimento', 'celebração', 'celebracao', 'valorização', 'valorizacao', 'elogio',
        'agradecimento', 'gratidão', 'gratidao', 'merece', 'merecido', 'esforço', 'esforco',
            
        # Feedback e Comunicação Positiva
        'feedback', 'positivo', 'construtivo', 'encorajamento', 'comentários', 'comentarios',
        'palavras', 'amáveis', 'amaveis', 'gentil', 'carinhoso', 'atencioso',
        'desenvolvimento', 'futuro', 'potencial', 'capacidade', 'habilidade',
            
        # Ambiente e Segurança
        'ambiente', 'seguro', 'proteção', 'protecao', 'respeito', 'cuidadoso', 'palavras',
        'acolhedor', 'inclusivo', 'tolerante', 'paciente', 'calmo', 'tranquilo',
            
        # Equilíbrio Vida-Trabalho (EXPANDIDO)
        'equilíbrio', 'equilibrio', 'flexibilidade', 'horários', 'horarios', 'tempo', 'família', 'familia',
        'pessoal', 'relação', 'relacao', 'vida pessoal', 'descanso', 'pausa', 'intervalo', 'folga', 
        'feriado', 'férias', 'ferias', 'licença', 'licenca',
            
        # Desenvolvimento e Crescimento
        'desenvolvimento', 'crescimento', 'pessoal', 'participação', 'participacao', 'motivação', 'motivacao',
        'aprendizado', 'evolução', 'evolucao', 'progresso', 'melhoria', 'oportunidades', 'expressar', 
        'ideias', 'opiniões', 'opinioes', 'criatividade',
            
        # Comunicação e Diálogo
        'comunicação', 'comunicacao', 'diálogo', 'dialogo', 'escuta', 'ouvir', 'conversa',
        'debate', 'discussão', 'discussao', 'colaboração', 'colaboracao', 'trabalho em equipe',
            
        # Confiança e Respeito
        'confiança', 'confianca', 'respeito', 'dignidade', 'humanidade', 'honestidade',
        'transparência', 'transparencia', 'ética', 'etica', 'moral', 'valores',
            
        # Prevenção e Gestão (NOVAS - para capturar questões de prevenção)
        'prevenção', 'prevencao', 'evitar', 'reduzir', 'diminuir', 'controlar', 'gerenciar',
        'administrar', 'organizar', 'planejar', 'estratégia', 'estrategia', 'método', 'metodo',
        'técnica', 'tecnica', 'ferramenta', 'recurso', 'solução', 'solucao', 'alternativa',
        'opção', 'opcao', 'escolha', 'decisão', 'decisao', 'ação', 'acao', 'medida',
        'política', 'politica', 'procedimento', 'protocolo', 'norma', 'regra', 'padrão', 'padrao',
            
        # Prevenção de Estresse - Palavras-chave ESPECÍFICAS das suas afirmações
        'preocupa com o tempo', 'preocupa com detalhes', 'preocupa se', 'preocupa com',
        'necessidade de se aprofundar', 'aprofundar nos detalhes', 'detalhes na execução',
        'detalhes de realização', 'detalhes do trabalho', 'sem necessidade de ficar de olho',
        'fazer todo o possivel', 'resolver problemas particulares', 'problemas particulares urgentes',
        'atuar na solução de conflitos', 'solução de conflitos em sua equipe',
        'risco calculado', 'resultasse em algo negativo', 'seriam apoiados',
        'leais uns com os outros', 'mais elogiados e incentivados', 'do que criticados'
    ]
    
    afirmacoes_se = []
    codigos_ja_processados = set()  # Para evitar repetições
    
    # Aplicar filtros aos dados
    df_arq_filtrado = df_arquetipos.copy()
    df_micro_filtrado = df_microambiente.copy()
    
    # Filtrar arquétipos
    if filtros['empresa'] != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['empresa'] == filtros['empresa']]
    if filtros['codrodada'] != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['codrodada'] == filtros['codrodada']]
    if 'emailLider' in filtros and filtros['emailLider'] != "Todos":
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
    
    # Filtrar microambiente
    if filtros['empresa'] != "Todas":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['empresa'] == filtros['empresa']]
    if filtros['codrodada'] != "Todas":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['codrodada'] == filtros['codrodada']]
    if 'emailLider' in filtros and filtros['emailLider'] != "Todos":
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['emailLider'] == filtros['emailLider']]
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
    
    # Analisar matriz de arquétipos
    for _, row in matriz_arq.iterrows():
        codigo = row['COD_AFIRMACAO']
        if codigo not in codigos_ja_processados:  # Evita repetições
            afirmacao = str(row['AFIRMACAO']).lower()
            if any(palavra in afirmacao for palavra in palavras_chave_saude_emocional):
                afirmacoes_se.append({
                    'tipo': 'Arquétipo',
                    'afirmacao': row['AFIRMACAO'],
                    'dimensao': row['ARQUETIPO'],
                    'subdimensao': 'N/A',
                    'chave': codigo
                })
                codigos_ja_processados.add(codigo)  # Marca como processado
    
    # Analisar matriz de microambiente
    for _, row in matriz_micro.iterrows():
        codigo = row['COD']
        if codigo not in codigos_ja_processados:  # Evita repetições
            afirmacao = str(row['AFIRMACAO']).lower()
            if any(palavra in afirmacao for palavra in palavras_chave_saude_emocional):
                afirmacoes_se.append({
                    'tipo': 'Microambiente',
                    'afirmacao': row['AFIRMACAO'],
                    'dimensao': row['DIMENSAO'],
                    'subdimensao': row['SUBDIMENSAO'],
                    'chave': codigo
                })
                codigos_ja_processados.add(codigo)  # Marca como processado
                
    
    
    return afirmacoes_se, df_arq_filtrado, df_micro_filtrado
    
# MAPEAR COMPLIANCE COM NR-1 (MANTIDO IGUAL)
def mapear_compliance_nr1(afirmacoes_saude_emocional):
    """Mapeia afirmações de saúde emocional com requisitos da NR-1"""
    
    
    compliance = {
        'Prevenção de Estresse': [],
        'Ambiente Psicológico Seguro': [],
        'Suporte Emocional': [],
        'Comunicação Positiva': [],
        'Equilíbrio Vida-Trabalho': []
    }
    
    # afirmacoes_saude_emocional já é uma lista
    for afirmacao in afirmacoes_saude_emocional:
        af = afirmacao['afirmacao'].lower()
        
        # Prevenção de Estresse (EXPANDIDO)
        if any(palavra in af for palavra in ['estresse', 'ansiedade', 'pressão', 'pressao', 'cobrança', 'cobranca', 'deadline', 'prazos', 'tensão', 'tensao', 'sobrecarga', 'preocupa com o tempo', 'preocupa com detalhes', 'preocupa se', 'necessidade de se aprofundar', 'aprofundar nos detalhes', 'detalhes na execução', 'detalhes de realização', 'detalhes do trabalho', 'sem necessidade de ficar de olho', 'fazer todo o possivel', 'resolver problemas particulares', 'problemas particulares urgentes', 'atuar na solução de conflitos', 'solução de conflitos em sua equipe', 'risco calculado', 'resultasse em algo negativo', 'seriam apoiados', 'leais uns com os outros', 'mais elogiados e incentivados', 'do que criticados']):
            compliance['Prevenção de Estresse'].append(afirmacao)
        
        # Ambiente Psicológico Seguro
        elif any(palavra in af for palavra in ['ambiente', 'seguro', 'proteção', 'protecao', 'respeito', 'cuidadoso', 'palavras']):
            compliance['Ambiente Psicológico Seguro'].append(afirmacao)
        
        # Suporte Emocional
        elif any(palavra in af for palavra in ['suporte', 'apoio', 'ajuda', 'assistência', 'assistencia', 'ajudar', 'resolver', 'percebe', 'oferece']):
            compliance['Suporte Emocional'].append(afirmacao)
        
        # Comunicação Positiva
        elif any(palavra in af for palavra in ['feedback', 'positivo', 'construtivo', 'encorajamento', 'comentários', 'comentarios', 'positivos', 'desenvolvimento', 'futuro']):
            compliance['Comunicação Positiva'].append(afirmacao)
        
        # Equilíbrio Vida-Trabalho (EXPANDIDO)
        elif any(palavra in af for palavra in ['equilíbrio', 'equilibrio', 'flexibilidade', 'horários', 'horarios', 'tempo', 'família', 'familia', 'pessoal', 'relação', 'relacao', 'vida pessoal']):
            compliance['Equilíbrio Vida-Trabalho'].append(afirmacao)
        
        # Se não couber em nenhuma categoria, coloca em Suporte Emocional (mais genérico)
        else:
            compliance['Suporte Emocional'].append(afirmacao)
    
    return compliance

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

    vals_real, vals_ideal = [], []
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
            # usa código da MATRIZ na chave (ex.: Q45_I6_R4)
            chave = f"{codigo_matriz}_I{i}_R{r}"
            linha = matriz_micro[matriz_micro['CHAVE'] == chave]
            if not linha.empty:
                vals_real.append(float(linha['PONTUACAO_REAL'].iloc[0]))
                vals_ideal.append(float(linha['PONTUACAO_IDEAL'].iloc[0]))

    if not vals_real or not vals_ideal:
        return None, None, None

    real_pct  = float(np.mean(vals_real))
    ideal_pct = float(np.mean(vals_ideal))
    gap       = ideal_pct - real_pct
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
    
        vals_real, vals_ideal = [], []
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
                chave = f"{codigo_matriz}_I{i}_R{r}"   # usa código da MATRIZ
                linha = matriz_micro[matriz_micro['CHAVE'] == chave]
                if not linha.empty:
                    vals_real.append(float(linha['PONTUACAO_REAL'].iloc[0]))
                    vals_ideal.append(float(linha['PONTUACAO_IDEAL'].iloc[0]))
    
        if not vals_real or not vals_ideal:
            return None, None, None
    
        real_pct  = float(np.mean(vals_real))
        ideal_pct = float(np.mean(vals_ideal))
        gap       = ideal_pct - real_pct
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
            
            # Buscar % tendência baseado na média arredondada
            chave = f"{arquétipo_clicado}{media_arredondada}{questao}"
            linha = matriz[matriz['CHAVE'] == chave]
            tendencia_percentual = linha['% Tendência'].iloc[0] * 100 if not linha.empty else 0
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
        
        todas_holdings = sorted(list(holdings_arq.union(holdings_micro)))
        
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
        todas_empresas = sorted(list(empresas_arq.union(empresas_micro)))
        empresas = ["Todas"] + todas_empresas
        empresa_selecionada = st.sidebar.selectbox("   Empresa", empresas)
        
        # Combinar codrodadas de ambos os datasets
        codrodadas_arq = set(df_arquetipos['codrodada'].unique())
        codrodadas_micro = set(df_microambiente['codrodada'].unique())
        todas_codrodadas = sorted(list(codrodadas_arq.union(codrodadas_micro)))
        codrodadas = ["Todas"] + todas_codrodadas
        codrodada_selecionada = st.sidebar.selectbox("   Código da Rodada", codrodadas)
        
        # Combinar emails de líderes de ambos os datasets
        emailliders_arq = set(df_arquetipos['emailLider'].unique())
        emailliders_micro = set(df_microambiente['emailLider'].unique())
        todos_emailliders = sorted(list(emailliders_arq.union(emailliders_micro)))
        emailliders = ["Todos"] + todos_emailliders
        emaillider_selecionado = st.sidebar.selectbox("👤 Email do Líder", emailliders)
        
        # Combinar estados de ambos os datasets
        estados_arq = set(df_arquetipos['estado'].unique())
        estados_micro = set(df_microambiente['estado'].unique())
        todos_estados = sorted(list(estados_arq.union(estados_micro)))
        estados = ["Todos"] + todos_estados
        estado_selecionado = st.sidebar.selectbox("🗺️ Estado", estados)
        
        # Combinar gêneros de ambos os datasets
        generos_arq = set(df_arquetipos['sexo'].unique())
        generos_micro = set(df_microambiente['sexo'].unique())
        todos_generos = sorted(list(generos_arq.union(generos_micro)))
        generos = ["Todos"] + todos_generos
        genero_selecionado = st.sidebar.selectbox("⚧ Gênero", generos)
        
        # Combinar etnias de ambos os datasets
        etnias_arq = set(df_arquetipos['etnia'].unique())
        etnias_micro = set(df_microambiente['etnia'].unique())
        todas_etnias = sorted(list(etnias_arq.union(etnias_micro)))
        etnias = ["Todas"] + todas_etnias
        etnia_selecionada = st.sidebar.selectbox("   Etnia", etnias)
        
        # Combinar departamentos de ambos os datasets
        departamentos_arq = set(df_arquetipos['departamento'].unique())
        departamentos_micro = set(df_microambiente['departamento'].unique())
        todos_departamentos = sorted(list(departamentos_arq.union(departamentos_micro)))
        departamentos = ["Todos"] + todos_departamentos
        departamento_selecionado = st.sidebar.selectbox("🏢 Departamento", departamentos)
        
        # Combinar cargos de ambos os datasets
        cargos_arq = set(df_arquetipos['cargo'].unique())
        cargos_micro = set(df_microambiente['cargo'].unique())
        todos_cargos = sorted(list(cargos_arq.union(cargos_micro)))
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
                            df_questoes_styled = df_questoes[['Questão', 'Afirmação', '% Tendência', 'Tendência', 'Média Estrelas', 'Média Arredondada', 'Nº Respostas']].style.applymap(color_tendencia, subset=['Tendência'])
                            
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
                            df_questoes_styled = df_questoes[['Questão', 'Afirmação', 'Dimensão', 'Subdimensão', 'Média Real', 'Média Ideal', 'Pontuação Real', 'Pontuação Ideal', 'Gap', 'Nº Respostas']].style.applymap(color_gap, subset=['Gap'])
                            
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

    vals_real, vals_ideal = [], []
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
            # usa código da MATRIZ na chave
            chave = f"{codigo_matriz}_I{i}_R{r}"
            linha = matriz_micro[matriz_micro['CHAVE'] == chave]
            if not linha.empty:
                vals_real.append(float(linha['PONTUACAO_REAL'].iloc[0]))
                vals_ideal.append(float(linha['PONTUACAO_IDEAL'].iloc[0]))

    if not vals_real or not vals_ideal:
        return None, None, None

    real_pct  = float(np.mean(vals_real))
    ideal_pct = float(np.mean(vals_ideal))
    gap       = ideal_pct - real_pct
    return real_pct, ideal_pct, gap

with tab3:
    st.header("💚 Análise de Saúde Emocional + Compliance NR-1")
    st.markdown("**🔍 Analisando afirmações existentes relacionadas à saúde emocional...**")
    
    # Analisar afirmações de saúde emocional
    with st.spinner("Identificando afirmações de saúde emocional..."):
        afirmacoes_saude_emocional, df_arq_filtrado, df_micro_filtrado = analisar_afirmacoes_saude_emocional(matriz_arq, matriz_micro, df_arquetipos, df_microambiente, filtros)
        
        
        
        # ✅ CALCULAR COMPLIANCE AQUI (DEPOIS DOS FILTROS!)
        compliance_nr1 = mapear_compliance_nr1(afirmacoes_saude_emocional)

    if afirmacoes_saude_emocional:
        # Métricas principais
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🧠 Arquétipos SE", len([a for a in afirmacoes_saude_emocional if a['tipo'] == 'Arquétipo']))
        
        with col2:
            st.metric(" Microambiente SE", len([a for a in afirmacoes_saude_emocional if a['tipo'] == 'Microambiente']))
        
        with col3:
            st.metric("💚 Total SE", len(afirmacoes_saude_emocional))
        
        with col4:
            percentual = (len(afirmacoes_saude_emocional) / 97) * 100
            st.metric("📊 % das 97 Afirmações", f"{percentual:.1f}%")
        
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
            categoria = None
            
            # Identificar categoria
            af_lower = af['afirmacao'].lower()
            if any(palavra in af_lower for palavra in ['estresse', 'ansiedade', 'pressão', 'pressao', 'cobrança', 'cobranca', 'deadline', 'prazos', 'tensão', 'tensao', 'sobrecarga' ,  'preocupa com o tempo', 'preocupa com detalhes', 'preocupa se', 'preocupa com',
'necessidade de se aprofundar', 'aprofundar nos detalhes', 'detalhes na execução', 'detalhes de realização', 'detalhes do trabalho', 'sem necessidade de ficar de olho', 'fazer todo o possivel', 'resolver problemas particulares', 'problemas particulares urgentes',
'atuar na solução de conflitos', 'solução de conflitos em sua equipe', 'risco calculado', 'resultasse em algo negativo', 'seriam apoiados', 'leais uns com os outros', 'mais elogiados e incentivados', 'do que criticados' ]):
                categoria = 'Prevenção de Estresse'
            elif any(palavra in af_lower for palavra in ['ambiente', 'seguro', 'proteção', 'protecao', 'respeito', 'cuidadoso', 'palavras']):
                categoria = 'Ambiente Psicológico Seguro'
            elif any(palavra in af_lower for palavra in ['suporte', 'apoio', 'ajuda', 'assistência', 'assistencia', 'ajudar', 'resolver', 'percebe', 'oferece']):
                categoria = 'Suporte Emocional'
            elif any(palavra in af_lower for palavra in ['feedback', 'positivo', 'construtivo', 'encorajamento', 'comentários', 'comentarios', 'positivos', 'desenvolvimento', 'futuro']):
                categoria = 'Comunicação Positiva'
            elif any(palavra in af_lower for palavra in ['equilíbrio', 'equilibrio', 'flexibilidade', 'horários', 'horarios', 'tempo', 'família', 'familia', 'pessoal', 'relação', 'relacao', 'vida pessoal']):
                categoria = 'Equilíbrio Vida-Trabalho'
            else:
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
                    
                    # Buscar % tendência
                    chave = f"{arquétipo}{media_arredondada}{codigo}"
                    linha_tendencia = matriz_arq[matriz_arq['CHAVE'] == chave]
                    
                    if not linha_tendencia.empty:
                        tendencia_percentual = linha_tendencia['% Tendência'].iloc[0] * 100
                        tendencia_info = linha_tendencia['Tendência'].iloc[0]
                        
                        # Converter para score positivo
                        if 'DESFAVORÁVEL' in tendencia_info:
                            valor = max(0, 100 - tendencia_percentual)
                        else:
                            valor = tendencia_percentual
                        
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
                    media_real = round(np.mean(estrelas_real))
                    media_ideal = round(np.mean(estrelas_ideal))
            
                    # Chave na MATRIZ usa o CANÔNICO
                    chave = f"{codigo_canonico}_I{media_ideal}_R{media_real}"
                    linha = matriz_micro[matriz_micro['CHAVE'] == chave]
            
                    if not linha.empty:
                        pontuacao_real = float(linha['PONTUACAO_REAL'].iloc[0])
                        pontuacao_ideal = float(linha['PONTUACAO_IDEAL'].iloc[0])
                        gap = pontuacao_ideal - pontuacao_real
            
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
        
        # Cores baseadas no valor
        cores_compliance = []
        for valor in categoria_medias.values():
            if valor >= 80:
                cores_compliance.append('rgba(0, 128, 0, 0.8)')  # Verde
            elif valor >= 60:
                cores_compliance.append('rgba(144, 238, 144, 0.7)')  # Verde claro
            elif valor >= 40:
                cores_compliance.append('rgba(255, 255, 0, 0.7)')  # Amarelo
            elif valor >= 20:
                cores_compliance.append('rgba(255, 165, 0, 0.7)')  # Laranja
            else:
                cores_compliance.append('rgba(255, 0, 0, 0.8)')  # Vermelho
        
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
            # Filtrar apenas questões da categoria selecionada
            questoes_filtradas = []
            for af in afirmacoes_saude_emocional:
                af_lower = af['afirmacao'].lower()
                
                # Aplicar a mesma lógica de categorização
                if categoria_selecionada == 'Prevenção de Estresse':
                    if any(palavra in af_lower for palavra in ['estresse', 'ansiedade', 'pressão', 'pressao', 'cobrança', 'cobranca', 'deadline', 'prazos', 'tensão', 'tensao', 'sobrecarga', 'preocupa com o tempo', 'preocupa com detalhes', 'preocupa se', 'preocupa com', 'necessidade de se aprofundar', 'aprofundar nos detalhes', 'detalhes na execução', 'detalhes de realização', 'detalhes do trabalho', 'sem necessidade de ficar de olho', 'fazer todo o possivel', 'resolver problemas particulares', 'problemas particulares urgentes', 'atuar na solução de conflitos', 'solução de conflitos em sua equipe', 'risco calculado', 'resultasse em algo negativo', 'seriam apoiados', 'leais uns com os outros', 'mais elogiados e incentivados', 'do que criticados']):
                        questoes_filtradas.append(af)
                elif categoria_selecionada == 'Ambiente Psicológico Seguro':
                    if any(palavra in af_lower for palavra in ['ambiente', 'seguro', 'proteção', 'protecao', 'respeito', 'cuidadoso', 'palavras']):
                        questoes_filtradas.append(af)
                elif categoria_selecionada == 'Suporte Emocional':
                    if any(palavra in af_lower for palavra in ['suporte', 'apoio', 'ajuda', 'assistência', 'assistencia', 'ajudar', 'resolver', 'percebe', 'oferece']):
                        questoes_filtradas.append(af)
                elif categoria_selecionada == 'Comunicação Positiva':
                    if any(palavra in af_lower for palavra in ['feedback', 'positivo', 'construtivo', 'encorajamento', 'comentários', 'comentarios', 'positivos', 'desenvolvimento', 'futuro']):
                        questoes_filtradas.append(af)
                elif categoria_selecionada == 'Equilíbrio Vida-Trabalho':
                    if any(palavra in af_lower for palavra in ['equilíbrio', 'equilibrio', 'flexibilidade', 'horários', 'horarios', 'tempo', 'família', 'familia', 'pessoal', 'relação', 'relacao', 'vida pessoal']):
                        questoes_filtradas.append(af)
        
            # Usar apenas questões filtradas para os gráficos
            if questoes_filtradas:
                afirmacoes_saude_emocional_filtradas = questoes_filtradas
                st.success(f"✅ **Filtro aplicado:** {len(questoes_filtradas)} questões da categoria '{categoria_selecionada}'")
            else:
                afirmacoes_saude_emocional_filtradas = afirmacoes_saude_emocional
                st.warning(f"⚠️ **Nenhuma questão encontrada** para a categoria '{categoria_selecionada}'. Mostrando todas as questões.")
        else:
            # Sem filtro ou "Todas" selecionada
            afirmacoes_saude_emocional_filtradas = afirmacoes_saude_emocional
        
        # Separar afirmações por tipo (DEPOIS do filtro)
        afirmacoes_arq = [a for a in afirmacoes_saude_emocional_filtradas if a['tipo'] == 'Arquétipo']
        
        if categoria_selecionada:
            st.markdown(f"### 📋 Questões da Categoria: **{categoria_selecionada}**")
            
            # Filtrar afirmações da categoria selecionada
            afirmacoes_categoria = []
            for af in afirmacoes_saude_emocional_filtradas:
                af_lower = af['afirmacao'].lower()
                
                # Aplicar a mesma lógica de categorização
                if categoria_selecionada == 'Prevenção de Estresse':
                    if any(palavra in af_lower for palavra in ['estresse', 'ansiedade', 'pressão', 'pressao', 'cobrança', 'cobranca', 'deadline', 'prazos', 'tensão', 'tensao', 'sobrecarga', 'preocupa com o tempo', 'preocupa com detalhes', 'preocupa se', 'preocupa com', 'necessidade de se aprofundar', 'aprofundar nos detalhes', 'detalhes na execução', 'detalhes de realização', 'detalhes do trabalho', 'sem necessidade de ficar de olho', 'fazer todo o possivel', 'resolver problemas particulares', 'problemas particulares urgentes', 'atuar na solução de conflitos', 'solução de conflitos em sua equipe', 'risco calculado', 'resultasse em algo negativo', 'seriam apoiados', 'leais uns com os outros', 'mais elogiados e incentivados', 'do que criticados']):
                        afirmacoes_categoria.append(af)
                elif categoria_selecionada == 'Ambiente Psicológico Seguro':
                    if any(palavra in af_lower for palavra in ['ambiente', 'seguro', 'proteção', 'protecao', 'respeito', 'cuidadoso', 'palavras']):
                        afirmacoes_categoria.append(af)
                elif categoria_selecionada == 'Suporte Emocional':
                    if any(palavra in af_lower for palavra in ['suporte', 'apoio', 'ajuda', 'assistência', 'assistencia', 'ajudar', 'resolver', 'percebe', 'oferece']):
                        afirmacoes_categoria.append(af)
                elif categoria_selecionada == 'Comunicação Positiva':
                    if any(palavra in af_lower for palavra in ['feedback', 'positivo', 'construtivo', 'encorajamento', 'comentários', 'comentarios', 'positivos', 'desenvolvimento', 'futuro']):
                        afirmacoes_categoria.append(af)
                elif categoria_selecionada == 'Equilíbrio Vida-Trabalho':
                    if any(palavra in af_lower for palavra in ['equilíbrio', 'equilibrio', 'flexibilidade', 'horários', 'horarios', 'tempo', 'família', 'familia', 'pessoal', 'relação', 'relacao', 'vida pessoal']):
                        afirmacoes_categoria.append(af)
            
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
                                media_real = np.mean(estrelas_real); media_ideal = np.mean(estrelas_ideal)
                                media_real_arredondada = round(media_real); media_ideal_arredondada = round(media_ideal)
                        
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
            st.warning(f"⚠️ Nenhuma questão encontrada na categoria {categoria_selecionada}")










    
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
        
        # Calcular score baseado nos dois gráficos
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
                        
                        # Buscar % tendência
                        chave = f"{arquétipo}{media_arredondada}{codigo}"
                        linha_tendencia = matriz_arq[matriz_arq['CHAVE'] == chave]
                        
                        if not linha_tendencia.empty:
                            tendencia_percentual = linha_tendencia['% Tendência'].iloc[0] * 100
                            tendencia_info = linha_tendencia['Tendência'].iloc[0]
                            
                            # Converter para score positivo
                            if 'DESFAVORÁVEL' in tendencia_info:
                                score = max(0, 100 - tendencia_percentual)
                            else:
                                score = tendencia_percentual
                            
                            tendencias_gerais.append(score)
            
            if tendencias_gerais:
                score_arquetipos = np.mean(tendencias_gerais)
        
        # Score Microambiente (baseado no gap médio)
        if afirmacoes_micro and 'gaps' in locals() and gaps:
            gap_medio = np.mean(gaps)
            # Converter gap para score (gap baixo = score alto)
            score_microambiente = max(0, 100 - gap_medio)
        
        # Score final combinado
        if score_arquetipos > 0 and score_microambiente > 0:
            score_final = (score_arquetipos + score_microambiente) / 2
        elif score_arquetipos > 0:
            score_final = score_arquetipos
        elif score_microambiente > 0:
            score_final = score_microambiente
        else:
            score_final = 0
        
        # Interpretação do score
        if score_final >= 80:
            interpretacao = "🟢 EXCELENTE - Ambiente muito saudável"
            cor_score = "green"
        elif score_final >= 60:
            interpretacao = "🟡 BOM - Ambiente saudável com melhorias"
            cor_score = "orange"
        elif score_final >= 40:
            interpretacao = " REGULAR - Ambiente com problemas moderados"
            cor_score = "darkorange"
        else:
            interpretacao = "🔴 RUIM - Ambiente com problemas sérios"
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
                <p><strong>🧠 Score Arquétipos:</strong> {score_arquetipos:.1f}% (baseado na tendência favorável/desfavorável)</p>
                <p><strong>🏢 Score Microambiente:</strong> {score_microambiente:.1f}% (baseado no gap Real vs Ideal)</p>
                <p><strong>💚 Score Final:</strong> Média dos dois scores</p>
                <p><strong>🎯 Interpretação:</strong> Quanto maior o score, melhor a saúde emocional proporcionada pelo líder</p>
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
                        
                        # Buscar % tendência
                        chave = f"{arquétipo}{media_arredondada}{codigo}"
                        linha_tendencia = matriz_arq[matriz_arq['CHAVE'] == chave]
                        
                        if not linha_tendencia.empty:
                            tendencia_percentual = linha_tendencia['% Tendência'].iloc[0] * 100
                            tendencia_info = linha_tendencia['Tendência'].iloc[0]
                            
                            tendencias_arq.append(tendencia_info)
                            percentuais_arq.append(f"{tendencia_percentual:.1f}%")
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
            df_arq_styled = df_arq_exibir.style.applymap(color_tendencia_arq, subset=['Tendência'])
            
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
            df_micro_styled = df_micro_exibir.style.applymap(color_gap_micro, subset=['Gap'])
            
            st.dataframe(df_micro_styled, use_container_width=True)
            
            # Download microambiente
            csv_micro = df_micro_exibir.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV - Microambiente SE",
                data=csv_micro,
                file_name="saude_emocional_microambiente.csv",
                mime="text/csv"
            )
    
    else:
        st.warning("⚠️ Nenhuma afirmação relacionada à saúde emocional foi identificada.")
        st.info(" Dica: Verifique se as palavras-chave estão presentes nas afirmações existentes.")

