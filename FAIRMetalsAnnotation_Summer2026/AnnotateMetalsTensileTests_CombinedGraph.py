#Acknowledgment
#This work is based on the tensile testing ontology and annotation script developed by Markus Schilling (BAM, Germany).
#This is a standalone script, it does not require any files to already be downloaded locally, and will extract data from https://zenodo.org/api/records/19007867/files/TensileTestProject.zip/content

#Imports
import csv
import os
import json
import zipfile
from urllib.parse import quote

#Check that the required third-party packages are installed, and if not, include installation command.
try:
    import requests
except ImportError:
    raise ImportError(
        "The 'requests' package is required. Install it with:\n"
        "pip install requests"
    )

try:
    import rdflib
except ImportError:
    raise ImportError(
        "The 'rdflib' package is required. Install it with:\n"
        "pip install rdflib"
    )

try:
    import jsonschema
except ImportError:
    raise ImportError(
        "The 'jsonschema' package is required. Install it with:\n"
        "pip install jsonschema"
    )

#Once the correct packages are installed, import the necessary classes
from rdflib import (
    Graph, #Graph stores RDF triples
    Namespace, #Namespace creates ontology prefixes
    Literal, #Literal represents data values
    URIRef, #URIRef creates unique identifiers
)
from rdflib.namespace import (
    RDF, #RDF provides core RDF terms
    XSD, #XSD provides standard datatypes so we can work with literals
    OWL #OWL provides ontology vocabulary
)
from jsonschema import (
    validate, #validate checks JSON file against a JSON validation schema
    ValidationError #ValidationError alerts of JSON validation schema violations
)

#This contains the Zenodo API URL, format in the form: https://zenodo.org/api/records/{RECORD_ID}
api_url = "https://zenodo.org/api/records/19007867"

#Once the data is downloaded, it will be stored in a directory. Name can be adjusted below.
data_dir = "importedData"

#This zip path lets the script know where to unzip the downloaded data from.
zip_path = os.path.join(data_dir, "dataset.zip")

#This function retrieves the zip file from the API URL, format in the form: https://zenodo.org/api/records/{RECORD_ID}
def get_zenodo_file_url(api_url):
    response = requests.get(api_url)
    response.raise_for_status()
    data = response.json()
    if not data.get("files"):
        raise Exception("No files found in Zenodo record.")

    #Search for the zip file to download
    for file in data["files"]:
        if file["key"].endswith(".zip"):
            print(f"Found zip file: {file['key']}")
            return file["links"]["self"]

#This function will look for the jsonFiles directory to download and extract from it
def download_and_extract(data_dir):
    #If the data directory with given name from data_dir does not exist, will create it.
    os.makedirs(data_dir, exist_ok=True)
    #Check if the dataset is already locally available, if so, skip the download.
    for root, dirs, files in os.walk(data_dir):
        if "jsonFiles" in dirs:
            print("Dataset already available, skipping download.")
            return
    #Begin downloading
    print("Downloading dataset from Zenodo...")
    file_url = get_zenodo_file_url(api_url)
    print(f"Downloading from: {file_url}")
    #Send HTTP get request
    response = requests.get(file_url, stream=True)
    #Check if successful
    response.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)
    #If so, extract all the data, and place all the files into the data directory.
    print("Download complete. Extracting...")
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        zip_ref.extractall(data_dir)
    print("Extraction complete.")

#Run the function to ensure the data is available to work on locally.
download_and_extract(data_dir)

#Set input directory to the directory that contains the jsonFiles.
#Note that if data was already local, dir must be named jsonFiles.
input_dir = None
for root, dirs, files in os.walk(data_dir):
    if "jsonFiles" in dirs:
        input_dir = os.path.join(root, "jsonFiles")
        break
if input_dir is None:
    raise FileNotFoundError("Could not find 'jsonFiles' directory after extraction.")

#Output directory names for the annotated jsonld, ttl, and csv files. If they don't exist, this will create them.
output_dir_jsonld = "outputCombinedGraph/annotated_metals_jsonld"
output_dir_ttl = "outputCombinedGraph/annotated_metals_ttl"
output_dir_csv = "outputCombinedGraph/metals_csv_data"
os.makedirs(output_dir_jsonld, exist_ok=True)
os.makedirs(output_dir_ttl, exist_ok=True)
os.makedirs(output_dir_csv, exist_ok=True)

#A JSON Schema Draft 07 helps describe the structure of JSON data. Used for validation of the input data.
#Note that schema defines the structure the data must be in the format of.
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
        "material",
        "Geometry",
        "youngs_modulus",
        "yield_strength",
        "strain_at_fracture",
        "raw_data"
    ]
}

#Empty graph to store triples
g = Graph()

