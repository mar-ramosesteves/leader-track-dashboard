import streamlit as st
from supabase import create_client, Client
import pandas as pd
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Leader Track - Dashboard Super Interativo",
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

# Função para buscar dados
@st.cache_data(ttl=300)
def fetch_data():
    try:
        supabase = init_supabase()
        
        # Buscar dados de todas as tabelas
        relatorios = supabase.table('relatorios_gerados').select('*').execute()
        consolidado_arq = supabase.table('consolidado_arquetipos').select('*').execute()
        consolidado_micro = supabase.table('consolidado_microambiente').select('*').execute()
        
        return {
            'relatorios': relatorios.data,
            'consolidado_arq': consolidado_arq.data,
            'consolidado_micro': consolidado_micro.data
        }
    except Exception as e:
        st.error(f"Erro ao conectar com Supabase: {str(e)}")
        return {}

# Função para extrair dados demográficos
def extract_demographic_data(consolidado_arq, consolidado_micro):
    demograficos = []
    
    # Processar dados de arquétipos
    for item in consolidado_arq:
        if isinstance(item, dict) and 'dados_json' in item:
            try:
                dados = item['dados_json']
                
                # Extrair dados da autoavaliação
                if 'autoavaliacao' in dados:
                    auto = dados['autoavaliacao']
                    demograficos.append({
                        'empresa': auto.get('empresa', 'N/A'),
                        'etnia': auto.get('etnia', 'N/A'),
                        'departamento': auto.get('departamento', 'N/A'),
                        'sexo': auto.get('sexo', 'N/A'),
                        'estado': auto.get('estado', 'N/A'),
                        'cidade': auto.get('cidade', 'N/A'),
                        'cargo': auto.get('cargo', 'N/A'),
                        'area': auto.get('area', 'N/A'),
                        'codrodada': auto.get('codrodada', 'N/A'),
                        'nomeLider': auto.get('nomeLider', 'N/A'),
                        'emailLider': auto.get('emailLider', 'N/A'),
                        'email': auto.get('email', 'N/A'),
                        'tipo': 'Arquétipos - Líder'
                    })
                
                # Extrair dados da equipe
                if 'avaliacoesEquipe' in dados:
                    for membro in dados['avaliacoesEquipe']:
                        demograficos.append({
                            'empresa': membro.get('empresa', 'N/A'),
                            'etnia': membro.get('etnia', 'N/A'),
                            'departamento': membro.get('departamento', 'N/A'),
                            'sexo': membro.get('sexo', 'N/A'),
                            'estado': membro.get('estado', 'N/A'),
                            'cidade': membro.get('cidade', 'N/A'),
                            'cargo': membro.get('cargo', 'N/A'),
                            'area': membro.get('area', 'N/A'),
                            'codrodada': membro.get('codrodada', 'N/A'),
                            'nomeLider': membro.get('nomeLider', 'N/A'),
                            'emailLider': membro.get('emailLider', 'N/A'),
                            'email': membro.get('email', 'N/A'),
                            'tipo': 'Arquétipos - Equipe'
                        })
            except Exception as e:
                continue
    
    # Processar dados de microambiente
    for item in consolidado_micro:
        if isinstance(item, dict) and 'dados_json' in item:
            try:
                dados = item['dados_json']
                
                # Extrair dados da autoavaliação
                if 'autoavaliacao' in dados:
                    auto = dados['autoavaliacao']
                    demograficos.append({
                        'empresa': auto.get('empresa', 'N/A'),
                        'etnia': auto.get('etnia', 'N/A'),
                        'departamento': auto.get('departamento', 'N/A'),
                        'sexo': auto.get('sexo', 'N/A'),
                        'estado': auto.get('estado', 'N/A'),
                        'cidade': auto.get('cidade', 'N/A'),
                        'cargo': auto.get('cargo', 'N/A'),
                        'area': auto.get('area', 'N/A'),
                        'codrodada': auto.get('codrodada', 'N/A'),
                        'nomeLider': auto.get('nomeLider', 'N/A'),
                        'emailLider': auto.get('emailLider', 'N/A'),
                        'email': auto.get('email', 'N/A'),
                        'tipo': 'Microambiente - Líder'
                    })
                
                # Extrair dados da equipe
                if 'avaliacoesEquipe' in dados:
                    for membro in dados['avaliacoesEquipe']:
                        demograficos.append({
                            'empresa': membro.get('empresa', 'N/A'),
                            'etnia': membro.get('etnia', 'N/A'),
                            'departamento': membro.get('departamento', 'N/A'),
                            'sexo': membro.get('sexo', 'N/A'),
                            'estado': membro.get('estado', 'N/A'),
                            'cidade': membro.get('cidade', 'N/A'),
                            'cargo': membro.get('cargo', 'N/A'),
                            'area': membro.get('area', 'N/A'),
                            'codrodada': membro.get('codrodada', 'N/A'),
                            'nomeLider': membro.get('nomeLider', 'N/A'),
                            'emailLider': membro.get('emailLider', 'N/A'),
                            'email': membro.get('email', 'N/A'),
                            'tipo': 'Microambiente - Equipe'
                        })
            except Exception as e:
                continue
    
    return pd.DataFrame(demograficos)

