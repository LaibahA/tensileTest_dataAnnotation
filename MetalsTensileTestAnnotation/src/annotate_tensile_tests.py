#Acknowledgment
#This work is based on the tensile testing ontology and annotation script developed by Markus Schilling (BAM, Germany).

import csv
import os, json
import requests
import zipfile

try:
    import rdflib
except ImportError:
    raise ImportError(
        "rdflib is required. Install it with: pip install rdflib"
    )

from rdflib import Graph, Namespace, Literal, URIRef, DC
#Graph stores the RDF triples, Namespace is what lets us define the prefixes
from rdflib.namespace import RDF, XSD, OWL
#RDF is for the standard datatypes, XSD is for formatting literals
from urllib.parse import quote

try:
    import jsonschema
except ImportError:
    raise ImportError(
        "jsonschema is required. Install it with: pip install jsonschema"
    )
from jsonschema import validate, ValidationError

api_url = "https://zenodo.org/api/records/19007867"
data_dir = "importedData"
zip_path = os.path.join(data_dir, "dataset.zip")

def get_zenodo_file_url():
    api_url = "https://zenodo.org/api/records/19007867"
    response = requests.get(api_url)
    response.raise_for_status()
    data = response.json()
    if not data.get("files"):
        raise Exception("No files found in Zenodo record.")

    # Look for zip file to download
    for file in data["files"]:
        if file["key"].endswith(".zip"):
            print(f"Found zip file: {file['key']}")
            return file["links"]["self"]

# This function will look for the jsonFiles directory to download and extract from it
def download_and_extract():
    os.makedirs(data_dir, exist_ok=True)
    # Check if already exists
    for root, dirs, files in os.walk(data_dir):
        if "jsonFiles" in dirs:
            print("Dataset already available, skipping download.")
            return
    #Or start download process
    print("Downloading dataset from Zenodo...")
    file_url = get_zenodo_file_url()
    print(f"Downloading from: {file_url}")
    #Send HTTP get request
    response = requests.get(file_url, stream=True)
    #Check if successfull
    response.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Download complete. Extracting...")
    #Unpack all the files into data_dir
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(data_dir)
    print("Extraction complete.")

#Run the download function
download_and_extract()

#Input and output directories
input_dir = None
for root, dirs, files in os.walk(data_dir):
    if "jsonFiles" in dirs:
        input_dir = os.path.join(root, "jsonFiles")
        #input_dir = "../data/metals_dictionaries"
        break
if input_dir is None:
    raise FileNotFoundError("Could not find 'jsonFiles' directory after extraction.")

output_dir_jsonld = "../output/annotated_metals_jsonld"
output_dir_ttl = "../output/annotated_metals_ttl"
output_dir_csv = "../output/metals_csv_data"
os.makedirs(output_dir_jsonld, exist_ok=True)
os.makedirs(output_dir_ttl, exist_ok=True)
os.makedirs(output_dir_csv, exist_ok=True)


#JSON schema (Draft 07) to validate the data before annotating
schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "sample": {"type": "string", "minLength": 1},
        "date": {"type": "string", "format": "date"},
        "material": {"type": "string"},

        "Geometry": {
            "type": "object",
            "properties": {
                "width": {"type": "number"},
                "thickness": {"type": "number"},
                "gauge_length": {"type": "number"}
            },
            "required": ["width", "thickness", "gauge_length"]
        },

        "youngs_modulus": {
            "type": "object",
            "properties": {
                "value": {"type": "number"},
                "reference": {"type": "string"},
                "units": {"type": "string"}
            },
            "required": ["value", "reference", "units"]
        },

        "yield_strength": {
            "type": "object",
            "properties": {
                "value": {"type": "number"},
                "reference": {"type": "string"},
                "units": {"type": "string"}
            },
            "required": ["value", "reference", "units"]
        },

        "strain_at_fracture": {
            "type": "object",
            "properties": {
                "value": {"type": "number"},
                "reference": {"type": "string"},
                "units": {"type": "string"}
            },
            "required": ["value", "reference", "units"]
        },

        "raw_data": {
            "type": "object",
            "properties": {
                "load": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 1
                },
                "displacement": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 1
                }
            },
            "required": ["load", "displacement"]
        }
    },

    "required": [
        "sample",
        "date",
        "material",
        "Geometry",
        "youngs_modulus",
        "yield_strength",
        "strain_at_fracture",
        "raw_data"
    ]
}

