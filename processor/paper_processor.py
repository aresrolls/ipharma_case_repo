from google import genai
from google.genai import types
import pathlib
import httpx

GENAI_API_KEY = "AIzaSyBppKTNCkGNFPr0zSddZSuByB2bMtgEByA"

client = genai.Client(api_key=GENAI_API_KEY)

import pandas as pd
import numpy as np


def process_paper(pdf_path: str) -> list:
    filepath = pathlib.Path(pdf_path)
    prompt = f'''
    Analyze this paper with feedback to consuming the drug and extract ALL mentioned symptoms/effects in English.
    Be aware that the patient might mention the disease they consume the drug due to - this symptom shouldn't be included in your response.
    Return ONLY a comma-separated list of standard medical terms.
    Chosse medical term that fits the described side effect best and avoid creating a big number of them.
    Choose EXCLUSIVELY from this list:
    {str(side_effects)}
    As a first word, include the general sentiment of the feedback report - only ONE of [very_good|good|neutral|bad|very_bad],
    as last word, return indications of damaged packaging - ONE of [damaged_pill|missing_pill|damaged_packaging|NONE],
    then place a comma and list all the medical terms. Be aware that a person might express struggles at the start
    of medical treatment, but feel good after time.
    Avoied including same sympton multiple times.
    '''
    # Step 1: Extract symptoms using Gemini
    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=[
            types.Part.from_bytes(
                data=filepath.read_bytes(),
                mime_type='application/pdf'),
            prompt
        ]
    )

    # Step 2: Clean and split symptoms and sentiment
    split_string = response.text.lower().strip().split(', ')
    sentiment = split_string[0]
    symptoms = split_string[1:-1]
    packaging = split_string[-1]

    # Step 3: Map to MedDRA codes
    results = [sentiment]
    for symptom in symptoms:
        matches = meddra_df[meddra_df['side_effect'].str.lower() == symptom]

        if not matches.empty:
            # Group by side_effect and take the first row for each group
            first_match = matches.groupby('side_effect').first().reset_index()

            for _, row in first_match.iterrows():  # Iterate over the first matches only
                results.append({
                    'reported_symptom': symptom,
                    'meddra_term': row['side_effect'],
                    'umls_id': row['meddra_umls'],
                    'concept_type': row['concept_type'],
                    'stitch_ids': f"{row['stitch_flat']}|{row['stitch_stereo']}"
                })
        else:
            results.append({
                'reported_symptom': symptom,
                'meddra_term': None,
                'umls_id': None,
                'concept_type': None,
                'stitch_ids': None
            })
    results.append(packaging)
    return results
