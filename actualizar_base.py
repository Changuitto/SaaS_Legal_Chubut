import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# 1. CONFIGURACIÓN
os.environ["OPENAI_API_KEY"] = "PONER_LLAVE_AQUÍ"
13rHkeh7nISs5fmSaDibqGS_mFP3schHc5QRM3N3siktkwcJx9UVxZYT3BlbkFJRYlx0WaZxTx098tggXwUKqjf_Fytsrc2etumuyeJTAdmSyXoells_rqlddkiEyEE1kJj8OJ9EA" # Poné tu llave real

# Usamos la ruta donde tenés tus TXT (la carpeta que creamos en tu proyecto)
ruta_txt = "./mi_base_legal" 
directorio_db = "./MI_BASE_VECTORIAL"

def cargar_toda_la_jurisprudencia():
    print("🚀 Iniciando la carga masiva a la Bóveda Vectorial...")
    
    # Usamos el DirectoryLoader de tu script que es más potente
    # Agregamos silent_errors=True para que si un archivo está roto, siga con el siguiente
    loader = DirectoryLoader(
        ruta_txt, 
        glob="**/*.txt", 
        loader_cls=TextLoader, 
        loader_kwargs={'encoding': 'utf-8'},
        silent_errors=True
    )
    
    try:
        print("📖 Leyendo archivos TXT (esto puede tardar un poco)...")
        documentos = loader.load()
        print(f"✅ Se cargaron {len(documentos)} archivos.")
    except Exception as e:
        print(f"❌ Error al leer los archivos: {e}")
        return

    # Usamos tu cortador de texto (Recursive) que es mejor para temas legales
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    textos_cortados = text_splitter.split_documents(documentos)
    print(f"✂️ Texto dividido en {len(textos_cortados)} fragmentos.")

    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    print("🧠 Guardando en la Bóveda Vectorial (MI_BASE_VECTORIAL)...")
    # Esto agrega los nuevos fallos a lo que ya tenías guardado
    vectordb = Chroma.from_documents(
        documents=textos_cortados, 
        embedding=embeddings, 
        persist_directory=directorio_db
    )
    
    print("\n✅ ¡MISIÓN COMPLETADA!")
    print(f"Ahora tu carpeta 'MI_BASE_VECTORIAL' tiene toda la jurisprudencia 2015-2026.")

if __name__ == "__main__":
    cargar_toda_la_jurisprudencia()