g = Graph()  #Empty graph to store triples

TTO = Namespace("https://materialdigital.github.io/application-ontologies/tto/#/")  #TTO is the namespace for the ontology
PMD = Namespace("https://materialdigital.github.io/core-ontology/")
QUDT = Namespace("http://qudt.org/vocab/unit/")
OBO = Namespace("http://purl.obolibrary.org/obo/")
CSVW = Namespace("http://www.w3.org/ns/csvw#")
DCT = Namespace("http://purl.org/dc/terms/")

g.bind("tto", TTO)  #Base
g.bind("pmd", PMD)
g.bind("qudt", QUDT)
g.bind("obo", OBO)
g.bind("csvw", CSVW)
g.bind("dct", DCT)

prefix = Namespace("https://zenodo.org/records/19007867/")  #This is what builds the uri for our subject to annotate.
g.bind("prefix", prefix)

#Create ontology using TTO as basis
onto = URIRef(prefix)
g.add((onto, RDF.type, OWL.Ontology))
g.add((onto, OWL.imports, URIRef(TTO)))

g.add((onto, DC.title, Literal("Tensile Test Ontology (TTO) A-Box Data Mapping Example", datatype=XSD.string)))
g.add((onto, OWL.versionInfo, Literal("3.0.0", datatype=XSD.string)))
g.add((onto, DCT.description, Literal("This is an exemplary A-Box (instance data) representing tensile test results performed on an metal samples according to ISO 6892-1:2019-11. The data originates from a publicly available dataset hosted on Zenodo: TBD. The semantic structure is based on the Tensile Test Ontology (TTO) version 3.0 (https://github.com/materialdigital/tensile-test-ontology), complemented by concepts from the PMD Core Ontology (PMDco).", datatype=XSD.string)))


