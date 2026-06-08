# RDF Annotation of Tensile Testing Data
This project processes tensile test JSON data and annotates it using RDF triples with vocabulary from the
[Tensile Test Ontology (TTO)](https://materialdigital.github.io/application-ontologies/tto/). The output is serialized in both 
`.ttl` (Turtle) and `.jsonld` (JSON-LD) formats

## What this does:
- For inputs in JSON format it parses through the tensile test data
- It uses the TTO ontology to create RDF triples effectively describing and annotating the data
- Outputs this linked data in .ttl and .jsonld serialization formats

## How to use:
- Clone the repo to a local environment
- Install dependencies using "pip install -r requirements.txt"
- Open the notebook src/TensileTest_Data_Annotation_Pipeline.ipynb
- Run this notebook to generate RDF triples for each JSON file in the data/FAIRtrain_data_json directory

### Output:

Each input file will output:
- annotated<sample_id>.ttl
- annotated<sample_id>.jsonld

Output will be saved to the output/FAIRtrain directory. 
