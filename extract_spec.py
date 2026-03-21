from docx import Document

doc = Document(r'c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\chainforge_simulator_spec.docx')
for para in doc.paragraphs:
    if para.text.strip():
        print(para.text)
