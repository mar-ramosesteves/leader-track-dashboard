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
    page_title="Leader Track - Dashboard Revolucionário",
    page_icon="��",
    layout="wide"
)

# Configurações do Supabase
SUPABASE_URL = "https://xmsjjknpnowsswwrbvpc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhtc2pqa25wbm93c3N3d3JidnBjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTI1MDg0NDUsImV4cCI6MjA2ODA4NDQ0NX0.OexXJX7lK_DefGb72VDWGLDcUXamoQIgYOv5Zo_e9L4"

# Inicializar cliente Supabase
@st.cache_resource
def init_supabase():
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# CARREGAR MATRIZ DE ARQUÉTIPOS
@st.cache_data(ttl=3600)
def carregar_matriz_arquetipos():
    """Carrega a matriz de arquétipos do Excel"""
    try:
        matriz = pd.read_excel('TABELA_GERAL_ARQUETIPOS_COM_CHAVE.xlsx')
        st.success("✅ Matriz de arquétipos carregada com sucesso!")
        return matriz
    except Exception as e:
        st.error(f"❌ Erro ao carregar matriz: {str(e)}")
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

# PROCESSAR DADOS INDIVIDUAIS
def processar_dados_individuais(consolidado_arq, matriz):
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
                    'arquétipos': arquétipos_auto
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
                            'arquétipos': arquétipos_equipe
                        })
    
    return pd.DataFrame(respondentes_processados)

# CALCULAR MÉDIAS COM FILTROS
def calcular_medias_com_filtros(df_respondentes, filtros):
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
        return None, None, None
    
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
    
    return arquétipos, medias_auto, medias_equipe


# GERAR GRÁFICO COMPARATIVO
def gerar_grafico_comparativo(medias_auto, medias_equipe, arquétipos, titulo, tipo_visualizacao):
    """Gera gráfico comparativo com dados calculados"""
    
    if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique":
        fig = go.Figure()
        
        fig.add_trace(go.Bar(
            name='Autoavaliação',
            x=arquétipos,
            y=medias_auto,
            marker_color='#1f77b4',
            text=[f"{v:.1f}%" for v in medias_auto],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Autoavaliação: %{y:.1f}%<br><extra>Clique para detalhes!</extra>'
        ))
        
        fig.add_trace(go.Bar(
            name='Média da Equipe',
            x=arquétipos,
            y=medias_equipe,
            marker_color='#ff7f0e',
            text=[f"{v:.1f}%" for v in medias_equipe],
            textposition='auto',
            hovertemplate='<b>%{x}</b><br>Média da Equipe: %{y:.1f}%<br><extra>Clique para detalhes!</extra>'
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

# Buscar dados
@st.cache_data(ttl=300)
def fetch_data():
    try:
        supabase = init_supabase()
        consolidado_arq = supabase.table('consolidado_arquetipos').select('*').execute()
        return consolidado_arq.data
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {str(e)}")
        return []

# INTERFACE PRINCIPAL
st.title("🎯 Leader Track - Dashboard Revolucionário")
st.markdown("---")

# Carregar matriz
with st.spinner("Carregando matriz de arquétipos..."):
    matriz = carregar_matriz_arquetipos()

if matriz is not None:
    # Buscar dados
    with st.spinner("Carregando dados dos respondentes..."):
        consolidado_arq = fetch_data()
    
    if consolidado_arq:
        st.success("✅ Conectado ao Supabase!")
        
        # Processar dados individuais
        with st.spinner("Calculando arquétipos individuais..."):
            df_respondentes = processar_dados_individuais(consolidado_arq, matriz)
        
        # Métricas
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("📊 Total de Respondentes", len(df_respondentes))
        with col2:
            auto_count = len(df_respondentes[df_respondentes['tipo'] == 'Autoavaliação'])
            st.metric("👤 Autoavaliações", auto_count)
        with col3:
            equipe_count = len(df_respondentes[df_respondentes['tipo'] == 'Avaliação Equipe'])
            st.metric("👥 Avaliações Equipe", equipe_count)
        with col4:
            st.metric("�� Última Atualização", datetime.now().strftime("%H:%M"))
        
        # FILTROS
        st.sidebar.header("🎛️ Filtros Globais")
        
        # Filtros principais
        st.sidebar.subheader("�� Filtros Principais")
        empresas = ["Todas"] + sorted(df_respondentes['empresa'].unique().tolist())
        empresa_selecionada = st.sidebar.selectbox("�� Empresa", empresas)
        
        codrodadas = ["Todas"] + sorted(df_respondentes['codrodada'].unique().tolist())
        codrodada_selecionada = st.sidebar.selectbox("�� Código da Rodada", codrodadas)
        
        emailliders = ["Todos"] + sorted(df_respondentes['emailLider'].unique().tolist())
        emaillider_selecionado = st.sidebar.selectbox("👤 Email do Líder", emailliders)
        
        # Filtros demográficos
        st.sidebar.subheader("📊 Filtros Demográficos")
        estados = ["Todos"] + sorted(df_respondentes['estado'].unique().tolist())
        estado_selecionado = st.sidebar.selectbox("🗺️ Estado", estados)
        
        generos = ["Todos"] + sorted(df_respondentes['sexo'].unique().tolist())
        genero_selecionado = st.sidebar.selectbox("⚧ Gênero", generos)
        
        etnias = ["Todas"] + sorted(df_respondentes['etnia'].unique().tolist())
        etnia_selecionada = st.sidebar.selectbox("👥 Etnia", etnias)
        
        departamentos = ["Todos"] + sorted(df_respondentes['departamento'].unique().tolist())
        departamento_selecionado = st.sidebar.selectbox("🏢 Departamento", departamentos)
        
        cargos = ["Todos"] + sorted(df_respondentes['cargo'].unique().tolist())
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
        
        # Calcular médias com filtros
        arquétipos, medias_auto, medias_equipe = calcular_medias_com_filtros(df_respondentes, filtros)
        
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
                horizontal=True
            )
            
            # Gerar e exibir gráfico
            fig = gerar_grafico_comparativo(medias_auto, medias_equipe, arquétipos, titulo, tipo_visualizacao)
            st.plotly_chart(fig, use_container_width=True)
            
            if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique":
                st.info("💡 **Dica:** Passe o mouse sobre as barras para ver detalhes! Clique para mais informações.")
            
            # Informações do relatório
            col1, col2, col3 = st.columns(3)
            with col1:
                st.info(f"**📊 Respondentes Analisados:** {len(df_respondentes)}")
            with col2:
                st.info(f"**👥 Total de Avaliações:** {len(df_respondentes)}")
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
    else:
        st.error("❌ Erro ao carregar dados do Supabase.")
else:
    st.error("❌ Erro ao carregar matriz de arquétipos.")

st.markdown("---")
st.markdown("🎯 **Leader Track Dashboard Revolucionário** - Desenvolvido com Streamlit + Supabase + Cálculo Individual")
