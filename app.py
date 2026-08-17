import json
import os
import sqlite3
from datetime import datetime

import pandas as pd
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

st.set_page_config(
    page_title="Gestão de Frota - RS Isolamentos Térmicos",
    layout="wide",
    page_icon="🚚",
)

# Diretórios para anexos e logos
for folder in ["uploads", "config"]:
    if not os.path.exists(folder):
        os.makedirs(folder)

LOGO_PATH = os.path.join("config", "logo_empresa.png")

# CORES OFICIAIS DA RS ISOLAMENTOS TÉRMICOS
COR_AZUL_RS = colors.HexColor("#002B66")
COR_LARANJA_RS = colors.HexColor("#E86C15")
COR_CINZA_TEXTO = colors.HexColor("#2D3748")


# --- BANCO DE DADOS ---
def conectar_bd():
    conn = sqlite3.connect("frota_local.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS veiculos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    placa TEXT UNIQUE,
                    renavam TEXT,
                    chassi TEXT,
                    modelo TEXT,
                    marca TEXT,
                    ano_modelo TEXT,
                    responsavel TEXT,
                    valor_veiculo REAL,
                    odometro_atual REAL,
                    status TEXT,
                    fotos_json TEXT
                )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS viagens (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veiculo_id INTEGER,
                    data TEXT,
                    condutor TEXT,
                    km_inicial REAL,
                    km_final REAL,
                    km_rodado REAL,
                    combustivel_litros REAL,
                    FOREIGN KEY(veiculo_id) REFERENCES veiculos(id)
                )"""
    )
    c.execute(
        """CREATE TABLE IF NOT EXISTS manutenções (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    veiculo_id INTEGER,
                    tipo TEXT,
                    descricao TEXT,
                    data TEXT,
                    km_realizada REAL,
                    km_proxima REAL,
                    custo REAL,
                    FOREIGN KEY(veiculo_id) REFERENCES veiculos(id)
                )"""
    )
    conn.commit()
    return conn


conn = conectar_bd()

# Migração defensiva do BD
try:
    c = conn.cursor()
    c.execute("ALTER TABLE veiculos ADD COLUMN renavam TEXT")
    c.execute("ALTER TABLE veiculos ADD COLUMN chassi TEXT")
    c.execute("ALTER TABLE veiculos ADD COLUMN ano_modelo TEXT")
    c.execute("ALTER TABLE veiculos ADD COLUMN responsavel TEXT")
    c.execute("ALTER TABLE veiculos ADD COLUMN valor_veiculo REAL")
    c.execute("ALTER TABLE veiculos ADD COLUMN fotos_json TEXT")
    conn.commit()
except Exception:
    pass


# Helper Functions
def formata_valor(val):
    if pd.isna(val) or val is None:
        return 0.0
    try:
        return float(val)
    except Exception:
        return 0.0


def formata_texto(txt):
    if (
        pd.isna(txt)
        or txt is None
        or str(txt).strip() == ""
        or str(txt).lower() == "none"
    ):
        return "-"
    return str(txt)


# --- ESTILOS DE PDF CUSTOMIZADOS PARA RS ISOLAMENTOS ---
def get_pdf_styles():
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "DocTitle",
        parent=styles["Title"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=COR_AZUL_RS,
        alignment=0,
    )

    subtitle_style = ParagraphStyle(
        "DocSubTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=11,
        leading=15,
        textColor=COR_LARANJA_RS,
    )

    header_table_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=11,
        textColor=colors.white,
        alignment=1,
    )

    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=COR_CINZA_TEXTO,
    )

    cell_center = ParagraphStyle(
        "TableCellCenter", parent=cell_style, alignment=1
    )

    cell_bold = ParagraphStyle(
        "TableCellBold", parent=cell_style, fontName="Helvetica-Bold"
    )

    return (
        styles,
        title_style,
        subtitle_style,
        header_table_style,
        cell_style,
        cell_center,
        cell_bold,
    )


def montar_cabecalho_pdf(titulo, subtitulo):
    styles, title_style, subtitle_style, _, _, _, _ = get_pdf_styles()

    header_data = []
    text_elements = [
        Paragraph(titulo, title_style),
        Spacer(1, 3),
        Paragraph(subtitulo, subtitle_style),
        Paragraph(
            "RS ISOLAMENTOS TÉRMICOS • Padrão de Qualidade e Equipe"
            " Especializada",
            ParagraphStyle(
                "SubSub",
                parent=styles["Normal"],
                fontSize=7.5,
                textColor=colors.HexColor("#718096"),
                fontName="Helvetica-Oblique",
            ),
        ),
        Paragraph(
            f"Emitido em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}",
            ParagraphStyle(
                "SubDate",
                parent=styles["Normal"],
                fontSize=7.5,
                textColor=colors.HexColor("#718096"),
            ),
        ),
    ]

    if os.path.exists(LOGO_PATH):
        try:
            img = Image(LOGO_PATH, width=1.8 * inch, height=0.7 * inch)
            img.hAlign = "RIGHT"
            header_data = [[text_elements, img]]
            t_head = Table(header_data, colWidths=[5.0 * inch, 2.0 * inch])
            t_head.setStyle(
                TableStyle([
                    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                    ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ])
            )
            return t_head
        except Exception:
            pass

    header_data = [[text_elements]]
    t_head = Table(header_data, colWidths=[7.0 * inch])
    return t_head

from reportlab.platypus import PageBreak  # Certifique-se de importar o PageBreak no topo do arquivo


def gerar_pdf_veiculo(v_info, df_viagens, df_manut):
    nome_pdf = f"Ficha_{v_info['placa']}.pdf"
    doc = SimpleDocTemplate(
        nome_pdf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    elements = []
    (
        styles,
        _,
        _,
        header_table_style,
        cell_style,
        cell_center,
        cell_bold,
    ) = get_pdf_styles()

    # --- PÁGINA 1: DADOS TÉCNICOS, VIAGENS E MANUTENÇÕES ---
    elements.append(
        montar_cabecalho_pdf(
            f"Ficha Técnica de Viatura - {v_info['placa']}",
            f"{v_info['marca']} {v_info['modelo']} | Status:"
            f" {v_info['status']}",
        )
    )
    elements.append(Spacer(1, 8))
    elements.append(
        HRFlowable(
            width="100%", thickness=2, color=COR_AZUL_RS, spaceAfter=12
        )
    )

    # Bloco de Informações Básicas
    val_veic = formata_valor(v_info.get("valor_veiculo"))
    info_box_data = [
        [
            Paragraph(f"<b>PLACA / PREFIXO:</b> {v_info['placa']}", cell_style),
            Paragraph(
                f"<b>RENAVAN:</b> {formata_texto(v_info.get('renavam'))}",
                cell_style,
            ),
        ],
        [
            Paragraph(
                f"<b>CHASSI:</b> {formata_texto(v_info.get('chassi'))}",
                cell_style,
            ),
            Paragraph(
                "<b>ANO / MODELO:</b>"
                f" {formata_texto(v_info.get('ano_modelo'))}",
                cell_style,
            ),
        ],
        [
            Paragraph(
                "<b>RESPONSÁVEL:</b>"
                f" {formata_texto(v_info.get('responsavel'))}",
                cell_style,
            ),
            Paragraph(
                f"<b>VALOR MATERIAL CARGA:</b> R$ {val_veic:,.2f}", cell_bold
            ),
        ],
        [
            Paragraph(
                f"<b>ODÔMETRO ATUAL:</b> {v_info['odometro_atual']:,.1f} KM",
                cell_style,
            ),
            Paragraph(f"<b>STATUS ATUAL:</b> {v_info['status']}", cell_bold),
        ],
    ]

    t_info = Table(info_box_data, colWidths=[3.5 * inch, 3.5 * inch])
    t_info.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#FFFAF0")),
            ("BOX", (0, 0), (-1, -1), 1, COR_LARANJA_RS),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#FEEBC8")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
            ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    elements.append(t_info)
    elements.append(Spacer(1, 12))

    # Seção Viagens
    elements.append(
        Paragraph(
            "🛣️ Histórico Recente de Viagens",
            ParagraphStyle(
                "SectionHeading",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=COR_AZUL_RS,
            ),
        )
    )
    elements.append(Spacer(1, 4))

    if df_viagens.empty:
        elements.append(
            Paragraph("<i>Nenhuma viagem registrada.</i>", cell_style)
        )
    else:
        v_headers = [
            Paragraph("Data", header_table_style),
            Paragraph("Condutor", header_table_style),
            Paragraph("KM Inicial", header_table_style),
            Paragraph("KM Final", header_table_style),
            Paragraph("Percorrido", header_table_style),
            Paragraph("Combustível", header_table_style),
        ]
        v_rows = [v_headers]
        for _, r in df_viagens.head(8).iterrows():
            v_rows.append([
                Paragraph(str(r["data"]), cell_center),
                Paragraph(formata_texto(r["condutor"]), cell_style),
                Paragraph(
                    f"{formata_valor(r['km_inicial']):,.1f}", cell_center
                ),
                Paragraph(
                    f"{formata_valor(r['km_final']):,.1f}", cell_center
                ),
                Paragraph(
                    f"{formata_valor(r['km_rodado']):,.1f} KM", cell_center
                ),
                Paragraph(
                    f"{formata_valor(r['combustivel_litros']):,.1f} L",
                    cell_center,
                ),
            ])

        t_v = Table(
            v_rows,
            colWidths=[
                0.9 * inch,
                2.0 * inch,
                1.0 * inch,
                1.0 * inch,
                1.1 * inch,
                1.0 * inch,
            ],
        )
        t_v_style = [
            ("BACKGROUND", (0, 0), (-1, 0), COR_AZUL_RS),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ]
        for i in range(1, len(v_rows)):
            bg = colors.HexColor("#F7FAFC") if i % 2 == 0 else colors.white
            t_v_style.append(("BACKGROUND", (0, i), (-1, i), bg))
        t_v.setStyle(TableStyle(t_v_style))
        elements.append(t_v)

    elements.append(Spacer(1, 12))

    # Seção Manutenções
    elements.append(
        Paragraph(
            "🔧 Histórico de Manutenções",
            ParagraphStyle(
                "SectionHeading2",
                parent=styles["Normal"],
                fontName="Helvetica-Bold",
                fontSize=11,
                textColor=COR_AZUL_RS,
            ),
        )
    )
    elements.append(Spacer(1, 4))

    if df_manut.empty:
        elements.append(
            Paragraph("<i>Nenhuma manutenção registrada.</i>", cell_style)
        )
    else:
        m_headers = [
            Paragraph("Data", header_table_style),
            Paragraph("Tipo", header_table_style),
            Paragraph("Descrição", header_table_style),
            Paragraph("KM Realizada", header_table_style),
            Paragraph("Próx. Preventiva", header_table_style),
            Paragraph("Custo", header_table_style),
        ]
        m_rows = [m_headers]
        for _, r in df_manut.head(8).iterrows():
            m_rows.append([
                Paragraph(str(r["data"]), cell_center),
                Paragraph(formata_texto(r["tipo"]), cell_center),
                Paragraph(formata_texto(r["descricao"]), cell_style),
                Paragraph(
                    f"{formata_valor(r['km_realizada']):,.0f} KM", cell_center
                ),
                Paragraph(
                    f"{formata_valor(r['km_proxima']):,.0f} KM", cell_center
                ),
                Paragraph(
                    f"R$ {formata_valor(r['custo']):,.2f}", cell_bold
                ),
            ])

        t_m = Table(
            m_rows,
            colWidths=[
                0.9 * inch,
                1.0 * inch,
                2.3 * inch,
                1.0 * inch,
                1.0 * inch,
                0.8 * inch,
            ],
        )
        t_m_style = [
            ("BACKGROUND", (0, 0), (-1, 0), COR_LARANJA_RS),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E0")),
        ]
        for i in range(1, len(m_rows)):
            bg = colors.HexColor("#FFFAF0") if i % 2 == 0 else colors.white
            t_m_style.append(("BACKGROUND", (0, i), (-1, i), bg))
        t_m.setStyle(TableStyle(t_m_style))
        elements.append(t_m)

    # --- PÁGINA ANEXO: GALERIA DE FOTOS EM TAMANHO GRANDE ---
    fotos_raw = v_info.get("fotos_json")
    fotos_lista = (
        json.loads(fotos_raw) if (fotos_raw and pd.notna(fotos_raw)) else []
    )
    fotos_validas = [p for p in fotos_lista if os.path.exists(p)]

    if fotos_validas:
        # Quebra de página para ir para a folha exclusiva de fotos
        elements.append(PageBreak())

        elements.append(
            montar_cabecalho_pdf(
                f"Anexo Fotográfico - {v_info['placa']}",
                "Registros Visuais da Viatura e Estado de Conservação",
            )
        )
        elements.append(Spacer(1, 8))
        elements.append(
            HRFlowable(
                width="100%", thickness=2, color=COR_AZUL_RS, spaceAfter=12
            )
        )

        for idx, path in enumerate(fotos_validas):
            try:
                # Foto em tamanho expandido (Largura: ~18cm / Altura: ~11.5cm)
                img = Image(path, width=7.0 * inch, height=4.5 * inch)
                img.hAlign = "CENTER"

                elements.append(
                    Paragraph(
                        f"<b>Foto #{idx+1} - Viatura {v_info['placa']}</b>",
                        ParagraphStyle(
                            "SubFoto",
                            parent=cell_bold,
                            textColor=COR_AZUL_RS,
                            fontSize=10,
                        ),
                    )
                )
                elements.append(Spacer(1, 4))
                elements.append(img)
                elements.append(Spacer(1, 14))
            except Exception:
                pass

    doc.build(elements)
    return nome_pdf

# --- GERADOR DE PDF GERAL DA FROTA RS ---
def gerar_pdf_frota(df_frota):
    nome_pdf = "Relatorio_Geral_Frota.pdf"
    doc = SimpleDocTemplate(
        nome_pdf,
        pagesize=letter,
        rightMargin=25,
        leftMargin=25,
        topMargin=30,
        bottomMargin=30,
    )

    elements = []
    (
        styles,
        _,
        _,
        header_table_style,
        cell_style,
        cell_center,
        cell_bold,
    ) = get_pdf_styles()

    elements.append(
        montar_cabecalho_pdf(
            "Relatório Geral da Frota - Material Carga",
            "Inventário Consolidado e Controle Patrimonial",
        )
    )
    elements.append(Spacer(1, 8))
    elements.append(
        HRFlowable(
            width="100%", thickness=2, color=COR_AZUL_RS, spaceAfter=10
        )
    )

    total_veiculos = len(df_frota)
    valor_total = (
        sum(formata_valor(v) for v in df_frota["valor_veiculo"])
        if "valor_veiculo" in df_frota
        else 0.0
    )
    disp_cnt = (
        len(df_frota[df_frota["status"] == "Disponível"])
        if "status" in df_frota
        else 0
    )
    manut_cnt = (
        len(df_frota[df_frota["status"] == "Em Manutenção"])
        if "status" in df_frota
        else 0
    )

    kpi_data = [[
        Paragraph(f"<b>Total de Veículos:</b> {total_veiculos}", cell_center),
        Paragraph(f"<b>Disponíveis:</b> {disp_cnt}", cell_center),
        Paragraph(f"<b>Em Manutenção:</b> {manut_cnt}", cell_center),
        Paragraph(
            f"<b>Valor Total Carga:</b><br/>R$ {valor_total:,.2f}",
            ParagraphStyle(
                "KPIBold",
                parent=cell_bold,
                alignment=1,
                textColor=COR_AZUL_RS,
            ),
        ),
    ]]
    t_kpi = Table(
        kpi_data,
        colWidths=[1.7 * inch, 1.7 * inch, 1.7 * inch, 2.2 * inch],
    )
    t_kpi.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EBF8FF")),
            ("BOX", (0, 0), (-1, -1), 1, COR_AZUL_RS),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BEE3F8")),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ])
    )
    elements.append(t_kpi)
    elements.append(Spacer(1, 12))

    f_headers = [
        Paragraph("Placa", header_table_style),
        Paragraph("Modelo / Marca", header_table_style),
        Paragraph("RENAVAN", header_table_style),
        Paragraph("CHASSI", header_table_style),
        Paragraph("Responsável", header_table_style),
        Paragraph("Valor Carga", header_table_style),
        Paragraph("Odômetro", header_table_style),
        Paragraph("Status", header_table_style),
    ]
    f_rows = [f_headers]

    for _, r in df_frota.iterrows():
        st_txt = str(r["status"])
        st_color = (
            colors.HexColor("#2F855A")
            if st_txt == "Disponível"
            else (
                colors.HexColor("#C53030")
                if st_txt == "Indisponível"
                else COR_LARANJA_RS
            )
        )
        st_style = ParagraphStyle(
            "StatusStyle",
            parent=cell_center,
            textColor=st_color,
            fontName="Helvetica-Bold",
        )

        f_rows.append([
            Paragraph(f"<b>{r['placa']}</b>", cell_center),
            Paragraph(
                f"{r['modelo']}<br/><font size=7"
                f" color='#718096'>{r['marca']}</font>",
                cell_style,
            ),
            Paragraph(formata_texto(r.get("renavam")), cell_center),
            Paragraph(formata_texto(r.get("chassi")), cell_center),
            Paragraph(formata_texto(r.get("responsavel")), cell_style),
            Paragraph(
                f"R$ {formata_valor(r.get('valor_veiculo')):,.2f}", cell_bold
            ),
            Paragraph(
                f"{formata_valor(r.get('odometro_atual')):,.0f} KM", cell_center
            ),
            Paragraph(st_txt, st_style),
        ])

    t_f = Table(
        f_rows,
        colWidths=[
            0.8 * inch,
            1.4 * inch,
            1.0 * inch,
            1.1 * inch,
            1.1 * inch,
            1.0 * inch,
            0.8 * inch,
            0.8 * inch,
        ],
    )
    t_f_style = [
        ("BACKGROUND", (0, 0), (-1, 0), COR_AZUL_RS),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
    ]
    for i in range(1, len(f_rows)):
        bg = colors.HexColor("#F7FAFC") if i % 2 == 0 else colors.white
        t_f_style.append(("BACKGROUND", (0, i), (-1, i), bg))
    t_f.setStyle(TableStyle(t_f_style))

    elements.append(t_f)
    doc.build(elements)
    return nome_pdf


# --- INTERFACE PRINCIPAL ---
st.sidebar.markdown("### 🏢 RS ISOLAMENTOS TÉRMICOS")
if os.path.exists(LOGO_PATH):
    st.sidebar.image(LOGO_PATH, use_container_width=True)

st.sidebar.markdown("---")
menu = st.sidebar.selectbox(
    "Navegação",
    ["Ficha do Veículo", "Cadastrar Novo Veículo", "Relatórios da Frota"],
)

st.title("🚚 Gestão de Frota - RS Isolamentos Térmicos")

# --- CADASTRAR VEÍCULO ---
if menu == "Cadastrar Novo Veículo":
    st.header("Cadastrar Nova Viatura / Veículo")
    with st.form("form_cadastro"):
        c1, c2 = st.columns(2)
        placa = c1.text_input("PLACA / Prefixo")
        renavam = c2.text_input("RENAVAN")
        chassi = c1.text_input("CHASSI")
        ano_modelo = c2.text_input("ANO / MODELO (ex: 2025/2025)")
        modelo = c1.text_input("Modelo")
        marca = c2.text_input("Marca")
        responsavel = c1.text_input("Responsável pelo Veículo")
        valor_veiculo = c2.number_input(
            "Valor do Veículo / Material Carga (R$)", min_value=0.0
        )
        odometro = c1.number_input("Odômetro Inicial (KM)", min_value=0.0)
        status = c2.selectbox(
            "Status Inicial", ["Disponível", "Em Manutenção", "Indisponível"]
        )

        fotos = st.file_uploader(
            "Fotos do Veículo (Selecione 2 ou mais)",
            type=["jpg", "png", "jpeg"],
            accept_multiple_files=True,
        )

        btn_salvar = st.form_submit_button("Cadastrar Viatura")

        if btn_salvar and placa:
            fotos_salvas = []
            if fotos:
                for f in fotos:
                    caminho = os.path.join("uploads", f"{placa}_{f.name}")
                    with open(caminho, "wb") as out:
                        out.write(f.getbuffer())
                    fotos_salvas.append(caminho)

            c = conn.cursor()
            try:
                c.execute(
                    """INSERT INTO veiculos 
                    (placa, renavam, chassi, modelo, marca, ano_modelo, responsavel, valor_veiculo, odometro_atual, status, fotos_json) 
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        placa,
                        renavam,
                        chassi,
                        modelo,
                        marca,
                        ano_modelo,
                        responsavel,
                        valor_veiculo,
                        odometro,
                        status,
                        json.dumps(fotos_salvas),
                    ),
                )
                conn.commit()
                st.success("Viatura cadastrada com sucesso!")
            except sqlite3.IntegrityError:
                st.error("Erro: Placa/Prefixo já cadastrado.")

