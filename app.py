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

# CALCULAR MICROAMBIENTE PARA UM RESPONDENTE
def calcular_microambiente_respondente(respostas, matriz, pontos_max_dimensao, pontos_max_subdimensao):
    """Calcula percentuais de microambiente para um respondente individual"""
    
    dimensoes = ['Adaptabilidade', 'Colaboração Mútua', 'Nitidez', 'Performance', 'Reconhecimento', 'Responsabilidade']
    subdimensoes = [
        'Criação', 'Simplificação de Processos', 'Credibilidade Recíproca', 'Dedicação', 'Parceria', 
        'Satisfação em Fazer Parte', 'Obrigações e Deveres', 'Propósito e Objetivo', 'Aprimoramento', 
        'Qualidade Superior', 'Celebração', 'Performance', 'Liberdade de Ação', 'Responsabilização'
    ]
    
    pontos_por_dimensao = {dim: 0 for dim in dimensoes}
    pontos_por_subdimensao = {sub: 0 for sub in subdimensoes}
    
    # Para cada questão respondida
    for questao, estrelas in respostas.items():
        if questao.startswith('Q'):
            estrelas_int = int(estrelas)
            
            # Buscar na matriz para Real (C) e Ideal (k)
            if questao.endswith('C'):  # Como é (Real)
                questao_num = questao[:-1]  # Remove o 'C'
                chave_real = f"{questao_num}_{estrelas_int}_R{estrelas_int}"
                linha_real = matriz[matriz['CHAVE'] == chave_real]
                
                if not linha_real.empty:
                    dimensao = linha_real['DIMENSAO'].iloc[0]
                    subdimensao = linha_real['SUBDIMENSAO'].iloc[0]
                    pontos_real = linha_real['PONTUACAO_REAL'].iloc[0]
                    
                    pontos_por_dimensao[dimensao] += pontos_real
                    pontos_por_subdimensao[subdimensao] += pontos_real
            
            elif questao.endswith('k'):  # Como deveria ser (Ideal)
                questao_num = questao[:-1]  # Remove o 'k'
                chave_ideal = f"{questao_num}_{estrelas_int}_Q{estrelas_int}"
                linha_ideal = matriz[matriz['CHAVE'] == chave_ideal]
                
                if not linha_ideal.empty:
                    dimensao = linha_ideal['DIMENSAO'].iloc[0]
                    subdimensao = linha_ideal['SUBDIMENSAO'].iloc[0]
                    pontos_ideal = linha_ideal['PONTUACAO_IDEAL'].iloc[0]
                    
                    pontos_por_dimensao[dimensao] += pontos_ideal
                    pontos_por_subdimensao[subdimensao] += pontos_ideal
    
    # Calcular percentuais por dimensão
    dimensoes_percentuais = {}
    for dimensao in dimensoes:
        pontos_total = pontos_por_dimensao[dimensao]
        pontos_maximos = pontos_max_dimensao[pontos_max_dimensao['DIMENSAO'] == dimensao]['PONTOS_MAXIMOS_DIMENSAO'].iloc[0]
        percentual = (pontos_total / pontos_maximos) * 100 if pontos_maximos > 0 else 0
        dimensoes_percentuais[dimensao] = percentual
    
    # Calcular percentuais por subdimensão
    subdimensoes_percentuais = {}
    for subdimensao in subdimensoes:
        pontos_total = pontos_por_subdimensao[subdimensao]
        pontos_maximos = pontos_max_subdimensao[pontos_max_subdimensao['SUBDIMENSAO'] == subdimensao]['PONTOS_MAXIMOS_SUBDIMENSAO'].iloc[0]
        percentual = (pontos_total / pontos_maximos) * 100 if pontos_maximos > 0 else 0
        subdimensoes_percentuais[subdimensao] = percentual
    
    return dimensoes_percentuais, subdimensoes_percentuais

# ==================== FUNÇÕES COMPARTILHADAS ====================

# PROCESSAR DADOS INDIVIDUAIS (ARQUÉTIPOS)
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
                    'tipo': 'Autoavaliação',
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
                            'tipo': 'Avaliação Equipe',
                            'arquétipos': arquétipos_equipe,
                            'respostas': membro['respostas']
                        })
    
    return pd.DataFrame(respondentes_processados)

