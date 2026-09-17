import os
import pypdf
import streamlit as st
from google import genai
from google.genai import types

# Configuração da página da web
st.set_page_config(page_title="Cintia IA", page_icon="🤖", layout="centered")

# Inicializa o cliente básico do Google
if "client" not in st.session_state:
    st.session_state.client = genai.Client(api_key=st.secrets["GOOGLE_API_KEY"])

# Inicializa o Chat dentro do Session State (assim o Streamlit nunca esquece a conexão)
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
    
    # Botão para enviar o documento de Logística/Dados
    arquivo_enviado = st.file_uploader(
        "Adicione sua Base de Conhecimento (PDF)", 
        type=["pdf"],
        help="Insira manuais, relatórios ou planilhas em PDF para a Cintia ler."
    )
    
    contexto_documento = ""
    if arquivo_enviado is not None:
        import pypdf
        try:
            leitor_pdf = pypdf.PdfReader(arquivo_enviado)
            for pagina in leitor_pdf.pages:
                contexto_documento += pagina.extract_text() + "\n"
            st.success("📄 Documento lido com sucesso!")
        except Exception as e:
            st.error("Erro ao ler o arquivo PDF.")

    st.markdown("---")
    st.info("Especialista em:\n- 📊 Engenharia de Dados\n- 📦 Supply Chain & Logística\n- 🧠 Analytics")
    st.success("Status: Online 🟢")


st.markdown("### 💬 Conversa com a Cintia")

# Mostra o histórico na tela
for msg in st.session_state.historico_visual:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Caixa de entrada para o usuário digitar
if pergunta := st.chat_input("Digite sua mensagem para a Cintia..."):
    
    # Mostra a pergunta do Ricardo na hora
    with st.chat_message("user"):
        st.write(pergunta)
    st.session_state.historico_visual.append({"role": "user", "content": pergunta})
    
                    # Envia a mensagem usando o chat guardado na memória do Streamlit
    try:
            # Se tiver um arquivo carregado, junta o texto dele com a pergunta do Ricardo
            if 'contexto_documento' in locals() and contexto_documento:
                pergunta_completa = f"Baseado neste documento:\n{contexto_documento}\n\nPergunta do usuário: {pergunta}"
            else:
                pergunta_completa = pergunta

            response = st.session_state.objeto_chat.send_message(pergunta_completa)
            
            # Mostra a resposta da Cintia
            with st.chat_message("assistant"):
                st.write(response.text)
            st.session_state.historico_visual.append({"role": "assistant", "content": response.text})
            
    except Exception as e:
            st.error(f"Erro de comunicação: {e}")
