import pandas as pd
import numpy as np


DIMENSOES_SE = [
    'Prevenção de Estresse',
    'Ambiente Psicológico Seguro',
    'Suporte Emocional',
    'Comunicação Positiva',
    'Equilíbrio Vida-Trabalho'
]


def carregar_tabela_saude_emocional():
    df = pd.read_csv('TABELA_SAUDE_EMOCIONAL.csv', sep=';', encoding='utf-8-sig')
    df['TIPO'] = df['TIPO'].astype(str).str.strip().str.upper()
    df['COD_AFIRMACAO'] = df['COD_AFIRMACAO'].astype(str).str.strip()
    df['DIMENSAO_SAUDE_EMOCIONAL'] = (
        df['DIMENSAO_SAUDE_EMOCIONAL']
        .astype(str)
        .str.strip()
        .replace({'Equilíbrio Vida- Trabalho': 'Equilíbrio Vida-Trabalho'})
    )
    return df


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


def calcular_tendencia_arquetipos_por_questao(df_arq_filtrado, matriz_arq, codigo_questao, arquetipo):
    percentuais_individuais = []
    soma_notas = 0
    count_notas = 0

    for _, respondente in df_arq_filtrado.iterrows():
        if 'respostas' in respondente and codigo_questao in respondente['respostas']:
            try:
                estrelas = int(respondente['respostas'][codigo_questao])
            except:
                continue

            chave = f"{arquetipo}{estrelas}{codigo_questao}"
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
    chave_tendencia = f"{arquetipo}{media_arredondada}{codigo_questao}"
    linha_tend = matriz_arq[matriz_arq['CHAVE'] == chave_tendencia]
    tendencia_info = linha_tend['Tendência'].iloc[0] if not linha_tend.empty else 'N/A'

    return percentual_medio, tendencia_info, len(percentuais_individuais)


def score_se_label(score):
    try:
        v = float(score)
        if v >= 80:
            return "🟢 Excelente"
        elif v >= 75:
            return "🟢 Ótimo"
        elif v >= 70:
            return "🟡 Bom"
        elif v >= 60:
            return "🟠 Regular"
        else:
            return "🔴 Não Adequado"
    except:
        return "—"



def analisar_afirmacoes_saude_emocional_core(matriz_arq, matriz_micro, df_arquetipos, df_microambiente, filtros):
    df_csv = carregar_tabela_saude_emocional()

    df_arq_filtrado = df_arquetipos.copy()
    df_micro_filtrado = df_microambiente.copy()

    if filtros.get('empresa', "Todas") != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['empresa'] == filtros['empresa']]
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['empresa'] == filtros['empresa']]

    if filtros.get('codrodada', "Todas") != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['codrodada'] == filtros['codrodada']]
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['codrodada'] == filtros['codrodada']]

    if filtros.get('emaillider', "Todos") != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['emailLider'] == filtros['emaillider']]
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['emailLider'] == filtros['emaillider']]

    if filtros.get('estado', "Todos") != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['estado'] == filtros['estado']]
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['estado'] == filtros['estado']]

    if filtros.get('sexo', "Todos") != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['sexo'] == filtros['sexo']]
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['sexo'] == filtros['sexo']]

    if filtros.get('etnia', "Todas") != "Todas":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['etnia'] == filtros['etnia']]
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['etnia'] == filtros['etnia']]

    if filtros.get('departamento', "Todos") != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['departamento'] == filtros['departamento']]
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['departamento'] == filtros['departamento']]

    if filtros.get('cargo', "Todos") != "Todos":
        df_arq_filtrado = df_arq_filtrado[df_arq_filtrado['cargo'] == filtros['cargo']]
        df_micro_filtrado = df_micro_filtrado[df_micro_filtrado['cargo'] == filtros['cargo']]

    if filtros.get('holding', "Todas") != "Todas":
        if 'holding' in df_arq_filtrado.columns:
            holding_filtro = str(filtros['holding']).upper().strip()
            df_arq_filtrado = df_arq_filtrado[
                df_arq_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro
            ]
        if 'holding' in df_micro_filtrado.columns:
            holding_filtro = str(filtros['holding']).upper().strip()
            df_micro_filtrado = df_micro_filtrado[
                df_micro_filtrado['holding'].astype(str).str.upper().str.strip() == holding_filtro
            ]

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

    afirmacoes_saude_emocional = []
    codigos_processados = set()

    matriz_arq_unicos = matriz_arq[['COD_AFIRMACAO', 'AFIRMACAO', 'ARQUETIPO']].drop_duplicates(subset=['COD_AFIRMACAO'])
    for _, row in matriz_arq_unicos.iterrows():
        codigo = str(row['COD_AFIRMACAO']).strip()
        tipo_codigo = f"arq_{codigo}"

        if tipo_codigo in csv_dict and tipo_codigo not in codigos_processados:
            afirmacoes_saude_emocional.append({
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
            afirmacoes_saude_emocional.append({
                'tipo': 'Microambiente',
                'afirmacao': row['AFIRMACAO'],
                'dimensao': row['DIMENSAO'],
                'subdimensao': row['SUBDIMENSAO'],
                'chave': codigo,
                'dimensao_saude_emocional': csv_dict[tipo_codigo]
            })
            codigos_processados.add(tipo_codigo)

    return afirmacoes_saude_emocional, df_arq_filtrado, df_micro_filtrado


def calcular_categoria_medias_app_like(matriz_arq, matriz_micro, df_arquetipos, df_microambiente, filtros):
    afirmacoes_saude_emocional, df_arq_filtrado, df_micro_filtrado = analisar_afirmacoes_saude_emocional_core(
        matriz_arq, matriz_micro, df_arquetipos, df_microambiente, filtros
    )

    categoria_valores = {
        'Prevenção de Estresse': [],
        'Ambiente Psicológico Seguro': [],
        'Suporte Emocional': [],
        'Comunicação Positiva': [],
        'Equilíbrio Vida-Trabalho': []
    }

    for af in afirmacoes_saude_emocional:
        codigo = af['chave']
        categoria = af.get('dimensao_saude_emocional', 'Suporte Emocional')

        if categoria not in categoria_valores:
            categoria = 'Suporte Emocional'

        if af['tipo'] == 'Arquétipo':
            arquetipo = af['dimensao']
            percentual_medio, tendencia_info, _ = calcular_tendencia_arquetipos_por_questao(
                df_arq_filtrado[df_arq_filtrado['tipo'] == 'Avaliação Equipe'],
                matriz_arq,
                codigo,
                arquetipo
            )

            if percentual_medio is not None and tendencia_info:
                if 'DESFAVORÁVEL' in str(tendencia_info):
                    valor = max(0, 100 - percentual_medio)
                else:
                    valor = percentual_medio
                categoria_valores[categoria].append(valor)

        else:
            real_pct, ideal_pct, gap = calcular_real_ideal_gap_por_questao(
                df_micro_filtrado,
                matriz_micro,
                codigo
            )

            if real_pct is not None and gap is not None:
                valor = max(0.0, 100.0 - gap)
                categoria_valores[categoria].append(valor)

    categoria_medias = {}
    for categoria, valores in categoria_valores.items():
        categoria_medias[categoria] = round(float(np.mean(valores)), 1) if valores else 0

    valores_validos = [v for v in categoria_medias.values() if v > 0]
    score_final = round(float(np.mean(valores_validos)), 1) if valores_validos else '—'

    resultado_dim = {}
    for dim in DIMENSOES_SE:
        resultado_dim[dim] = categoria_medias[dim] if categoria_medias[dim] > 0 else '—'

    return resultado_dim, score_final