# PROCESSAR DADOS INDIVIDUAIS (MICROAMBIENTE)
def processar_dados_microambiente(consolidado_micro, matriz, pontos_max_dimensao, pontos_max_subdimensao):
    """Processa todos os respondentes e calcula microambiente"""
    
    respondentes_processados = []
    
    for item in consolidado_micro:
        if isinstance(item, dict) and 'dados_json' in item:
            dados = item['dados_json']
            
            # Processar autoavaliação
            if 'autoavaliacao' in dados:
                auto = dados['autoavaliacao']
                dimensoes_auto, subdimensoes_auto = calcular_microambiente_respondente(auto, matriz, pontos_max_dimensao, pontos_max_subdimensao)
                
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
                    'dimensoes': dimensoes_auto,
                    'subdimensoes': subdimensoes_auto,
                    'respostas': auto
                })
            
            # Processar avaliações da equipe
            if 'avaliacoesEquipe' in dados:
                for membro in dados['avaliacoesEquipe']:
                    dimensoes_equipe, subdimensoes_equipe = calcular_microambiente_respondente(membro, matriz, pontos_max_dimensao, pontos_max_subdimensao)
                    
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
                        'dimensoes': dimensoes_equipe,
                        'subdimensoes': subdimensoes_equipe,
                        'respostas': membro
                    })
    
    return pd.DataFrame(respondentes_processados)

# CALCULAR MÉDIAS COM FILTROS (ARQUÉTIPOS)
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