#Define ontology namespaces. This helps us access and reference them throughout the script.
TTO = Namespace("https://materialdigital.github.io/application-ontologies/tto/#/")  #Tensile testing ontology terms
PMD = Namespace("https://materialdigital.github.io/core-ontology/") #Core terms for materials science and engineering
QUDT = Namespace("http://qudt.org/vocab/unit/") #Measurment units
OBO = Namespace("http://purl.obolibrary.org/obo/") #Reusable scientific vocabulary terms
CSVW = Namespace("http://www.w3.org/ns/csvw#") #CSV metadata terms
DC = Namespace("http://purl.org/dc/terms/") #Metadata such as title, date, etc

#Bind namespace prefixes to the graph. This makes our RDF output more readable.
g.bind("tto", TTO)
g.bind("pmd", PMD)
g.bind("qudt", QUDT)
g.bind("obo", OBO)
g.bind("csvw", CSVW)
g.bind("dc", DC)

#Define base namespace according to API URL. This allows us to create URIs (unique identifiers) for annotated entities.
prefix = Namespace(api_url)
g.bind("prefix", prefix)

#Create an ontology entity, and import ontologies vocabulary so we can them it to annotate tensile testing data.
onto = URIRef(prefix) #We need to create an ontology entity to enforce that our RDF file is an ontology based dataset.
g.add((onto, RDF.type, OWL.Ontology))
for ns in [TTO, PMD, QUDT, OBO, CSVW, DC]:
    g.add((onto, OWL.imports, URIRef(ns)))

#Adding metadata to describe the ontology entity.
g.add((onto, DC.title, Literal("Tensile Test Ontology (TTO) A-Box Data Mapping Example", datatype=XSD.string)))
g.add((onto, OWL.versionInfo, Literal("3.0.0", datatype=XSD.string)))
g.add((onto, DC.description, Literal("This is an exemplary A-Box (instance data) representing tensile test results performed on an metal samples according to ISO 6892-1:2019-11. The data originates from a publicly available dataset hosted on Zenodo: https://zenodo.org/records/19007867. The semantic structure is based on the Tensile Test Ontology (TTO) version 3.0 (https://github.com/materialdigital/tensile-test-ontology), complemented primarily by concepts from the PMD Core Ontology (PMDco).", datatype=XSD.string)))

