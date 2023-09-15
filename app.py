# importação dos módulos necessários
import pandas as pd
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objs as go
from ipywidgets import interact
import ipywidgets as widgets
from plotly.subplots import make_subplots

# Carregamento de nossa base de dados em um dataframe
dados_abastecimento = pd.read_excel("Comb SUDOESTE (3 Meses).xlsx", sheet_name='DADOS')

# Amostra dos dados do dataframe (5 linhas)
dados_abastecimento.head()

# Descrição dos tipos de dados
dados_abastecimento.info()

# Separando a base de dados dos seguintes cartões: COR, POD, RET
abastecimento_filtrado_por_placa = dados_abastecimento[~dados_abastecimento['Placa'].str.startswith(('COR', 'POD', 'RET'))]

# Selecionando as colunas de valor para a nossa análise específica
abastecimento_limpo = abastecimento_filtrado_por_placa[['Cartao', 'Placa', 'Data/Hora',
                                                        'Motorista', 'Servico', 'Valor',
                                                        'Km Rodados', 'Horas Trabalhadas',
                                                        'Km/litro', 'Litros/Hora']]

# Separando a base dados em dois tipos de serviço para a análise
dados_gasolina = abastecimento_limpo[abastecimento_limpo['Servico'] == 'GASOLINA COMUM']
dados_diesel = abastecimento_limpo[(abastecimento_limpo['Servico'] == 'DIESEL') | (abastecimento_limpo['Servico'] == 'DIESEL S-10 COMUM')]
dados_arla = abastecimento_limpo[abastecimento_limpo['Servico'] == 'Arla 32']

# Armazenando a média de Km/litro por motorista
km_litro_por_motorista = dados_gasolina.groupby(['Motorista'])['Km/litro'].mean().reset_index()

# Armazenando a média de litros/hora por motorista
litro_hora_por_motorista = dados_diesel.groupby(['Motorista'])['Litros/Hora'].mean().reset_index()

app = dash.Dash(__name__)
server = app.server

# Layout do aplicativo
app.layout = html.Div([
    html.H1("Análise de Consumo de Combustível"),

    dcc.Graph(id='boxplot-gasolina-diesel'),

    dcc.Dropdown(
        id='motorista-dropdown',
        options=[{'label': motorista, 'value': motorista} for motorista in dados_gasolina['Motorista'].unique()],
        value=dados_gasolina['Motorista'].unique()[0],
        multi=False
    ),

    dcc.RangeSlider(
        id='km-range-slider',
        min=-20,
        max=20,
        step=1,
        marks={i: str(i) for i in range(-20, 21)},
        value=[-20, 20]
    ),

    dcc.Graph(id='scatter-motorista'),
    
    dcc.Dropdown(
        id='placa-dropdown',
        options=[{'label': placa, 'value': placa} for placa in dados_gasolina['Placa'].unique()],
        value=dados_gasolina['Placa'].unique()[0],
        multi=False
    ),
    
    dcc.Graph(id='scatter-placa'),

    # Novo componente Dropdown e RangeSlider para Litros/Hora
    dcc.Dropdown(
        id='litros-hora-motorista-dropdown',
        options=[{'label': motorista, 'value': motorista} for motorista in dados_diesel['Motorista'].unique()],
        value=dados_diesel['Motorista'].unique()[0],
        multi=False
    ),
    
    dcc.RangeSlider(
        id='litros-hora-range-slider',
        min=-20,
        max=20,
        step=1,
        marks={i: str(i) for i in range(-20, 21)},
        value=[-20, 20]
    ),
    
    dcc.Graph(id='scatter-litros-hora')
])