# --- FICHA INDIVIDUAL ---
elif menu == "Ficha do Veículo":
    df_veiculos = pd.read_sql_query("SELECT * FROM veiculos", conn)

    if df_veiculos.empty:
        st.info("Nenhum veículo cadastrado.")
    else:
        placa_sel = st.selectbox(
            "Selecione a Viatura", df_veiculos["placa"].tolist()
        )
        v_info = df_veiculos[df_veiculos["placa"] == placa_sel].iloc[0]
        veiculo_id = int(v_info["id"])

        st.subheader(f"Ficha Individual: {v_info['modelo']} ({v_info['placa']})")

        t_dados, t_viagens, t_manut, t_rel, t_editar = st.tabs([
            "📋 Dados & Fotos",
            "🛣️ Viagens",
            "🔧 Manutenções",
            "📄 Documentos/PDF",
            "✏️ Editar / Excluir Veículo",
        ])

        with t_dados:
            c1, c2 = st.columns(2)
            valor_formatado = formata_valor(v_info.get("valor_veiculo"))

            with c1:
                st.write(f"**PLACA:** {v_info['placa']}")
                st.write(
                    f"**RENAVAN:** {formata_texto(v_info.get('renavam'))}"
                )
                st.write(f"**CHASSI:** {formata_texto(v_info.get('chassi'))}")
                st.write(
                    "**ANO/MODELO:**"
                    f" {formata_texto(v_info.get('ano_modelo'))}"
                )
            with c2:
                st.write(
                    "**RESPONSÁVEL:**"
                    f" {formata_texto(v_info.get('responsavel'))}"
                )
                st.write(
                    "**VALOR MATERIAL CARGA:** R$"
                    f" {valor_formatado:,.2f}"
                )
                st.write(f"**ODÔMETRO:** {v_info['odometro_atual']} KM")
                st.write(f"**STATUS:** {v_info['status']}")

            st.markdown("---")
            st.markdown("### Galeria de Fotos")
            fotos_raw = v_info.get("fotos_json")
            fotos_lista = (
                json.loads(fotos_raw)
                if (fotos_raw and pd.notna(fotos_raw))
                else []
            )
            if fotos_lista:
                cols = st.columns(
                    len(fotos_lista) if len(fotos_lista) < 4 else 4
                )
                for idx, path in enumerate(fotos_lista):
                    if os.path.exists(path):
                        cols[idx % 4].image(path, use_container_width=True)
            else:
                st.info("Nenhuma foto cadastrada para esta viatura.")

        with t_viagens:
            with st.form("form_v"):
                st.markdown("#### Lançar Viagem")
                c1, c2 = st.columns(2)
                dt = c1.date_input("Data", datetime.now())
                cond = c2.text_input("Condutor")
                kmi = c1.number_input(
                    "KM Inicial", value=float(v_info["odometro_atual"])
                )
                kmf = c2.number_input(
                    "KM Final", value=float(v_info["odometro_atual"])
                )
                comb = c1.number_input("Combustível (L)", min_value=0.0)
                if st.form_submit_button("Salvar Viagem"):
                    if kmf >= kmi:
                        rod = kmf - kmi
                        c = conn.cursor()
                        c.execute(
                            "INSERT INTO viagens (veiculo_id, data, condutor,"
                            " km_inicial, km_final, km_rodado,"
                            " combustivel_litros) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (veiculo_id, str(dt), cond, kmi, kmf, rod, comb),
                        )
                        c.execute(
                            "UPDATE veiculos SET odometro_atual = ? WHERE id ="
                            " ?",
                            (kmf, veiculo_id),
                        )
                        conn.commit()
                        st.success("Viagem salva!")
                        st.rerun()
            df_v = pd.read_sql_query(
                "SELECT data, condutor, km_inicial, km_final, km_rodado,"
                " combustivel_litros FROM viagens WHERE veiculo_id = ?"
                " ORDER BY id DESC",
                conn,
                params=(veiculo_id,),
            )
            st.dataframe(df_v, use_container_width=True)

        with t_manut:
            st.markdown("#### Lançar Nova Manutenção")
            with st.form("form_m"):
                tp = st.selectbox(
                    "Tipo", ["Preventiva", "Corretiva", "Preditiva"]
                )
                desc = st.text_input("Descrição / Peças")
                c1, c2 = st.columns(2)
                dt_m = c1.date_input("Data", datetime.now())
                custo = c2.number_input("Custo (R$)", min_value=0.0)
                km_px = c1.number_input(
                    "Próxima Preventiva (KM)",
                    value=float(v_info["odometro_atual"]) + 10000,
                )
                if st.form_submit_button("Salvar Manutenção"):
                    c = conn.cursor()
                    c.execute(
                        "INSERT INTO manutenções (veiculo_id, tipo, descricao,"
                        " data, km_realizada, km_proxima, custo) VALUES (?, ?,"
                        " ?, ?, ?, ?, ?)",
                        (
                            veiculo_id,
                            tp,
                            desc,
                            str(dt_m),
                            v_info["odometro_atual"],
                            km_px,
                            custo,
                        ),
                    )
                    conn.commit()
                    st.success("Manutenção salva!")
                    st.rerun()

            st.markdown("---")
            st.markdown("#### Histórico e Gerenciamento de Manutenções")
            df_m = pd.read_sql_query(
                "SELECT id, data, tipo, descricao, km_realizada, km_proxima,"
                " custo FROM manutenções WHERE veiculo_id = ? ORDER BY id DESC",
                conn,
                params=(veiculo_id,),
            )

            if df_m.empty:
                st.info("Nenhuma manutenção registrada para este veículo.")
            else:
                st.dataframe(
                    df_m.drop(columns=["id"]), use_container_width=True
                )

                st.markdown(
                    "##### ✏️ Editar ou Excluir Lançamento de Manutenção"
                )

                opcoes_m = {
                    f"ID: {row['id']} | Data: {row['data']} - {row['tipo']}"
                    f" ({row['descricao']})": row["id"]
                    for _, row in df_m.iterrows()
                }
                manut_sel_text = st.selectbox(
                    "Selecione a manutenção para editar/excluir",
                    list(opcoes_m.keys()),
                )
                manut_id_sel = opcoes_m[manut_sel_text]

                row_m = df_m[df_m["id"] == manut_id_sel].iloc[0]

                col_e1, col_e2 = st.columns(2)

                with col_e1:
                    with st.expander("🛠️ Editar Manutenção Selecionada"):
                        with st.form(f"form_edit_m_{manut_id_sel}"):
                            try:
                                dt_edit_val = datetime.strptime(
                                    str(row_m["data"]), "%Y-%m-%d"
                                )
                            except Exception:
                                dt_edit_val = datetime.now()

                            tipo_edit = st.selectbox(
                                "Tipo",
                                ["Preventiva", "Corretiva", "Preditiva"],
                                index=(
                                    [
                                        "Preventiva",
                                        "Corretiva",
                                        "Preditiva",
                                    ].index(row_m["tipo"])
                                    if row_m["tipo"]
                                    in [
                                        "Preventiva",
                                        "Corretiva",
                                        "Preditiva",
                                    ]
                                    else 0
                                ),
                            )
                            desc_edit = st.text_input(
                                "Descrição", value=str(row_m["descricao"])
                            )
                            dt_edit = st.date_input("Data", value=dt_edit_val)
                            custo_edit = st.number_input(
                                "Custo (R$)",
                                value=formata_valor(row_m["custo"]),
                                min_value=0.0,
                            )
                            km_real_edit = st.number_input(
                                "KM Realizada",
                                value=formata_valor(row_m["km_realizada"]),
                                min_value=0.0,
                            )
                            km_prox_edit = st.number_input(
                                "Próxima Preventiva (KM)",
                                value=formata_valor(row_m["km_proxima"]),
                                min_value=0.0,
                            )

                            if st.form_submit_button(
                                "💾 Salvar Alterações na Manutenção"
                            ):
                                c = conn.cursor()
                                c.execute(
                                    """UPDATE manutenções SET 
                                            tipo=?, descricao=?, data=?, km_realizada=?, km_proxima=?, custo=? 
                                            WHERE id=?""",
                                    (
                                        tipo_edit,
                                        desc_edit,
                                        str(dt_edit),
                                        km_real_edit,
                                        km_prox_edit,
                                        custo_edit,
                                        manut_id_sel,
                                    ),
                                )
                                conn.commit()
                                st.success("Manutenção atualizada!")
                                st.rerun()

                with col_e2:
                    with st.expander("🗑️ Excluir Manutenção Selecionada"):
                        st.warning(
                            "Tem certeza que deseja apagar esta manutenção?"
                        )
                        if st.button(
                            "Confirmar Exclusão da Manutenção",
                            type="primary",
                            key=f"btn_del_m_{manut_id_sel}",
                        ):
                            c = conn.cursor()
                            c.execute(
                                "DELETE FROM manutenções WHERE id=?",
                                (manut_id_sel,),
                            )
                            conn.commit()
                            st.success("Manutenção excluída com sucesso!")
                            st.rerun()

        with t_rel:
            st.markdown("#### Relatório Individual Oficial")
            if st.button("Gerar Ficha Individual em PDF (RS Isolamentos)"):
                df_v_pdf = pd.read_sql_query(
                    "SELECT * FROM viagens WHERE veiculo_id = ?",
                    conn,
                    params=(veiculo_id,),
                )
                df_m_pdf = pd.read_sql_query(
                    "SELECT * FROM manutenções WHERE veiculo_id = ?",
                    conn,
                    params=(veiculo_id,),
                )
                pdf_f = gerar_pdf_veiculo(v_info, df_v_pdf, df_m_pdf)
                with open(pdf_f, "rb") as f:
                    st.download_button(
                        "📥 Baixar PDF da Viatura",
                        f,
                        file_name=pdf_f,
                        mime="application/pdf",
                    )

        # --- ABA EDITAR OU EXCLUIR VEÍCULO ---
        with t_editar:
            st.markdown("### Editar Dados do Veículo")
            with st.form("form_edicao"):
                c1, c2 = st.columns(2)
                nova_placa = c1.text_input(
                    "PLACA / Prefixo", value=v_info["placa"]
                )
                novo_renavam = c2.text_input(
                    "RENAVAN",
                    value=formata_texto(v_info.get("renavam")).replace("-", ""),
                )
                novo_chassi = c1.text_input(
                    "CHASSI",
                    value=formata_texto(v_info.get("chassi")).replace("-", ""),
                )
                novo_ano_modelo = c2.text_input(
                    "ANO / MODELO",
                    value=formata_texto(v_info.get("ano_modelo")).replace(
                        "-", ""
                    ),
                )
                novo_modelo = c1.text_input("Modelo", value=v_info["modelo"])
                nova_marca = c2.text_input("Marca", value=v_info["marca"])
                novo_responsavel = c1.text_input(
                    "Responsável pelo Veículo",
                    value=formata_texto(v_info.get("responsavel")).replace(
                        "-", ""
                    ),
                )
                novo_valor = c2.number_input(
                    "Valor Material Carga (R$)",
                    value=formata_valor(v_info.get("valor_veiculo")),
                    min_value=0.0,
                )
                novo_odometro = c1.number_input(
                    "Odômetro (KM)",
                    value=float(v_info["odometro_atual"]),
                    min_value=0.0,
                )

                opcoes_status = ["Disponível", "Em Manutenção", "Indisponível"]
                idx_st = (
                    opcoes_status.index(v_info["status"])
                    if v_info["status"] in opcoes_status
                    else 0
                )
                novo_status = c2.selectbox(
                    "Status", opcoes_status, index=idx_st
                )

                novas_fotos = st.file_uploader(
                    "Adicionar/Atualizar Fotos",
                    type=["jpg", "png", "jpeg"],
                    accept_multiple_files=True,
                )

                if st.form_submit_button("💾 Salvar Alterações no Veículo"):
                    c = conn.cursor()

                    fotos_existentes = (
                        json.loads(v_info["fotos_json"])
                        if (
                            v_info.get("fotos_json")
                            and pd.notna(v_info.get("fotos_json"))
                        )
                        else []
                    )
                    if novas_fotos:
                        for f in novas_fotos:
                            caminho = os.path.join(
                                "uploads", f"{nova_placa}_{f.name}"
                            )
                            with open(caminho, "wb") as out:
                                out.write(f.getbuffer())
                            fotos_existentes.append(caminho)

                    c.execute(
                        """UPDATE veiculos SET 
                                placa=?, renavam=?, chassi=?, modelo=?, marca=?, ano_modelo=?, 
                                responsavel=?, valor_veiculo=?, odometro_atual=?, status=?, fotos_json=? 
                                WHERE id=?""",
                        (
                            nova_placa,
                            novo_renavam,
                            novo_chassi,
                            novo_modelo,
                            nova_marca,
                            novo_ano_modelo,
                            novo_responsavel,
                            novo_valor,
                            novo_odometro,
                            novo_status,
                            json.dumps(fotos_existentes),
                            veiculo_id,
                        ),
                    )
                    conn.commit()
                    st.success("Dados do veículo atualizados com sucesso!")
                    st.rerun()

            st.markdown("---")
            st.markdown("### ⚠️ Zona de Perigo: Excluir Veículo")
            st.warning(
                "Esta ação é irreversível e excluirá todo o histórico de"
                " viagens e manutenções desta viatura."
            )

            confirmar = st.checkbox(
                f"Tenho certeza de que quero excluir a viatura {v_info['placa']}"
            )
            if st.button(
                "🗑️ Excluir Veículo Definitivamente",
                type="primary",
                disabled=not confirmar,
            ):
                c = conn.cursor()
                c.execute(
                    "DELETE FROM viagens WHERE veiculo_id=?", (veiculo_id,)
                )
                c.execute(
                    "DELETE FROM manutenções WHERE veiculo_id=?", (veiculo_id,)
                )
                c.execute("DELETE FROM veiculos WHERE id=?", (veiculo_id,))
                conn.commit()
                st.success(
                    f"Viatura {v_info['placa']} excluída com sucesso!"
                )
                st.rerun()

