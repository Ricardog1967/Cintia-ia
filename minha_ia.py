import os
import pypdf
import streamlit as st
from google import genai
from google.genai import types
import pandas as pd
import plotly.express as px
from fpdf import FPDF
from fpdf.enums import XPos, YPos
import numpy as np
import time

# Configuração da página da web - Modo Claro Moderno
st.set_page_config(page_title="Cintia IA - Universal Data Analytics", page_icon="🤖", layout="centered")

# --- 🎨 TRUQUE VISUAL: Esconde os menus e customiza o tamanho da letra do Chat Input ---
hide_menu_style = """
        <style>
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        .stDeployButton {display:none;}
        
        /* Altera o tamanho da letra ao digitar e do texto informativo (placeholder) */
        .stChatInput textarea, 
        .stChatInput textarea::placeholder,
        .stChatInput p {
            font-size: 24px !important;
            font-weight: bold !important;
        }
        
        /* Ajusta a altura da caixa para acomodar a letra maior */
        .stChatInput div {
            min-height: 55px !important;
        }
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
    instrucao_sistema = "Seu nome é Cintia. Você é uma IA assistente focada em engenharia de dados, análise de negócios, BI e análise de currículos, pronta para ajudar o Ricardo."
    st.session_state.objeto_chat = st.session_state.client.chats.create(
        model="gemini-3.6-flash",
        config=types.GenerateContentConfig(
            system_instruction=instrucao_sistema,
            temperature=0.7
        )
    )

if "historico_visual" not in st.session_state:
    st.session_state.historico_visual = [
        {"role": "assistant", "content": "Olá! Sou a Cintia. Faça perguntas na barra inferior que eu farei o diagnóstico em tempo real baseado no seu painel ou documentos!"}
    ]

st.title("🤖 Cintia IA - Universal Data Analytics")
st.markdown(
    """
    **Desenvolvido por Ricardo G.** | [🔗 Acesse meu LinkedIn](https://linkedin.com) 
    
    Este aplicativo é uma plataforma de **Business Intelligence, Data Science e Document Analytics** agnóstica a dados.
    """
)
st.markdown("---")
def processar_previsao_ml(df, valores_eixo_y, df_agrupado):
    colunas_data = []
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                pd.to_datetime(df[col].head(3), errors='raise')
                colunas_data.append(col)
            except:
                pass
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            colunas_data.append(col)
    
    # Tratamento cronológico dinâmico utilizando a primeira coluna de data como string
    if colunas_data:
        coluna_data_eleita = colunas_data[0]
        df_temp = df.copy()
        df_temp[coluna_data_eleita] = pd.to_datetime(df_temp[coluna_data_eleita], errors='coerce')
        df_temp = df_temp.dropna(subset=[coluna_data_eleita])
        
        df_temporal = df_temp.groupby(df_temp[coluna_data_eleita].dt.to_period("M"))[valores_eixo_y].mean().reset_index()
        df_temporal[coluna_data_eleita] = df_temporal[coluna_data_eleita].astype(str)
        
        meses_historicos = np.arange(len(df_temporal))
        volumes_reais = df_temporal[valores_eixo_y].to_numpy()
        
        if len(meses_historicos) > 1:
            coef_angular, coef_linear = np.polyfit(meses_historicos, volumes_reais, 1)
        else:
            coef_angular, coef_linear = 0.0, volumes_reais if len(volumes_reais) > 0 else 100
        
        meses_futuros = np.array([len(df_temporal), len(df_temporal)+1, len(df_temporal)+2])
        volumes_projetados = coef_angular * meses_futuros + coef_linear
        
        ultimo_periodo = pd.Period(df_temporal[coluna_data_eleita].iloc[-1], freq='M')
        meses_nomes = list(df_temporal[coluna_data_eleita]) + [str(ultimo_periodo + i) + " (Previsto)" for i in range(1, 4)]
        valores_finais = list(volumes_reais) + list(volumes_projetados)
        tipos = ['Histórico Real']*len(df_temporal) + ['Projeção (ML)']*3
        fator_escala = volumes_reais.mean() if len(volumes_reais) > 0 else 100
    else:
        fator_escala = df_agrupado[valores_eixo_y].mean() if not df_agrupado.empty else 100
        volumes_reais = np.array([fator_escala*0.8, factor_escala*0.85, factor_escala*0.9, factor_escala*0.95, factor_escala*1.0, factor_escala*1.05])
        meses_historicos = np.arange(6)
        coef_angular, coef_linear = np.polyfit(meses_historicos, volumes_reais, 1)
        meses_futuros = np.array([])
        volumes_projetados = coef_angular * meses_futuros + coef_linear
        meses_nomes = ['Mês 1', 'Mês 2', 'Mês 3', 'Mês 4', 'Mês 5', 'Mês 6', 'Mês 7 (Previsto)', 'Mês 8 (Previsto)', 'Mês 9 (Previsto)']
        valores_finais = list(volumes_reais) + list(volumes_projetados)
        tipos = ['Histórico Simulando']*6 + ['Projeção (ML)']*3

    return meses_nomes, valores_finais, tipos, volumes_projetados, fator_escala
contexto_documento = ""
df = None
nome_arquivo = "Nenhum arquivo carregado"
total_registros = 0
coluna_selecionada = "N/A"
metrica_selecionada = "N/A"

# Inicializa chaves de controle de estado persistentes na sessão para livre chaveamento
if 'fonte_dados' not in st.session_state:
    st.session_state['fonte_dados'] = None
if 'dados_planilha_ativos' not in st.session_state:
    st.session_state['dados_planilha_ativos'] = None
if 'nome_arquivo_ativo' not in st.session_state:
    st.session_state['nome_arquivo_ativo'] = "Nenhum arquivo carregado"

with st.sidebar:
    st.subheader("📁 Upload de Documentos")
    arquivo_enviado = st.file_uploader("Suba seu arquivo de dados (PDF, CSV ou Excel)", type=["pdf", "csv", "xlsx"])
    st.markdown("---")
    st.subheader("💡 Teste Rápido")
    usar_exemplo = st.button("Carregar Planilha de Exemplo")
    st.markdown("---")
    st.info("Especialista em:\n- 📊 Engenharia de Dados\n- 📈 BI Universais\n- 🔮 Modelos Preditivos (ML)\n- 📄 Análise Doc/Currículos")
    st.success("Status: Online 🟢")

# --- LOGICA DE ALTERNÂNCIA EM SESSÃO ---
if usar_exemplo:
    st.session_state['fonte_dados'] = 'exemplo'
    nome_arquivo = "Planilha_Exemplo_Supply_Chain.xlsx"
    import random
    random.seed(42)
    datas_simuladas = pd.date_range(start="2026-01-01", periods=100, freq="D")
    dados_ficticios = {
        'Data_Envio': datas_simuladas,
        'ShipmentID': [f'SHP-{i:05d}' for i in range(1, 101)],
        'OrderID': [f'ORD-{i:05d}' for i in range(1001, 1101)],
        'SupplierID': ['SUP-05']*35 + ['SUP-04']*25 + ['SUP-01']*15 + ['SUP-02']*15 + ['SUP-03']*10,
        'Transportadora': ['DHL']*40 + ['FedEx']*30 + ['EKart']*15 + ['Delivery']*15,
        'Custo_Frete_R$': [round(random.uniform(500, 4500), 2) for _ in range(100)]
    }
    st.session_state['dados_planilha_ativos'] = pd.DataFrame(dados_ficticios)
    st.session_state['nome_arquivo_ativo'] = nome_arquivo
    st.info("💡 Usando dados de exemplo simulados com indicadores financeiros!")

elif arquivo_enviado is not None and st.session_state['fonte_dados'] != 'exemplo':
    nome_arquivo = arquivo_enviado.name
    if nome_arquivo.endswith('.pdf'):
        try:
            leitor_pdf = pypdf.PdfReader(arquivo_enviado)
            contexto_documento = "".join([pagina.extract_text() or "" for pagina in leitor_pdf.pages])
            if contexto_documento.strip():
                st.success(f"📄 Texto do PDF '{nome_arquivo}' extraído com sucesso!")
            else:
                st.error("⚠️ Não foi possível extrair texto deste PDF.")
        except Exception as e:
            st.error(f"Erro ao ler o arquivo PDF: {e}")
    else:
        try:
            df_real = pd.read_csv(arquivo_enviado) if nome_arquivo.endswith('.csv') else pd.read_excel(arquivo_enviado)
            st.session_state['dados_planilha_ativos'] = df_real
            st.session_state['nome_arquivo_ativo'] = nome_arquivo
            st.session_state['fonte_dados'] = 'uploader'
        except Exception as e:
            st.error(f"Erro ao ler a planilha: {e}")

elif arquivo_enviado is None and st.session_state['fonte_dados'] == 'uploader':
    st.session_state['fonte_dados'] = None
    st.session_state['dados_planilha_ativos'] = None
    st.session_state['nome_arquivo_ativo'] = "Nenhum arquivo carregado"

# Dispositivo de segurança: se houver arquivo real e mudar de filtro, força a saída do modo exemplo
if arquivo_enviado is not None and st.session_state['fonte_dados'] == 'exemplo' and not usar_exemplo:
    st.session_state['fonte_dados'] = 'uploader'
    st.rerun()

df = st.session_state['dados_planilha_ativos']
nome_arquivo = st.session_state['nome_arquivo_ativo']
if df is not None:
    st.success(f"📊 Dados de '{nome_arquivo}' carregados com sucesso!")
    st.dataframe(df.head(5))
    total_registros = len(df)
    
    colunas_texto = df.select_dtypes(include=['object', 'string']).columns.tolist()
    colunas_numericas = df.select_dtypes(include=['number']).columns.tolist()

    if colunas_texto:
        col1_sel, col2_sel = st.columns(2)
        with col1_sel:
            coluna_selecionada = st.selectbox("🔍 Agrupar dados pela coluna de texto:", options=colunas_texto, index=0)
        with col2_sel:
            if colunas_numericas:
                metrica_selecionada = st.selectbox("🧮 Analisar valor da coluna métrica:", options=colunas_numericas, index=0)
                modo_calculo = "Soma"
            else:
                metrica_selecionada = "Contagem_Registros"
                modo_calculo = "Contagem"

        if modo_calculo == "Soma":
            df_agrupado = df.groupby(coluna_selecionada)[metrica_selecionada].sum().reset_index()
            valores_eixo_y = metrica_selecionada
        else:
            df_agrupado = df[coluna_selecionada].value_counts().reset_index()
            df_agrupado.columns = [coluna_selecionada, 'Quantidade']
            valores_eixo_y = 'Quantidade'

        aba_barras, aba_pizza, aba_previsao = st.tabs(["📊 Gráfico de Volumetria", "🍕 Distribuição Percentual", "🔮 Previsão de Tendências (ML)"])
        
        with aba_barras:
            st.plotly_chart(px.bar(df_agrupado, x=coluna_selecionada, y=valores_eixo_y, title=f"Total acumulado por {coluna_selecionada}", color_discrete_sequence=["#007BFF"], template="plotly_white"), use_container_width=True)
            
        with aba_pizza:
            st.plotly_chart(px.pie(df_agrupado, values=valores_eixo_y, names=coluna_selecionada, title=f"Distribuição Percentual por {coluna_selecionada}", template="plotly_white"), use_container_width=True)

        with aba_previsao:
            st.markdown("### 📈 Projeção Estatística Baseada no Histórico Temporal Real")
            
            # Executa a chamada do bloco lógico matemático corrigido (Bloco 2)
            meses_nomes, valores_finais, tipos, volumes_projetados, fator_escala = processar_previsao_ml(df, valores_eixo_y, df_agrupado)

            df_ml = pd.DataFrame({'Período': meses_nomes, 'Métrica Analisada': valores_finais, 'Status': tipos})
            st.plotly_chart(px.line(df_ml, x='Período', y='Métrica Analisada', color='Status', title="Tendência Estatística Preditiva Automatizada", markers=True, color_discrete_map={'Histórico Real': '#007BFF', 'Histórico Simulando': '#007BFF', 'Projeção (ML)': '#FF4B4B'}, template="plotly_white"), use_container_width=True)
            
            volume_pico_previsto = max(volumes_projetados) if len(volumes_projetados) > 0 else 0
            limite_capacidade = fator_escala * 1.12
            if volume_pico_previsto > limite_capacidade:
                risco_financeiro = (volume_pico_previsto - limite_capacidade) * (fator_escala * 0.15)
                st.error(f"⚠️ **ALERTA DE CAPACIDADE DETECTADO:** Pico estimado ultrapassa os níveis estáveis.")
                st.metric(label="💸 EXPOSIÇÃO FINANCEIRA ESTIMADA AO RISCO", value=f"R$ {risco_financeiro:,.2f}", delta="Variação Crítica de Custo", delta_color="inverse")
            else:
                st.success("✅ **Indicadores sob Controle:** Estabilidade projetada para os próximos 90 dias.")

        st.markdown(f"### 💡 Diagnóstico Corporativo sobre {coluna_selecionada}:")
        top_registro = df[coluna_selecionada].value_counts().idxmax()
        percentual = (df[coluna_selecionada].value_counts().max() / total_registros) * 100
        
        col1, col2 = st.columns(2)
        with col1: st.metric(label=f"Maior Frequência ({coluna_selecionada})", value=str(top_registro))
        with col2: st.metric(label="Total de Linhas Processadas", value=f"{total_registros}")
        
        alerta_texto = f"O indicador '{top_registro}' concentra {percentual:.1f}% de todas as ocorrências na coluna {coluna_selecionada}."
        st.warning(f"⚠️ **Gestão de Concentração:** {alerta_texto}")

        # --- GERAÇÃO DO PARECER EM PDF ---
        st.markdown("---")
        st.markdown("### 📝 Sumário Analítico Gerencial (Gerado por IA)")
        texto_sumario_pdf = "Relatório analítico estruturado pronto para tomada de decisão."
        
        try:
            prompt_sumario = (
                f"Aja como uma consultora sênior de inteligência de negócios. Analise esses indicadores agregados da planilha '{nome_arquivo}':\n"
                f"- Linhas totais: {total_registros}\n"
                f"- Coluna de foco selecionada: {coluna_selecionada}.\n"
                f"- Alerta chave: {alerta_texto}\n"
                f"- Métrica numérica avaliada: {metrica_selecionada}.\n"
                f"Escreva um Sumário Executivo muito curto, direto e corporativo (máximo de 2 parágrafos)."
            )
            response_sumario = st.session_state.client.models.generate_content(model="gemini-3.6-flash", contents=prompt_sumario)
            if response_sumario and response_sumario.text:
                texto_sumario_pdf = response_sumario.text
            st.info(texto_sumario_pdf)
        except:
            st.info(texto_sumario_pdf)
        
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(40, 10, "Relatorio Analitico Universal - Cintia IA", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 12)
            pdf.cell(40, 10, f"Origem dos Dados: {nome_arquivo} | Volume: {total_registros}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.ln(10)
            pdf.set_font("Helvetica", "B", 14)
            pdf.cell(40, 10, "Parecer Gerencial da Inteligencia Artificial:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("Helvetica", "", 11)
            
            map_carac = {"•": "-", "–": "-", "—": "-", "“": '"', "”": '"', "‘": "'", "’": "'", "…": "..."}
            texto_tratado = texto_sumario_pdf
            for orig, dest in map_carac.items():
                texto_tratado = texto_tratado.replace(orig, dest)
                
            texto_limpo = texto_tratado.encode('latin-1', 'ignore').decode('latin-1')
            pdf.multi_cell(0, 10, texto_limpo)
            
            pdf_bytes = bytes(pdf.output())
            st.download_button(label="📥 Baixar Parecer Executivo em PDF", data=pdf_bytes, file_name="Relatorio_Universal_Cintia_IA.pdf", mime="application/pdf")
        except Exception as pdf_err:
            st.error(f"Erro ao gerar o relatório PDF: {pdf_err}")

# --- INTERFACE DO CHAT INTEGRADO ---
st.markdown("---")
st.markdown("### 💬 Converse com a Cintia IA sobre este Painel")

for msg in st.session_state.historico_visual:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if pergunta_texto := st.chat_input("Digite sua pergunta sobre o relatório aqui..."):
    st.session_state.historico_visual.append({"role": "user", "content": pergunta_texto})
    
    with st.chat_message("user"):
        st.markdown(pergunta_texto)
        
    resumo_dados_ia = f"[Contexto - Arquivo: {nome_arquivo} | Registros: {total_registros} | Foco: {coluna_selecionada}]"
    prompt_completo_ia = f"{resumo_dados_ia}\n[CONTEÚDO DO PDF]:\n{contexto_documento}\n\nUsuário perguntou: {pergunta_texto}" if contexto_documento else f"{resumo_dados_ia}\n\nUsuário perguntou: {pergunta_texto}"

    with st.chat_message("assistant"):
        resposta_texto = ""
        with st.spinner("Cintia IA analisando e respondendo..."):
            try:
                response_chat = st.session_state.objeto_chat.send_message(prompt_completo_ia)
                if response_chat and response_chat.text:
                    resposta_texto = response_chat.text
            except:
                resposta_texto = "⚠️ Servidor instável. Por favor, tente enviar a mensagem novamente."
                        
        st.markdown(resposta_texto)
        st.session_state.historico_visual.append({"role": "assistant", "content": resposta_texto})
        st.rerun()