# CALCULAR MÉDIAS COM FILTROS (MICROAMBIENTE)
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
    
    if df_filtrado.empty:
        return None, None, None, None, df_filtrado
    
    # Separar autoavaliação e equipe
    df_auto = df_filtrado[df_filtrado['tipo'] == 'Autoavaliação']
    df_equipe = df_filtrado[df_filtrado['tipo'] == 'Avaliação Equipe']
    
    dimensoes = ['Adaptabilidade', 'Colaboração Mútua', 'Nitidez', 'Performance', 'Reconhecimento', 'Responsabilidade']
    
    # Calcular médias de autoavaliação (Real)
    medias_real = []
    for dim in dimensoes:
        valores = []
        for _, row in df_auto.iterrows():
            if 'dimensoes' in row and isinstance(row['dimensoes'], dict) and dim in row['dimensoes']:
                valores.append(row['dimensoes'][dim])
        media = np.mean(valores) if valores else 0
        medias_real.append(media)
    
    # Calcular médias da equipe (Real)
    medias_equipe_real = []
    for dim in dimensoes:
        valores = []
        for _, row in df_equipe.iterrows():
            if 'dimensoes' in row and isinstance(row['dimensoes'], dict) and dim in row['dimensoes']:
                valores.append(row['dimensoes'][dim])
        media = np.mean(valores) if valores else 0
        medias_equipe_real.append(media)
    
    return dimensoes, medias_real, medias_equipe_real, df_filtrado

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
def gerar_grafico_microambiente(medias_real, medias_equipe_real, dimensoes, titulo, tipo_visualizacao):
    """Gera gráfico comparativo de microambiente"""
    
    if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique":
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Autoavaliação (Real)',
            x=dimensoes,
            y=medias_real,
            marker_color='#2E86AB',
            text=[f"{v:.1f}%" for v in medias_real],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Autoavaliação: %{y:.1f}%<br><extra>Clique para ver questões!</extra>',
            customdata=dimensoes
        ))
        
        fig.add_trace(go.Bar(
            name='Média da Equipe (Real)',
            x=dimensoes,
            y=medias_equipe_real,
            marker_color='#A23B72',
            text=[f"{v:.1f}%" for v in medias_equipe_real],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Média da Equipe: %{y:.1f}%<br><extra>Clique para ver questões!</extra>',
            customdata=dimensoes
        ))
        
        fig.update_layout(
            title=f"🏢 {titulo}",
            xaxis_title="Dimensões do Microambiente",
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
            name='Autoavaliação (Real)',
            x=dimensoes,
            y=medias_real,
            marker_color='#2E86AB',
            hovertemplate='<b>%{x}</b><br>Autoavaliação: %{y:.1f}%<extra></extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='Média da Equipe (Real)',
            x=dimensoes,
            y=medias_equipe_real,
            marker_color='#A23B72',
            hovertemplate='<b>%{x}</b><br>Média da Equipe: %{y:.1f}%<extra></extra>'
        ))
        
        fig.update_layout(
            title=f"🏢 {titulo}",
            xaxis_title="Dimensões do Microambiente",
            yaxis_title="Pontuação (%)",
            yaxis=dict(range=[0, 100]),
            barmode='group',
            height=500,
            hovermode='closest',
            showlegend=True
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

# DRILL-DOWN MICROAMBIENTE
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
            # Calcular médias e arredondar
            media_real = round(np.mean(estrelas_real))
            media_ideal = round(np.mean(estrelas_ideal))
            
            # Buscar pontuações na matriz
            chave_real = f"{questao}_{media_real}_R{media_real}"
            chave_ideal = f"{questao}_{media_ideal}_Q{media_ideal}"
            
            linha_real = matriz[matriz['CHAVE'] == chave_real]
            linha_ideal = matriz[matriz['CHAVE'] == chave_ideal]
            
            pontuacao_real = linha_real['PONTUACAO_REAL'].iloc[0] if not linha_real.empty else 0
            pontuacao_ideal = linha_ideal['PONTUACAO_IDEAL'].iloc[0] if not linha_ideal.empty else 0
            
            questoes_detalhadas.append({
                'questao': questao,
                'afirmacao': afirmacao,
                'media_real': np.mean(estrelas_real),
                'media_ideal': np.mean(estrelas_ideal),
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
            st.metric(" Última Atualização", datetime.now().strftime("%H:%M"))
        
        # FILTROS
        st.sidebar.header("🎛️ Filtros Globais")
        
        # Filtros principais
        st.sidebar.subheader(" Filtros Principais")
        empresas = ["Todas"] + sorted(df_arquetipos['empresa'].unique().tolist())
        empresa_selecionada = st.sidebar.selectbox(" Empresa", empresas)
        
        codrodadas = ["Todas"] + sorted(df_arquetipos['codrodada'].unique().tolist())
        codrodada_selecionada = st.sidebar.selectbox(" Código da Rodada", codrodadas)
        
        emailliders = ["Todos"] + sorted(df_arquetipos['emailLider'].unique().tolist())
        emaillider_selecionado = st.sidebar.selectbox("👤 Email do Líder", emailliders)
        
        # Filtros demográficos
        st.sidebar.subheader("📊 Filtros Demográficos")
        estados = ["Todos"] + sorted(df_arquetipos['estado'].unique().tolist())
        estado_selecionado = st.sidebar.selectbox("🗺️ Estado", estados)
        
        generos = ["Todos"] + sorted(df_arquetipos['sexo'].unique().tolist())
        genero_selecionado = st.sidebar.selectbox("⚧ Gênero", generos)
        
        etnias = ["Todas"] + sorted(df_arquetipos['etnia'].unique().tolist())
        etnia_selecionada = st.sidebar.selectbox("👥 Etnia", etnias)
        
        departamentos = ["Todos"] + sorted(df_arquetipos['departamento'].unique().tolist())
        departamento_selecionado = st.sidebar.selectbox("🏢 Departamento", departamentos)
        
        cargos = ["Todos"] + sorted(df_arquetipos['cargo'].unique().tolist())
        cargo_selecionado = st.sidebar.selectbox("💼 Cargo", cargos)
        
        # Dicionário de filtros
        filtros = {
            'empresa': empresa_selecionada,
            'codrodada': codrodada_selecionada,
            'emaillider': emaillider_selecionado,
            'estado': estado_selecionado,
            'sexo': genero_selecionado,
            'etnia': etnia_selecionada,
            'departamento': departamento_selecionado,
            'cargo': cargo_selecionado
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
            dimensoes, medias_real, medias_equipe_real, df_filtrado_micro = calcular_medias_microambiente(df_microambiente, filtros)
            
            if dimensoes:
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
                    key="microambiente"
                )
                
                # Gerar e exibir gráfico
                fig = gerar_grafico_microambiente(medias_real, medias_equipe_real, dimensoes, titulo, tipo_visualizacao)
                st.plotly_chart(fig, use_container_width=True)
                
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
                        key="dimensao_select"
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
                    'Autoavaliação (Real) (%)': [f"{v:.1f}%" for v in medias_real],
                    'Média Equipe (Real) (%)': [f"{v:.1f}%" for v in medias_equipe_real]
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
