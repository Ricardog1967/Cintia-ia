import os
import streamlit as st
from google import genai
from google.genai import types

# Configuração da página da web
st.set_page_config(page_title="Cintia IA", page_icon="🤖", layout="centered")

# Sua chave de API do Google AI Studio
os.environ["GEMINI_API_KEY"] = "AQ.Ab8RN6JXpkPOv4Ym2emCICb-snhPwN5MO4u91Jo-of1lZjkBFw"

# Inicializa o cliente básico do Google
if "client" not in st.session_state:
    st.session_state.client = genai.Client()

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
        response = st.session_state.objeto_chat.send_message(pergunta)
        
        # Mostra a resposta da Cintia
        with st.chat_message("assistant"):
            st.write(response.text)
        st.session_state.historico_visual.append({"role": "assistant", "content": response.text})
        
    except Exception as e:
        st.error(f"Erro de comunicação: {e}")
