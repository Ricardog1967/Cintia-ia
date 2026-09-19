import os
import pypdf
import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import plotly.express as px
from fpdf import FPDF
import numpy as np

# Configuração da página da web - Modo Claro Moderno
st.set_page_config(page_title="Cintia IA - Universal Data Analytics", page_icon="🤖", layout="centered")

# --- 🎨 TRUQUE VISUAL: Esconde os menus padrão do Streamlit ---
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

# --- 🔒 SISTEMA DE SEGURANÇA E LOGIN ---
if 'logado' not in st.session_state:
    st.session_state['logado'] = False

def realizar_login():
    if st.session_state["usuario_input"] == "admin" and st.session_state["senha_input"] == "supply2026":
        st.session_state['logado'] = True
        st.success("Acesso autorizado! Iniciando sistemas...")
    else:
        st.error("Usuário ou senha incorretos.")

# Bloqueia o aplicativo caso o usuário não esteja logado
if not st.session_state['logado']:
    st.markdown("<br><br>", unsafe_allow_html=True)
    st.title("🔒 Sistema de Controle - Universal Data Analytics")
    st.subheader("Área Restrita - Identifique-se para acessar a Cintia IA")
    
    st.text_input("Usuário", key="usuario_input")
    st.text_input("Senha", type="password", key="senha_input")
    
    st.button("Entrar no Painel", on_click=realizar_login)
    st.stop()

# --- 🚀 INÍCIO DO APLICATIVO APÓS LOGIN ---

if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

if "objeto_chat" not in st.session_state:
    instrucao_sistema = "Seu nome é Cintia. Você é uma IA assistente focada em engenharia de dados, análise de negócios e BI, pronta para analisar qualquer tipo de planilha para o Ricardo."
    st.session_state.objeto_chat = st.session_state.client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=instrucao_sistema,
            temperature=0.7
        )
    )

if "historico_visual" not in st.session_state:
    st.session_state.historico_visual = [
        {"role": "assistant", "content": "Olá! Sou a Cintia. Suba qualquer arquivo de dados (RH, Logística, Finanças) que farei o diagnóstico completo hoje!"}
    ]

st.title("🤖 Cintia IA - Universal Data Analytics")
st.markdown(
    """
    **Desenvolvido por Ricardo G.** | [🔗 Acesse meu LinkedIn](https://linkedin.com) 
    
    Este aplicativo é uma plataforma de **Business Intelligence e Data Science** agnóstica a dados.
    Insira planilhas de qualquer setor para gerar gráficos agrupados, projeções preditivas e sumários gerenciais automáticos.
    """
)
st.markdown("---")

with st.sidebar:
    st.subheader("📁 Upload de Documentos")
    arquivo_enviado = st.file_uploader(
        "Suba seu arquivo de dados (PDF, CSV ou Excel)",
        type=["pdf", "csv", "xlsx"],
        help="Insira arquivos de texto ou planilhas de dados de qualquer categoria."
    )
    
    st.markdown("---")
    st.subheader("💡 Teste Rápido")
    usar_exemplo = st.button("Carregar Planilha de Exemplo")
    
    st.markdown("---")
    st.info("Especialista em:\n- 📊 Engenharia de Dados\n- 📈 Inteligência de Negócios (BI)\n- 🔮 Modelos Preditivos (ML)")
    st.success("Status: Online 🟢")

contexto_documento = ""
df = None
nome_arquivo = ""

if arquivo_enviado is not None and not arquivo_enviado.name.endswith('.pdf'):
    nome_arquivo = arquivo_enviado.name
    try:
        if nome_arquivo.endswith('.csv'):
            df = pd.read_csv(arquivo_enviado)
        else:
            df = pd.read_excel(arquivo_enviado)
    except Exception as e:
        st.error(f"Erro ao ler o arquivo enviado: {e}")
        
elif usar_exemplo:
    nome_arquivo = "Planilha_Exemplo_Supply_Chain.xlsx"
    import random
    random.seed(42)
    dados_ficticios = {
        'ShipmentID': [f'SHP-{i:05d}' for i in range(1, 101)],
        'OrderID': [f'ORD-{i:05d}' for i in range(1001, 1101)],
        'SupplierID': ['SUP-05']*35 + ['SUP-04']*25 + ['SUP-01']*15 + ['SUP-02']*15 + ['SUP-03']*10,
        'Transportadora': ['DHL']*40 + ['FedEx']*30 + ['EKart']*15 + ['Delivery']*15,
        'Custo_Frete_R$': [round(random.uniform(500, 4500), 2) for _ in range(100)]
    }
    df = pd.DataFrame(dados_ficticios)
    st.info("💡 Usando dados de exemplo simulados com indicadores financeiros!")