#Loop through each JSON file in the input directory
for filename in os.listdir(input_dir):
    print(f"Beginning JSON validation and annotation for file: {filename}.")
    if filename.endswith(".json"):
        filepath = os.path.join(input_dir, filename)

        with open(filepath) as f:
            data = json.load(f)

            #Validate the data before annotating
            try:
                validate(instance=data, schema=schema)
            except ValidationError as e:
                print(f"\nValidation failed for file: {filename}")
                print(f"Error: {e.message}")
                continue  #Skip this file and move to next

            #First, read in all the lines and save the variables.
            process_id = quote(data["sample"])
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

            # Make uris
            # Represents the experiment
            experimentIRI = URIRef(prefix + process_id)
            g.add((experimentIRI, RDF.type, OBO.IAO_0020000))  # ExperimentIRI is an identifier

            # Represents the process
            processIRI = URIRef(experimentIRI + "_process")
            g.add((processIRI, RDF.type, PMD.PMD_0000974))  # ProcessIRI is a tensile testing process
            g.add((experimentIRI, OBO.IAO_0000219, processIRI))  # ExperimentIRI denotes tensile testing process

            # Represents the test piece
            testPieceIRI = URIRef(experimentIRI + "_test_piece")
            g.add((testPieceIRI, RDF.type, PMD.PMD_0000975))  # is of test piece role
            g.add((processIRI, PMD.OBI_0000293, testPieceIRI))  # ProcessIRI has specified input test piece

            # Maps to Original Thickness from TTO
            # Thickness quality
            thicknessIRI_quality = URIRef(experimentIRI + "_thickness_quality")
            g.add((thicknessIRI_quality, RDF.type, TTO.TTO_0000029))  # is original thickness
            g.add((processIRI, OBO.RO_0002234, thicknessIRI_quality))  # processIRI has output thickness
            g.add((testPieceIRI, PMD.PMD_0025998, thicknessIRI_quality))  # Test piece has relational quality thickness
            # Thickness specification
            thicknessIRI_scalar_value = URIRef(experimentIRI + "_thickness_scalar_value_specification")
            g.add((thicknessIRI_scalar_value, RDF.type, OBO.OBI_0001931))  # is a scalar value specification
            g.add((thicknessIRI_scalar_value, PMD.PMD_0000006, Literal(thickness, datatype=XSD.float)))  # has value literal
            g.add((thicknessIRI_scalar_value, OBO.IAO_0000039, QUDT.MilliM))  # has unit MilliM
            g.add((thicknessIRI_scalar_value, OBO.OBI_0001927, thicknessIRI_quality))  # Scalar value specifies value of quality thickness
            g.add((thicknessIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            # Maps to Original Width from TTO
            # Width quality
            widthIRI_quality = URIRef(experimentIRI + "_width_quality")
            g.add((widthIRI_quality, RDF.type, TTO.TTO_0000030))  # is original width
            g.add((processIRI, OBO.RO_0002234, widthIRI_quality))  # processIRI has output width
            g.add((testPieceIRI, PMD.PMD_0025998, widthIRI_quality))  # Test piece has relational quality width
            # Width scalar value specification
            widthIRI_scalar_value = URIRef(experimentIRI + "_width_scalar_value_specification")
            g.add((widthIRI_scalar_value, RDF.type, OBO.OBI_0001931))  # is a scalar value specification
            g.add((widthIRI_scalar_value, PMD.PMD_0000006, Literal(width, datatype=XSD.float)))  # has value literal
            g.add((widthIRI_scalar_value, OBO.IAO_0000039, QUDT.MilliM))  # has unit mm
            g.add((widthIRI_scalar_value, OBO.OBI_0001927, widthIRI_quality))  # Scalar value specifies value of quality width
            g.add((widthIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            # Maps to Original Gauge Length from TTO
            # Gauge length quality
            lengthIRI_quality = URIRef(experimentIRI + "_gauge_length_quality")
            g.add((lengthIRI_quality, RDF.type, TTO.TTO_0000028))  # is an original gauge length
            g.add((processIRI, OBO.RO_0002234, lengthIRI_quality))  # processIRI has output quality length
            g.add((testPieceIRI, PMD.PMD_0025998, lengthIRI_quality))  # Test piece has relational quality gauge length
            # Gauge length specification
            lengthIRI_scalar_value = URIRef(experimentIRI + "_gauge_length_scalar_value_specification")
            g.add((lengthIRI_scalar_value, RDF.type, OBO.OBI_0001931))  # is a scalar value specification
            g.add((lengthIRI_scalar_value, PMD.PMD_0000006, Literal(gauge_length, datatype=XSD.float)))  # has value literal
            g.add((lengthIRI_scalar_value, OBO.IAO_0000039, QUDT.MilliM))  # has unit MilliM
            g.add((lengthIRI_scalar_value, OBO.OBI_0001927, lengthIRI_quality))  # Scalar value specifies value of quality length
            g.add((lengthIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            # Maps to Elastic Modulus from PMD
            # Elastic modulus quality
            ymIRI_quality = URIRef(experimentIRI + "_youngs_modulus_quality")
            g.add((ymIRI_quality, RDF.type, PMD.PMD_0000618))  # is an elastic modulus
            g.add((processIRI, OBO.RO_0002234, ymIRI_quality))  # processIRI has output elastic modulus
            g.add((testPieceIRI, PMD.PMD_0025998, ymIRI_quality))  # Test piece has relational quality elastic modulus
            # Elastic modulus specification
            ymIRI_scalar_value = URIRef(experimentIRI + "_youngs_modulus_scalar_value_specification")
            g.add((ymIRI_scalar_value, RDF.type, OBO.OBI_0001931))  # is a scalar value specification
            g.add((ymIRI_scalar_value, PMD.PMD_0000006, Literal(ymVal, datatype=XSD.float)))  # has value literal
            g.add((ymIRI_scalar_value, OBO.IAO_0000039, QUDT.MegaPa))  # has unit MegaPa
            g.add((ymIRI_scalar_value, OBO.OBI_0001927, ymIRI_quality))  # Scalar value specifies value of quality elastic modulus
            g.add((ymIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            # Maps to Force at proof strength plastic extension f02 from TTO
            # Force at proof strength plastic extension f02 quality
            ysIRI_quality = URIRef(experimentIRI + "_yield_strength_quality")
            g.add((ysIRI_quality, RDF.type, TTO.TTO_0000042))  # is a Force at proof strength plastic extension f02
            g.add((processIRI, OBO.RO_0002234, ysIRI_quality))  # processIRI has output Force at proof strength plastic extension f02
            g.add((testPieceIRI, PMD.PMD_0025998, ysIRI_quality))  # Test piece has relational quality Force at proof strength plastic extension f02
            # Force at proof strength plastic extension f02 specification
            ysIRI_scalar_value = URIRef(experimentIRI + "_yield_strength_scalar_value_specification")
            g.add((ysIRI_scalar_value, RDF.type, OBO.OBI_0001931))  # is a scalar value specification
            g.add((ysIRI_scalar_value, PMD.PMD_0000006, Literal(ysVal, datatype=XSD.float)))  # has value literal
            g.add((ysIRI_scalar_value, OBO.IAO_0000039, QUDT.MegaPa))  # has unit MegaPa
            g.add((ysIRI_scalar_value, OBO.OBI_0001927, ysIRI_quality))  # Scalar value specifies value of quality Force at proof strength plastic extension f02
            g.add((ysIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            # Maps to Percentage Total Extension at Fracture from TTO
            # Strain at fracture quality
            safIRI_quality = URIRef(experimentIRI + "_strain_at_fracture_quality")
            g.add((safIRI_quality, RDF.type, TTO.TTO_0000039))  # is a PercentageTotalExtensionAtFracture
            g.add((processIRI, OBO.RO_0002234, safIRI_quality))  # processIRI has output percentage total extension at fracture
            g.add((testPieceIRI, PMD.PMD_0025998, safIRI_quality))  # Test piece has relational quality strain at fracture
            # Strain at fracture specification
            safIRI_scalar_value = URIRef(experimentIRI + "_strain_at_fracture_value_specification")
            g.add((safIRI_scalar_value, RDF.type, OBO.OBI_0001931))  # is a scalar value specification
            g.add((safIRI_scalar_value, PMD.PMD_0000006, Literal(safVal, datatype=XSD.float)))  # has value literal
            g.add((safIRI_scalar_value, OBO.IAO_0000039, Literal(safUnit)))  # has unit mm/mm
            g.add((safIRI_scalar_value, OBO.OBI_0001927, safIRI_quality))  # Scalar value specifies value of quality strain at fracture
            g.add((safIRI_scalar_value, OBO.IAO_0000136, testPieceIRI))  # is about test piece

            #Create CSV files for each of the JSON input files to represent the Force and Elongation pairs
            csv_filename = os.path.join(output_dir_csv, process_id + "_data.csv")
            with open(csv_filename, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Force(N)", "Elongation(mm)"])  # header

                # zip() pairs the 1st force with the 1st elongation, then the 2nd, etc.
                for f_val, e_val in zip(forces, elongations):
                    writer.writerow([f_val, e_val])

            #Represents the dataset
            datasetIRI = URIRef(experimentIRI + "_dataset")
            g.add((processIRI, PMD.PMD_0000016, datasetIRI)) #processIRI has output dataset datasetIRI
            g.add((datasetIRI, RDF.type, CSVW.Table)) # is a table
            csv_name = process_id + "_data.csv"
            g.add((datasetIRI, CSVW.url, URIRef(f"https://zenodo.org/records/19007867/files/{csv_name}")))
            g.add((datasetIRI, RDF.type, OBO.IAO_0000109)) # is a measurement datum
            g.add((datasetIRI, DC.title, Literal(process_id + "Force Elongation Curve", datatype=XSD.string)))
            #Make a schema to connect the columns to
            schemaIRI = URIRef(experimentIRI + "_table_schema")
            g.add((datasetIRI, CSVW.tableSchema, schemaIRI))
            g.add((schemaIRI, RDF.type, CSVW.Schema))
            # Column 1: Force
            forceColumnIRI = URIRef(experimentIRI + "_force_column")
            g.add((schemaIRI, CSVW.column, forceColumnIRI))
            g.add((forceColumnIRI, RDF.type, CSVW.Column))  # is a column
            g.add((forceColumnIRI, CSVW.name, Literal("Force(N)")))
            g.add((forceColumnIRI, OBO.IAO_0000039, QUDT.N))  # has unit N
            g.add((forceColumnIRI, CSVW.propertyUrl,
                   PMD.PMD_0020200))  # Every value in the column corresponds to Force from PMD
            # Column 2: Elongation
            elongationColumnIRI = URIRef(experimentIRI + "_elongation_column")
            g.add((schemaIRI, CSVW.column, elongationColumnIRI))
            g.add((elongationColumnIRI, RDF.type, CSVW.Column))
            g.add((elongationColumnIRI, CSVW.name, Literal("Elongation(mm)")))
            g.add((elongationColumnIRI, OBO.IAO_0000039, QUDT.MilliM))  # has unit mm
            g.add((elongationColumnIRI, CSVW.propertyUrl, TTO.TTO_0000004))  # Every value in the column corresponds to elongation from TTO
            print("Annotation complete.")

#Serializing in jsonld and ttl
g.serialize(os.path.join(output_dir_jsonld, "annotated_all_tests.jsonld"), format="json-ld")
g.serialize(os.path.join(output_dir_ttl, "annotated_all_tests.ttl"), format="turtle")
print("Serialization complete.")
print("Annotated data will be found at output directory.")
