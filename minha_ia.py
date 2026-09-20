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
        {"role": "assistant", "content": "Olá! Sou a Cintia. Faça perguntas na barra inferior que eu farei o diagnóstico em tempo real baseado no seu painel!"}
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

contexto_documento = ""
df = None
nome_arquivo = "Nenhum arquivo carregado"

# Variáveis globais para o chat ler com segurança
total_registros = 0
coluna_selecionada = "N/A"
metrica_selecionada = "N/A"

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
    st.info("Especialista em:\n- 📊 Engenharia de Dados\n- 📈 BI Universais\n- 🔮 Modelos Preditivos (ML)")
    st.success("Status: Online 🟢")

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
    
    # Criamos datas reais consecutivas para o nosso modelo de exemplo performar perfeitamente
    datas_simuladas = pd.date_range(start="2026-01-01", periods=100, freq="D")
    
    dados_ficticios = {
        'Data_Envio': datas_simuladas,
        'ShipmentID': [f'SHP-{i:05d}' for i in range(1, 101)],
        'OrderID': [f'ORD-{i:05d}' for i in range(1001, 1101)],
        'SupplierID': ['SUP-05']*35 + ['SUP-04']*25 + ['SUP-01']*15 + ['SUP-02']*15 + ['SUP-03']*10,
        'Transportadora': ['DHL']*40 + ['FedEx']*30 + ['EKart']*15 + ['Delivery']*15,
        'Custo_Frete_R$': [round(random.uniform(500, 4500), 2) for _ in range(100)]
    }
    df = pd.DataFrame(dados_ficticios)
    st.info("💡 Usando dados de exemplo simulados com indicadores financeiros e de tempo reais!")

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
            st.plotly_chart(fig_barras, width="stretch")
            
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
            st.plotly_chart(fig_pizza, width="stretch")

        with aba_previsao:
            st.markdown("### 📈 Projeção Estatística Baseada no Histórico Temporal Real")
            
            # --- 🔮 MOTOR DE INTELIGÊNCIA TEMPORAL (DATAS REAIS) ---
            colunas_data = []
            for col in df.columns:
                if df[col].dtype == 'object':
                    try:
                        # Tenta converter colunas de texto suspeitas para data
                        pd.to_datetime(df[col].head(3), errors='raise')
                        colunas_data.append(col)
                    except:
                        pass
                elif pd.api.types.is_datetime64_any_dtype(df[col]):
                    colunas_data.append(col)
            
            if colunas_data:
                coluna_data_eleita = colunas_data[0]
                df_temp = df.copy()
                df_temp[coluna_data_eleita] = pd.to_datetime(df_temp[coluna_data_eleita])
                
                # Agrupa por mês/ano real encontrado na planilha
                df_temporal = df_temp.groupby(df_temp[coluna_data_eleita].dt.to_period("M"))[valores_eixo_y].mean().reset_index()
                df_temporal[coluna_data_eleita] = df_temporal[coluna_data_eleita].astype(str)
                
                meses_historicos = np.arange(len(df_temporal))
                volumes_reais = df_temporal[valores_eixo_y].to_numpy()
                
                if len(meses_historicos) > 1:
                    coef_angular, coef_linear = np.polyfit(meses_historicos, volumes_reais, 1)
                else:
                    coef_angular, coef_linear = 0.0, volumes_reais[0] if len(volumes_reais) > 0 else 100
                
                meses_futuros = np.array([len(df_temporal), len(df_temporal)+1, len(df_temporal)+2])
                volumes_projetados = coef_angular * meses_futuros + coef_linear
                
                # Cria a linha do tempo estendida com os próximos 3 meses reais
                ultimo_periodo = pd.Period(df_temporal[coluna_data_eleita].iloc[-1], freq='M')
                meses_nomes = list(df_temporal[coluna_data_eleita]) + [str(ultimo_periodo + i) + " (Previsto)" for i in range(1, 4)]
                valores_finais = list(volumes_reais) + list(volumes_projetados)
                tipos = ['Histórico Real']*len(df_temporal) + ['Projeção (ML)']*3
                
                fator_escala = volumes_reais.mean() if len(volumes_reais) > 0 else 100
            else:
                # Fallback de segurança caso a planilha não tenha nenhuma data
                meses_historicos = np.array([1, 2, 3, 4, 5, 6])
                fator_escala = df_agrupado[valores_eixo_y].mean() if not df_agrupado.empty else 100
                volumes_reais = np.array([fator_escala*0.8, fator_escala*0.85, fator_escala*0.9, fator_escala*0.95, fator_escala*1.0, fator_escala*1.05])
                coef_angular, coef_linear = np.polyfit(meses_historicos, volumes_reais, 1)
                meses_futuros = np.array([7, 8, 9])
                volumes_projetados = coef_angular * meses_futuros + coef_linear
                meses_nomes = ['Mês 1', 'Mês 2', 'Mês 3', 'Mês 4', 'Mês 5', 'Mês 6', 'Mês 7 (Previsto)', 'Mês 8 (Previsto)', 'Mês 9 (Previsto)']
                valores_finais = list(volumes_reais) + list(volumes_projetados)
                tipos = ['Histórico Simulando']*6 + ['Projeção (ML)']*3

            df_ml = pd.DataFrame({'Período': meses_nomes, 'Métrica Analisada': valores_finais, 'Status': tipos})
            
            fig_linha = px.line(
                df_ml, x='Período', y='Métrica Analisada', color='Status',
                title="Tendência Estatística Preditiva Automatizada",
                markers=True,
                color_discrete_map={'Histórico Real': '#007BFF', 'Histórico Simulando': '#007BFF', 'Projeção (ML)': '#FF4B4B'},
                template="plotly_white"
            )
            fig_linha.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
            st.plotly_chart(fig_linha, width="stretch")
            
            limite_capacidade = fator_escala * 1.12
            volume_pico_previsto = max(volumes_projetados)
            
            if volume_pico_previsto > limite_capacidade:
                excesso_calculado = volume_pico_previsto - limite_capacidade
                risco_financeiro = excesso_calculado * (fator_escala * 0.15)
                
                st.error(f"⚠️ **ALERTA DE CAPACIDADE DETECTADO:** A curva preditiva indica crescimento acentuado com pico estimado de **{volume_pico_previsto:.1f}** no fechamento do trimestre, ultrapassando os níveis de estabilidade da empresa.")
                st.metric(
                    label="💸 EXPOSIÇÃO FINANCEIRA ESTIMADA AO RISCO", 
                    value=f"R$ {risco_financeiro:,.2f}", 
                    delta="Variação Crítica de Custo", 
                    delta_color="inverse"
                )
            else:
                st.success(f"✅ **Indicadores sob Controle:** A posição matemática aponta estabilidade dentro das metas corporativas para os próximos 90 dias.")
        
        # --- 👑 DIAGNÓSTICO CORPORATIVO ---
        st.markdown(f"### 💡 Diagnóstico Corporativo sobre {coluna_selecionada}:")
        
        top_registro = df[coluna_selecionada].value_counts().idxmax()
        Qtd_top_registro = df[coluna_selecionada].value_counts().max()
        percentual = (Qtd_top_registro / total_registros) * 100
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label=f"Maior Frequência ({coluna_selecionada})", value=str(top_registro))
        with col2:
            st.metric(label="Total de Linhas Processadas", value=f"{total_registros}")
            
        alerta_texto = f"O indicador '{top_registro}' concentra {percentual:.1f}% de todas as ocorrências na coluna {coluna_selecionada}."
        st.warning(f"⚠️ **Gestão de Concentração:** {alerta_texto}")

        # --- 🤖 SUMÁRIO EXECUTIVO COMPLETO VIA GEMINI ---
        st.markdown("---")
        st.markdown("### 📝 Sumário Analítico Gerencial (Gerado por IA)")
        texto_sumario_pdf = "Relatório analítico estruturado pronto para tomada de decisão."
        
        try:
            prompt_sumario = (
                f"Aja como uma consultora sênior de inteligência de negócios. Analise esses indicadores agregados da planilha '{nome_arquivo}':\n"
                f"- Linhas totais: {total_registros}\n"
                f"- Coluna de foco selecionada: {coluna_selecionada} (Maior volume: {top_registro} com {percentual:.1f}% de presença).\n"
                f"- Métrica numérica avaliada: {metrica_selecionada}.\n"
                f"Escreva um Sumário Executivo muito curto, direto e corporativo (máximo de 2 parágrafos) analisando o cenário e propondo mitigações de risco."
            )
            response_sumario = st.session_state.client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt_sumario
            )
            texto_sumario_pdf = response_sumario.text
            st.info(texto_sumario_pdf)
        except Exception as e:
            st.info(texto_sumario_pdf)
        
        # --- 📥 EXPORTAÇÃO EM PDF ---
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(40, 10, "Relatorio Analitico Universal - Cintia IA", ln=True)
            pdf.set_font("Arial", "", 12)
            pdf.cell(40, 10, f"Origem dos Dados: {nome_arquivo}", ln=True)
            pdf.cell(40, 10, f"Dimensao Analisada: {coluna_selecionada}", ln=True)
            pdf.cell(40, 10, f"Metrica Avaliada: {metrica_selecionada}", ln=True)
            pdf.cell(40, 10, f"Volume de Registros: {total_registros}", ln=True)
            pdf.ln(10)
            pdf.set_font("Arial", "B", 14)
            pdf.cell(40, 10, "Parecer Gerencial da Inteligencia Artificial:", ln=True)
            pdf.set_font("Arial", "", 11)
            
            texto_limpo = texto_sumario_pdf.replace("•", "-").encode('latin-1', 'ignore').decode('latin-1')
            pdf.multi_cell(0, 10, texto_limpo)
            
            pdf_bytes = bytes(pdf.output())
            st.download_button(
                label="📥 Baixar Parecer Executivo em PDF",
                data=pdf_bytes,
                file_name=f"Relatorio_Universal_Cintia_IA.pdf",
                mime="application/pdf"
            )
        except Exception as pdf_err:
            st.error(f"Erro ao gerar o relatório PDF: {pdf_err}")

