import os
import PyPDF2
import pdfplumber

RAW_DIR = "data/raw"
PROCESSED_DIR = "data/processed"

# Créer le dossier de sortie s'il n'existe pas
os.makedirs(PROCESSED_DIR, exist_ok=True)

def extract_from_pdf_pypdf2(filepath):
    """Extraction rapide avec PyPDF2 (PDF simples)"""
    text = ""
    try:
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
    except Exception as e:
        print(f"  ❌ Erreur PyPDF2 : {e}")
    return text

def extract_from_pdf_plumber(filepath):
    """Extraction avancée avec pdfplumber (PDF complexes)"""
    text = ""
    try:
        with pdfplumber.open(filepath) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n\n"
    except Exception as e:
        print(f"  ❌ Erreur pdfplumber : {e}")
    return text

def extract_from_txt(filepath):
    """Lecture directe de fichiers texte"""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except UnicodeDecodeError:
        with open(filepath, "r", encoding="latin-1") as f:
            return f.read()

# Traitement de tous les fichiers
total_files = 0
success_files = 0

for filename in os.listdir(RAW_DIR):
    filepath = os.path.join(RAW_DIR, filename)
    
    # Ignorer les dossiers et fichiers cachés
    if os.path.isdir(filepath) or filename.startswith("."):
        continue
    
    total_files += 1
    print(f"\n📄 Traitement : {filename}")
    
    text = ""
    ext = filename.lower().split(".")[-1]
    
    if ext == "pdf":
        # Essayer d'abord PyPDF2 (rapide)
        text = extract_from_pdf_pypdf2(filepath)
        
        # Si le résultat est trop court, essayer pdfplumber
        if len(text.strip()) < 100:
            print("  ⚠️ PyPDF2 a peu extrait, essai avec pdfplumber...")
            text = extract_from_pdf_plumber(filepath)
    
    elif ext in ["txt", "md"]:
        text = extract_from_txt(filepath)
    
    elif ext in ["docx"]:
        try:
            import docx
            doc = docx.Document(filepath)
            text = "\n\n".join([p.text for p in doc.paragraphs])
        except Exception as e:
            print(f"  ❌ Erreur DOCX : {e}")
    
    else:
        print(f"  ⚠️ Format non supporté : .{ext}")
        continue
    
    # Vérifier le résultat
    if len(text.strip()) < 50:
        print(f"  ⚠️ Texte trop court ({len(text.strip())} caractères). "
              f"Le PDF est peut-être un scan (image).")
        continue
    
    # Sauvegarder le texte extrait
    output_name = os.path.splitext(filename)[0] + ".txt"
    output_path = os.path.join(PROCESSED_DIR, output_name)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)
    
    print(f"  ✅ {len(text)} caractères extraits → {output_name}")
    success_files += 1

print(f"\n{'='*50}")
print(f"📊 Résumé : {success_files}/{total_files} fichiers traités avec succès")
print(f"📁 Résultats dans : {PROCESSED_DIR}/")