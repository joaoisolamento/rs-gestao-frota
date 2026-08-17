import json
import os
import pandas as pd
import psycopg2
import streamlit as st


# --- CONEXÃO COM O BANCO DE DADOS DA NUVEM (SUPABASE / POSTGRESQL) ---
def conectar_bd():
    try:
        # Pega a URL salva no Secrets do Streamlit
        db_url = st.secrets["DATABASE_URL"]
        conn = psycopg2.connect(db_url)
        return conn
    except Exception as e:
        # Fallback local para desenvolvimento se não houver Secrets
        import sqlite3

        return sqlite3.connect("frota_rs.db", check_same_thread=False)


def inicializar_bd():
    conn = conectar_bd()
    cursor = conn.cursor()

    # Criação das tabelas compatível com PostgreSQL e SQLite
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS veiculos (
            placa TEXT PRIMARY KEY,
            marca TEXT NOT NULL,
            modelo TEXT NOT NULL,
            ano_modelo TEXT,
            renavam TEXT,
            chassi TEXT,
            responsavel TEXT,
            valor_veiculo REAL,
            odometro_atual REAL DEFAULT 0,
            status TEXT DEFAULT 'Operacional',
            fotos_json TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS viagens (
            id SERIAL PRIMARY KEY,
            placa TEXT NOT NULL,
            data DATE NOT NULL,
            condutor TEXT NOT NULL,
            km_inicial REAL NOT NULL,
            km_final REAL NOT NULL,
            km_rodado REAL NOT NULL,
            combustivel_litros REAL,
            FOREIGN KEY (placa) REFERENCES veiculos(placa) ON DELETE CASCADE
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS manutencoes (
            id SERIAL PRIMARY KEY,
            placa TEXT NOT NULL,
            data DATE NOT NULL,
            tipo TEXT NOT NULL,
            descricao TEXT,
            km_realizada REAL NOT NULL,
            km_proxima REAL,
            custo REAL DEFAULT 0,
            FOREIGN KEY (placa) REFERENCES veiculos(placa) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()


# --- FUNÇÕES DE CONSULTA E OPERAÇÕES ---
def carregar_veiculos():
    conn = conectar_bd()
    df = pd.read_sql_query("SELECT * FROM veiculos", conn)
    conn.close()
    return df


def carregar_viagens(placa=None):
    conn = conectar_bd()
    if placa:
        df = pd.read_sql_query(
            "SELECT * FROM viagens WHERE placa = %s ORDER BY data DESC",
            conn,
            params=(placa,),
        )
    else:
        df = pd.read_sql_query("SELECT * FROM viagens ORDER BY data DESC", conn)
    conn.close()
    return df


def carregar_manutencoes(placa=None):
    conn = conectar_bd()
    if placa:
        df = pd.read_sql_query(
            "SELECT * FROM manutencoes WHERE placa = %s ORDER BY data DESC",
            conn,
            params=(placa,),
        )
    else:
        df = pd.read_sql_query(
            "SELECT * FROM manutencoes ORDER BY data DESC", conn
        )
    conn.close()
    return df


def salvar_veiculo(
    placa,
    marca,
    modelo,
    ano_modelo,
    renavam,
    chassi,
    responsavel,
    valor_veiculo,
    odometro,
    status,
    fotos_paths,
):
    conn = conectar_bd()
    cursor = conn.cursor()
    fotos_json = json.dumps(fotos_paths)

    # Upsert (Atualiza se já existir, insere se for novo)
    cursor.execute(
        """
        INSERT INTO veiculos (placa, marca, modelo, ano_modelo, renavam, chassi, responsavel, valor_veiculo, odometro_atual, status, fotos_json)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (placa) DO UPDATE SET
            marca=EXCLUDED.marca,
            modelo=EXCLUDED.modelo,
            ano_modelo=EXCLUDED.ano_modelo,
            renavam=EXCLUDED.renavam,
            chassi=EXCLUDED.chassi,
            responsavel=EXCLUDED.responsavel,
            valor_veiculo=EXCLUDED.valor_veiculo,
            odometro_atual=EXCLUDED.odometro_atual,
            status=EXCLUDED.status,
            fotos_json=EXCLUDED.fotos_json;
    """,
        (
            placa.upper(),
            marca,
            modelo,
            ano_modelo,
            renavam,
            chassi,
            responsavel,
            valor_veiculo,
            odometro,
            status,
            fotos_json,
        ),
    )

    conn.commit()
    conn.close()


def salvar_viagem(
    placa, data, condutor, km_inicial, km_final, combustivel_litros
):
    km_rodado = km_final - km_inicial
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO viagens (placa, data, condutor, km_inicial, km_final, km_rodado, combustivel_litros)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """,
        (
            placa,
            data,
            condutor,
            km_inicial,
            km_final,
            km_rodado,
            combustivel_litros,
        ),
    )

    # Atualiza o odômetro do veículo automaticamente se a nova KM for maior
    cursor.execute(
        """
        UPDATE veiculos SET odometro_atual = GREATEST(odometro_atual, %s) WHERE placa = %s
    """,
        (km_final, placa),
    )

    conn.commit()
    conn.close()


def salvar_manutencao(
    placa, data, tipo, descricao, km_realizada, km_proxima, custo
):
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO manutencoes (placa, data, tipo, descricao, km_realizada, km_proxima, custo)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
    """,
        (placa, data, tipo, descricao, km_realizada, km_proxima, custo),
    )

    conn.commit()
    conn.close()


def excluir_veiculo(placa):
    conn = conectar_bd()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM veiculos WHERE placa = %s", (placa,))
    conn.commit()
    conn.close()
