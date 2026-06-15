import sys
import os
import sqlite3

# Adiciona a raiz do projeto ao path para conseguir importar 'table_manager' e 'dyntable'
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from table_manager import TableManager

def main():
    data_dir = os.path.join(project_root, 'dados')
    manager = TableManager(data_dir)
    
    table_name = 'sensor_readings'
    
    if not manager.exists(table_name):
        print(f"Tabela '{table_name}' não encontrada no diretório '{data_dir}'.")
        return
        
    table = manager.get(table_name)
    
    print("=" * 60)
    print(f"TABELA: {table.name} (.dyndb)")
    print("=" * 60)
    
    print(f"\n1. ESTRUTURA (Colunas detectadas):")
    for col in table.columns:
        # Acessa os atributos da coluna definidos no DynColumn
        print(f"  - {col.name:15} | Tipo: {col.dtype.name:10} | Aceita Nulo: {col.nullable}")
        
    print(f"\n2. CONTEÚDO FORMATADO ({table.row_count} linhas):")
    # A classe DynTable possui um método mágico __str__ que imprime a matriz formatada
    print(table)
    
    print("\n3. INSPECIONANDO OS DADOS LINHA A LINHA (Formato dicionário):")
    for row in table:
        # row é um DynRow, mas podemos acessar os valores pelo nome da coluna
        row_dict = {col: row[col] for col in table.column_names}
        print(f"  -> [ID: {row.id}] {row_dict}")

    # --- NOVO: Lê o .gpkg usando sqlite3 ---
    read_gpkg(data_dir, table_name)

def read_gpkg(data_dir, table_name):
    gpkg_path = os.path.join(data_dir, f"{table_name}.gpkg")
    if not os.path.exists(gpkg_path):
        print(f"\nArquivo GPKG '{gpkg_path}' não encontrado.")
        return
        
    print("\n" + "=" * 60)
    print(f"TABELA: {table_name} (.gpkg)")
    print("=" * 60)
    
    con = sqlite3.connect(gpkg_path)
    try:
        cursor = con.cursor()
        
        # Pega a estrutura da tabela
        cursor.execute(f"PRAGMA table_info('{table_name}')")
        columns_info = cursor.fetchall()
        
        if not columns_info:
            print(f"Tabela '{table_name}' não encontrada dentro do GPKG.")
            return
            
        print(f"\n1. ESTRUTURA GPKG (Colunas):")
        col_names = []
        for col in columns_info:
            # PRAGMA table_info retorna: (cid, name, type, notnull, dflt_value, pk)
            name = col[1]
            col_type = col[2]
            print(f"  - {name:15} | Tipo SQLite: {col_type:10}")
            col_names.append(name)
            
        # Pega os dados
        cursor.execute(f"SELECT * FROM '{table_name}'")
        rows = cursor.fetchall()
        
        print(f"\n2. CONTEÚDO BRUTO GPKG ({len(rows)} linhas):")
        # Cabeçalho
        header = " | ".join([f"{name:15}" for name in col_names])
        print(header)
        print("-" * len(header))
        
        # Linhas
        for row in rows:
            row_display = []
            for i, val in enumerate(row):
                if col_names[i] == 'geom' and val is not None:
                    row_display.append(f"{'<WKB BINARY>':15}")
                else:
                    val_str = str(val) if val is not None else "NULL"
                    row_display.append(f"{val_str[:15]:15}")
            print(" | ".join(row_display))
            
    except Exception as e:
        print(f"Erro ao ler GPKG: {e}")
    finally:
        con.close()

if __name__ == '__main__':
    main()
