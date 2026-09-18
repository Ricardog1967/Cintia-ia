import os
import pypdf
import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import plotly.express as px
from fpdf import FPDF # <-- Nova ferramenta para gerar o PDF de exportação

# Configuração da página da web - Modo Claro Moderno
st.set_page_config(page_title="Cintia IA - Supply Chain Analytics", page_icon="🤖", layout="centered")

# --- 🎨 TRUQUE VISUAL: Esconde os menus padrão do Streamlit para parecer um App Próprio ---
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        </style>
        """
st.markdown(hide_menu_style, unsafe_allow_html=True)

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
        help="Insira manuais in PDF ou planilhas de dados para a Cintia ler."
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
if arquivo_enviado is not None:
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
    
    st.write("📊 **Análise Visual Avançada:**")
    colunas_texto = df.select_dtypes(include=['object']).columns.tolist()
    colunas_numericas = df.select_dtypes(include=['number']).columns.tolist()

    if colunas_texto:
        padrao_index = colunas_texto.index('Transportadora') if 'Transportadora' in colunas_texto else 0
        coluna_selecionada = st.selectbox(
            "🔍 Escolha o indicador para analisar no gráfico:",
            options=colunas_texto,
            index=padrao_index
        )
        
        # Abas de gráficos
        aba_barras, aba_pizza = st.tabs(["📊 Gráfico de Volumetria", "🍕 Distribuição Percentual"])
        
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
        
        # --- 🧠 INSIGHTS AUTOMÁTICOS COM PAINEL FINANCEIRO ---
        st.markdown(f"### 💡 Diagnóstico da Cintia sobre {coluna_selecionada}:")
        
        top_registro = df[coluna_selecionada].value_counts().idxmax()
        Qtd_top_registro = df[coluna_selecionada].value_counts().max()
        total_registros = len(df)
        percentual = (Qtd_top_registro / total_registros) * 100
        
        total_financeiro_str = "N/A"
        if colunas_numericas:
            col1, col2, col3 = st.columns(3)
            col_financeira = colunas_numericas[0]
            total_financeiro = df[col_financeira].sum()
            total_financeiro_str = f"R$ {total_financeiro:,.2f}"
            
            with col1:
                st.metric(label=f"Maior Volume ({coluna_selecionada})", value=str(top_registro))
            with col2:
                st.metric(label="Total de Movimentações", value=f"{total_registros}")
            with col3:
                st.metric(label="Custo Total Identificado", value=total_financeiro_str)
        else:
            col1, col2 = st.columns(2)
            with col1:
                st.metric(label=f"Maior Volume ({coluna_selecionada})", value=str(top_registro))
            with col2:
                st.metric(label="Total de Movimentações", value=f"{total_registros} envios")
        
        alerta_texto = (
            f"O indicador {top_registro} concentra {percentual:.1f}% de toda a sua operação "
            f"analisada nesta coluna (com {Qtd_top_registro} envios). Monitore de perto essa concentração."
        )
        st.warning(f"⚠️ **Aviso de Gestão de Risco:** {alerta_texto}")

        # --- 🤖 SUMÁRIO EXECUTIVO AUTOMÁTICO VIA GEMINI ---
        st.markdown("---")
        st.markdown("### 📝 Sumário Executivo Analítico (Gerado por IA)")
        texto_sumario_pdf = ""
        
        with st.spinner("Cintia analisando padrões na planilha..."):
            try:
                prompt_sumario = (
                    f"Aja como uma consultora sênior de Supply Chain. Analise esses dados agregados:\n"
                    f"- Total de registros: {total_registros}\n"
                    f"- Maior concentração na coluna '{coluna_selecionada}': {top_registro} ({percentual:.1f}%).\n"
                    f"Gere um Sumário Executivo curto e direto (máximo de 2 parágrafos objetivos) focado em eficiência "
                    f"logística para o relatório do Ricardo."
                )
                response_sumario = st.session_state.client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt_sumario
                )
                texto_sumario_pdf = response_sumario.text
                st.info(texto_sumario_pdf)
            except Exception as e:
                texto_sumario_pdf = "Relatório operacional estruturado pronto para tomada de decisão."
                st.info(texto_sumario_pdf)
        
        # --- 📥 NOVO RECURSO: EXPORTAÇÃO COMPLETA DE RELATÓRIO PDF ---
        try:
            # Cria a estrutura do arquivo PDF na memória
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(40, 10, "Relatorio Executivo - Cintia IA", ln=True)
            pdf.set_font("Arial", "", 12)
            pdf.cell(40, 10, f"Arquivo Analisado: {nome_arquivo}", ln=True)
            pdf.cell(40, 10, f"Indicador de Analise: {coluna_selecionada}", ln=True)
            pdf.cell(40, 10, f"Total de Movimentacoes: {total_registros}", ln=True)
            pdf.cell(40, 10, f"Maior Concentracao: {top_registro} ({percentual:.1f}%)", ln=True)
            pdf.cell(40, 10, f"Custo Total Operacional: {total_financeiro_str}", ln=True)
            pdf.ln(10)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(40, 10, "Sumario Analitico da IA:", ln=True)
            pdf.set_font("Arial", "", 11)
            # Remove caracteres especiais para evitar erros de codificação no PDF simples