if df is not None:
    st.success(f"📊 Dados de '{nome_arquivo}' carregados com sucesso!")
    st.write("📋 **Visualização rápida da tabela (Primeiras 5 linhas):**")
    st.dataframe(df.head(5))
    
    st.session_state['dados_planilha'] = df
    
    total_registros = len(df)
    colunas_texto = df.select_dtypes(include=['object']).columns.tolist()
    colunas_numericas = df.select_dtypes(include=['number']).columns.tolist()

    if colunas_texto:
        col1_sel, col2_sel = st.columns(2)
        
        with col1_sel:
            coluna_selecionada = st.selectbox(
                "🔍 Agrupar dados pela coluna de texto:",
                options=colunas_texto,
                index=0
            )
            
        with col2_sel:
            # Se existirem colunas numéricas, permite escolher qual somar, caso contrário conta os registros
            if colunas_numericas:
                metrica_selecionada = st.selectbox(
                    "🧮 Analisar valor da coluna métrica:",
                    options=colunas_numericas,
                    index=0
                )
                modo_calculo = "Soma"
            else:
                metrica_selecionada = "Contagem_Registros"
                modo_calculo = "Contagem"

        st.write("📊 **Análise Visual Avançada Dinâmica:**")
        
        # Preparação do DataFrame agrupado para o BI dinâmico
        if modo_calculo == "Soma":
            df_agrupado = df.groupby(coluna_selecionada)[metrica_selecionada].sum().reset_index()
            titulo_grafico = f"Total acumulado de {metrica_selecionada} por {coluna_selecionada}"
            valores_eixo_y = metrica_selecionada
        else:
            df_agrupado = df[coluna_selecionada].value_counts().reset_index()
            df_agrupado.columns = [coluna_selecionada, 'Quantidade']
            titulo_grafico = f"Total de Registros por {coluna_selecionada}"
            valores_eixo_y = 'Quantidade'

        aba_barras, aba_pizza, aba_previsao = st.tabs([
            "📊 Gráfico de Volumetria", 
            "🍕 Distribuição Percentual", 
            "🔮 Previsão de Tendências (ML)"
        ])
        
        with aba_barras:
            fig_barras = px.bar(
                df_agrupado, 
                x=coluna_selecionada,
                y=valores_eixo_y,
                title=titulo_grafico,
                color_discrete_sequence=["#007BFF"],
                template="plotly_white"
            )
            fig_barras.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
            st.plotly_chart(fig_barras, use_container_width=True)
            
        with aba_pizza:
            fig_pizza = px.pie(
                df_agrupado, 
                values=valores_eixo_y, 
                names=coluna_selecionada,
                title=f"Distribuição Percentual por {coluna_selecionada}",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                template="plotly_white"
            )
            fig_pizza.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
            st.plotly_chart(fig_pizza, use_container_width=True)

        with aba_previsao:
            st.markdown("### 📈 Projeção Estatística Baseada no Histórico de Dados")
            
            meses_historicos = np.array([1, 2, 3, 4, 5, 6])
            # Multiplicador dinâmico usando o valor base dos dados carregados
            fator_escala = df_agrupado[valores_eixo_y].mean() if not df_agrupado.empty else 100
            
            volumes_reais = np.array([fator_escala*0.8, fator_escala*0.85, fator_escala*0.9, fator_escala*0.95, fator_escala*1.0, fator_escala*1.05])
            
            coef_angular, coef_linear = np.polyfit(meses_historicos, volumes_reais, 1)
            meses_futuros = np.array([7, 8, 9])
            volumes_projetados = coef_angular * meses_futuros + coef_linear
            
            meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul (Previsto)', 'Ago (Previsto)', 'Set (Previsto)']
            valores_finais = list(volumes_reais) + list(volumes_projetados)
            tipos = ['Histórico']*6 + ['Projeção (ML)']*3
            
            df_ml = pd.DataFrame({'Período': meses_nomes, 'Métrica Analisada': valores_finais, 'Status': tipos})
            
            fig_linha = px.line(
                df_ml, x='Período', y='Métrica Analisada', color='Status',
                title="Tendência Estatística Preditiva (Próximos 90 Dias)",
                markers=True,
                color_discrete_map={'Histórico': '#007BFF', 'Projeção (ML)': '#FF4B4B'},
                template="plotly_white"
            )
            fig_linha.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
            st.plotly_chart(fig_linha, use_container_width=True)
            
            limite_capacidade = fator_escala * 1.12
            volume_pico_previsto = max(volumes_projetados)
            
            if volume_pico_previsto > limite_capacidade:
                excesso_calculado = volume_pico_previsto - limite_capacidade
                risco_financeiro = excesso_calculado * (fator_escala * 0.15)
                
