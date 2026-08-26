# Devolutiva Organizacional LeaderTrack

## Objetivo

Criar uma devolutiva premium para RH, CEO e diretoria a partir dos dados reais do LeaderTrack, usando o dashboard como motor analitico e o Leadertrackbot como camada interpretativa.

Esta devolutiva nao substitui a devolutiva individual do lider. Ela e uma entrega organizacional, com foco em padroes coletivos, riscos de microambiente, saude emocional, engajamento, diferencas entre grupos e plano de acao institucional.

## Publico autorizado

- RH.
- CEO.
- Diretoria.
- Gestao autorizada da empresa ou holding.

## Regra sobre saude emocional

Saude emocional nunca deve ser entregue individualmente ao lider.

Ela pode aparecer apenas em devolutivas organizacionais para RH, CEO ou gestao autorizada, sempre de forma agregada e com protecao de amostra.

O sistema nao deve:

- diagnosticar ansiedade, depressao, burnout ou qualquer condicao clinica;
- atribuir causa direta a um lider;
- expor recortes com poucas pessoas;
- mostrar dados que permitam identificar pessoas indiretamente.

## Fontes permitidas

1. Dados reais enviados pelo LeaderTrack.
2. Matriz oficial de Arquetipos de Gestao.
3. Matriz oficial de Microambiente.
4. Tabela oficial de Saude Emocional.
5. Guia oficial de entendimento do LeaderTrack.
6. Correlacao autorizada entre Arquetipos LeaderTrack e estilos de lideranca inspirados no artigo de Daniel Goleman/HBR.

O modelo principal e sempre o LeaderTrack. Goleman/HBR entra apenas como apoio conceitual para repertorio situacional de lideranca, sem citacao textual e sem tratar a correlacao como prova.

## Regras de verdade

- Nunca inventar resultado, percentual, causa, diagnostico ou contexto.
- Se um cruzamento nao tiver dados suficientes, nao informar o achado.
- Se houver dado, mas a amostra for pequena, informar apenas de forma agregada ou omitir.
- Separar claramente fato medido, hipotese interpretativa e recomendacao.
- Usar linguagem prudente: "os dados sugerem", "pode indicar", "merece investigacao", "uma hipotese de leitura".

## Entradas do motor analitico

Contexto:

- `nivel_contexto`: holding, empresa ou filial.
- `holding_id`, `empresa_id`, `filial_id`.
- `holding_nome`, `empresa_nome`, `company_name`, `branch_name`.

Filtros:

- holding.
- empresa.
- rodada.
- lider.
- estado.
- cidade.
- genero/sexo.
- etnia.
- geracao.
- departamento.
- cargo.
- tipo de avaliacao.

Dados:

- consolidados de arquetipos.
- consolidados de microambiente.
- cadastro de colaboradores, quando disponivel.
- dados de desempenho/9Box, quando disponiveis e autorizados.

## Saidas esperadas

### 1. Resumo executivo

- Contexto analisado.
- Rodada analisada.
- Tamanho de amostra.
- Principais fortalezas.
- Principais riscos.
- Temas prioritarios para acao.
- Nivel de confianca da analise.

### 2. Indicadores gerais

- Total de respondentes.
- Total de lideres.
- Distribuicao por empresa, area, departamento, estado, genero, etnia e geracao.
- IGL medio.
- Score medio de saude emocional organizacional.
- Indice de engajamento da rodada, quando houver base suficiente.
- Quantidade de gaps medios e criticos.

### 3. Microambiente organizacional

- Dimensoes com melhor resultado real.
- Dimensoes com pior resultado real.
- Maiores gaps entre "como e" e "como deveria ser".
- Heatmap por dimensao x departamento.
- Heatmap por dimensao x lider.
- Heatmap por dimensao x empresa/holding.
- Recortes por genero, etnia, geracao e regiao, somente com amostra suficiente.

### 4. Saude emocional organizacional

- Score geral.
- Score por categoria:
  - Prevencao de Estresse.
  - Ambiente Psicologico Seguro.
  - Suporte Emocional.
  - Comunicacao Positiva.
  - Equilibrio Vida-Trabalho.
- Comparacao contra media da rodada.
- Achados relevantes por recorte demografico ou organizacional, respeitando amostra minima.
- Pontos de atencao sem rotulo clinico.

