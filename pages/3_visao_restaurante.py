#Bibliotecas
import pandas as pd
import re
import plotly.express as px
import plotly.graph_objects as go
import folium
from haversine import haversine
import streamlit as st
from PIL import Image
from streamlit_folium import folium_static
import numpy as np

st.set_page_config(page_title='Visão Restaurantes', page_icon='', layout='wide')

#=====================================
#Funções
#=====================================
def clean_code(df1):
    """ Esta função tem aaa responsabilidade de limpar o dataframe
        Tipos de limpeza:
        1. Remoção dos dados NaN
        2. Mudança do tipo da coluna de dados
        3. Remoção dos espaços das variáveis de texto
        4. Formatação da coluna de datas
        5. Limpeza da coluna de tempo (remoção do texto da variável númerica)
        
        Input: Datafraame
        Output: Dataframe
    """
    #1. covertendo a coluna Age de texto para numero
    linhas_vazias = (df1['Delivery_person_Age'] != 'NaN ')
    df1 = df1.loc[linhas_vazias, :].copy()
    linhas_vazias = (df1['Road_traffic_density'] != 'NaN ')
    df1 = df1.loc[linhas_vazias, :].copy()
    linhas_vazias = (df1['City'] != 'NaN ')
    df1 = df1.loc[linhas_vazias, :].copy()
    linhas_vazias = (df1['Festival'] != 'NaN ')
    df1 = df1.loc[linhas_vazias, :].copy()

    df1['Delivery_person_Age'] = df1['Delivery_person_Age'].astype(int)

    #2. convertendo a coluna Ratings de texto para numero decimaal 
    df1['Delivery_person_Ratings'] = df1['Delivery_person_Ratings'].astype(float)

    #3. convertendo a coluna order_date de texto para data
    df1['Order_Date'] = pd.to_datetime(df1['Order_Date'], format='%d-%m-%Y')

    #4. convertendo multiple_deliveries de texto para numero inteiro(int)
    linhas_selecionadas = (df1['multiple_deliveries'] != 'NaN ')
    df1 = df1.loc[linhas_selecionadas, :].copy()
    df1['multiple_deliveries'] = df1['multiple_deliveries'].astype(int)

    #5. removendo os espacos dentro de strings/texto/object
    df1.loc[:, 'ID'] = df1.loc[:, 'ID'].str.strip()
    df1.loc[:, 'Type_of_order'] = df1.loc[:, 'Type_of_order'].str.strip()
    df1.loc[:, 'Type_of_vehicle'] = df1.loc[:, 'Type_of_vehicle'].str.strip()
    df1.loc[:, 'City'] = df1.loc[:, 'City'].str.strip()
    df1.loc[:, 'Road_traffic_density'] = df1.loc[:, 'Road_traffic_density'].str.strip()
    df1.loc[:, 'Festival'] = df1.loc[:, 'Festival'].str.strip()

    # Comando para remover o texto de números
    df1 = df1.reset_index( drop=True )

    # Retirando os numeros da coluna Time_taken(min)
    df1['Time_taken(min)'] = df1['Time_taken(min)'].apply(lambda x: x.split( '(min) ')[1])
    df1['Time_taken(min)'] = df1['Time_taken(min)'].astype(int)
    
    return df1

def distance(df1, fig):
    if fig == False:
        cols = ['Delivery_location_latitude', 'Delivery_location_longitude', 'Restaurant_latitude', 'Restaurant_longitude']
        df1['distance'] = df1.loc[:, cols].apply( lambda x: haversine( (x['Restaurant_latitude'], x['Restaurant_longitude']), 
                                                                  (x['Delivery_location_latitude'], x['Delivery_location_longitude']) ), axis=1 )
        avg_distance = np.round(df1['distance'].mean(), 2)
    
        return avg_distance
    else:
        cols = ['Delivery_location_latitude', 'Delivery_location_longitude', 'Restaurant_latitude', 'Restaurant_longitude']
        df1['distance'] = df1.loc[:, cols].apply( lambda x: haversine( (x['Restaurant_latitude'], x['Restaurant_longitude']), 
                                                                  (x['Delivery_location_latitude'], x['Delivery_location_longitude']) ), axis=1 )
        avg_distance = df1.loc[:, ['City', 'distance']].groupby('City').mean().reset_index()
        fig = go.Figure( data=[go.Pie( labels=avg_distance['City'], values=avg_distance['distance'], pull=[0, 0.1, 0])])
        
        return fig
    

def avg_std_time_delivery(df1, festival, op):
    """ Esta função calcula o tempo médio e o desvio padrão do tempo de entrega.
            Parâmetros:
                Input:
                    - df: Dataframe com os dados necessários para o cálculo
                    - op: Tipo de operação que precisa ser calculado
                        'avg_time': Calcula o tempo médio
                        'std_time': Calcula o desvio padrão
                Output:
                    - df: Dataframe com 2 colunas e 1 linha
    """
    df_aux = (df1.loc[:, ['Time_taken(min)', 'Festival']]
                      .groupby('Festival')
                      .agg( {'Time_taken(min)': ['mean', 'std']}))

    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()
    df_aux = np.round(df_aux.loc[df_aux['Festival'] == festival, op], 2)
    
    return df_aux

