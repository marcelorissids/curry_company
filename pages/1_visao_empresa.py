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

st.set_page_config(page_title='Visão Empresa', page_icon='', layout='wide')

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

def order_metric(df1):
    cols = ['ID', 'Order_Date']
    df_aux = df1.loc[:, cols].groupby('Order_Date').count().reset_index()
    fig = px.bar(df_aux, x='Order_Date', y='ID')
            
    return fig

def traffic_order_share(df1):
    df_aux = df1.loc[:, ['ID', 'Road_traffic_density']].groupby('Road_traffic_density').count().reset_index()
    df_aux = df_aux.loc[df_aux['Road_traffic_density'] != 'NaN',:]
    df_aux['entregas_perc'] = df_aux['ID'] / df_aux['ID'].sum()
    fig = px.pie(df_aux, values='entregas_perc', names='Road_traffic_density')
                
    return fig

def traffic_order_city(df1):
    df_aux = df1.loc[:, ['ID', 'City', 'Road_traffic_density']].groupby(['City', 'Road_traffic_density']).count().reset_index()
    df_aux = df_aux.loc[df_aux['City'] != 'NaN', :]
    df_aux = df_aux.loc[df_aux['Road_traffic_density'] != 'NaN', :]
    fig = px.scatter(df_aux, x='City', y='Road_traffic_density', size='ID', color='City')
    
    return fig

def order_by_week(df1):
    df1['week_of_year'] = df1['Order_Date'].dt.strftime('%U')
    df_aux = df1.loc[:, ['ID', 'week_of_year']].groupby('week_of_year').count().reset_index()
    fig = px.line(df_aux, x='week_of_year', y='ID')
        
    return fig
    
def order_share_by_week(df1):
    df_aux01 = df1.loc[:, ['ID', 'week_of_year']].groupby('week_of_year').count().reset_index()
    df_aux02 = df1.loc[:, ['Delivery_person_ID', 'week_of_year']].groupby('week_of_year').nunique().reset_index()
    df_aux = pd.merge(df_aux01, df_aux02, how='inner')
    df_aux['order_by_deliver'] = df_aux['ID'] / df_aux['Delivery_person_ID']
    fig = px.line(df_aux, x='week_of_year', y='order_by_deliver')
    
    return fig

def country_maps(df1):
    df_aux = df1.loc[:, ['City', 'Road_traffic_density', 'Delivery_location_latitude', 'Delivery_location_longitude']].groupby(['City', 'Road_traffic_density']).median().reset_index()
    
    map = folium.Map()

    for index, location_info in df_aux.iterrows():
        folium.Marker([location_info['Delivery_location_latitude'],
                      location_info['Delivery_location_longitude']],
                      popup=location_info[['City', 'Road_traffic_density']]).add_to(map)
        
    folium_static(map, width=1024, height=600)
    
    return None
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
st.header('Marketplace - Visão Cliente')

#image_path = 'logo.png'
image = Image.open('logo.png')
st.sidebar.image(image, width=120)

st.sidebar.markdown('# Cury Company')
st.sidebar.markdown('## Fastest Delivery in Town')
st.sidebar.markdown("""---""")

st. sidebar.markdown('## Selecione uma data limite')
data_slider = st.sidebar.slider(
    'Até qual valor?',
    value=pd.datetime( 2024, 4, 13 ),
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
tab1, tab2, tab3 = st.tabs(['Visão Gerencial', 'Visão Tática', 'Visão Geográfica'])

with tab1:
    with st.container():
        fig = order_metric(df1)
        st.markdown('# Orders by Day')
        st.plotly_chart(fig, use_container_width=True)
             
        
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            fig = traffic_order_share(df1)
            st.markdown('# Traffic Order Share')
            st.plotly_chart(fig, use_container_width=True)
            
                        
        with col2:
            fig = traffic_order_city(df1)
            st.markdown('# Traffic Order City')
            st.plotly_chart(fig, use_container_width=True)
                        
with tab2:
    with st.container():
        fig = order_by_week(df1)
        st.markdown('#  Order by Week')
        st.plotly_chart(fig, use_container_width=True)  
        
        
    with st.container():
        fig = order_share_by_week(df1)
        st.markdown('#  Order Share by Week')
        st.plotly_chart(fig, use_container_width=True)        

with tab3:
    st.markdown('# Country Maps')
    country_maps(df1)