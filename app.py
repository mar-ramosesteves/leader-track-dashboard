import streamlit as st
from supabase import create_client, Client
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
import openpyxl

# Configuração da página
st.set_page_config(
    page_title="🎯 Leader Track - Dashboard Completo (Arquétipos + Microambiente)",
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
def calcular_microambiente_respondente(respostas, matriz, pontos_max_dimensao, pontos_max_subdimensao):
    """Calcula percentuais de microambiente para um respondente individual"""
    
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
            
            # Chave com combinação Real + Ideal
            chave = f"{questao}_I{estrelas_ideal}_R{estrelas_real}"
            linha = matriz[matriz['CHAVE'] == chave]
            
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
    
    # Aplicar filtro de tipo de avaliação
    if filtros['tipo_avaliacao'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo'] == filtros['tipo_avaliacao']]
    
    if df_filtrado.empty:
        return None, None, None, df_filtrado
    
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


# CALCULAR MÉDIAS COM FILTROS (MICROAMBIENTE) - ATUALIZADA
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
    
    # Aplicar filtro de tipo de avaliação
    if filtros['tipo_avaliacao'] != "Todos":
        df_filtrado = df_filtrado[df_filtrado['tipo'] == filtros['tipo_avaliacao']]
    
    if df_filtrado.empty:
        return None, None, None, None, None, df_filtrado
    
    # Separar autoavaliação e equipe
    df_auto = df_filtrado[df_filtrado['tipo'] == 'Autoavaliação']
    df_equipe = df_filtrado[df_filtrado['tipo'] == 'Avaliação Equipe']
    
    dimensoes = ['Adaptabilidade', 'Colaboração Mútua', 'Nitidez', 'Performance', 'Reconhecimento', 'Responsabilidade']
    
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
    
    # Calcular médias da equipe (Real)
    medias_equipe_real = []
    for dim in dimensoes:
        valores = []
        for _, row in df_equipe.iterrows():
            if 'dimensoes_real' in row and isinstance(row['dimensoes_real'], dict) and dim in row['dimensoes_real']:
                valores.append(row['dimensoes_real'][dim])
        media = np.mean(valores) if valores else 0
        medias_equipe_real.append(media)
    
    # Calcular médias da equipe (Ideal)
    medias_equipe_ideal = []
    for dim in dimensoes:
        valores = []
        for _, row in df_equipe.iterrows():
            if 'dimensoes_ideal' in row and isinstance(row['dimensoes_ideal'], dict) and dim in row['dimensoes_ideal']:
                valores.append(row['dimensoes_ideal'][dim])
        media = np.mean(valores) if valores else 0
        medias_equipe_ideal.append(media)
    
    return dimensoes, medias_real, medias_ideal, medias_equipe_real, medias_equipe_ideal, df_filtrado
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
        title=f"�� {titulo}",
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
            tendencia = linha['% Tendência'].iloc[0] * 100 if not linha.empty else 0
            
            questoes_detalhadas.append({
                'questao': questao,
                'afirmacao': afirmacao,
                'media_estrelas': media_estrelas,
                'media_arredondada': media_arredondada,
                'tendencia': tendencia,
                'n_respostas': len(estrelas_questao)
            })
    
    # Ordenar por % tendência (maior para menor)
    questoes_detalhadas.sort(key=lambda x: x['tendencia'], reverse=True)
    
    return questoes_detalhadas

# DRILL-DOWN MICROAMBIENTE (CORRIGIDA)
# DRILL-DOWN MICROAMBIENTE (CORRIGIDA COM ARREDONDAMENTO)
def gerar_drill_down_microambiente(dimensao_clicada, df_respondentes_filtrado, matriz):
    """Gera detalhamento das questões de microambiente"""
    
    # Identificar questões de impacto para a dimensão
    questoes_impacto = matriz[matriz['DIMENSAO'] == dimensao_clicada]['COD'].unique().tolist()
    
    if not questoes_impacto:
        return None
    
    questoes_detalhadas = []
    
    for questao in questoes_impacto:
        # Buscar afirmação na matriz
        linha_questao = matriz[matriz['COD'] == questao].iloc[0]
        afirmacao = linha_questao['AFIRMACAO']
        
        # Calcular médias de estrelas para Real e Ideal
        estrelas_real = []
        estrelas_ideal = []
        
        for _, respondente in df_respondentes_filtrado.iterrows():
            if 'respostas' in respondente:
                respostas = respondente['respostas']
                questao_real = f"{questao}C"
                questao_ideal = f"{questao}k"
                
                if questao_real in respostas:
                    estrelas_real.append(int(respostas[questao_real]))
                if questao_ideal in respostas:
                    estrelas_ideal.append(int(respostas[questao_ideal]))
        
        if estrelas_real and estrelas_ideal:
            # Calcular médias
            media_real = np.mean(estrelas_real)
            media_ideal = np.mean(estrelas_ideal)
            
            # ARREDONDAMENTO NATURAL para buscar na matriz
            media_real_arredondada = round(media_real)
            media_ideal_arredondada = round(media_ideal)
            
            # Buscar pontuações na matriz usando a chave combinada
            chave = f"{questao}_I{media_ideal_arredondada}_R{media_real_arredondada}"
            linha = matriz[matriz['CHAVE'] == chave]
            
            if not linha.empty:
                pontuacao_real = linha['PONTUACAO_REAL'].iloc[0]
                pontuacao_ideal = linha['PONTUACAO_IDEAL'].iloc[0]
            else:
                pontuacao_real = 0
                pontuacao_ideal = 0
            
            questoes_detalhadas.append({
                'questao': questao,
                'afirmacao': afirmacao,
                'media_real': media_real,
                'media_ideal': media_ideal,
                'pontuacao_real': pontuacao_real,
                'pontuacao_ideal': pontuacao_ideal,
                'gap': pontuacao_ideal - pontuacao_real,
                'n_respostas': len(estrelas_real)
            })
    
    # Ordenar por gap (maior para menor)
    questoes_detalhadas.sort(key=lambda x: x['gap'], reverse=True)
    
    return questoes_detalhadas
# ==================== BUSCAR DADOS ====================

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
st.title("🎯 Leader Track - Dashboard Completo (Arquétipos + Microambiente)")
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
                
        
        
        
        # Processar dados individuais
        with st.spinner("Calculando arquétipos individuais..."):
            df_arquetipos = processar_dados_arquetipos(consolidado_arq, matriz_arq)
        
        with st.spinner("Calculando microambiente individual..."):
            df_microambiente = processar_dados_microambiente(consolidado_micro, matriz_micro, pontos_max_dimensao, pontos_max_subdimensao)
        
        # Normalizar dados para minúsculas
        df_arquetipos['empresa'] = df_arquetipos['empresa'].str.lower()
        df_microambiente['empresa'] = df_microambiente['empresa'].str.lower()
        
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("�� Total Arquétipos", len(df_arquetipos))
        with col2:
            st.metric("🏢 Total Microambiente", len(df_microambiente))
        with col3:
            auto_count = len(df_arquetipos[df_arquetipos['tipo'] == 'Autoavaliação'])
            st.metric("👤 Autoavaliações", auto_count)
        with col4:
            st.metric("�� Última Atualização", datetime.now().strftime("%H:%M"))
        
                # FILTROS
        st.sidebar.header("🎛️ Filtros Globais")
        
        # Filtros principais
        st.sidebar.subheader(" Filtros Principais")
        
        # Combinar empresas de ambos os datasets (tudo minúsculas)
        empresas_arq = set(df_arquetipos['empresa'].str.lower().unique())
        empresas_micro = set(df_microambiente['empresa'].str.lower().unique())
        todas_empresas = sorted(list(empresas_arq.union(empresas_micro)))
        empresas = ["Todas"] + todas_empresas  # Tudo minúsculas
        empresa_selecionada = st.sidebar.selectbox(" Empresa", empresas)
        
        # Combinar codrodadas de ambos os datasets
        codrodadas_arq = set(df_arquetipos['codrodada'].unique())
        codrodadas_micro = set(df_microambiente['codrodada'].unique())
        todas_codrodadas = sorted(list(codrodadas_arq.union(codrodadas_micro)))
        codrodadas = ["Todas"] + todas_codrodadas
        codrodada_selecionada = st.sidebar.selectbox(" Código da Rodada", codrodadas)
        
        # Combinar emails de líderes de ambos os datasets
        emailliders_arq = set(df_arquetipos['emailLider'].unique())
        emailliders_micro = set(df_microambiente['emailLider'].unique())
        todos_emailliders = sorted(list(emailliders_arq.union(emailliders_micro)))
        emailliders = ["Todos"] + todos_emailliders
        emaillider_selecionado = st.sidebar.selectbox("👤 Email do Líder", emailliders)
        
        # Filtros demográficos
        st.sidebar.subheader("📊 Filtros Demográficos")
        
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
        etnia_selecionada = st.sidebar.selectbox("👥 Etnia", etnias)
        
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

        
        
        # Filtro de tipo de avaliação
        st.sidebar.subheader("📋 Tipo de Avaliação")
        tipo_avaliacao = st.sidebar.selectbox(
            "Escolha o tipo de avaliação:",
            ["Todos", "Autoavaliação", "Avaliação da Equipe"],
            key="tipo_avaliacao"
        )
        
        # Dicionário de filtros
        filtros = {
            'empresa': empresa_selecionada,
            'codrodada': codrodada_selecionada,
            'emaillider': emaillider_selecionado,
            'estado': estado_selecionado,
            'sexo': genero_selecionado,
            'etnia': etnia_selecionada,
            'departamento': departamento_selecionado,
            'cargo': cargo_selecionado,
            'tipo_avaliacao': tipo_avaliacao
        }
        
        # TABS PRINCIPAIS
        tab1, tab2 = st.tabs(["📊 Arquétipos", "🏢 Microambiente"])
        
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
                            tendencias = [q['tendencia'] for q in questoes_detalhadas]
                            
                            fig_questoes = go.Figure()
                            fig_questoes.add_trace(go.Bar(
                                x=questoes,
                                y=tendencias,
                                marker_color='#2E86AB',
                                text=[f"{v:.1f}%" for v in tendencias],
                                textposition='auto',
                                hovertemplate='<b>%{x}</b><br>% Tendência: %{y:.1f}%<br>Média: %{customdata:.1f} estrelas<extra></extra>',
                                customdata=[q['media_estrelas'] for q in questoes_detalhadas]
                            ))
                            
                            fig_questoes.update_layout(
                                title=f"📊 % Tendência das Questões - {arquétipo_selecionado}",
                                xaxis_title="Questões",
                                yaxis_title="% Tendência",
                                yaxis=dict(range=[0, 100]),
                                height=400
                            )
                            
                            st.plotly_chart(fig_questoes, use_container_width=True)
                            
                            # Tabela detalhada
                            st.subheader("📋 Detalhamento das Questões")
                            
                            df_questoes = pd.DataFrame(questoes_detalhadas)
                            df_questoes['% Tendência'] = df_questoes['tendencia'].apply(lambda x: f"{x:.1f}%")
                            df_questoes['Questão'] = df_questoes['questao']
                            df_questoes['Afirmação'] = df_questoes['afirmacao']
                            df_questoes['Média Estrelas'] = df_questoes['media_estrelas'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Média Arredondada'] = df_questoes['media_arredondada']
                            df_questoes['Nº Respostas'] = df_questoes['n_respostas']
                            
                            st.dataframe(
                                df_questoes[['Questão', 'Afirmação', '% Tendência', 'Média Estrelas', 'Média Arredondada', 'Nº Respostas']],
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
            dimensoes, medias_real, medias_ideal, medias_equipe_real, medias_equipe_ideal, df_filtrado_micro = calcular_medias_microambiente(df_microambiente, filtros)
            
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
                    ["👤 Autoavaliação", "👥 Média da Equipe", "📊 Comparativo (Auto vs Equipe)"],
                    horizontal=True,
                    key="tipo_analise_micro"
                )
                
                # Separar dados por tipo
                df_auto = df_filtrado_micro[df_filtrado_micro['tipo'] == 'Autoavaliação']
                df_equipe = df_filtrado_micro[df_filtrado_micro['tipo'] == 'Avaliação Equipe']
                
                # Calcular médias baseado no tipo selecionado
                if tipo_analise == "👤 Autoavaliação":
                    medias_real_final = medias_real
                    medias_ideal_final = medias_ideal
                    titulo_analise = "Autoavaliação"
                elif tipo_analise == "�� Média da Equipe":
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
                st.plotly_chart(fig, use_container_width=True)
                
                # ==================== GRÁFICO DE SUBDIMENSÕES ====================
                st.subheader("📊 Análise por Subdimensões")
                
                # Calcular médias por subdimensão baseado no tipo selecionado
                subdimensoes = [
                    'Criação', 'Simplificação de Processos', 'Credibilidade Recíproca', 'Dedicação', 'Parceria', 
                    'Satisfação em Fazer Parte', 'Obrigações e Deveres', 'Propósito e Objetivo', 'Aprimoramento', 
                    'Qualidade Superior', 'Celebração', 'Performance', 'Liberdade de Ação', 'Responsabilização'
                ]
                
                if tipo_analise == "👤 Autoavaliação":
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
                fig_sub = gerar_grafico_microambiente_linha(medias_sub_real, medias_sub_ideal, subdimensoes, f"Microambiente por Subdimensões - {titulo_analise}")
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
                        questoes_detalhadas = gerar_drill_down_microambiente(dimensao_selecionada, df_filtrado_micro, matriz_micro)
                        
                        if questoes_detalhadas:
                            # Criar gráfico das questões
                            questoes = [q['questao'] for q in questoes_detalhadas]
                            gaps = [q['gap'] for q in questoes_detalhadas]
                            
                            fig_questoes = go.Figure()
                            fig_questoes.add_trace(go.Bar(
                                x=questoes,
                                y=gaps,
                                marker_color='#A23B72',
                                text=[f"{v:.1f}" for v in gaps],
                                textposition='auto',
                                hovertemplate='<b>%{x}</b><br>Gap: %{y:.1f}<br>Real: %{customdata[0]:.1f} | Ideal: %{customdata[1]:.1f}<extra></extra>',
                                customdata=[[q['pontuacao_real'], q['pontuacao_ideal']] for q in questoes_detalhadas]
                            ))
                            
                            fig_questoes.update_layout(
                                title=f"�� Gap das Questões - {dimensao_selecionada}",
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
                            df_questoes['Média Real'] = df_questoes['media_real'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Média Ideal'] = df_questoes['media_ideal'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Pontuação Real'] = df_questoes['pontuacao_real'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Pontuação Ideal'] = df_questoes['pontuacao_ideal'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Gap'] = df_questoes['gap'].apply(lambda x: f"{x:.1f}")
                            df_questoes['Nº Respostas'] = df_questoes['n_respostas']
                            
                            st.dataframe(
                                df_questoes[['Questão', 'Afirmação', 'Média Real', 'Média Ideal', 'Pontuação Real', 'Pontuação Ideal', 'Gap', 'Nº Respostas']],
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
        
    else:
        st.error("❌ Erro ao carregar dados do Supabase.")
else:
    st.error("❌ Erro ao carregar matrizes.")

st.markdown("---")
st.markdown("🎯 **Leader Track Dashboard Completo** - Desenvolvido com Streamlit + Supabase + Cálculo Individual")