# Função para processar dados de gráficos comparativos
def process_grafico_comparativo(data):
    graficos = []
    for item in data:
        if isinstance(item, dict) and 'dados_json' in item:
            try:
                dados = json.loads(item['dados_json'])
                if 'arquetipos' in dados:
                    dados['id_registro'] = item.get('id')
                    dados['empresa'] = item.get('empresa')
                    dados['codrodada'] = item.get('codrodada')
                    dados['emaillider'] = item.get('emaillider')
                    graficos.append(dados)
            except:
                continue
    return graficos

# Função para calcular média dos gráficos com filtros demográficos
def calcular_media_graficos_com_filtros(graficos_filtrados, df_demograficos, filtros):
    if not graficos_filtrados:
        return None, None, None
    
    # Filtrar dados demográficos
    df_filtrado = df_demograficos.copy()
    
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
    
    # Obter critérios dos dados demográficos filtrados
    empresas_demograficas = set(df_filtrado['empresa'].unique())
    rodadas_demograficas = set(df_filtrado['codrodada'].unique())
    lideres_demograficos = set(df_filtrado['emailLider'].unique())
    
    # Filtrar gráficos que correspondem aos dados demográficos
    graficos_filtrados_por_demografia = []
    for g in graficos_filtrados:
        # Verificar se o gráfico corresponde aos critérios demográficos
        if (g.get('empresa') in empresas_demograficas or 
            g.get('codrodada') in rodadas_demograficas or 
            g.get('emaillider') in lideres_demograficos):
            graficos_filtrados_por_demografia.append(g)
    
    # Se não encontrou correspondências, usar todos os gráficos
    if not graficos_filtrados_por_demografia:
        graficos_filtrados_por_demografia = graficos_filtrados
    
    # Coletar todos os arquétipos únicos
    todos_arquetipos = set()
    for g in graficos_filtrados_por_demografia:
        if 'arquetipos' in g:
            todos_arquetipos.update(g['arquetipos'])
    
    todos_arquetipos = sorted(list(todos_arquetipos))
    
    # Calcular médias
    medias_auto = []
    medias_equipe = []
    
    for arq in todos_arquetipos:
        valores_auto = []
        valores_equipe = []
        
        for g in graficos_filtrados_por_demografia:
            if 'arquetipos' in g and 'autoavaliacao' in g and 'mediaEquipe' in g:
                if arq in g['arquetipos']:
                    auto_val = g['autoavaliacao'].get(arq, 0)
                    equipe_val = g['mediaEquipe'].get(arq, 0)
                    
                    if auto_val > 0:
                        valores_auto.append(auto_val)
                    if equipe_val > 0:
                        valores_equipe.append(equipe_val)
        
        # Calcular médias
        media_auto = np.mean(valores_auto) if valores_auto else 0
        media_equipe = np.mean(valores_equipe) if valores_equipe else 0
        
        medias_auto.append(media_auto)
        medias_equipe.append(media_equipe)
    
    return todos_arquetipos, medias_auto, medias_equipe

# Função para filtrar dados demográficos
def filtrar_dados_demograficos(df_demograficos, filtros):
    df_filtrado = df_demograficos.copy()
    
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
    
    return df_filtrado