# --- RELATÓRIOS DA FROTA COMPLETA ---
elif menu == "Relatórios da Frota":
    st.header("📊 Controle Geral da Frota / Material Carga")
    df_frota = pd.read_sql_query("SELECT * FROM veiculos", conn)

    if df_frota.empty:
        st.info("Nenhum veículo cadastrado.")
    else:
        v_total = (
            sum(formata_valor(v) for v in df_frota["valor_veiculo"])
            if "valor_veiculo" in df_frota
            else 0.0
        )
        st.metric("Valor Total da Carga da Frota RS", f"R$ {v_total:,.2f}")

        # Tabela completa de exibição no Dashboard
        st.dataframe(
            df_frota[[
                "placa",
                "modelo",
                "marca",
                "renavam",
                "chassi",
                "ano_modelo",
                "responsavel",
                "valor_veiculo",
                "odometro_atual",
                "status",
            ]],
            use_container_width=True,
        )

        st.markdown("---")
        st.markdown("### Exportar Relatório Geral Consolidado")

        if st.button("Gerar Relatório da Frota Completa (PDF)"):
            pdf_geral = gerar_pdf_frota(df_frota)
            with open(pdf_geral, "rb") as f:
                st.download_button(
                    "📥 Baixar Relatório Consolidador da Frota (PDF)",
                    f,
                    file_name=pdf_geral,
                    mime="application/pdf",
                )