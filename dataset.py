
#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup  # Corrected "Beautifulsoup" to "BeautifulSoup"
import pandas as pd
import time
import json  # For JSON serialization if needed


def scrape_verbs(limit=5):
    """Scrape verb names and URLs from the main page."""
    try:
        HEADERS = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(MAIN_URL, timeout=10, headers=HEADERS)
        response.raise_for_status()
        
        # Save HTML for debugging
        with open("debug.html", "w", encoding="utf-8") as f:
            f.write(response.text)
        
        soup = BeautifulSoup(response.content, 'html.parser')
        verbs = []
        
        # Extract verb links (adjust selector based on debug.html)
        for link in soup.select('a[href^="vis.php?lemma="]'):
            if len(verbs) >= limit:
                break
            verb_name = link.text.strip()
            verb_url = BASE_URL + link['href']
            verbs.append({
                'verb': verb_name,
                'url': verb_url
            })
        return verbs
    except Exception as e:
        print(f"Error scraping verbs: {e}")
        return []

# Rest of the code...


def extract_conjugations(soup):
    tables = soup.find_all('table')
    table = tables[1] 
    rows = table.find_all('tr')
    
    conj = {'present': [], 'pra': [], 'perfect': [], 'imperative': []}
    
    # Row 3 contains forms
    forms = rows[2].find_all('td')
    if len(forms) >= 3:
        conj['present'] = [forms[1].text.strip()]
        conj['imperative'] = [forms[0].text.strip()]  # Changed from forms[2]
    
    # Past forms are in row 3
    past_forms = rows[4].find_all('td')
    if past_forms:
        conj['pra'] = [past_forms[0].text.strip()]
        conj['perfect'] = [past_forms[1].text.strip()]
    
    print("\nRow data:", [f.text.strip() for f in forms])
    
    return conj


def extract_structures(soup):
    structures = []
    
    # Print raw HTML to debug
    print(soup.prettify())
    
    # Find the Strukturen heading and get its following table row
    strukturen = soup.find('h4', string='Strukturen')
    if strukturen:
        next_tr = strukturen.find_next('tr')
        if next_tr:
            content = next_tr.find('td')
            if content:
                lines = content.get_text(separator='\n').split('\n')
                
                current_structure = None
                current_examples = []
                
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('Ich'):
                        if current_structure:
                            structures.append({
                                'structure': current_structure,
                                'examples': current_examples
                            })
                        current_structure = line
                        current_examples = []
                    elif line:
                        current_examples.append(line)
                
                if current_structure:
                    structures.append({
                        'structure': current_structure,
                        'examples': current_examples
                    })
    
    return structures

def extract_examples(soup):
   examples = []
   beispiele = soup.find('h4', string='Beispiele')
   if beispiele:
       content = beispiele.find_next('td')
       if content:
           lines = content.get_text(separator='\n').split('\n')
           for line in lines:
               if '=' in line:
                   # Split explanation from example
                   example, explanation = line.split('=', 1)
                   examples.append({
                       'example': example.strip(),
                       'explanation': explanation.strip('() ')
                   })
               elif line.strip():
                   examples.append({
                       'example': line.strip(),
                       'explanation': ''
                   })
   return examples

def extract_anmerkung(soup):
    annotations = []
    anmerkung = soup.find('h4', string='Anmerkung')
    if not anmerkung:
        return annotations

    td = anmerkung.find_next('td')
    if not td:
        return annotations

    # Find prefix verbs by looking for italicized text
    prefix_blocks = td.find_all('i')
    
    for block in prefix_blocks:
        prefix = block.text.strip()
        examples = []
        
        # Get the next blockquote after this prefix
        example_block = block.find_next('blockquote')
        if example_block:
            examples = [ex.strip() for ex in example_block.stripped_strings]
            
        if prefix and examples:
            annotations.append({
                'prefix': prefix,
                'examples': examples
            })

    return annotations

def extract_wortfamilie(soup):
   word_families = []
   wortfamilie = soup.find('h4', string='Wortfamilie')
   if wortfamilie:
       content = wortfamilie.find_next('td')
       if content:
           text = content.get_text()
           # Split by article words to get new entries
           parts = [part.strip() for part in text.split('die ') if part.strip()]
           parts = [part.strip() for part in ' '.join(parts).split('der ') if part.strip()]
           
           for part in parts:
               if part:
                   if not part.startswith('die') and not part.startswith('der'):
                       word_families.append(f"die {part}")
                   else:
                       word_families.append(part)
                       
   return word_families


def scrape_all_verbs():
   base_url = ""
   main_url = base_url + ""
   
   # Get all verb links
   print("Getting verb list...")
   response = requests.get(main_url)
   soup = BeautifulSoup(response.content, 'html.parser')
   verb_links = soup.select('a[href*="lemma="]')
   
   data = []
   total = len(verb_links)
   
   for i, link in enumerate(verb_links, 1):
       verb = {
           'verb': link.text.strip(),
           'url': base_url + link['href']
       }
       
       print(f"Processing verb {i}/{total}: {verb['verb']}")
       
       try:
           response = requests.get(verb['url'])
           verb_soup = BeautifulSoup(response.content, 'html.parser')
           
           verb_data = {
               'verb': verb['verb'],
               'conjugations_present': ', '.join(extract_conjugations(verb_soup)['present']),
               'conjugations_past': ', '.join(extract_conjugations(verb_soup)['pra']),
               'conjugations_perfect': ', '.join(extract_conjugations(verb_soup)['perfect']),
               'conjugations_imperative': ', '.join(extract_conjugations(verb_soup)['imperative']),
               'structures': '|'.join(f"{s['structure']}: {'; '.join(s['examples'])}" for s in extract_structures(verb_soup)),
               'wortfamilie': ' | '.join(extract_wortfamilie(verb_soup)),
               'prefix_verbs': '|'.join(f"{p['prefix']}: {'; '.join(p['examples'])}" for p in extract_anmerkung(verb_soup))
           }
           
           data.append(verb_data)
           time.sleep(1)  # Polite delay
           
       except Exception as e:
           print(f"Error processing {verb['verb']}: {e}")
           continue
           
   df = pd.DataFrame(data)
   df.to_csv('all_german_verbs.csv', index=False, encoding='utf-8')
   print(f"\nCompleted! Saved {len(data)} verbs to all_german_verbs.csv")
   return df

if __name__ == "__main__":
   scrape_all_verbs()