# ==============================================================================
# --- 💬 🤖 NOVO MÓDULO: CHAT INTEGRADO PROFISSIONAL NA ÁREA PRINCIPAL ---
# ==============================================================================
st.markdown("---")
st.markdown("### 💬 Converse com a Cintia IA sobre este Painel")

# Renderiza as mensagens anteriores direto no corpo da página
for msg in st.session_state.historico_visual:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Campo flutuante moderno de input no rodapé da página principal
if pergunta_texto := st.chat_input("Digite sua pergunta sobre o relatório aqui..."):
    st.session_state.historico_visual.append({"role": "user", "content": pergunta_texto})
    
    with st.chat_message("user"):
        st.markdown(pergunta_texto)
        
    resumo_dados_ia = f"Contexto do Arquivo:\n- Nome: {nome_arquivo}\n- Linhas Totais: {total_registros}\n- Coluna Foco: {coluna_selecionada}\n- Métrica: {metrica_selecionada}"
    prompt_completo_ia = f"{resumo_dados_ia}\n\nPergunta do Ricardo: {pergunta_texto}"

    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        try:
            response_chat = st.session_state.objeto_chat.send_message(prompt_completo_ia)
            resposta_texto = response_chat.text
            message_placeholder.markdown(resposta_texto)
            st.session_state.historico_visual.append({"role": "assistant", "content": resposta_texto})
        except Exception as chat_err:
            resposta_erro = f"⚠️ Erro de comunicação com o Google Gemini: {chat_err}"
            message_placeholder.markdown(resposta_erro)
            st.session_state.historico_visual.append({"role": "assistant", "content": resposta_erro})
            
    st.rerun()
