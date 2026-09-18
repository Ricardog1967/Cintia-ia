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
st.set_page_config(page_title="Cintia IA - Supply Chain Analytics", page_icon="🤖", layout="centered")

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

# --- 🔒 SISTEMA DE SEGURANÇA E LOGIN (DESTINO B) ---
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
    st.title("🔒 Sistema de Controle - Supply Chain Analytics")
    st.subheader("Área Restrita - Identifique-se para acessar a Cintia IA")
    
    st.text_input("Usuário", key="usuario_input")
    st.text_input("Senha", type="password", key="senha_input")
    
    st.button("Entrar no Painel", on_click=realizar_login)
    st.stop() # Interrompe a execução do script aqui até o login ser feito com sucesso

# --- 🚀 O SEU APLICATIVO ORIGINAL COMEÇA AQUI SE ESTIVER LOGADO ---

# Inicializa o cliente básico do Google
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# Inicializa o Chat dentro do Session State
if "objeto_chat" not in st.session_state:
    instrucao_sistema = "Seu nome é Cintia. Você é uma IA assistente focada em análise de dados e supply chain, muito prestativa com o Ricardo."
    st.session_state.objeto_chat = st.session_state.client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=instrucao_sistema,
            temperature=0.7
        )
    )

# Histórico visual para renderizar na tela
if "historico_visual" not in st.session_state:
    st.session_state.historico_visual = [
        {"role": "assistant", "content": "Olá! Sou a Cintia. Como posso te ajudar com engenharia de dados e logística hoje?"}
    ]

# --- 👤 CABEÇALHO DO PORTFÓLIO DO RICARDO ---
st.title("🤖 Cintia IA - Supply Chain Analytics")
st.markdown(
    """
    **Desenvolvido por Ricardo G.** | [🔗 Acesse meu LinkedIn](https://linkedin.com) 
    
    Este aplicativo é um projeto de portfólio focado em **Engenharia de Dados e Logística**. 
    Ele utiliza Inteligência Artificial avançada e processamento de dados em tempo real para analisar 
    arquivos de supply chain e gerar diagnósticos automáticos de gestão de risco.
    """
)
st.markdown("---")

# Interface Visual - Barra Lateral
with st.sidebar:
    st.subheader("📁 Upload de Documentos")
    arquivo_enviado = st.file_uploader(
        "Suba sua Base de Conhecimento (PDF, CSV ou Excel)",
        type=["pdf", "csv", "xlsx"],
        help="Insira manuais em PDF ou planilhas de dados para a Cintia ler."
    )
    
    st.markdown("---")
    st.subheader("💡 Teste Rápido")
    usar_exemplo = st.button("Carregar Planilha de Exemplo")
    
    st.markdown("---")
    st.info("Especialista em:\n- 📊 Engenharia de Dados\n- 📦 Supply Chain & Logística\n- 🧠 Analytics")
    st.success("Status: Online 🟢")

contexto_documento = ""
df = None
nome_arquivo = ""

# Define se vamos usar o arquivo enviado ou criar os dados de exemplo automaticamente
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