### 5. Arquetipos de lideranca

- Arquetipos predominantes na organizacao.
- Diferenca entre autoavaliacao e percepcao da equipe.
- Liderancas com padroes positivos de microambiente.
- Padroes de risco quando Imperativo ou Prescritivo aparecem com impacto negativo.
- Repertorios a desenvolver em nivel organizacional.

### 6. Cruzamentos automaticos

O sistema deve avaliar cruzamentos relevantes entre:

- rodada x empresa;
- rodada x departamento;
- rodada x lider;
- rodada x genero;
- rodada x etnia;
- rodada x geracao;
- rodada x estado/regiao;
- departamento x genero;
- departamento x etnia;
- lider x dimensao de microambiente;
- lider x saude emocional agregada da equipe;
- empresa x saude emocional;
- holding x empresa.

Um cruzamento so vira achado se cumprir criterios minimos:

- amostra minima configuravel;
- diferenca relevante contra a media;
- resultado nao identificavel;
- presenca de dado suficiente para explicar o achado.

## Criterios sugeridos de relevancia

- Amostra minima padrao: 5 respondentes.
- Diferenca relevante de score: 5 pontos ou mais.
- Gap medio: acima de 20 pontos.
- Gap critico: acima de 35 pontos.
- Saude emocional em atencao: abaixo de 75.
- Saude emocional critica: abaixo de 65.

Esses parametros devem ser configuraveis.

## Cache sob demanda

Nao pre-gerar todas as combinacoes possiveis.

O cache deve ser criado quando uma combinacao for acessada ou quando uma devolutiva organizacional for gerada.

Chave sugerida:

- contexto normalizado;
- filtros normalizados e ordenados;
- rodada;
- versao das regras de calculo;
- versao do prompt;
- data de atualizacao da base.

O cache deve guardar:

- pacote analitico calculado;
- achados detectados;
- graficos/dados para graficos;
- resposta da IA, quando gerada;
- data de geracao;
- validade;
- motivo de invalidacao.

## Papel da IA

A IA nao calcula numeros novos. Ela interpreta apenas o pacote analitico enviado pelo backend.

A IA deve:

- explicar achados reais;
- priorizar temas;
- sugerir acoes institucionais;
- conectar LeaderTrack, Microambiente, Saude Emocional e Arquetipos;
- usar Goleman/HBR apenas como apoio conceitual;
- diferenciar fato, hipotese e recomendacao.

A IA nao deve:

- inventar cruzamentos;
- inventar percentuais;
- inferir causa sem dado;
- diagnosticar condicoes clinicas;
- atribuir culpa a lideres;
- expor informacao individual sensivel.

## Estrutura do relatorio premium

1. Capa executiva.
2. Carta ao RH/CEO.
3. Resumo executivo visual.
4. Metodologia e cuidados de leitura.
5. Panorama da rodada.
6. Perfil da amostra.
7. Termometro organizacional.
8. Saude emocional organizacional.
9. Microambiente por dimensao.
10. Gaps medios e criticos.
11. Arquetipos de lideranca.
12. Achados por recortes relevantes.
13. Heatmaps.
14. Liderancas e setores que exigem atencao institucional.
15. Fortalezas culturais identificadas.
16. Riscos organizacionais.
17. Plano de acao 30/60/90 dias.
18. Indicadores de acompanhamento.
19. Anexo tecnico de filtros, amostras e regras.

## Plano de implementacao

Fase 1:

- Criar motor analitico organizacional isolado.
- Gerar pacote JSON com KPIs, recortes, gaps e achados.
- Nao alterar calculos existentes do dashboard.

Fase 2:

- Criar endpoint de geracao organizacional no backend do bot.
- Reaproveitar regras do prompt LeaderTrack.
- Adicionar prompt organizacional especifico.

Fase 3:

- Criar cache persistente sob demanda no Supabase.
- Salvar pacotes analiticos e respostas da IA.

Fase 4:

- Criar tela/relatorio visual premium.
- Incluir exportacao HTML/PDF quando o pacote estiver validado.

Fase 5:

- Validar com LEVEN e PROSPERA.
- Criar evidencias de amostra, tempos, consistencia de calculo e nao exposicao de dados sensiveis.
