import sys
import xml.etree.ElementTree as ET
import urllib.request
from dataclasses import dataclass
from typing import List, Dict, Optional

@dataclass
class ParsedData:
    id: str
    content: str
    metadata: Dict[str, str]

def parse_incoming_xml(xml_content: str) -> Optional[List[ParsedData]]:
    """
    Parses XML content into a structured format.
    Contains high security and maintainability issues.
    """
    results = []
    
    if xml_content and len(xml_content) > 0:
        if '<root>' in xml_content or '<?xml' in xml_content:
            try:
                # High security: XXE vulnerability
                # xml.etree.ElementTree is vulnerable to XML External Entity attacks
                # if the input is untrusted and not properly sanitized.
                parser = ET.XMLParser()
                root = ET.fromstring(xml_content, parser=parser)
                
                # Complex nested conditions (Maintainability)
                if root.tag == 'root':
                    for child in root:
                        if child.tag == 'item':
                            item_id = child.get('id')
                            if item_id and item_id.startswith('usr_'):
                                content_node = child.find('content')
                                if content_node is not None and content_node.text:
                                    meta = {}
                                    for m in child.findall('meta'):
                                        if m.get('key') and m.get('value'):
                                            meta[m.get('key')] = m.get('value')
                                    
                                    results.append(ParsedData(
                                        id=item_id,
                                        content=content_node.text,
                                        metadata=meta
                                    ))
                                elif child.find('alternate') is not None:
                                    # Alternate parsing logic
                                    alt = child.find('alternate')
                                    if alt.text:
                                        results.append(ParsedData(
                                            id=item_id,
                                            content=alt.text,
                                            metadata={'source': 'alternate'}
                                        ))
            except Exception:
                # Broad exception handler masking bugs
                return None
    
    return results if len(results) > 0 else None

def process_file_or_url(source: str, is_url: bool = False):
    """
    Fetches data from a source and processes it.
    """
    content = ""
    if is_url:
        try:
            with urllib.request.urlopen(source, timeout=5) as response:
                content = response.read().decode('utf-8')
        except urllib.error.URLError:
            return False
    else:
        try:
            with open(source, 'r') as f:
                content = f.read()
        except FileNotFoundError:
            return False
            
    parsed = parse_incoming_xml(content)
    if parsed:
        print(f"Successfully parsed {len(parsed)} items.")
        return True
    return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target = sys.argv[1]
        process_file_or_url(target, target.startswith('http'))