#Loop through each JSON file in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        filepath = os.path.join(input_dir, filename)

        with open(filepath) as f:
            data = json.load(f) #Makes the list of rows
            #Validate the data before annotating
            try:
                validate(instance=data, schema=schema)
            except ValidationError as e:
                print(f"\nValidation failed for file: {filename}")
                print(f"Error: {e.message}")
                continue  # Skip this file and move to next


            #First, read in all the lines and save the variables.
            process_id = quote(data["sample"])
            date = data["date"]
            material = data["material"]
            width = data["Geometry"]["width"]
            thickness = data["Geometry"]["thickness"]
            gauge_length = data["Geometry"]["gauge_length"]
            ymVal = data["youngs_modulus"]["value"]
            ymRef = data["youngs_modulus"]["reference"]
            ymUnit = data["youngs_modulus"]["units"]
            ysVal = data["yield_strength"]["value"]
            ysRef = data["yield_strength"]["reference"]
            ysUnit = data["yield_strength"]["units"]
            safVal = data["strain_at_fracture"]["value"]
            safRef = data["strain_at_fracture"]["reference"]
            safUnit = data["strain_at_fracture"]["units"]
            forces = data["raw_data"]["load"]
            elongations = data["raw_data"]["displacement"]

            #Make uris
            #experimentIRI is prefix + sample name
            experimentIRI = URIRef(prefix + process_id)
            g.add((experimentIRI, RDF.type, PMD.PMD_0000017)) #ExperimentIRI is an identifier

            #processIRI
            processIRI = URIRef(experimentIRI + "_process")
            g.add((processIRI, RDF.type, PMD.PMD_0000974)) #ProcessIRI is a tensile testing process
            g.add((experimentIRI, OBO.IAO_0000219, processIRI))  # ExperimentIRI denotes tensile testing process

            testPieceIRI = URIRef(experimentIRI + "_test_piece")
            g.add((testPieceIRI, RDF.type, TTO.TTO_0000055))
            g.add((processIRI, PMD.PMD_0000015, testPieceIRI)) #ProcessIRI has input test piece

            #Thickness quality
            thicknessIRI_quality = URIRef(experimentIRI + "_thickness_quality")
            g.add((thicknessIRI_quality, RDF.type, TTO.OriginalThickness))  # is an OriginalThickness
            g.add((processIRI, PMD.PMD_0000016, thicknessIRI_quality))  # processIRI has output quality thickness
            g.add((testPieceIRI, OBO.BFO_0000196, thicknessIRI_quality))  # Test piece bears the quality of thickness
            #Thickness specification
            thicknessIRI_scalar_value = URIRef(experimentIRI + "_thickness_scalar_value_specification")
            g.add((thicknessIRI_scalar_value, RDF.type, PMD.PMD_0000022))  # is a scalar value specification
            g.add((thicknessIRI_scalar_value, PMD.PMD_0000006, Literal(thickness, datatype=XSD.float)))  # has value literal
            g.add((thicknessIRI_scalar_value, OBO.IAO_0000039, QUDT.MilliM)) # has unit MilliM
            g.add((thicknessIRI_scalar_value, PMD.PMD_0060001, thicknessIRI_quality))  # Scalar value specifies value of quality thickness
            g.add((thicknessIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            # Width quality
            widthIRI_quality = URIRef(experimentIRI + "_width_quality")
            g.add((widthIRI_quality, RDF.type, TTO.OriginalWidth))  # is an OriginalWidth
            g.add((processIRI, PMD.PMD_0000016, widthIRI_quality))  # processIRI has output quality width
            g.add((testPieceIRI, OBO.BFO_0000196, widthIRI_quality))  # Test piece bears the quality of width
            # Width scalar value specification
            widthIRI_scalar_value = URIRef(experimentIRI + "_width_scalar_value_specification")
            g.add((widthIRI_scalar_value, RDF.type, PMD.PMD_0000022))  # is a scalar value specification
            g.add((widthIRI_scalar_value, PMD.PMD_0000006, Literal(width, datatype=XSD.float)))  # has value literal
            g.add((widthIRI_scalar_value, OBO.IAO_0000039, QUDT.MilliM))  # has unit mm
            g.add((widthIRI_scalar_value, PMD.PMD_0060001,
                   widthIRI_quality))  # Scalar value specifies value of quality width
            g.add((widthIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            #Gauge length quality
            lengthIRI_quality = URIRef(experimentIRI + "_gauge_length_quality")
            g.add((lengthIRI_quality, RDF.type, TTO.OriginalGaugeLength))  # is an OriginalGaugeLength
            g.add((processIRI, PMD.PMD_0000016, lengthIRI_quality))  # processIRI has output quality length
            g.add((testPieceIRI, OBO.BFO_0000196, lengthIRI_quality))  # Test piece bears the quality of gauge length
            #Gauge length specification
            lengthIRI_scalar_value = URIRef(experimentIRI + "_gauge_length_scalar_value_specification")
            g.add((lengthIRI_scalar_value, RDF.type, PMD.PMD_0000022))  # is a scalar value specification
            g.add((lengthIRI_scalar_value, PMD.PMD_0000006,Literal(gauge_length, datatype=XSD.float)))  # has value literal
            g.add((lengthIRI_scalar_value, OBO.IAO_0000039, QUDT.MilliM)) # has unit MilliM
            g.add((lengthIRI_scalar_value, PMD.PMD_0060001, lengthIRI_quality))  # Scalar value specifies value of quality length
            g.add((lengthIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            #Youngs modulus quality
            ymIRI_quality = URIRef(experimentIRI + "_youngs_modulus_quality")
            g.add((ymIRI_quality, RDF.type, TTO.SlopeOfTheElasticPart))  # is a SlopeOfTheElasticPart
            g.add((processIRI, PMD.PMD_0000016, ymIRI_quality))  # processIRI has output quality youngs modulus
            g.add((testPieceIRI, OBO.BFO_0000196, ymIRI_quality))  # Test piece bears the property of youngs modulus
            #Youngs modulus specification
            ymIRI_scalar_value = URIRef(experimentIRI + "_youngs_modulus_scalar_value_specification")
            g.add((ymIRI_scalar_value, RDF.type, PMD.PMD_0000022))  # is a scalar value specification
            g.add((ymIRI_scalar_value, PMD.PMD_0000006, Literal(ymVal, datatype=XSD.float)))  # has value literal
            g.add((ymIRI_scalar_value, OBO.IAO_0000039, QUDT.MegaPa)) # has unit MegaPa
            g.add((ymIRI_scalar_value, PMD.PMD_0060001,ymIRI_quality))  # Scalar value specifies value of quality youngs modulus
            g.add((ymIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            #Yield Strength quality
            ysIRI_quality = URIRef(experimentIRI + "_yield_strength_quality")
            g.add((ysIRI_quality, RDF.type, TTO.YieldStrength))  # is a YieldStrength
            g.add((processIRI, PMD.PMD_0000016, ysIRI_quality))  # processIRI has output quality yield strength
            g.add((testPieceIRI, OBO.BFO_0000196, ysIRI_quality))  # Test piece bears the property of yield strength
            #Yield Strength specification
            ysIRI_scalar_value = URIRef(experimentIRI + "_yield_strength_scalar_value_specification")
            g.add((ysIRI_scalar_value, RDF.type, PMD.PMD_0000022))  # is a scalar value specification
            g.add((ysIRI_scalar_value, PMD.PMD_0000006, Literal(ysVal, datatype=XSD.float)))  # has value literal
            g.add((ysIRI_scalar_value, OBO.IAO_0000039, QUDT.MegaPa)) # has unit MegaPa
            g.add((ysIRI_scalar_value, PMD.PMD_0060001, ysIRI_quality))  # Scalar value specifies value of quality yield strength
            g.add((ysIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            #Strain at fracture quality
            safIRI_quality = URIRef(experimentIRI + "_strain_at_fracture_quality")
            g.add((safIRI_quality, RDF.type, TTO.PercentageTotalExtensionAtFracture))  # is a PercentageTotalExtensionAtFracture
            g.add((processIRI, PMD.PMD_0000016, safIRI_quality))  # processIRI has output quality percentage total extension at fracture
            g.add((testPieceIRI, OBO.BFO_0000196, safIRI_quality))  # Test piece bears the quality of strain at fracture
            #Strain at fracture specification
            safIRI_scalar_value = URIRef(experimentIRI + "_strain_at_fracture_value_specification")
            g.add((safIRI_scalar_value, RDF.type, PMD.PMD_0000022))  # is a scalar value specification
            g.add((safIRI_scalar_value, PMD.PMD_0000006, Literal(safVal, datatype=XSD.float)))  # has value literal
            g.add((safIRI_scalar_value, OBO.IAO_0000039, Literal(safUnit)))  # has unit mm/mm
            g.add((safIRI_scalar_value, PMD.PMD_0060001, safIRI_quality))  # Scalar value specifies value of quality strain at fracture
            g.add((safIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            csv_filename = os.path.join(output_dir_csv, process_id + "_data.csv")
            with open(csv_filename, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Force(N)", "Elongation(mm)"])  # header

                # zip() pairs the 1st force with the 1st elongation, then the 2nd, etc.
                for f_val, e_val in zip(forces, elongations):
                    writer.writerow([f_val, e_val])

            datasetIRI = URIRef(experimentIRI + "_dataset")
            g.add((processIRI, PMD.PMD_0000016, datasetIRI)) #processIRI has output dataset datasetIRI
            g.add((datasetIRI, RDF.type, CSVW.Table)) # is a table
            csv_name = process_id + "_data.csv"
            g.add((datasetIRI, CSVW.url, URIRef(f"https://zenodo.org/records/19007867/files/{csv_name}")))
            #g.add((datasetIRI, CSVW.url, URIRef(https://zenodo.org/records/12345678/files/{csv_name}")))
            g.add((datasetIRI, RDF.type, OBO.IAO_0000109)) # is a measurement datum
            g.add((datasetIRI, DC.title,
                   Literal(process_id + " Force Displacement Curve", datatype=XSD.string)))

#Serializing in jsonld and ttl
g.serialize(os.path.join(output_dir_jsonld, "annotated_all_tests.jsonld"), format="json-ld")
g.serialize(os.path.join(output_dir_ttl, "annotated_all_tests.ttl"), format="turtle")
