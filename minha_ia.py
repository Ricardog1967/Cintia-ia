import os
import pypdf
import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import plotly.express as px

# Configuração da página da web
st.set_page_config(page_title="Cintia IA", page_icon="🤖", layout="centered")

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
        {"role": "assistant", "content": "Olá, Ricardo! Sou a Cintia. Como posso te ajudar com engenharia de dados e logística hoje?"}
    ]

# Interface Visual - Barra Lateral
with st.sidebar:
    st.title("🤖 Cintia IA")
    st.subheader("Sua Assistente de Dados")
    st.markdown("---")
    
    arquivo_enviado = st.file_uploader(
        "Adicione sua Base de Conhecimento (PDF, CSV ou Excel)",
        type=["pdf", "csv", "xlsx"],
        help="Insira manuais em PDF ou planilhas de dados para a Cintia ler."
    )
    
    st.markdown("---")
    st.info("Especialista em:\n- 📊 Engenharia de Dados\n- 📦 Supply Chain & Logística\n- 🧠 Analytics")
    st.success("Status: Online 🟢")

contexto_documento = ""

if arquivo_enviado is not None:
    nome_arquivo = arquivo_enviado.name
    
    # 📊 CASO 1: SE FOR PLANILHA (Excel ou CSV)
    if nome_arquivo.endswith('.csv') or nome_arquivo.endswith('.xlsx'):
        try:
            if nome_arquivo.endswith('.csv'):
                df = pd.read_csv(arquivo_enviado)
            else:
                df = pd.read_excel(arquivo_enviado)
                
            st.success(f"📊 Planilha '{nome_arquivo}' lida com sucesso!")
            st.write("📋 **Visualização rápida dos dados (Primeiras 5 linhas):**")
            st.dataframe(df.head(5))
            
            st.session_state['dados_planilha'] = df
            
            st.write("📊 **Análise Visual Avançada:**")
            colunas_texto = df.select_dtypes(include=['object']).columns.tolist()
        
            if colunas_texto:
                # 🎛️ FILTRO DINÂMICO: Cria uma caixa de seleção para escolher o que ver no gráfico
                coluna_selecionada = st.selectbox(
                    "🔍 Escolha o indicador para analisar no gráfico:",
                    options=colunas_texto,
                    index=colunas_texto.index('SupplierID') if 'SupplierID' in colunas_texto else 0
                )
                
                # O gráfico agora muda de acordo com o que você selecionar na caixa!
                fig = px.histogram(
                    df, 
                    x=coluna_selecionada, 
                    title=f"Total de Envios por {coluna_selecionada}",
                    color_discrete_sequence=["#007BFF"],
                    template="plotly_white"
                )
                
                fig.update_layout(
                    margin=dict(l=20, r=20, t=40, b=20),
                    height=350
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # --- 🧠 INSIGHTS AUTOMÁTICOS BASEADOS NO FILTRO ---
                st.markdown(f"### 💡 Diagnóstico da Cintia sobre {coluna_selecionada}:")
                
                top_registro = df[coluna_selecionada].value_counts().idxmax()
                Qtd_top_registro = df[coluna_selecionada].value_counts().max()
                total_registros = len(df)
                percentual = (Qtd_top_registro / total_registros) * 100
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric(label=f"Maior Volume ({coluna_selecionada})", value=str(top_registro))
                with col2:
                    st.metric(label="Total de Movimentações", value=f"{total_registros} envios")
                
                st.warning(
                    f"⚠️ **Aviso de Gestão de Risco:** O indicador **{top_registro}** concentra "
                    f"**{percentual:.1f}%** de toda a sua operação analisada nesta coluna (com {Qtd_top_registro} envios). "
                    f"Monitore de perto essa concentração para garantir a eficiência do fluxo de Supply Chain."
                )
                # --------------------------------------------------------
            
            contexto_documento = f"O usuário enviou uma planilha chamada {nome_arquivo}.\n"
            contexto_documento += f"Colunas presentes: {', '.join(df.columns)}\n"
            contexto_documento += f"Amostra dos dados:\n{df.head(3).to_string()}"
            
        except Exception as e:
            st.error(f"Erro ao ler o arquivo de planilha: {e}")

    # 📄 CASO 2: SE FOR PDF
    elif nome_arquivo.endswith('.pdf'):
        try:
            leitor_pdf = pypdf.PdfReader(arquivo_enviado)
            for pagina in leitor_pdf.pages:
                contexto_documento += pagina.extract_text() + "\n"
            st.success("📄 Documento lido com sucesso!")
        except Exception as e:
            st.error("Erro ao ler o arquivo PDF.")

st.markdown("### 💬 Conversa com a Cintia")

for msg in st.session_state.historico_visual:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

if pergunta := st.chat_input("Digite sua mensagem para a Cintia..."):
    with st.chat_message("user"):
        st.write(pergunta)
    st.session_state.historico_visual.append({"role": "user", "content": pergunta})
    
    try:
        if 'contexto_documento' in locals() and contexto_documento:
            pergunta_completa = f"Baseado neste documento:\n{contexto_documento}\n\nPergunta do usuário: {pergunta}"
        else:
            pergunta_completa = pergunta

        response = st.session_state.objeto_chat.send_message(pergunta_completa)
        
        with st.chat_message("assistant"):
            st.write(response.text)
        st.session_state.historico_visual.append({"role": "assistant", "content": response.text})
            
    except Exception as e:
        st.error(f"Erro de comunicação: {e}")