# Interface principal
st.title("🎯 Leader Track - Dashboard Super Interativo")
st.markdown("---")

# Buscar dados
with st.spinner("Carregando dados de todas as tabelas..."):
    data = fetch_data()

if data:
    st.success("✅ Conectado ao Supabase!")
    
    # Processar dados
    relatorios = data.get('relatorios', [])
    consolidado_arq = data.get('consolidado_arq', [])
    consolidado_micro = data.get('consolidado_microambiente', [])
    
    graficos_comparativos = process_grafico_comparativo(relatorios)
    df_demograficos = extract_demographic_data(consolidado_arq, consolidado_micro)
    
    # Métricas principais
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(" Total de Registros", len(relatorios))
    
    with col2:
        st.metric("📈 Gráficos Comparativos", len(graficos_comparativos))
    
    with col3:
        st.metric(" Dados Demográficos", len(df_demograficos) if not df_demograficos.empty else 0)
    
    with col4:
        st.metric(" Última Atualização", datetime.now().strftime("%H:%M"))
    
    # FILTROS GLOBAIS (funcionam em todas as abas)
    st.sidebar.header("🎛️ Filtros Globais")
    st.sidebar.markdown("**Estes filtros funcionam em TODAS as abas!**")
    
    # Filtros principais
    st.sidebar.subheader(" Filtros Principais")
    
    if not df_demograficos.empty:
        empresas = ["Todas"] + sorted(df_demograficos['empresa'].unique().tolist())
        empresa_selecionada = st.sidebar.selectbox(" Empresa", empresas)
        
        codrodadas = ["Todas"] + sorted(df_demograficos['codrodada'].unique().tolist())
        codrodada_selecionada = st.sidebar.selectbox(" Código da Rodada", codrodadas)
        
        emailliders = ["Todos"] + sorted(df_demograficos['emailLider'].unique().tolist())
        emaillider_selecionado = st.sidebar.selectbox("👤 Email do Líder", emailliders)
    else:
        empresa_selecionada = "Todas"
        codrodada_selecionada = "Todas"
        emaillider_selecionado = "Todos"
    
    # Filtros demográficos
    st.sidebar.subheader("📊 Filtros Demográficos")
    
    if not df_demograficos.empty:
        estados = ["Todos"] + sorted(df_demograficos['estado'].unique().tolist())
        estado_selecionado = st.sidebar.selectbox("🗺️ Estado", estados)
        
        generos = ["Todos"] + sorted(df_demograficos['sexo'].unique().tolist())
        genero_selecionado = st.sidebar.selectbox(" Gênero", generos)
        
        etnias = ["Todas"] + sorted(df_demograficos['etnia'].unique().tolist())
        etnia_selecionada = st.sidebar.selectbox("👥 Etnia", etnias)
        
        departamentos = ["Todos"] + sorted(df_demograficos['departamento'].unique().tolist())
        departamento_selecionado = st.sidebar.selectbox("🏢 Departamento", departamentos)
        
        cargos = ["Todos"] + sorted(df_demograficos['cargo'].unique().tolist())
        cargo_selecionado = st.sidebar.selectbox("💼 Cargo", cargos)
    else:
        estado_selecionado = "Todos"
        genero_selecionado = "Todos"
        etnia_selecionada = "Todas"
        departamento_selecionado = "Todos"
        cargo_selecionado = "Todos"
    
    # Dicionário com todos os filtros
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
    
    # Aplicar filtros aos dados demográficos
    df_demograficos_filtrado = filtrar_dados_demograficos(df_demograficos, filtros)
    
    # Filtrar gráficos baseado nos filtros principais
    graficos_filtrados = []
    for g in graficos_comparativos:
        if (empresa_selecionada == "Todas" or g.get('empresa') == empresa_selecionada) and \
           (codrodada_selecionada == "Todas" or g.get('codrodada') == codrodada_selecionada) and \
           (emaillider_selecionado == "Todos" or g.get('emaillider') == emaillider_selecionado):
            graficos_filtrados.append(g)
    
    # Mostrar resumo dos filtros aplicados
    st.sidebar.markdown("---")
    st.sidebar.subheader(" Resumo dos Filtros")
    
    filtros_ativos = []
    for key, value in filtros.items():
        if value not in ["Todas", "Todos"]:
            filtros_ativos.append(f"{key}: {value}")
    
    if filtros_ativos:
        for filtro in filtros_ativos:
            st.sidebar.info(f"✅ {filtro}")
    else:
        st.sidebar.info("✅ Todos os filtros: TODOS")
    
    # Tabs para organizar as seções
    tab1, tab2, tab3 = st.tabs(["🎯 Análise por Líder", "📊 Análise Demográfica", "🔄 Comparação entre Rodadas"])
    
    with tab1:
        st.header(" Análise Específica por Líder")
        
        # Seção de Gráficos Comparativos
        if graficos_comparativos:
            st.subheader("📊 Gráficos Comparativos de Arquétipos")
            
            # Opções de visualização
            st.markdown("**🎨 Escolha o tipo de visualização:**")
            tipo_visualizacao = st.radio(
                "Tipo de Gráfico:",
                ["📊 Gráfico com Rótulos e Clique", "📈 Gráfico Simples"],
                horizontal=True
            )
            
            if graficos_filtrados:
                # Adicionar informações de debug
                st.info(f"📊 **Filtros Demográficos Aplicados:** {len(df_demograficos_filtrado)} registros demográficos encontrados")
                
                # Filtrar gráficos por demografia
                empresas_demograficas = set(df_demograficos_filtrado['empresa'].unique())
                rodadas_demograficas = set(df_demograficos_filtrado['codrodada'].unique())
                lideres_demograficos = set(df_demograficos_filtrado['emailLider'].unique())
                
                graficos_filtrados_por_demografia = []
                for g in graficos_filtrados:
                    if (g.get('empresa') in empresas_demograficas or 
                        g.get('codrodada') in rodadas_demograficas or 
                        g.get('emaillider') in lideres_demograficos):
                        graficos_filtrados_por_demografia.append(g)
                
                if not graficos_filtrados_por_demografia:
                    graficos_filtrados_por_demografia = graficos_filtrados
                
                st.info(f"📈 **Gráficos Selecionados:** {len(graficos_filtrados_por_demografia)} gráficos correspondem aos filtros demográficos")
                
                # Calcular médias dos gráficos filtrados com filtros demográficos
                arquétipos, medias_auto, medias_equipe = calcular_media_graficos_com_filtros(
                    graficos_filtrados_por_demografia, df_demograficos, filtros
                )
                
                if arquétipos:
                    # Criar título dinâmico
                    titulo_parts = []
                    if empresa_selecionada != "Todas":
                        titulo_parts.append(f"Empresa: {empresa_selecionada}")
                    if codrodada_selecionada != "Todas":
                        titulo_parts.append(f"Rodada: {codrodada_selecionada}")
                    if emaillider_selecionado != "Todos":
                        titulo_parts.append(f"Líder: {emaillider_selecionado}")
                    
                    # Adicionar filtros demográficos ao título
                    if genero_selecionado != "Todos":
                        titulo_parts.append(f"Gênero: {genero_selecionado}")
                    if etnia_selecionada != "Todas":
                        titulo_parts.append(f"Etnia: {etnia_selecionada}")
                    if estado_selecionado != "Todos":
                        titulo_parts.append(f"Estado: {estado_selecionado}")
                    
                    titulo = " | ".join(titulo_parts) if titulo_parts else "Média Geral de Todos os Relatórios"
                    
                    if tipo_visualizacao == "📊 Gráfico com Rótulos e Clique":
                        # Gráfico interativo com rótulos e clique
                        fig = go.Figure()
                        
                        # Adicionar barras com rótulos
                        fig.add_trace(go.Bar(
                            name='Autoavaliação (Média)',
                            x=arquétipos,
                            y=medias_auto,
                            marker_color='#1f77b4',
                            text=[f"{v:.1f}%" for v in medias_auto],
                            textposition='auto',
                            hovertemplate='<b>%{x}</b><br>Autoavaliação: %{y:.1f}%<br><extra>Clique para detalhes!</extra>',
                            customdata=arquétipos
                        ))
                        
                        fig.add_trace(go.Bar(
                            name='Média da Equipe',
                            x=arquétipos,
                            y=medias_equipe,
                            marker_color='#ff7f0e',
                            text=[f"{v:.1f}%" for v in medias_equipe],
                            textposition='auto',
                            hovertemplate='<b>%{x}</b><br>Média da Equipe: %{y:.1f}%<br><extra>Clique para detalhes!</extra>',
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
                        
                        # Renderizar gráfico
                        st.plotly_chart(fig, use_container_width=True, key="grafico_interativo")

                        # Informação sobre interatividade
                        st.info("💡 **Dica:** Passe o mouse sobre as barras para ver detalhes! Clique para mais informações.")
                        
                    else:
                        # Gráfico simples
                        fig = go.Figure()
                        
                        fig.add_trace(go.Bar(
                            name='Autoavaliação (Média)',
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
                        
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Informações do relatório
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.info(f"**📊 Relatórios Analisados:** {len(graficos_filtrados_por_demografia)}")
                    with col2:
                        total_respondentes = sum(g.get('n_avaliacoes', 0) for g in graficos_filtrados_por_demografia)
                        st.info(f"**👥 Total de Respondentes:** {total_respondentes}")
                    with col3:
                        st.info(f"**📈 Arquétipos Analisados:** {len(arquétipos)}")
                    
                    # Tabela com as médias
                    st.subheader("📋 Tabela de Médias")
                    df_medias = pd.DataFrame({
                        'Arquétipo': arquétipos,
                        'Autoavaliação (%)': [f"{v:.1f}%" for v in medias_auto],
                        'Média Equipe (%)': [f"{v:.1f}%" for v in medias_equipe],
                        'Diferença (%)': [f"{auto - equipe:.1f}%" for auto, equipe in zip(medias_auto, medias_equipe)]
                    })
                    st.dataframe(df_medias, use_container_width=True)
                    
                    # Drill-down: Detalhes por arquétipo
                    st.subheader("🔍 Detalhes por Arquétipo")
                    
                    arquétipo_selecionado = st.selectbox(
                        "Selecione um arquétipo para ver detalhes:",
                        arquétipos
                    )
                    
                    if arquétipo_selecionado:
                        # Mostrar dados detalhados do arquétipo selecionado
                        st.write(f"**Detalhes do arquétipo: {arquétipo_selecionado}**")
                        
                        detalhes = []
                        for g in graficos_filtrados_por_demografia:
                            if 'arquetipos' in g and arquétipo_selecionado in g['arquetipos']:
                                auto_val = g['autoavaliacao'].get(arquétipo_selecionado, 0)
                                equipe_val = g['mediaEquipe'].get(arquétipo_selecionado, 0)
                                
                                detalhes.append({
                                    'Empresa': g.get('empresa', 'N/A'),
                                    'Rodada': g.get('codrodada', 'N/A'),
                                    'Líder': g.get('emaillider', 'N/A'),
                                    'Autoavaliação': f"{auto_val:.1f}%",
                                    'Equipe': f"{equipe_val:.1f}%",
                                    'Diferença': f"{auto_val - equipe_val:.1f}%"
                                })
                        
                        if detalhes:
                            df_detalhes = pd.DataFrame(detalhes)
                            st.dataframe(df_detalhes, use_container_width=True)
                        else:
                            st.warning("Nenhum detalhe encontrado para este arquétipo.")
            else:
                st.warning("Nenhum gráfico encontrado com os filtros selecionados.")
        else:
            st.warning("Nenhum gráfico comparativo encontrado.")
    
    with tab2:
        st.header("📊 Análise Demográfica Geral")
        
        if not df_demograficos.empty:
            # Mostrar estatísticas dos filtros aplicados
            st.subheader(f" Estatísticas dos Filtros Aplicados")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total de Registros", len(df_demograficos_filtrado))
            
            with col2:
                st.metric("Líderes", len(df_demograficos_filtrado[df_demograficos_filtrado['tipo'].str.contains('Líder')]))
            
            with col3:
                st.metric("Membros da Equipe", len(df_demograficos_filtrado[df_demograficos_filtrado['tipo'].str.contains('Equipe')]))
            
            # Gráficos demográficos
            col1, col2 = st.columns(2)
            
            with col1:
                # Distribuição por etnia
                fig_etnia = px.pie(
                    df_demograficos_filtrado,
                    names='etnia',
                    title="Distribuição por Etnia"
                )
                st.plotly_chart(fig_etnia, use_container_width=True)
            
            with col2:
                # Distribuição por gênero
                fig_genero = px.pie(
                    df_demograficos_filtrado,
                    names='sexo',
                    title="Distribuição por Gênero"
                )
                st.plotly_chart(fig_genero, use_container_width=True)
            
            col3, col4 = st.columns(2)
            
            with col3:
                # Distribuição por departamento
                fig_dept = px.bar(
                    df_demograficos_filtrado['departamento'].value_counts(),
                    title="Distribuição por Departamento"
                )
                st.plotly_chart(fig_dept, use_container_width=True)
            
            with col4:
                # Distribuição por estado
                fig_estado = px.bar(
                    df_demograficos_filtrado['estado'].value_counts(),
                    title="Distribuição por Estado"
                )
                st.plotly_chart(fig_estado, use_container_width=True)
            
            # Tabela com dados filtrados
            st.subheader(" Dados Filtrados")
            st.dataframe(df_demograficos_filtrado, use_container_width=True)
        else:
            st.warning("Nenhum dado demográfico encontrado.")
    
    with tab3:
        st.header("🔄 Comparação entre Rodadas")
        
        if not df_demograficos.empty:
            # Selecionar duas rodadas para comparar
            rodadas_disponiveis = sorted(df_demograficos['codrodada'].unique().tolist())
            
            if len(rodadas_disponiveis) >= 2:
                col1, col2 = st.columns(2)
                
                with col1:
                    rodada1 = st.selectbox("Selecione a primeira rodada:", rodadas_disponiveis)
                
                with col2:
                    rodada2 = st.selectbox("Selecione a segunda rodada:", rodadas_disponiveis)
                
                if rodada1 != rodada2:
                    # Filtrar dados das duas rodadas (aplicando filtros globais)
                    df_rodada1 = df_demograficos_filtrado[df_demograficos_filtrado['codrodada'] == rodada1]
                    df_rodada2 = df_demograficos_filtrado[df_demograficos_filtrado['codrodada'] == rodada2]
                    
                    # Comparação demográfica
                    st.subheader(f"📊 Comparação Demográfica: {rodada1} vs {rodada2}")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(f"Registros {rodada1}", len(df_rodada1))
                        st.metric(f"Líderes {rodada1}", len(df_rodada1[df_rodada1['tipo'].str.contains('Líder')]))
                    
                    with col2:
                        st.metric(f"Registros {rodada2}", len(df_rodada2))
                        st.metric(f"Líderes {rodada2}", len(df_rodada2[df_rodada2['tipo'].str.contains('Líder')]))
                    
                    # Gráfico comparativo de gênero
                    fig_comparacao = go.Figure()
                    
                    generos_rodada1 = df_rodada1['sexo'].value_counts()
                    generos_rodada2 = df_rodada2['sexo'].value_counts()
                    
                    fig_comparacao.add_trace(go.Bar(
                        name=f'Gênero {rodada1}',
                        x=generos_rodada1.index,
                        y=generos_rodada1.values,
                        marker_color='#1f77b4'
                    ))
                    
                    fig_comparacao.add_trace(go.Bar(
                        name=f'Gênero {rodada2}',
                        x=generos_rodada2.index,
                        y=generos_rodada2.values,
                        marker_color='#ff7f0e'
                    ))
                    
                    fig_comparacao.update_layout(
                        title="Comparação de Gênero entre Rodadas",
                        barmode='group'
                    )
                    
                    st.plotly_chart(fig_comparacao, use_container_width=True)
                else:
                    st.warning("Selecione rodadas diferentes para comparar.")
            else:
                st.warning("É necessário ter pelo menos 2 rodadas para fazer comparação.")
        else:
            st.warning("Nenhum dado disponível para comparação.")
    
    # Dados brutos para debug
    st.header(" Dados Completos")
    with st.expander("Ver dados demográficos"):
        if not df_demograficos.empty:
            st.dataframe(df_demograficos)
        else:
            st.write("Nenhum dado demográfico encontrado")
        
else:
    st.error("❌ Não foi possível carregar os dados.")

# Informações do sistema
st.markdown("---")
st.markdown("**🎯 Leader Track Dashboard Super Interativo - Desenvolvido com Streamlit + Supabase**")
