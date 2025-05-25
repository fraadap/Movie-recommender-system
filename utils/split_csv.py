import pandas as pd
import os

# Percorso del file originale
input_file = 'ratings.csv'

# Verifica se il file esiste
if not os.path.exists(input_file):
    print(f"❌ Il file {input_file} non esiste nella directory corrente.")
else:
    print(f"✅ File {input_file} trovato.")

    # Leggi il file CSV
    try:
        df = pd.read_csv(input_file)

        total_rows = len(df)
        print(f"Il file contiene {total_rows} righe (incluso l'header).")

        if total_rows <= 1:
            print("❌ Non ci sono dati da suddividere dopo l'header.")
        else:
            # Crea la cartella per i file divisi
            output_folder = 'split_csv'
            os.makedirs(output_folder, exist_ok=True)

            # Numero totale di dati (senza header)
            data_rows_count = total_rows - 1  # Escludi l'header
            rows_per_file = data_rows_count // 10
            remainder = data_rows_count % 10

            start_idx = 1  # Partiamo dalla seconda riga (prima riga = header)

            print(f"Saranno create 10 parti, circa {rows_per_file} righe per parte (+1 per le prime {remainder} parti)")

            for i in range(10):
                end_idx = start_idx + rows_per_file + (1 if i < remainder else 0)

                # Seleziona il blocco di dati con .iloc
                part_df = df.iloc[start_idx:end_idx]

                # Ricostruiamo un DataFrame con l'header
                final_part = pd.concat([df.iloc[[0]], part_df], ignore_index=True)

                # Salva il file
                filename = f'{output_folder}/ratings_part_{i+1}.csv'
                final_part.to_csv(filename, index=False)

                print(f"File {i+1}: {len(part_df)} righe di dati salvate in {filename}")

                start_idx = end_idx

            print("✅ Divisione completata correttamente!")

    except Exception as e:
        print("❌ Errore durante la lettura del file:", e)