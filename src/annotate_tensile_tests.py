import csv
import os, json

from rdflib import Graph, Namespace, Literal
#Graph stores the RDF triples, Namespace is what lets us define the prefixes
from rdflib.namespace import RDF, XSD
#RDF is for the standard datatypes, XSD is for formatting literals

#Input and output directories
input_dir = "../data/FAIRtrain_data_json"
#input_dir = "../data/FAIRtrain_example"
output_dir_jsonld = "../output/annotatedBy_TTO/jsonld_output"
output_dir_ttl = "../output/annotatedBy_TTO/ttl_output"
output_dir_csv = "../output/csv_data"
os.makedirs(output_dir_jsonld, exist_ok=True)
os.makedirs(output_dir_ttl, exist_ok=True)
os.makedirs(output_dir_csv, exist_ok=True)

g = Graph()  #Empty graph to store triples

TTO = Namespace("https://materialdigital.github.io/application-ontologies/tto/#/")  #TTO is the namespace for the ontology
PMD = Namespace("https://materialdigital.github.io/core-ontology/")
QUDT = Namespace("http://qudt.org/vocab/unit/")
BFO = Namespace("http://purl.obolibrary.org/obo/")
CSVW = Namespace("http://www.w3.org/ns/csvw#")

g.bind("tto", TTO)  #Binding namespace to prefix, makes it easier to use
g.bind("pmd", PMD)
g.bind("qudt", QUDT)
g.bind("bfo", BFO)
g.bind("csvw", CSVW)

'''
Need to update namespace below to our domain
'''
EX = Namespace("http://example.org/tensile/")  #This is an example, its gna be what builds the uri for our subject to annotate.
g.bind("ex", EX)

#Loop through each JSON file in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        filepath = os.path.join(input_dir, filename)

        with open(filepath) as f:
            data = json.load(f) #Makes the list of rows

            #Make uris
            sample_id = data["sample_id"]
            test_uri = EX[sample_id]
            test_piece_id = sample_id.split("_")[2]
            test_piece_uri = EX["testPiece_" + test_piece_id]
            machine_uri = EX[data["sample_id"][:6]]

            #Declare test, test machine, and test piece
            g.add((test_uri, RDF.type, TTO.TensileTest))
            g.add((test_piece_uri, RDF.type, PMD.TestPiece))
            g.add((machine_uri, RDF.type, TTO.TensileTestingMachine))

            #Establish relationships between tensile test to test piece and machine
            g.add((test_uri, PMD.input, test_piece_uri))
            g.add((test_uri, PMD.input, machine_uri))

            #Original width
            #Creating a node to represent the concept of width for our data
            width_node = EX[f"{sample_id}_width"]
            #Saying this node (subject) is a (predicate) object of this type (object)
            g.add((width_node, RDF.type, TTO.OriginalWidth))
            #Saying this node (subject) has value (predicate) of this float (object)
            g.add((width_node, PMD.value, Literal(data["width"], datatype=XSD.float)))
            #Saying this node (subject) has unit (predicate) of this unit type (object)
            g.add((width_node, PMD.unit, QUDT.MilliM))
            #Saying this node (subject) is a characteristic of (predicate) the test piece (object)
            g.add((width_node, PMD.characteristic, test_piece_uri))

            #Original thickness
            thickness_node = EX[f"{sample_id}_thickness"]
            g.add((thickness_node, RDF.type, TTO.OriginalThickness))
            g.add((thickness_node, PMD.value, Literal(data["thickness"], datatype=XSD.float)))
            g.add((thickness_node, PMD.unit, QUDT.MilliM))
            g.add((thickness_node, PMD.characteristic, test_piece_uri))

            #Gauge length
            length_node = EX[f"{sample_id}_length"]
            g.add((length_node, RDF.type, TTO.OriginalGaugeLength))
            g.add((length_node, PMD.value, Literal(data["length"], datatype=XSD.float)))
            g.add((length_node, PMD.unit, QUDT.MilliM))
            g.add((length_node, PMD.characteristic, test_piece_uri))

            #Youngs modulus / slope of the elastic part
            youngs_mod_node = EX[f"{sample_id}_youngs_modulus"]
            g.add((youngs_mod_node, RDF.type, TTO.SlopeOfTheElasticPart))
            g.add((youngs_mod_node, PMD.value, Literal(data["extracted_properties"]["youngs_modulus"], datatype=XSD.float)))
            g.add((youngs_mod_node, PMD.unit, QUDT.MegaPa))
            g.add((test_uri, PMD.output, youngs_mod_node))

            #Ultimate tensile strength / upper yield strength
            ult_tensile_strength = EX[f"{sample_id}_ultimate_tensile_strength"]
            g.add((ult_tensile_strength, RDF.type, TTO.UpperYieldStrength))
            g.add((ult_tensile_strength, PMD.value, Literal(data["extracted_properties"]["ultimate_tensile_strength"], datatype=XSD.float)))
            g.add((ult_tensile_strength, PMD.unit, QUDT.MegaPa))
            g.add((test_uri, PMD.output, ult_tensile_strength))

            csv_filename = os.path.join(output_dir_csv, sample_id + "_data.csv")
            with open(csv_filename, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["Force(N)", "Elongation(mm)"])  # header
                for point in data["data"]:
                    writer.writerow([point["N"], point["mm"]])

            csv_node = EX[sample_id+"_csv_data"]
            g.add((csv_node, RDF.type, CSVW.Table))  # Data table
            g.add((test_uri, PMD.output, csv_node))  #the test has output of this data table
            g.add((csv_node, CSVW.url, Literal(os.path.basename(csv_filename))))


#Serializing in jsonld and ttl
g.serialize(os.path.join(output_dir_jsonld, "annotated_all_tests.jsonld"), format="json-ld")
g.serialize(os.path.join(output_dir_ttl, "annotated_all_tests.ttl"), format="turtle")