def avg_std_time_graph(df1):
    cols = ['City', 'Time_taken(min)']
    df_aux = df1.loc[:, cols].groupby('City').agg( {'Time_taken(min)': ['mean', 'std']} )
    df_aux.columns = ['avg_time', 'std_time'] 
    df_aux = df_aux.reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(name='Control', x=df_aux['City'], y=df_aux['avg_time'], error_y=dict( type='data', array=df_aux['std_time'])))
    fig.update_layout(barmode='group')
                
    return fig

def avg_std_time_on_traffic(df1):
    cols = ['City', 'Time_taken(min)', 'Road_traffic_density']
    df_aux = df1.loc[:, cols].groupby(['City', 'Road_traffic_density']).agg( {'Time_taken(min)': ['mean', 'std']} )
    df_aux.columns = ['avg_time', 'std_time']
    df_aux = df_aux.reset_index()

    fig = px.sunburst(df_aux, path=['City', 'Road_traffic_density'], values='avg_time',
                              color='std_time', color_continuous_scale='RdBu',
                              color_continuous_midpoint=np.average(df_aux['std_time']))
                
    return fig


#======================================================== Inicio da Estrutura lógica do código =================================================================

#=====================================
# Import dataset
#=====================================
df = pd.read_csv('train.csv')

#=====================================
# Limpeza dos dados
#=====================================
df1 = clean_code(df)

#=====================================
#Sidebar -  Streamlit
#=====================================
st.header('Marketplace - Visão Restaurantes')

#image_path = 'logo.png'
image = Image.open('logo.png')
st.sidebar.image(image, width=120)

st.sidebar.markdown('# Cury Company')
st.sidebar.markdown('## Fastest Delivery in Town')
st.sidebar.markdown("""---""")

st. sidebar.markdown('## Selecione uma data limite')
data_slider = st.sidebar.slider(
    'Até qual valor?',
    value=pd.datetime( 2022, 4, 13 ),
    min_value=pd.datetime(2022, 2, 11),
    max_value=pd.datetime(2022, 4, 6),
    format='DD-MM-YYYY')


st.sidebar.markdown("""---""")

traffic_options = st.sidebar.multiselect(
    'Quais as condições do trânsito',
    ['Low', 'Medium', 'High', 'Jam'],
    default=['Low', 'Medium', 'High', 'Jam'])

st.sidebar.markdown("""---""")
st.sidebar.markdown('### Powered by Comunidade DS')

#Filtro de data
linhas_selecionadas = df1['Order_Date'] < data_slider
df1 = df1.loc[linhas_selecionadas, :]

#Filtro de transito
linhas_selecionadas = df1['Road_traffic_density'].isin(traffic_options)
df1 = df1.loc[linhas_selecionadas, :]

#=====================================
#Layout -  Streamlit
#=====================================
tab1, tab2, tab3 = st.tabs(['Visão Gerencial', ' - ', ' - '])

with tab1:
    with st.container():
        st.markdown("""---""")
        st.title('Overall Metrics')
        
        col1, col2, col3, col4, col5, col6 = st.columns(6)
        
        with col1:
            delivery_unique = len(df1.loc[:, 'Delivery_person_ID'].unique())
            col1.metric('Entregadores', delivery_unique)

        with col2:
            avg_distance = distance(df1, fig=False)
            col2.metric('A distância média', avg_distance)                        
            
        with col3:
            df_aux = avg_std_time_delivery(df1, 'Yes', 'avg_time')
            col3.metric('Tempo Médio', df_aux)                 
            
        with col4:
            df_aux = avg_std_time_delivery(df1, 'Yes', 'std_time')
            col4.metric('STD Entrega', df_aux)
            
        with col5:
            df_aux = avg_std_time_delivery(df1, 'No', 'avg_time')
            col5.metric('Tempo Médio', df_aux)
            
        with col6:
            df_aux = avg_std_time_delivery(df1, 'No', 'std_time')
            col6.metric('STD Entrega', df_aux)
        
    with st.container():
        st.markdown("""---""")
        col1, col2,  = st.columns(2)
        
        with col1:
            st.markdown('##### Tempo Médio de entrega por cidade')
            fig = avg_std_time_graph(df1)
            st.plotly_chart(fig)
                        
        with col2:
            st.markdown('##### Distribuição da Distância')
            df_aux = df1.loc[:, ['City', 'Time_taken(min)', 'Type_of_order']].groupby(['City', 'Type_of_order']).agg( {'Time_taken(min)': ['mean', 'std']} )
            df_aux.columns = ['avg_time', 'std_time']
            df_aux = df_aux.reset_index()
            st.dataframe(df_aux)

        
    with st.container():
        st.markdown("""---""")
        st.markdown('##### Distribuição do Tempo')
     
        col1, col2,  = st.columns(2)
        with col1:
            fig = distance(df1, fig=True)
            st.plotly_chart(fig)
 
        with col2:
            fig = avg_std_time_on_traffic(df1)
            st.plotly_chart(fig) 
    