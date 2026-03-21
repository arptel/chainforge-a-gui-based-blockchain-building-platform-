import zipfile
import xml.etree.ElementTree as ET
import os

def extract_docx(docx_path, output_path):
    if not os.path.exists(docx_path):
        print(f"Error: {docx_path} not found")
        return
    
    try:
        with zipfile.ZipFile(docx_path) as doc:
            xml_content = doc.read('word/document.xml')
            tree = ET.fromstring(xml_content)
            ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            paragraphs = tree.findall('.//w:p', ns)
            lines = []
            for p in paragraphs:
                texts = [t.text for t in p.findall('.//w:t', ns) if t.text]
                if texts:
                    lines.append("".join(texts))
            
            full_text = "\n".join(lines)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(full_text)
            print(f"Successfully extracted {len(lines)} paragraphs to {output_path}")
    except Exception as e:
        print(f"Error extracting docx: {e}")

if __name__ == "__main__":
    extract_docx(r'c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\chainforge_simulator_spec.docx', '/tmp/spec_final.txt')