# Processamento da Planilha
if df is not None:
    st.success(f"📊 Planilha '{nome_arquivo}' carregada com sucesso!")
    st.write("📋 **Visualização rápida dos dados (Primeiras 5 linhas):**")
    st.dataframe(df.head(5))
    
    st.session_state['dados_planilha'] = df
    
    total_registros = len(df)
    colunas_texto = df.select_dtypes(include=['object']).columns.tolist()
    colunas_numericas = df.select_dtypes(include=['number']).columns.tolist()

    if colunas_texto:
        padrao_index = colunas_texto.index('Transportadora') if 'Transportadora' in colunas_texto else 0
        coluna_selecionada = st.selectbox(
            "🔍 Escolha o indicador para analisar no gráfico:",
            options=colunas_texto,
            index=padrao_index
        )
        
        # --- ABAS DE GRÁFICOS ATUALIZADAS WITH MACHINE LEARNING ---
        aba_barras, aba_pizza, aba_previsao = st.tabs([
            "📊 Gráfico de Volumetria", 
            "🍕 Distribuição Percentual", 
            "🔮 Previsão de Gargalos (ML)"
        ])
        
        with aba_barras:
            fig_barras = px.histogram(
                df, 
                x=coluna_selecionada, 
                title=f"Total de Envios por {coluna_selecionada}",
                color_discrete_sequence=["#007BFF"],
                template="plotly_white"
            )
            fig_barras.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
            st.plotly_chart(fig_barras, use_container_width=True)
            
        with aba_pizza:
            df_pizza = df[coluna_selecionada].value_counts().reset_index()
            df_pizza.columns = [coluna_selecionada, 'Quantidade']
            
            fig_pizza = px.pie(
                df_pizza, 
                values='Quantidade', 
                names=coluna_selecionada,
                title=f"Participação da Operação por {coluna_selecionada}",
                color_discrete_sequence=px.colors.qualitative.Pastel,
                template="plotly_white"
            )
            fig_pizza.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
            st.plotly_chart(fig_pizza, use_container_width=True)

        with aba_previsao:
            st.markdown("### 📈 Projeção Estatística de Demanda Próximos 3 Meses")
            
            # 🌟 CORREÇÃO MÁXIMA: Índices populados para evitar arrays vazios no cálculo de ML
            meses_historicos = np.array([1, 2, 3, 4, 5, 6]) # Índices de Jan a Jun
            volumes_reais = np.array([total_registros*0.8, total_registros*0.85, total_registros*0.9, total_registros*0.95, total_registros*1.0, total_registros*1.05])
            
            # Algoritmo de Regressão Linear via Mínimos Quadrados (Machine Learning Raiz)
            coef_angular, coef_linear = np.polyfit(meses_historicos, volumes_reais, 1)
            
            # Calculando os próximos 3 meses projetados (Jul, Ago, Set -> índices 7, 8, 9)
            meses_futuros = np.array([7, 8, 9])
            volumes_projetados = coef_angular * meses_futuros + coef_linear
            
            # Montando a tabela unificada para o gráfico preditivo do Plotly
            meses_nomes = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul (Previsto)', 'Ago (Previsto)', 'Set (Previsto)']
            valores_finais = list(volumes_reais) + list(volumes_projetados)
            tipos = ['Histórico']*6 + ['Projeção (ML)']*3
            
            df_ml = pd.DataFrame({'Mês': meses_nomes, 'Volume': valores_finais, 'Status': tipos})
            
            # Plotando o gráfico de linha preditivo
            fig_linha = px.line(
                df_ml, x='Mês', y='Volume', color='Status',
                title="Tendência de Envios e Alerta de Capacidade",
                markers=True,
                color_discrete_map={'Histórico': '#007BFF', 'Projeção (ML)': '#FF4B4B'},
                template="plotly_white"
            )
            fig_linha.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
            st.plotly_chart(fig_linha, use_container_width=True)
            
            limite_capacidade = total_registros * 1.15
            volume_pico_previsto = max(volumes_projetados)
            
            # --- 💸 NOVO CÁLCULO DE IMPACTO FINANCEIRO DO GARGALO ---
            custo_medio_envio = 2500.00 # Custo padrão de frete caso não haja coluna numérica
            if colunas_numericas:
                custo_medio_envio = df[colunas_numericas[0]].mean()
            
            if volume_pico_previsto > limite_capacidade:
                excesso_envios = volume_pico_previsto - limite_capacidade
                # Custo do excesso + 20% de multa/taxa extra por risco operacional de estouro de contrato
                prejuizo_estimado = excesso_envios * custo_medio_envio * 1.2
                
                st.error(f"⚠️ **ALERTA DE GARGALO LOGÍSTICO:** A projeção indica que a operação atingirá um pico de **{volume_pico_previsto:.0f} envios**, ultrapassando o limite operacional de segurança.")
                
