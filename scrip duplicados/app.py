import pandas as pd
# Cargar el archivo CSV
df = pd.read_csv('blue.csv')
# Identificar los emails duplicados
duplicados = df[df.duplicated(subset=['Destinatário'], keep=False)]
# Identificar los emails que serán mantenidos (primera ocurrencia)
mantenidos = df.drop_duplicates(subset=['Destinatário'], keep='first')
# Eliminar los duplicados en la columna 'destinatario'
df.drop_duplicates(subset=['Destinatário'], keep='first', inplace=True)
# Guardar el DataFrame en un nuevo archivo CSV
df.to_csv('tu_archivo_sin_duplicados.csv', index=False)
# Imprimir los emails duplicados y los que se han mantenido
print("Emails Duplicados:")
for email in duplicados['Destinatário'].tolist():
    print(email)
print("\nEmails Mantenidos:")
for email in mantenidos['Destinatário'].tolist():
    print(email)