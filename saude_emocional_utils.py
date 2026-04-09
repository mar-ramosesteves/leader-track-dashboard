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