# Callbacks para atualizar os gráficos interativos
@app.callback(
    Output('boxplot-gasolina-diesel', 'figure'),
    Output('scatter-motorista', 'figure'),
    Output('scatter-placa', 'figure'),
    Output('scatter-litros-hora', 'figure'),  # Novo gráfico de dispersão para Litros/Hora
    Input('motorista-dropdown', 'value'),
    Input('km-range-slider', 'value'),
    Input('placa-dropdown', 'value'),
    Input('litros-hora-motorista-dropdown', 'value'),  # Novo Dropdown para Litros/Hora
    Input('litros-hora-range-slider', 'value')  # Novo RangeSlider para Litros/Hora
)
def update_graphs(motorista_selecionado, km_intervalo, placa_selecionada, litros_hora_motorista, litros_hora_intervalo):
    km_min, km_max = km_intervalo

    # Atualizar o gráfico de dispersão por motorista
    dados_filtrados_motorista = dados_gasolina[(dados_gasolina['Motorista'] == motorista_selecionado) &
                                               (dados_gasolina['Km/litro'] >= km_min) &
                                               (dados_gasolina['Km/litro'] <= km_max)]

    scatter_fig_motorista = go.Figure()
    for placa, dados_placa in dados_filtrados_motorista.groupby('Placa'):
        scatter_fig_motorista.add_trace(go.Scatter(x=dados_placa['Data/Hora'], y=dados_placa['Km/litro'], mode='markers', name=placa))

    scatter_fig_motorista.update_layout(title=f'Km por Litro por Placa para {motorista_selecionado}',
                                        xaxis_title='Data/Hora', yaxis_title='Km/litro')

    # Atualizar o gráfico de dispersão por placa
    dados_filtrados_placa = dados_gasolina[(dados_gasolina['Placa'] == placa_selecionada) &
                                           (dados_gasolina['Km/litro'] >= km_min) &
                                           (dados_gasolina['Km/litro'] <= km_max)]

    scatter_fig_placa = go.Figure()
    for placa, dados_placa in dados_filtrados_placa.groupby('Placa'):
        scatter_fig_placa.add_trace(go.Scatter(x=dados_placa['Data/Hora'], y=dados_placa['Km/litro'], mode='markers', name=placa))

    scatter_fig_placa.update_layout(title=f'Km por Litro para a Placa {placa_selecionada}',
                                    xaxis_title='Data/Hora', yaxis_title='Km/litro')

    # Atualizar o gráfico de dispersão por Litros/Hora
    litros_hora_min, litros_hora_max = litros_hora_intervalo
    dados_filtrados_litros_hora = dados_diesel[(dados_diesel['Motorista'] == litros_hora_motorista) &
                                                 (dados_diesel['Litros/Hora'] >= litros_hora_min) &
                                                 (dados_diesel['Litros/Hora'] <= litros_hora_max)]

    scatter_fig_litros_hora = go.Figure()
    for placa, dados_placa in dados_filtrados_litros_hora.groupby('Placa'):
        scatter_fig_litros_hora.add_trace(go.Scatter(x=dados_placa['Data/Hora'], y=dados_placa['Litros/Hora'], mode='markers', name=placa))

    scatter_fig_litros_hora.update_layout(title=f'Litros por Hora por Placa para {litros_hora_motorista}',
                                          xaxis_title='Data/Hora', yaxis_title='Litros/Hora')

    # Criar boxplots lado a lado
    fig = make_subplots(rows=1, cols=2, subplot_titles=['Km/litro Gasolina Comum', 'Litro/Hora Diesel'])

    box_gasolina = px.box(km_litro_por_motorista, y='Km/litro', points='all', hover_data=['Motorista', 'Km/litro'],
                          labels={'Km/litro': 'Km/litro'}, title='Boxplot de Km por Litro por Motorista')
    
    box_diesel = px.box(litro_hora_por_motorista, y='Litros/Hora', points='all', hover_data=['Motorista', 'Litros/Hora'],
                        labels={'Litros/Hora': 'Litros/Hora'}, title='Boxplot de Litros por Hora por Motorista')

    box_diesel.update_traces(marker=dict(color='orange'), line_color='orange')    
    fig.add_trace(box_gasolina.data[0], row=1, col=1)
    fig.add_trace(box_diesel.data[0], row=1, col=2)

    return fig, scatter_fig_motorista, scatter_fig_placa, scatter_fig_litros_hora

if __name__ == '__main__':
    app.run_server(debug=True)
    app.run_server(host='192.168.1.53', port=8050, debug=True)
